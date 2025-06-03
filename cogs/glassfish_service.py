import discord
import json
import logging
import datetime
import asyncio
from typing import Dict, Any, Optional
from .glassfish_models import UsageData
from .glassfish_config import (
    CARGO_TI_ID,
    LOGS_CHANNEL_ID,
    PERSISTENT_CHANNEL_ID,
    TEMPO_MAXIMO_USO,
    VERIFICAR_INTERVALO,
    LEMBRETE_INTERVALO,
    MAX_EXTENSOES,
    load_config,
    save_config,
    reload_config
)
from .glassfish_ui import CheckView


class GlassfishService:
    def __init__(self, bot):
        self.bot = bot
        self.tempo_maximo_uso = TEMPO_MAXIMO_USO
        self.verificar_intervalo = VERIFICAR_INTERVALO
        self.lembrete_intervalo = LEMBRETE_INTERVALO
        self.max_extensoes = MAX_EXTENSOES
        self.services_file = "services.json"
        self.persistent_message = None
        
        # Carrega as configurações salvas, se existirem
        self._load_config_from_file()

    def _load_config_from_file(self):
        """Carrega as configurações do arquivo config.json"""
        try:
            config = load_config()
            
            if "timeout" in config:
                self.tempo_maximo_uso = config["timeout"].get("tempo_maximo_uso", self.tempo_maximo_uso)
                self.verificar_intervalo = config["timeout"].get("verificar_intervalo", self.verificar_intervalo)
                self.lembrete_intervalo = config["timeout"].get("lembrete_intervalo", self.lembrete_intervalo)
                self.max_extensoes = config["timeout"].get("max_extensoes", self.max_extensoes)
                
            logging.info("Configurações de serviço carregadas do arquivo config.json")
        except Exception as e:
            logging.error(f"Erro ao carregar configurações de serviço: {str(e)}")
            logging.info("Usando valores padrão para as configurações de serviço")

    def load_services(self) -> Dict[str, Any]:
        """Carrega os serviços do arquivo services.json"""
        try:
            with open(self.services_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logging.warning("Arquivo services.json não encontrado. Criando um novo.")
            return {}
        except json.JSONDecodeError as e:
            logging.error(f"Erro ao decodificar JSON do arquivo services.json: {str(e)}")
            return {}
        except Exception as e:
            logging.error(f"Erro ao carregar serviços: {str(e)}")
            return {}

    def save_services(self, services: Dict[str, Any]):
        """Salva os serviços no arquivo services.json"""
        try:
            with open(self.services_file, "w", encoding="utf-8") as f:
                json.dump(services, f, indent=4, ensure_ascii=False)
            logging.info("Serviços salvos com sucesso em services.json")
        except Exception as e:
            logging.error(f"Erro ao salvar serviços: {str(e)}")

    def reload_config(self):
        """Recarrega as configurações do arquivo config.json"""
        try:
            config = reload_config()
            self._load_config_from_file()
            return config
        except Exception as e:
            logging.error(f"Erro ao recarregar configurações: {str(e)}")
            return None

    def update_config(self, new_config: Dict[str, Any]):
        """Atualiza as configurações de timeout"""
        try:
            config = load_config()
            config.update(new_config)
            
            if save_config(config):
                self._load_config_from_file()
                return True
            return False
        except Exception as e:
            logging.error(f"Erro ao atualizar configurações: {str(e)}")
            return False

    def get_config(self) -> Dict[str, Any]:
        """Retorna as configurações atuais"""
        return {
            "timeout": {
                "tempo_maximo_uso": self.tempo_maximo_uso,
                "verificar_intervalo": self.verificar_intervalo,
                "lembrete_intervalo": self.lembrete_intervalo,
                "max_extensoes": self.max_extensoes
            }
        }

    async def check_services_loop(self):
        """Loop principal para verificação de timeout dos serviços"""
        while True:
            try:
                await self.check_services()
                await asyncio.sleep(self.verificar_intervalo * 60)  # Converte minutos para segundos
            except Exception as e:
                logging.error(f"Erro no loop de verificação de serviços: {str(e)}")
                await asyncio.sleep(60)  # Espera 1 minuto antes de tentar novamente

    async def check_services(self):
        """Verifica o timeout dos serviços e envia lembretes/libera automaticamente"""
        try:
            logging.info("Iniciando verificação de timeout de serviços Glassfish")
            
            servicos_config = self.load_services()
            if not servicos_config:
                logging.info("Nenhum serviço encontrado para verificar")
                return

            agora = datetime.datetime.now()
            alteracoes = False
            servicos_verificados = 0
            servicos_liberados = 0
            
            # Verifica cada serviço
            for servico_id, config in servicos_config.items():
                # Pula serviços disponíveis ou sem dados de uso
                if config.get("status") != "em uso" or "usage_data" not in config:
                    continue
                
                servicos_verificados += 1
                
                try:
                    # Converte os dados de uso
                    usage_data_dict = config["usage_data"]
                    ultimo_uso = datetime.datetime.fromisoformat(usage_data_dict["timestamp"])
                    user_id = usage_data_dict.get("user_id")
                    
                    # Calcula o tempo em uso
                    horas_em_uso = (agora - ultimo_uso).total_seconds() / 3600
                    
                    # Verifica último check se existir
                    ultima_verificacao = None
                    horas_desde_verificacao = horas_em_uso
                    if usage_data_dict.get("last_check"):
                        try:
                            ultima_verificacao = datetime.datetime.fromisoformat(usage_data_dict["last_check"])
                            horas_desde_verificacao = (agora - ultima_verificacao).total_seconds() / 3600
                        except (ValueError, TypeError) as e:
                            logging.error(f"Erro ao processar última verificação: {str(e)}")
                            
                    # Verifica último lembrete se existir
                    ultimo_lembrete = None
                    horas_desde_lembrete = horas_em_uso
                    if usage_data_dict.get("last_reminder"):
                        try:
                            ultimo_lembrete = datetime.datetime.fromisoformat(usage_data_dict["last_reminder"])
                            horas_desde_lembrete = (agora - ultimo_lembrete).total_seconds() / 3600
                        except (ValueError, TypeError) as e:
                            logging.error(f"Erro ao processar último lembrete: {str(e)}")
                    
                    # Verifica o número de extensões utilizadas
                    extension_count = int(usage_data_dict.get("extension_count", 0))
                    
                    logging.info(f"Serviço {servico_id} em uso por {config['usuario']} há {horas_em_uso:.1f} horas")
                    
                    # Determina se deve liberar automaticamente
                    deve_liberar = False
                    motivo_liberacao = ""
                    
                    if horas_desde_verificacao > self.tempo_maximo_uso:
                        segundos_verificacao = horas_desde_verificacao * 3600
                        verificacao_horas = int(segundos_verificacao / 3600)
                        verificacao_minutos = int((segundos_verificacao % 3600) / 60)
                        verificacao_formatado = f"{verificacao_horas} horas e {verificacao_minutos} minutos"
                        
                        deve_liberar = True
                        motivo_liberacao = f"após {verificacao_formatado} sem verificação"
                    elif ultimo_lembrete and not ultima_verificacao:
                        # Se há lembrete mas nunca houve verificação
                        if horas_desde_lembrete > self.lembrete_intervalo:
                            segundos_lembrete = horas_desde_lembrete * 3600
                            lembrete_horas = int(segundos_lembrete / 3600)
                            lembrete_minutos = int((segundos_lembrete % 3600) / 60)
                            lembrete_formatado = f"{lembrete_horas} horas e {lembrete_minutos} minutos"
                            
                            deve_liberar = True
                            motivo_liberacao = f"após {lembrete_formatado} sem resposta ao lembrete"
                    elif ultimo_lembrete and ultima_verificacao:
                        # Se o último lembrete é mais recente que a última verificação
                        if ultimo_lembrete > ultima_verificacao and horas_desde_lembrete > self.lembrete_intervalo:
                            segundos_lembrete = horas_desde_lembrete * 3600
                            lembrete_horas = int(segundos_lembrete / 3600)
                            lembrete_minutos = int((segundos_lembrete % 3600) / 60)
                            lembrete_formatado = f"{lembrete_horas} horas e {lembrete_minutos} minutos"
                            
                            deve_liberar = True
                            motivo_liberacao = f"após {lembrete_formatado} sem resposta ao lembrete"
                    
                    if deve_liberar:
                        # Libera o serviço automaticamente
                        await self._liberar_servico_automaticamente(servico_id, config, motivo_liberacao, user_id)
                        alteracoes = True
                        servicos_liberados += 1
                    else:
                        # Verifica se deve enviar lembrete
                        if await self._verificar_enviar_lembrete(servico_id, config, agora, horas_desde_lembrete, user_id, extension_count):
                            alteracoes = True
                
                except Exception as e:
                    logging.error(f"Erro ao processar verificação para o serviço {servico_id}: {str(e)}")
            
            # Log do resultado da verificação
            if servicos_verificados > 0:
                logging.info(f"Verificação concluída: {servicos_verificados} serviços verificados, {servicos_liberados} liberados")
            
            # Salva as alterações se houver mudanças
            if alteracoes:
                self.save_services(servicos_config)
                # Atualiza a mensagem persistente
                await self._refresh_persistent_message()
                
        except Exception as e:
            logging.error(f"Erro geral na verificação de timeout: {str(e)}")

    async def _liberar_servico_automaticamente(self, servico_id: str, config: Dict[str, Any], motivo: str, user_id: Optional[int]):
        """Libera um serviço automaticamente e notifica o usuário"""
        try:
            logging.warning(f"Timeout automático para o serviço {servico_id} - {config['nome']} {motivo}")
            
            # Calcula tempo de uso para exibição
            if "usage_data" in config:
                usage_data_dict = config["usage_data"]
                ultimo_uso = datetime.datetime.fromisoformat(usage_data_dict["timestamp"])
                segundos_em_uso = (datetime.datetime.now() - ultimo_uso).total_seconds()
                horas_formatadas = int(segundos_em_uso / 3600)
                minutos_formatados = int((segundos_em_uso % 3600) / 60)
                tempo_uso = f"{horas_formatadas} horas e {minutos_formatados} minutos"
            else:
                tempo_uso = "tempo indeterminado"
            
            # Notifica no canal de logs
            channel = self.bot.get_channel(LOGS_CHANNEL_ID)
            if channel:
                await channel.send(
                    f"⏰ **Timeout Automático**: O serviço **{config['nome']}** foi liberado automaticamente {motivo}. " +
                    f"Estava sendo usado por **{config['usuario']}** por {tempo_uso}."
                )
            
            # Verifica se o usuário já foi notificado
            ja_notificado = config.get("notificacao_timeout", False)
            
            # Tenta notificar o usuário por DM sobre a desconexão somente se ele ainda não foi notificado
            if not ja_notificado and user_id:
                try:
                    user = await self.bot.fetch_user(int(user_id))
                    await user.send(
                        f"⚠️ **Aviso de Desconexão do Glassfish**\n" +
                        f"Você foi desconectado automaticamente do serviço **{config['nome']}** {motivo}.\n" +
                        f"Se ainda precisar usar este serviço, por favor solicite-o novamente."
                    )
                    # Marca como notificado
                    config["notificacao_timeout"] = True
                except Exception as dm_error:
                    logging.error(f"Erro ao enviar DM para o usuário {user_id}: {str(dm_error)}")
            
            # Limpa completamente os dados do usuário e de uso
            config["status"] = "disponível"
            config["usuario"] = None
            if "usage_data" in config:
                del config["usage_data"]
                
        except Exception as e:
            logging.error(f"Erro ao liberar serviço automaticamente {servico_id}: {str(e)}")

    async def _verificar_enviar_lembrete(self, servico_id: str, config: Dict[str, Any], agora: datetime.datetime, 
                                       horas_desde_lembrete: float, user_id: Optional[int], extension_count: int) -> bool:
        """Verifica se deve enviar lembrete e o envia se necessário"""
        try:
            # Envia lembretes para verificação a cada lembrete_intervalo horas
            if horas_desde_lembrete >= self.lembrete_intervalo and user_id:
                # Evita enviar lembretes em cascata - só envia se o tempo desde o último lembrete
                # está dentro de uma janela de 15 minutos após completar o intervalo exato
                janela_lembrete = horas_desde_lembrete - self.lembrete_intervalo
                
                # Só envia se estiver dentro da primeira janela de 15 minutos após o intervalo
                if janela_lembrete < 0.25:  # 15 minutos em horas
                    try:
                        user = await self.bot.fetch_user(int(user_id))
                        
                        # Calcula tempo em horas e minutos para exibição mais precisa ANTES de atualizar os dados
                        usage_data_dict = config["usage_data"]  # Assegura que a variável existe
                        logging.info(f"Processando lembrete - usage_data_dict carregado: {usage_data_dict.get('timestamp', 'N/A')}")
                        
                        ultimo_uso = datetime.datetime.fromisoformat(usage_data_dict["timestamp"])
                        segundos_em_uso = (agora - ultimo_uso).total_seconds()
                        horas_formatadas = int(segundos_em_uso / 3600)
                        minutos_formatados = int((segundos_em_uso % 3600) / 60)
                        tempo_formatado = f"{horas_formatadas} horas e {minutos_formatados} minutos"
                        
                        logging.info(f"Tempo formatado calculado: {tempo_formatado}")
                        
                        # Atualiza o timestamp do último lembrete ANTES de criar o CheckView
                        usage_data = UsageData.from_dict(usage_data_dict)
                        usage_data.update_reminder()
                        config["usage_data"] = usage_data.to_dict()
                        
                        logging.info(f"Timestamp de lembrete atualizado para {config['usuario']} (ID: {user_id}) sobre o serviço {servico_id}")
                        
                        # Carrega serviços atualizados para o CheckView
                        servicos_config = self.load_services()
                        view = CheckView(servico_id, servicos_config)
                        
                        # Verifica se o usuário atingiu o limite de extensões
                        info_extensoes = ""
                        if extension_count >= self.max_extensoes:
                            info_extensoes = f"\n⚠️ **Atenção**: Você já utilizou todas as {extension_count}/{self.max_extensoes} extensões permitidas."
                        else:
                            info_extensoes = f"\n📝 Você já utilizou {extension_count}/{self.max_extensoes} extensões de tempo."
                        
                        # Envia mensagem para o usuário
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

    async def _refresh_persistent_message(self):
        """Atualiza a mensagem persistente se existir"""
        try:
            # Importa aqui para evitar import circular
            from .glassfish_ui import ServiceDropdown
            
            channel = self.bot.get_channel(PERSISTENT_CHANNEL_ID)
            if not channel:
                logging.error(f"Canal {PERSISTENT_CHANNEL_ID} não encontrado")
                return

            if self.persistent_message:
                servicos_config = self.load_services()
                view = ServiceDropdown(None, servicos_config, check_permissions=False)
                try:
                    await self.persistent_message.edit(view=view)
                    logging.info("Mensagem persistente do Glassfish atualizada")
                except discord.NotFound:
                    logging.warning("Mensagem persistente não encontrada, será recriada")
                    self.persistent_message = None
                except Exception as e:
                    logging.error(f"Erro ao atualizar mensagem persistente: {str(e)}")
        except Exception as e:
            logging.error(f"Erro ao atualizar mensagem persistente: {str(e)}")

    async def setup_persistent_message(self):
        """Configura ou atualiza a mensagem persistente no canal específico"""
        try:
            # Importa aqui para evitar import circular
            from .glassfish_ui import ServiceDropdown
            
            channel = self.bot.get_channel(PERSISTENT_CHANNEL_ID)
            if not channel:
                logging.error(f"Canal {PERSISTENT_CHANNEL_ID} não encontrado")
                return

            # Procura por mensagem existente do bot
            async for message in channel.history(limit=100):
                if message.author == self.bot.user and "**Serviços Glassfish**" in message.content:
                    self.persistent_message = message
                    break

            servicos_config = self.load_services()
            view = ServiceDropdown(None, servicos_config, check_permissions=False)
            message_content = (
                "**Serviços Glassfish**\n"
                "Selecione um serviço abaixo para gerenciá-lo.\n"
                "🟢 = Disponível | 🔴 = Em uso\n"
                f"⚠️ Serviços em uso por mais de {self.tempo_maximo_uso} horas sem confirmação serão liberados automaticamente."
            )

            if self.persistent_message:
                await self.persistent_message.edit(content=message_content, view=view)
            else:
                self.persistent_message = await channel.send(message_content, view=view)
            
            logging.info("Mensagem persistente do Glassfish configurada/atualizada")
        except Exception as e:
            logging.error(f"Erro ao configurar mensagem persistente: {str(e)}")

    def _tem_permissao_ti(self, user) -> bool:
        """Verifica se o usuário tem permissão de TI"""
        return any(role.id == CARGO_TI_ID for role in user.roles) 