import datetime
import logging
from typing import Any, Dict, Optional

from . import config as settings
from .contracts import GlassfishServiceContract
from .models import UsageData
from ..ui.service_actions import CheckView


class GlassfishUsageMonitor:
    async def check_services(self, service: GlassfishServiceContract) -> None:
        """Verifica o timeout dos serviços e envia lembretes/libera automaticamente"""
        try:
            logging.info("Iniciando verificação de timeout de serviços Glassfish")

            servicos_config = service.load_services()
            if not servicos_config:
                logging.info("Nenhum serviço encontrado para verificar")
                return

            agora = datetime.datetime.now()
            alteracoes_servicos = {}
            servicos_verificados = 0
            servicos_liberados = 0

            for servico_id, config in servicos_config.items():

                if config.get("status") != "em uso" or "usage_data" not in config:
                    continue

                servicos_verificados += 1

                try:

                    usage_data_dict = config["usage_data"]
                    dados_uso_original = dict(usage_data_dict)
                    usuario_original = config.get("usuario")
                    ultimo_uso = datetime.datetime.fromisoformat(usage_data_dict["timestamp"])
                    user_id = usage_data_dict.get("user_id")

                    horas_em_uso = (agora - ultimo_uso).total_seconds() / 3600

                    ultima_verificacao = None
                    horas_desde_verificacao = horas_em_uso
                    if usage_data_dict.get("last_check"):
                        try:
                            ultima_verificacao = datetime.datetime.fromisoformat(usage_data_dict["last_check"])
                            horas_desde_verificacao = (agora - ultima_verificacao).total_seconds() / 3600
                        except (ValueError, TypeError) as e:
                            logging.error(f"Erro ao processar última verificação: {str(e)}")

                    ultimo_lembrete = None
                    horas_desde_lembrete = horas_em_uso
                    if usage_data_dict.get("last_reminder"):
                        try:
                            ultimo_lembrete = datetime.datetime.fromisoformat(usage_data_dict["last_reminder"])
                            horas_desde_lembrete = (agora - ultimo_lembrete).total_seconds() / 3600
                        except (ValueError, TypeError) as e:
                            logging.error(f"Erro ao processar último lembrete: {str(e)}")

                    extension_count = int(usage_data_dict.get("extension_count", 0))

                    logging.info(f"Serviço {servico_id} em uso por {config['usuario']} há {horas_em_uso:.1f} horas")

                    deve_liberar = False
                    motivo_liberacao = ""

                    if horas_desde_verificacao > service.tempo_maximo_uso:
                        segundos_verificacao = horas_desde_verificacao * 3600
                        verificacao_horas = int(segundos_verificacao / 3600)
                        verificacao_minutos = int((segundos_verificacao % 3600) / 60)
                        verificacao_formatado = f"{verificacao_horas} horas e {verificacao_minutos} minutos"

                        deve_liberar = True
                        motivo_liberacao = f"após {verificacao_formatado} sem verificação"
                    elif ultimo_lembrete and not ultima_verificacao:

                        if horas_desde_lembrete > service.lembrete_intervalo:
                            segundos_lembrete = horas_desde_lembrete * 3600
                            lembrete_horas = int(segundos_lembrete / 3600)
                            lembrete_minutos = int((segundos_lembrete % 3600) / 60)
                            lembrete_formatado = f"{lembrete_horas} horas e {lembrete_minutos} minutos"

                            deve_liberar = True
                            motivo_liberacao = f"após {lembrete_formatado} sem resposta ao lembrete"
                    elif ultimo_lembrete and ultima_verificacao:

                        if ultimo_lembrete > ultima_verificacao and horas_desde_lembrete > service.lembrete_intervalo:
                            segundos_lembrete = horas_desde_lembrete * 3600
                            lembrete_horas = int(segundos_lembrete / 3600)
                            lembrete_minutos = int((segundos_lembrete % 3600) / 60)
                            lembrete_formatado = f"{lembrete_horas} horas e {lembrete_minutos} minutos"

                            deve_liberar = True
                            motivo_liberacao = f"após {lembrete_formatado} sem resposta ao lembrete"

                    if deve_liberar:

                        await self._liberar_servico_automaticamente(service, servico_id, config, motivo_liberacao, user_id)
                        alteracoes_servicos[servico_id] = {
                            "tipo": "liberar",
                            "dados_uso": dados_uso_original,
                            "usuario": usuario_original,
                            "tem_notificacao": "notificacao_timeout" in config,
                            "notificacao": config.get("notificacao_timeout"),
                        }
                        servicos_liberados += 1
                    else:

                        if await self._verificar_enviar_lembrete(service, servico_id, config, agora, horas_desde_lembrete, user_id, extension_count):
                            alteracoes_servicos[servico_id] = {
                                "tipo": "lembrete",
                                "dados_uso": dados_uso_original,
                                "usuario": usuario_original,
                                "dados_uso_atualizados": dict(config["usage_data"]),
                            }

                except Exception as e:
                    logging.error(f"Erro ao processar verificação para o serviço {servico_id}: {str(e)}")

            if servicos_verificados > 0:
                logging.info(f"Verificação concluída: {servicos_verificados} serviços verificados, {servicos_liberados} liberados")

            if alteracoes_servicos:
                def aplicar_alteracoes(services):
                    atualizados = 0
                    for service_id, alteracao in alteracoes_servicos.items():
                        service = services.get(service_id)
                        if service:
                            dados_uso = service.get("usage_data", {})
                        else:
                            dados_uso = {}
                        dados_originais = alteracao["dados_uso"]
                        if (
                            not service
                            or service.get("status") != "em uso"
                            or service.get("usuario") != alteracao["usuario"]
                            or dados_uso != dados_originais
                        ):
                            continue

                        if alteracao["tipo"] == "liberar":
                            service["status"] = "disponível"
                            service["usuario"] = None
                            service.pop("usage_data", None)
                            if alteracao["tem_notificacao"]:
                                service["notificacao_timeout"] = alteracao["notificacao"]
                            else:
                                service.pop("notificacao_timeout", None)
                        else:
                            service["usage_data"] = alteracao["dados_uso_atualizados"]
                        atualizados += 1

                    return atualizados > 0, atualizados

                saved, atualizados = await service.update_services(aplicar_alteracoes)
                if not saved:
                    logging.error("Não foi possível persistir as alterações da verificação Glassfish")
                elif atualizados:

                    await service.refresh_persistent_message()

        except Exception as e:
            logging.error(f"Erro geral na verificação de timeout: {str(e)}")

    async def _liberar_servico_automaticamente(
        self,
        service: GlassfishServiceContract,
        servico_id: str,
        config: Dict[str, Any],
        motivo: str,
        user_id: Optional[int],
    ) -> None:
        """Libera um serviço automaticamente e notifica o usuário"""
        try:
            logging.warning(f"Timeout automático para o serviço {servico_id} - {config['nome']} {motivo}")

            if "usage_data" in config:
                usage_data_dict = config["usage_data"]
                ultimo_uso = datetime.datetime.fromisoformat(usage_data_dict["timestamp"])
                segundos_em_uso = (datetime.datetime.now() - ultimo_uso).total_seconds()
                horas_formatadas = int(segundos_em_uso / 3600)
                minutos_formatados = int((segundos_em_uso % 3600) / 60)
                tempo_uso = f"{horas_formatadas} horas e {minutos_formatados} minutos"
            else:
                tempo_uso = "tempo indeterminado"

            channel = service.bot.get_channel(settings.LOGS_CHANNEL_ID)
            if channel:
                await channel.send(
                    f"⏰ **Timeout Automático**: O serviço **{config['nome']}** foi liberado automaticamente {motivo}. " +
                    f"Estava sendo usado por **{config['usuario']}** por {tempo_uso}."
                )

            ja_notificado = config.get("notificacao_timeout", False)

            if not ja_notificado and user_id:
                try:
                    user = await service.bot.fetch_user(int(user_id))
                    await user.send(
                        f"⚠️ **Aviso de Desconexão do Glassfish**\n" +
                        f"Você foi desconectado automaticamente do serviço **{config['nome']}** {motivo}.\n" +
                        f"Se ainda precisar usar este serviço, por favor solicite-o novamente."
                    )

                    config["notificacao_timeout"] = True
                except Exception as dm_error:
                    logging.error(f"Erro ao enviar DM para o usuário {user_id}: {str(dm_error)}")

            config["status"] = "disponível"
            config["usuario"] = None
            if "usage_data" in config:
                del config["usage_data"]

        except Exception as e:
            logging.error(f"Erro ao liberar serviço automaticamente {servico_id}: {str(e)}")

    async def _verificar_enviar_lembrete(
        self,
        service: GlassfishServiceContract,
        servico_id: str,
        config: Dict[str, Any],
        agora: datetime.datetime,
        horas_desde_lembrete: float,
        user_id: Optional[int],
        extension_count: int,
    ) -> bool:
        """Verifica se deve enviar lembrete e o envia se necessário"""
        try:

            if horas_desde_lembrete >= service.lembrete_intervalo and user_id:

                janela_lembrete = horas_desde_lembrete - service.lembrete_intervalo

                if janela_lembrete < 0.25:
                    try:
                        user = await service.bot.fetch_user(int(user_id))

                        usage_data_dict = config["usage_data"]
                        logging.info(f"Processando lembrete - usage_data_dict carregado: {usage_data_dict.get('timestamp', 'N/A')}")

                        ultimo_uso = datetime.datetime.fromisoformat(usage_data_dict["timestamp"])
                        segundos_em_uso = (agora - ultimo_uso).total_seconds()
                        horas_formatadas = int(segundos_em_uso / 3600)
                        minutos_formatados = int((segundos_em_uso % 3600) / 60)
                        tempo_formatado = f"{horas_formatadas} horas e {minutos_formatados} minutos"

                        logging.info(f"Tempo formatado calculado: {tempo_formatado}")

                        # Evita reenviar lembretes se o envio da DM falhar.
                        usage_data = UsageData.from_dict(usage_data_dict)
                        usage_data.update_reminder()
                        config["usage_data"] = usage_data.to_dict()

                        logging.info(f"Timestamp de lembrete atualizado para {config['usuario']} (ID: {user_id}) sobre o serviço {servico_id}")

                        view = CheckView(servico_id, service)

                        info_extensoes = ""
                        if extension_count >= service.max_extensoes:
                            info_extensoes = f"\n⚠️ **Atenção**: Você já utilizou todas as {extension_count}/{service.max_extensoes} extensões permitidas."
                        else:
                            info_extensoes = f"\n📝 Você já utilizou {extension_count}/{service.max_extensoes} extensões de tempo."

                        await user.send(
                            f"⚠️ **Lembrete de uso do Glassfish**\n" +
                            f"Você está usando o serviço **{config['nome']}** há {tempo_formatado}.\n" +
                            f"Por favor, confirme se ainda está utilizando este serviço ou libere-o se não estiver mais usando." +
                            info_extensoes,
                            view=view
                        )

                        logging.info(f"Lembrete enviado para {config['usuario']} (ID: {user_id}) sobre o serviço {servico_id}")

                        return True

                    except Exception as e:
                        logging.error(f"Erro ao enviar lembrete para o usuário {user_id}: {str(e)}")

            return False
        except Exception as e:
            logging.error(f"Erro ao verificar envio de lembrete: {str(e)}")
            return False
