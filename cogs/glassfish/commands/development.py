import datetime
import logging

import discord

from .base import GlassfishCommandBase
from ..ui.tests import TestarLembreteView

class GlassfishDevelopmentCommands(GlassfishCommandBase):
    async def cmd_testar_lembrete_glassfish(self, interaction: discord.Interaction, simular_tempo: int = 3):
        """Envia um lembrete de teste para um serviço específico"""
        if not self._tem_permissao_ti(interaction.user):
            await interaction.response.send_message(
                "❌ Apenas usuários com cargo de TI podem executar este comando.",
                ephemeral=True
            )
            return

        try:
            servicos_config = self.service.load_services()
            view = TestarLembreteView(self.service, servicos_config, simular_tempo)
            await interaction.response.send_message(
                "**Selecione o serviço para testar o lembrete:**\n" +
                "Apenas serviços em uso são mostrados.",
                view=view,
                ephemeral=True
            )

        except Exception as e:
            logging.error(f"Erro ao iniciar teste de lembrete: {str(e)}")
            await interaction.response.send_message(
                f"❌ Ocorreu um erro ao iniciar o teste: {str(e)}",
                ephemeral=True
            )

    async def cmd_modo_desenvolvimento_glassfish(self, interaction: discord.Interaction, ativar: bool):
        """Ativa/desativa o modo de desenvolvimento para testes"""
        if not self._tem_permissao_ti(interaction.user):
            await interaction.response.send_message(
                "❌ Apenas usuários com cargo de TI podem usar este comando.",
                ephemeral=True
            )
            return

        try:
            from ..core.config import load_config, save_config
            config = load_config()

            if "desenvolvimento" not in config:
                config["desenvolvimento"] = {}

            config["desenvolvimento"]["ativo"] = ativar

            if ativar:
                config["timeout"]["tempo_maximo_uso"] = 1
                config["timeout"]["verificar_intervalo"] = 1
                config["timeout"]["lembrete_intervalo"] = 1
                config["timeout"]["max_extensoes"] = 2

                status = "✅ **ATIVADO**"
                detalhes = (
                    "- Tempo máximo de uso: **1 hora**\n"
                    "- Verificação: **1 minuto**\n"
                    "- Lembretes: **1 hora**\n"
                    "- Máximo extensões: **2**"
                )
            else:
                config["timeout"]["tempo_maximo_uso"] = 24
                config["timeout"]["verificar_intervalo"] = 15
                config["timeout"]["lembrete_intervalo"] = 2
                config["timeout"]["max_extensoes"] = 3

                status = "❌ **DESATIVADO**"
                detalhes = (
                    "- Tempo máximo de uso: **24 horas**\n"
                    "- Verificação: **15 minutos**\n"
                    "- Lembretes: **2 horas**\n"
                    "- Máximo extensões: **3**"
                )

            if save_config(config):
                self.service.reload_config()

                await interaction.response.send_message(
                    f"🔧 **Modo de Desenvolvimento** {status}\n\n"
                    f"**Configurações aplicadas:**\n{detalhes}\n\n"
                    f"⚠️ **Nota**: As alterações são aplicadas imediatamente.",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "❌ Erro ao salvar configurações de desenvolvimento.",
                    ephemeral=True
                )

        except Exception as e:
            logging.error(f"Erro ao configurar modo de desenvolvimento: {str(e)}")
            await interaction.response.send_message(
                f"❌ Erro ao configurar modo de desenvolvimento: {str(e)}",
                ephemeral=True
            )

    async def cmd_simular_tempo_glassfish(self, interaction: discord.Interaction, servico_id: str, horas_atras: int):
        """Simula que um serviço está em uso há X horas (apenas desenvolvimento)"""
        if not self._tem_permissao_ti(interaction.user):
            await interaction.response.send_message(
                "❌ Apenas usuários com cargo de TI podem usar este comando.",
                ephemeral=True
            )
            return

        try:
            agora = datetime.datetime.now()
            tempo_simulado = agora - datetime.timedelta(hours=horas_atras)

            def simulate_service_time(config):
                if config.get("status") != "em uso":
                    return False, ("not_in_use", dict(config))

                usage_data = dict(config.get("usage_data", {}))
                usage_data.update({
                    "usuario": config["usuario"],
                    "user_id": usage_data.get("user_id", interaction.user.id),
                    "timestamp": tempo_simulado.isoformat(),
                    "last_check": None,
                    "last_reminder": None,
                    "extension_count": 0,
                })
                config["usage_data"] = usage_data
                return True, ("simulated", dict(config))

            saved, result, config = await self.service.update_service(servico_id, simulate_service_time)
            if result == "not_found" or not config:
                await interaction.response.send_message(
                    f"❌ Serviço '{servico_id}' não encontrado.",
                    ephemeral=True,
                )
                return
            if not saved:
                await interaction.response.send_message(
                    "❌ Não foi possível salvar a simulação. Tente novamente.",
                    ephemeral=True,
                )
                return
            result_type, config = result
            if result_type == "not_in_use":
                await interaction.response.send_message(
                    f"❌ O serviço '{servico_id}' não está em uso.",
                    ephemeral=True,
                )
                return

            await interaction.response.send_message(
                f"✅ **Simulação aplicada ao serviço '{config['nome']}'**\n"
                f"- Simula uso há: **{horas_atras} horas**\n"
                f"- Timestamp ajustado para: {tempo_simulado.strftime('%d/%m/%Y %H:%M:%S')}\n"
                f"- Verificações resetadas para forçar lembretes/timeouts\n\n"
                f"⚠️ Use `/verificacao_forcada_glassfish` para testar imediatamente.",
                ephemeral=True
            )

        except Exception as e:
            logging.error(f"Erro ao simular tempo: {str(e)}")
            await interaction.response.send_message(
                f"❌ Erro ao simular tempo: {str(e)}",
                ephemeral=True
            )

    async def cmd_status_servico_glassfish(self, interaction: discord.Interaction, servico_id: str):
        """Mostra o status detalhado de um serviço específico"""
        if not self._tem_permissao_ti(interaction.user):
            await interaction.response.send_message(
                "❌ Apenas usuários com cargo de TI podem usar este comando.",
                ephemeral=True
            )
            return

        try:
            servicos_config = self.service.load_services()

            if servico_id not in servicos_config:
                await interaction.response.send_message(
                    f"❌ Serviço '{servico_id}' não encontrado.\n\n" +
                    f"**Serviços disponíveis:**\n" +
                    "\n".join([f"• `{key}`: {config['nome']}" for key, config in servicos_config.items()]),
                    ephemeral=True
                )
                return

            config = servicos_config[servico_id]
            agora = datetime.datetime.now()

            if config.get("status") == "em uso":
                status = "🔴 **EM USO**"
            else:
                status = "🟢 **DISPONÍVEL**"
            usuario = config.get("usuario", "Nenhum")

            resposta = [
                f"📊 **Status Detalhado do Serviço**",
                f"**Nome:** {config['nome']}",
                f"**ID:** {servico_id}",
                f"**Status:** {status}",
                f"**Usuário:** {usuario}"
            ]

            if config.get("status") == "em uso" and "usage_data" in config:
                usage_data = config["usage_data"]

                try:
                    timestamp = datetime.datetime.fromisoformat(usage_data["timestamp"])
                    segundos_em_uso = (agora - timestamp).total_seconds()
                    horas_em_uso = int(segundos_em_uso / 3600)
                    minutos_em_uso = int((segundos_em_uso % 3600) / 60)
                    tempo_uso = f"{horas_em_uso} horas e {minutos_em_uso} minutos"

                    resposta.append(f"\n**⏱️ Detalhes de Uso:**")
                    resposta.append(f"• **Tempo em uso:** {tempo_uso}")
                    resposta.append(f"• **Início do uso:** {timestamp.strftime('%d/%m/%Y %H:%M:%S')}")
                    resposta.append(f"• **User ID:** {usage_data.get('user_id', 'N/A')}")
                    resposta.append(f"• **Extensões utilizadas:** {usage_data.get('extension_count', 0)}/{self.service.max_extensoes}")

                    if usage_data.get("last_check"):
                        last_check = datetime.datetime.fromisoformat(usage_data["last_check"])
                        segundos_desde_check = (agora - last_check).total_seconds()
                        horas_desde_check = int(segundos_desde_check / 3600)
                        minutos_desde_check = int((segundos_desde_check % 3600) / 60)
                        resposta.append(f"• **Última confirmação:** {last_check.strftime('%d/%m/%Y %H:%M:%S')} (há {horas_desde_check}h{minutos_desde_check}m)")
                    else:
                        resposta.append(f"• **Última confirmação:** Nunca confirmado")

                    if usage_data.get("last_reminder"):
                        last_reminder = datetime.datetime.fromisoformat(usage_data["last_reminder"])
                        segundos_desde_lembrete = (agora - last_reminder).total_seconds()
                        horas_desde_lembrete = int(segundos_desde_lembrete / 3600)
                        minutos_desde_lembrete = int((segundos_desde_lembrete % 3600) / 60)
                        resposta.append(f"• **Último lembrete:** {last_reminder.strftime('%d/%m/%Y %H:%M:%S')} (há {horas_desde_lembrete}h{minutos_desde_lembrete}m)")
                    else:
                        resposta.append(f"• **Último lembrete:** Nenhum lembrete enviado")

                    resposta.append(f"\n**🔮 Próximas Ações:**")

                    if usage_data.get("last_reminder"):
                        last_reminder = datetime.datetime.fromisoformat(usage_data["last_reminder"])
                        proximo_lembrete = last_reminder + datetime.timedelta(hours=self.service.lembrete_intervalo)
                        if proximo_lembrete > agora:
                            tempo_para_lembrete = (proximo_lembrete - agora).total_seconds()
                            horas_lembrete = int(tempo_para_lembrete / 3600)
                            minutos_lembrete = int((tempo_para_lembrete % 3600) / 60)
                            resposta.append(f"• **Próximo lembrete:** Em {horas_lembrete}h{minutos_lembrete}m")
                        else:
                            resposta.append(f"• **Próximo lembrete:** Agendado para a próxima verificação")
                    else:
                        tempo_para_primeiro_lembrete = self.service.lembrete_intervalo * 3600 - segundos_em_uso
                        if tempo_para_primeiro_lembrete > 0:
                            horas_lembrete = int(tempo_para_primeiro_lembrete / 3600)
                            minutos_lembrete = int((tempo_para_primeiro_lembrete % 3600) / 60)
                            resposta.append(f"• **Primeiro lembrete:** Em {horas_lembrete}h{minutos_lembrete}m")
                        else:
                            resposta.append(f"• **Primeiro lembrete:** Agendado para a próxima verificação")

                    if usage_data.get("last_check"):
                        last_check = datetime.datetime.fromisoformat(usage_data["last_check"])
                        timeout_automatico = last_check + datetime.timedelta(hours=self.service.tempo_maximo_uso)
                    else:
                        timeout_automatico = timestamp + datetime.timedelta(hours=self.service.tempo_maximo_uso)

                    if timeout_automatico > agora:
                        tempo_para_timeout = (timeout_automatico - agora).total_seconds()
                        horas_timeout = int(tempo_para_timeout / 3600)
                        minutos_timeout = int((tempo_para_timeout % 3600) / 60)
                        resposta.append(f"• **Timeout automático:** Em {horas_timeout}h{minutos_timeout}m")
                    else:
                        resposta.append(f"• **Timeout automático:** Agendado para a próxima verificação")

                except Exception as e:
                    logging.error(f"Erro ao processar dados de uso: {str(e)}")
                    resposta.append(f"\n❌ **Erro ao processar dados de uso:** {str(e)}")

            resposta.append(f"\n**🔐 Permissões:**")
            grupos_permitidos = config.get("grupos_permitidos", [])
            if grupos_permitidos:
                role_names = []
                for grupo_id in grupos_permitidos:
                    try:
                        role = interaction.guild.get_role(int(grupo_id))
                        if role:
                            role_names.append(role.name)
                        else:
                            role_names.append(f"Cargo não encontrado ({grupo_id})")
                    except (ValueError, TypeError):
                        role_names.append(f"ID inválido ({grupo_id})")

                resposta.append(f"• **Cargos permitidos:** {', '.join(role_names)}")
            else:
                resposta.append(f"• **Cargos permitidos:** Nenhum")

            await interaction.response.send_message("\n".join(resposta), ephemeral=True)

        except Exception as e:
            logging.error(f"Erro ao obter status do serviço: {str(e)}")
            await interaction.response.send_message(
                f"❌ Erro ao obter status do serviço: {str(e)}",
                ephemeral=True
            )

    async def cmd_testar_envio_lembrete_glassfish(self, interaction: discord.Interaction):
        """Testa o envio de lembrete direto (apenas desenvolvimento)"""
        if not self._tem_permissao_ti(interaction.user):
            await interaction.response.send_message(
                "❌ Apenas usuários com cargo de TI podem usar este comando.",
                ephemeral=True
            )
            return

        try:
            await interaction.response.send_message(
                "🧪 Testando envio de lembrete...",
                ephemeral=True
            )

            servicos_config = self.service.load_services()

            servico_em_uso = None
            for servico_id, config in servicos_config.items():
                if config.get("status") == "em uso":
                    servico_em_uso = (servico_id, config)
                    break

            if not servico_em_uso:
                await interaction.followup.send(
                    "❌ Nenhum serviço em uso encontrado para testar.",
                    ephemeral=True
                )
                return

            servico_id, config = servico_em_uso

            if "usage_data" not in config:
                await interaction.followup.send(
                    f"❌ Serviço {servico_id} não possui dados de uso.",
                    ephemeral=True
                )
                return

            usage_data = config["usage_data"]
            user_id = usage_data.get("user_id")

            if not user_id:
                await interaction.followup.send(
                    f"❌ Serviço {servico_id} não possui user_id válido.",
                    ephemeral=True
                )
                return

            try:
                agora = datetime.datetime.now()
                extension_count = usage_data.get("extension_count", 0)

                user = await self.bot.fetch_user(int(user_id))

                usage_data_dict = config["usage_data"]
                ultimo_uso = datetime.datetime.fromisoformat(usage_data_dict["timestamp"])
                segundos_em_uso = (agora - ultimo_uso).total_seconds()
                horas_formatadas = int(segundos_em_uso / 3600)
                minutos_formatados = int((segundos_em_uso % 3600) / 60)
                tempo_formatado = f"{horas_formatadas} horas e {minutos_formatados} minutos"

                info_extensoes = ""
                if extension_count >= self.service.max_extensoes:
                    info_extensoes = f"\n⚠️ **Atenção**: Você já utilizou todas as {extension_count}/{self.service.max_extensoes} extensões permitidas."
                else:
                    info_extensoes = f"\n📝 Você já utilizou {extension_count}/{self.service.max_extensoes} extensões de tempo."

                from ..ui.services import CheckView
                view = CheckView(servico_id, self.service)

                await user.send(
                    f"🧪 **TESTE - Lembrete de uso do Glassfish**\n" +
                    f"Você está usando o serviço **{config['nome']}** há {tempo_formatado}.\n" +
                    f"Por favor, confirme se ainda está utilizando este serviço ou libere-o se não estiver mais usando." +
                    info_extensoes,
                    view=view
                )

                await interaction.followup.send(
                    f"✅ **Teste bem-sucedido!**\n" +
                    f"Lembrete de teste enviado para <@{user_id}> sobre o serviço **{config['nome']}**.\n" +
                    f"Tempo formatado: {tempo_formatado}",
                    ephemeral=True
                )

            except Exception as e:
                await interaction.followup.send(
                    f"❌ **Erro no teste de lembrete:** {str(e)}\n" +
                    f"Serviço: {config['nome']}\n" +
                    f"User ID: {user_id}",
                    ephemeral=True
                )
                logging.error(f"Erro no teste de lembrete: {str(e)}")

        except Exception as e:
            logging.error(f"Erro geral no teste de lembrete: {str(e)}")
            try:
                await interaction.followup.send(
                    f"❌ Erro geral no teste: {str(e)}",
                    ephemeral=True
                )
            except discord.HTTPException as response_error:
                logging.warning(f"Não foi possível enviar a resposta do teste: {response_error}")
