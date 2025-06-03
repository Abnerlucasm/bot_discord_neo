import discord
from discord.ext import commands
from discord import app_commands
import logging
import json
import datetime
from typing import Dict, Any, Optional
from .glassfish_config import CARGO_TI_ID, LOGS_CHANNEL_ID, DEVELOPMENT_MODE
from .glassfish_ui import ServiceDropdown
from .glassfish_admin_ui import (
    GlassfishAddModal, 
    GlassfishSelectView,
    TestarLembreteView
)


class GlassfishCommands:
    def __init__(self, bot, service):
        self.bot = bot
        self.service = service

    def _tem_permissao_ti(self, user) -> bool:
        """Verifica se o usuário tem permissão de TI"""
        return any(role.id == CARGO_TI_ID for role in user.roles)

    async def cmd_glassfish(self, interaction: discord.Interaction):
        """Lista os serviços disponíveis"""
        try:
            logging.info(f"{interaction.user.name} executou o comando /glassfish")
            
            if not interaction.user.roles:
                await interaction.response.send_message(
                    "Você precisa ter um cargo para acessar os serviços.",
                    ephemeral=True
                )
                return
                
            user_roles = [role.id for role in interaction.user.roles]
            logging.info(f"Cargos do usuário {interaction.user.name}: {user_roles}")
            
            servicos_config = self.service.load_services()
            
            # Verificar permissões para cada serviço
            servicos_permitidos = {}
            for key, config in servicos_config.items():
                grupos_permitidos = [int(x) for x in config["grupos_permitidos"]]
                logging.info(f"Serviço {key} - Grupos permitidos: {grupos_permitidos}")
                
                if any(role in grupos_permitidos for role in user_roles):
                    servicos_permitidos[key] = config
                    logging.info(f"Usuário tem permissão para o serviço {key}")
            
            if not servicos_permitidos:
                await interaction.response.send_message(
                    "Você não tem permissão para acessar nenhum serviço.",
                    ephemeral=True
                )
                logging.info(f"{interaction.user.name} tentou acessar serviços sem permissão")
                return
            
            view = ServiceDropdown(user_roles, servicos_config)
            await interaction.response.send_message(
                "**Serviços disponíveis:** Selecione uma opção abaixo:", 
                view=view,
                ephemeral=True
            )
            
        except Exception as e:
            logging.error(f"Erro ao executar comando glassfish: {str(e)}")
            await interaction.response.send_message(
                "Ocorreu um erro ao listar os serviços. Tente novamente mais tarde.",
                ephemeral=True
            )

    async def cmd_recarregar_config_glassfish(self, interaction: discord.Interaction):
        """Recarrega as configurações do arquivo config.json"""
        if not self._tem_permissao_ti(interaction.user):
            await interaction.response.send_message(
                "Apenas o setor de TI pode recarregar as configurações.",
                ephemeral=True
            )
            return
            
        config = self.service.reload_config()
        
        if config:
            await interaction.response.send_message(
                f"✅ Configurações recarregadas com sucesso:\n" +
                f"- Tempo máximo de uso: {self.service.tempo_maximo_uso} horas\n" +
                f"- Intervalo de lembretes: {self.service.lembrete_intervalo} horas\n" +
                f"- Verificação de serviços: a cada {self.service.verificar_intervalo} minutos",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "❌ Ocorreu um erro ao recarregar as configurações. Verifique os logs para mais detalhes.",
                ephemeral=True
            )

    async def cmd_verificacao_forcada_glassfish(self, interaction: discord.Interaction):
        """Força a verificação de timeout dos serviços"""
        if not self._tem_permissao_ti(interaction.user):
            await interaction.response.send_message(
                "Apenas o setor de TI pode executar este comando.",
                ephemeral=True
            )
            return
        
        await interaction.response.send_message(
            "Iniciando verificação forçada dos serviços Glassfish...",
            ephemeral=True
        )
        
        try:
            await self.service.check_services()
            await interaction.followup.send(
                "Verificação concluída com sucesso!",
                ephemeral=True
            )
        except Exception as e:
            logging.error(f"Erro na verificação forçada: {str(e)}")
            await interaction.followup.send(
                f"Erro ao verificar os serviços: {str(e)}",
                ephemeral=True
            )

    async def cmd_configurar_timeout_glassfish(
        self, 
        interaction: discord.Interaction, 
        horas: Optional[int] = None,
        intervalo_verificacao: Optional[int] = None,
        intervalo_lembrete: Optional[int] = None,
        max_extensoes: Optional[int] = None
    ):
        """Configura o timeout para serviços Glassfish"""
        if not self._tem_permissao_ti(interaction.user):
            await interaction.response.send_message(
                "Você não tem permissão para usar este comando.", 
                ephemeral=True
            )
            return

        # Verifica se pelo menos um parâmetro foi fornecido
        if all(param is None for param in [horas, intervalo_verificacao, intervalo_lembrete, max_extensoes]):
            config = self.service.get_config()["timeout"]
            await interaction.response.send_message(
                f"Configuração atual:\n"
                f"⏱️ Tempo máximo de uso: **{config['tempo_maximo_uso']}** horas\n"
                f"🔄 Intervalo de verificação: **{config['verificar_intervalo']}** minutos\n"
                f"🔔 Intervalo de lembretes: **{config['lembrete_intervalo']}** horas\n"
                f"🔢 Máximo de extensões: **{config['max_extensoes']}**\n"
                f"Forneça pelo menos um parâmetro para alterar as configurações.",
                ephemeral=True
            )
            return

        # Prepara a nova configuração
        new_config = {"timeout": {}}
        
        if horas is not None:
            if not (1 <= horas <= 168):
                await interaction.response.send_message(
                    "Horas deve estar entre 1 e 168.", 
                    ephemeral=True
                )
                return
            new_config["timeout"]["tempo_maximo_uso"] = horas
            
        if intervalo_verificacao is not None:
            if not (5 <= intervalo_verificacao <= 60):
                await interaction.response.send_message(
                    "Intervalo de verificação deve estar entre 5 e 60 minutos.", 
                    ephemeral=True
                )
                return
            new_config["timeout"]["verificar_intervalo"] = intervalo_verificacao
            
        if intervalo_lembrete is not None:
            if not (1 <= intervalo_lembrete <= 12):
                await interaction.response.send_message(
                    "Intervalo de lembrete deve estar entre 1 e 12 horas.", 
                    ephemeral=True
                )
                return
            new_config["timeout"]["lembrete_intervalo"] = intervalo_lembrete
            
        if max_extensoes is not None:
            if not (1 <= max_extensoes <= 10):
                await interaction.response.send_message(
                    "Máximo de extensões deve estar entre 1 e 10.", 
                    ephemeral=True
                )
                return
            new_config["timeout"]["max_extensoes"] = max_extensoes

        # Atualiza as configurações
        if self.service.update_config(new_config):
            config = self.service.get_config()["timeout"]
            await interaction.response.send_message(
                f"✅ Configurações atualizadas:\n"
                f"⏱️ Tempo máximo de uso: **{config['tempo_maximo_uso']}** horas\n"
                f"🔄 Intervalo de verificação: **{config['verificar_intervalo']}** minutos\n"
                f"🔔 Intervalo de lembretes: **{config['lembrete_intervalo']}** horas\n"
                f"🔢 Máximo de extensões: **{config['max_extensoes']}**",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "❌ Erro ao salvar configurações.",
                ephemeral=True
            )

    async def cmd_obter_timeout_glassfish(self, interaction: discord.Interaction):
        """Mostra as configurações atuais de timeout"""
        config = self.service.get_config()["timeout"]
        await interaction.response.send_message(
            f"**Configurações atuais de timeout dos serviços Glassfish:**\n" +
            f"- Tempo máximo sem confirmação: {config['tempo_maximo_uso']} horas\n" +
            f"- Intervalo de lembretes: {config['lembrete_intervalo']} horas\n" +
            f"- Verificação de serviços: a cada {config['verificar_intervalo']} minutos\n" +
            f"- Limite de extensões permitidas: {config['max_extensoes']} vezes",
            ephemeral=True
        )

    async def cmd_relatorio_glassfish(self, interaction: discord.Interaction):
        """Gera um relatório detalhado de uso dos serviços"""
        if not self._tem_permissao_ti(interaction.user):
            await interaction.response.send_message(
                "Apenas o setor de TI pode gerar relatórios dos serviços.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            servicos_config = self.service.load_services()
            
            # Cria listas para organizar os dados
            em_uso = []
            notificados = []
            agora = datetime.datetime.now()
            
            # Processa serviços em uso
            for servico_id, config in servicos_config.items():
                if config.get("status") == "em uso":
                    tempo_uso = "Tempo desconhecido"
                    ultima_confirmacao = "Nunca confirmado"
                    ultimo_lembrete = "Nenhum lembrete enviado"
                    
                    if "usage_data" in config:
                        try:
                            usage_data = config["usage_data"]
                            
                            # Calcula tempo em uso
                            timestamp = datetime.datetime.fromisoformat(usage_data["timestamp"])
                            segundos_em_uso = (agora - timestamp).total_seconds()
                            horas_em_uso = segundos_em_uso / 3600
                            minutos_em_uso = (segundos_em_uso % 3600) / 60
                            tempo_uso = f"{int(horas_em_uso)} horas e {int(minutos_em_uso)} minutos"
                            
                            # Verifica última confirmação
                            if usage_data.get("last_check"):
                                last_check = datetime.datetime.fromisoformat(usage_data["last_check"])
                                segundos_desde_check = (agora - last_check).total_seconds()
                                horas_desde_check = int(segundos_desde_check / 3600)
                                minutos_desde_check = int((segundos_desde_check % 3600) / 60)
                                ultima_confirmacao = f"Há {horas_desde_check} horas e {minutos_desde_check} minutos"
                            
                            # Verifica último lembrete
                            if usage_data.get("last_reminder"):
                                last_reminder = datetime.datetime.fromisoformat(usage_data["last_reminder"])
                                segundos_desde_lembrete = (agora - last_reminder).total_seconds()
                                horas_desde_lembrete = int(segundos_desde_lembrete / 3600)
                                minutos_desde_lembrete = int((segundos_desde_lembrete % 3600) / 60)
                                ultimo_lembrete = f"Há {horas_desde_lembrete} horas e {minutos_desde_lembrete} minutos"
                                
                                # Se recebeu lembrete mas não confirmou
                                if (not usage_data.get("last_check") or 
                                    last_reminder > datetime.datetime.fromisoformat(usage_data["last_check"])):
                                    notificados.append({
                                        "nome": config["nome"],
                                        "usuario": config["usuario"],
                                        "quando": f"Há {horas_desde_lembrete} horas e {minutos_desde_lembrete} minutos",
                                        "resposta": "Sem resposta ainda"
                                    })
                            
                        except Exception as e:
                            logging.error(f"Erro ao calcular tempo de uso para {servico_id}: {str(e)}")
                    
                    servico_info = {
                        "nome": config["nome"], 
                        "usuario": config["usuario"],
                        "tempo_uso": tempo_uso,
                        "ultima_confirmacao": ultima_confirmacao,
                        "ultimo_lembrete": ultimo_lembrete
                    }
                    em_uso.append(servico_info)
            
            # Monta o relatório
            resposta = ["**📊 Relatório de Uso dos Serviços Glassfish**\n"]
            
            # Serviços em uso
            resposta.append("**🔴 Serviços em Uso:**")
            if em_uso:
                for servico in em_uso:
                    resposta.append(
                        f"• **{servico['nome']}** - Usuário: {servico['usuario']} | " +
                        f"Em uso por: {servico['tempo_uso']} | " +
                        f"Última confirmação: {servico['ultima_confirmacao']} | " +
                        f"Último lembrete: {servico['ultimo_lembrete']}"
                    )
            else:
                resposta.append("• Nenhum serviço em uso no momento.")
            
            # Usuários notificados
            resposta.append("\n**📨 Lembretes Enviados Sem Resposta:**")
            if notificados:
                for notificacao in notificados:
                    resposta.append(
                        f"• **{notificacao['nome']}** - Usuário: {notificacao['usuario']} | " +
                        f"Lembrete enviado: {notificacao['quando']} | {notificacao['resposta']}"
                    )
            else:
                resposta.append("• Nenhum lembrete pendente de resposta.")
            
            # Estatísticas gerais
            total_servicos = len(servicos_config)
            disponiveis = total_servicos - len(em_uso)
            
            resposta.append(f"\n**📈 Estatísticas:**")
            resposta.append(f"• Total de serviços: {total_servicos}")
            resposta.append(f"• Serviços disponíveis: {disponiveis} ({int(disponiveis/total_servicos*100)}%)")
            resposta.append(f"• Serviços em uso: {len(em_uso)} ({int(len(em_uso)/total_servicos*100)}%)")
            
            # Envia o relatório
            await interaction.followup.send("\n".join(resposta), ephemeral=True)
            
        except Exception as e:
            logging.error(f"Erro ao gerar relatório: {str(e)}")
            await interaction.followup.send(
                f"Ocorreu um erro ao gerar o relatório: {str(e)}",
                ephemeral=True
            )

    async def cmd_adicionar_glassfish(self, interaction: discord.Interaction):
        """Adiciona um novo serviço Glassfish"""
        if not self._tem_permissao_ti(interaction.user):
            await interaction.response.send_message(
                "Apenas o setor de TI pode gerenciar os serviços.",
                ephemeral=True
            )
            return
        
        servicos_config = self.service.load_services()
        await interaction.response.send_modal(GlassfishAddModal(servicos_config, self.bot))

    async def cmd_editar_glassfish(self, interaction: discord.Interaction):
        """Edita um serviço Glassfish existente"""
        if not self._tem_permissao_ti(interaction.user):
            await interaction.response.send_message(
                "Apenas o setor de TI pode gerenciar os serviços.",
                ephemeral=True
            )
            return
            
        try:
            servicos_config = self.service.load_services()
            
            if not servicos_config:
                await interaction.response.send_message(
                    "Não há serviços configurados para editar.",
                    ephemeral=True
                )
                return
                
            view = GlassfishSelectView(servicos_config, "editar")
            await interaction.response.send_message(
                "Selecione o serviço que deseja editar:",
                view=view,
                ephemeral=True
            )
            
        except Exception as e:
            logging.error(f"Erro ao preparar edição de serviço: {str(e)}")
            await interaction.response.send_message(
                f"Ocorreu um erro ao selecionar o serviço: {str(e)}",
                ephemeral=True
            )

    async def cmd_remover_glassfish(self, interaction: discord.Interaction):
        """Remove um serviço Glassfish"""
        if not self._tem_permissao_ti(interaction.user):
            await interaction.response.send_message(
                "Apenas o setor de TI pode gerenciar os serviços.",
                ephemeral=True
            )
            return
            
        try:
            servicos_config = self.service.load_services()
            
            if not servicos_config:
                await interaction.response.send_message(
                    "Não há serviços configurados para remover.",
                    ephemeral=True
                )
                return
                
            view = GlassfishSelectView(servicos_config, "remover")
            await interaction.response.send_message(
                "Selecione o serviço que deseja remover:",
                view=view,
                ephemeral=True
            )
            
        except Exception as e:
            logging.error(f"Erro ao preparar remoção de serviço: {str(e)}")
            await interaction.response.send_message(
                f"Ocorreu um erro ao selecionar o serviço: {str(e)}",
                ephemeral=True
            )

    async def cmd_liberar_todos_glassfish(self, interaction: discord.Interaction):
        """Libera todos os serviços Glassfish em uso"""
        if not self._tem_permissao_ti(interaction.user):
            await interaction.response.send_message(
                "❌ Apenas usuários com cargo de TI podem executar este comando.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            servicos_config = self.service.load_services()
            servicos_liberados = 0
            servicos_em_uso = []
            
            # Obtém a lista de serviços em uso
            for servico_id, config in servicos_config.items():
                if config.get("status") == "em uso":
                    servicos_em_uso.append({
                        "id": servico_id,
                        "nome": config["nome"],
                        "usuario": config["usuario"]
                    })
            
            if not servicos_em_uso:
                await interaction.followup.send(
                    "ℹ️ Não há serviços em uso para liberar.",
                    ephemeral=True
                )
                return
            
            # Libera cada serviço em uso
            for servico in servicos_em_uso:
                servico_id = servico["id"]
                config = servicos_config[servico_id]
                
                # Remove dados de uso
                if "usage_data" in config:
                    del config["usage_data"]
                
                # Limpa a flag de notificação de timeout
                if "notificacao_timeout" in config:
                    del config["notificacao_timeout"]
                
                config["status"] = "disponível"
                config["usuario"] = None
                servicos_liberados += 1
            
            # Salva as alterações
            self.service.save_services(servicos_config)
            
            # Atualiza a mensagem persistente
            await self.service._refresh_persistent_message()
            
            # Notifica no canal de logs
            channel = interaction.guild.get_channel(LOGS_CHANNEL_ID)
            if channel:
                nomes_servicos = ", ".join([f"**{s['nome']}** (em uso por {s['usuario']})" for s in servicos_em_uso])
                await channel.send(
                    f"🔄 **Liberação em Massa**: Todos os serviços ({servicos_liberados}) foram liberados por <@{interaction.user.id}>.\n"
                    f"Serviços liberados: {nomes_servicos}"
                )
            
            # Responde ao usuário
            await interaction.followup.send(
                f"✅ {servicos_liberados} serviços Glassfish foram liberados com sucesso!\n\n"
                f"Serviços liberados:\n" + 
                "\n".join([f"🔸 **{s['nome']}** (estava em uso por {s['usuario']})" for s in servicos_em_uso]),
                ephemeral=True
            )
            
            logging.info(f"{interaction.user.name} liberou todos os serviços Glassfish ({servicos_liberados} serviços)")
            
        except Exception as e:
            logging.error(f"Erro ao liberar todos os serviços: {str(e)}")
            await interaction.followup.send(
                f"❌ Ocorreu um erro ao liberar os serviços: {str(e)}",
                ephemeral=True
            )

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
            view = TestarLembreteView(servicos_config, simular_tempo)
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
            # Carrega configuração atual
            from .glassfish_config import load_config, save_config
            config = load_config()
            
            # Atualiza o modo de desenvolvimento
            if "desenvolvimento" not in config:
                config["desenvolvimento"] = {}
            
            config["desenvolvimento"]["ativo"] = ativar
            
            if ativar:
                # Configurações de teste (tempos reduzidos)
                config["timeout"]["tempo_maximo_uso"] = 1  # 1 hora
                config["timeout"]["verificar_intervalo"] = 1  # 1 minuto
                config["timeout"]["lembrete_intervalo"] = 1  # 1 hora
                config["timeout"]["max_extensoes"] = 2  # 2 extensões
                
                status = "✅ **ATIVADO**"
                detalhes = (
                    "- Tempo máximo de uso: **1 hora**\n"
                    "- Verificação: **1 minuto**\n" 
                    "- Lembretes: **1 hora**\n"
                    "- Máximo extensões: **2**"
                )
            else:
                # Configurações de produção
                config["timeout"]["tempo_maximo_uso"] = 24  # 24 horas
                config["timeout"]["verificar_intervalo"] = 15  # 15 minutos
                config["timeout"]["lembrete_intervalo"] = 2  # 2 horas
                config["timeout"]["max_extensoes"] = 3  # 3 extensões
                
                status = "❌ **DESATIVADO**"
                detalhes = (
                    "- Tempo máximo de uso: **24 horas**\n"
                    "- Verificação: **15 minutos**\n"
                    "- Lembretes: **2 horas**\n"
                    "- Máximo extensões: **3**"
                )
            
            # Salva configuração
            if save_config(config):
                # Recarrega as configurações no service
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
            servicos_config = self.service.load_services()
            
            if servico_id not in servicos_config:
                await interaction.response.send_message(
                    f"❌ Serviço '{servico_id}' não encontrado.",
                    ephemeral=True
                )
                return
            
            config = servicos_config[servico_id]
            
            if config.get("status") != "em uso":
                await interaction.response.send_message(
                    f"❌ O serviço '{servico_id}' não está em uso.",
                    ephemeral=True
                )
                return
            
            # Simula o tempo passado
            agora = datetime.datetime.now()
            tempo_simulado = agora - datetime.timedelta(hours=horas_atras)
            
            # Atualiza os dados de uso
            if "usage_data" in config:
                usage_data = config["usage_data"]
                usage_data["timestamp"] = tempo_simulado.isoformat()
                # Remove verificações para forçar lembretes/timeouts
                usage_data["last_check"] = None
                usage_data["last_reminder"] = None
                usage_data["extension_count"] = 0
            else:
                # Cria dados de uso simulados
                config["usage_data"] = {
                    "usuario": config["usuario"],
                    "user_id": interaction.user.id,  # Simula com o usuário atual
                    "timestamp": tempo_simulado.isoformat(),
                    "last_check": None,
                    "last_reminder": None,
                    "extension_count": 0
                }
            
            # Salva as alterações
            self.service.save_services(servicos_config)
            
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
            
            # Informações básicas
            status = "🔴 **EM USO**" if config.get("status") == "em uso" else "🟢 **DISPONÍVEL**"
            usuario = config.get("usuario", "Nenhum")
            
            resposta = [
                f"📊 **Status Detalhado do Serviço**",
                f"**Nome:** {config['nome']}",
                f"**ID:** {servico_id}",
                f"**Status:** {status}",
                f"**Usuário:** {usuario}"
            ]
            
            # Se estiver em uso, mostra detalhes de usage_data
            if config.get("status") == "em uso" and "usage_data" in config:
                usage_data = config["usage_data"]
                
                try:
                    # Tempo em uso
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
                    
                    # Última verificação
                    if usage_data.get("last_check"):
                        last_check = datetime.datetime.fromisoformat(usage_data["last_check"])
                        segundos_desde_check = (agora - last_check).total_seconds()
                        horas_desde_check = int(segundos_desde_check / 3600)
                        minutos_desde_check = int((segundos_desde_check % 3600) / 60)
                        resposta.append(f"• **Última confirmação:** {last_check.strftime('%d/%m/%Y %H:%M:%S')} (há {horas_desde_check}h{minutos_desde_check}m)")
                    else:
                        resposta.append(f"• **Última confirmação:** Nunca confirmado")
                    
                    # Último lembrete
                    if usage_data.get("last_reminder"):
                        last_reminder = datetime.datetime.fromisoformat(usage_data["last_reminder"])
                        segundos_desde_lembrete = (agora - last_reminder).total_seconds()
                        horas_desde_lembrete = int(segundos_desde_lembrete / 3600)
                        minutos_desde_lembrete = int((segundos_desde_lembrete % 3600) / 60)
                        resposta.append(f"• **Último lembrete:** {last_reminder.strftime('%d/%m/%Y %H:%M:%S')} (há {horas_desde_lembrete}h{minutos_desde_lembrete}m)")
                    else:
                        resposta.append(f"• **Último lembrete:** Nenhum lembrete enviado")
                    
                    # Calcula próximas ações
                    resposta.append(f"\n**🔮 Próximas Ações:**")
                    
                    # Próximo lembrete
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
                    
                    # Timeout automático
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
            
            # Configurações de permissão
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
            
            # Encontra um serviço em uso
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
            
            # Testa o envio do lembrete
            try:
                # Simula o método _verificar_enviar_lembrete
                agora = datetime.datetime.now()
                extension_count = usage_data.get("extension_count", 0)
                
                user = await self.bot.fetch_user(int(user_id))
                
                # Calcula tempo formatado
                usage_data_dict = config["usage_data"]
                ultimo_uso = datetime.datetime.fromisoformat(usage_data_dict["timestamp"])
                segundos_em_uso = (agora - ultimo_uso).total_seconds()
                horas_formatadas = int(segundos_em_uso / 3600)
                minutos_formatados = int((segundos_em_uso % 3600) / 60)
                tempo_formatado = f"{horas_formatadas} horas e {minutos_formatados} minutos"
                
                # Verifica se o usuário atingiu o limite de extensões
                info_extensoes = ""
                if extension_count >= self.service.max_extensoes:
                    info_extensoes = f"\n⚠️ **Atenção**: Você já utilizou todas as {extension_count}/{self.service.max_extensoes} extensões permitidas."
                else:
                    info_extensoes = f"\n📝 Você já utilizou {extension_count}/{self.service.max_extensoes} extensões de tempo."
                
                # Importa o CheckView
                from .glassfish_ui import CheckView
                view = CheckView(servico_id, servicos_config)
                
                # Envia mensagem de teste
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
            except:
                pass 