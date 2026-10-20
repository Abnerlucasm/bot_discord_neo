import datetime
import logging
from typing import Optional

import discord

from .base import GlassfishCommandBase
from ..core import config as settings
from ..ui.service_admin import GlassfishSelectView
from ..ui.service_forms import GlassfishAddModal

class GlassfishAdminCommands(GlassfishCommandBase):
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

            em_uso = []
            notificados = []
            agora = datetime.datetime.now()

            for servico_id, config in servicos_config.items():
                if config.get("status") == "em uso":
                    tempo_uso = "Tempo desconhecido"
                    ultima_confirmacao = "Nunca confirmado"
                    ultimo_lembrete = "Nenhum lembrete enviado"

                    if "usage_data" in config:
                        try:
                            usage_data = config["usage_data"]

                            timestamp = datetime.datetime.fromisoformat(usage_data["timestamp"])
                            segundos_em_uso = (agora - timestamp).total_seconds()
                            horas_em_uso = segundos_em_uso / 3600
                            minutos_em_uso = (segundos_em_uso % 3600) / 60
                            tempo_uso = f"{int(horas_em_uso)} horas e {int(minutos_em_uso)} minutos"

                            if usage_data.get("last_check"):
                                last_check = datetime.datetime.fromisoformat(usage_data["last_check"])
                                segundos_desde_check = (agora - last_check).total_seconds()
                                horas_desde_check = int(segundos_desde_check / 3600)
                                minutos_desde_check = int((segundos_desde_check % 3600) / 60)
                                ultima_confirmacao = f"Há {horas_desde_check} horas e {minutos_desde_check} minutos"

                            if usage_data.get("last_reminder"):
                                last_reminder = datetime.datetime.fromisoformat(usage_data["last_reminder"])
                                segundos_desde_lembrete = (agora - last_reminder).total_seconds()
                                horas_desde_lembrete = int(segundos_desde_lembrete / 3600)
                                minutos_desde_lembrete = int((segundos_desde_lembrete % 3600) / 60)
                                ultimo_lembrete = f"Há {horas_desde_lembrete} horas e {minutos_desde_lembrete} minutos"

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

            resposta = ["**📊 Relatório de Uso dos Serviços Glassfish**\n"]

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

            resposta.append("\n**📨 Lembretes Enviados Sem Resposta:**")
            if notificados:
                for notificacao in notificados:
                    resposta.append(
                        f"• **{notificacao['nome']}** - Usuário: {notificacao['usuario']} | " +
                        f"Lembrete enviado: {notificacao['quando']} | {notificacao['resposta']}"
                    )
            else:
                resposta.append("• Nenhum lembrete pendente de resposta.")

            total_servicos = len(servicos_config)
            disponiveis = total_servicos - len(em_uso)
            if total_servicos:
                percentual_disponiveis = int(disponiveis / total_servicos * 100)
                percentual_em_uso = int(len(em_uso) / total_servicos * 100)
            else:
                percentual_disponiveis = 0
                percentual_em_uso = 0

            resposta.append(f"\n**📈 Estatísticas:**")
            resposta.append(f"• Total de serviços: {total_servicos}")
            resposta.append(f"• Serviços disponíveis: {disponiveis} ({percentual_disponiveis}%)")
            resposta.append(f"• Serviços em uso: {len(em_uso)} ({percentual_em_uso}%)")

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

        await interaction.response.send_modal(GlassfishAddModal(self.service, self.bot))

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

            view = GlassfishSelectView(self.service, servicos_config, "editar")
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

            view = GlassfishSelectView(self.service, servicos_config, "remover")
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
            def release_all_services(services):
                services_in_use = []
                for service_id, config in services.items():
                    if config.get("status") != "em uso":
                        continue

                    services_in_use.append({
                        "id": service_id,
                        "nome": config["nome"],
                        "usuario": config["usuario"],
                    })
                    config.pop("usage_data", None)
                    config.pop("notificacao_timeout", None)
                    config["status"] = "disponível"
                    config["usuario"] = None

                return bool(services_in_use), services_in_use

            saved, servicos_em_uso = await self.service.update_services(release_all_services)
            if not saved:
                await interaction.followup.send(
                    "❌ Não foi possível salvar a liberação dos serviços. Tente novamente.",
                    ephemeral=True,
                )
                return

            servicos_liberados = len(servicos_em_uso)
            if not servicos_em_uso:
                await interaction.followup.send(
                    "ℹ️ Não há serviços em uso para liberar.",
                    ephemeral=True
                )
                return

            await self.service.refresh_persistent_message()

            channel = interaction.guild.get_channel(settings.LOGS_CHANNEL_ID)
            if channel:
                nomes_servicos = ", ".join([f"**{s['nome']}** (em uso por {s['usuario']})" for s in servicos_em_uso])
                await channel.send(
                    f"🔄 **Liberação em Massa**: Todos os serviços ({servicos_liberados}) foram liberados por <@{interaction.user.id}>.\n"
                    f"Serviços liberados: {nomes_servicos}"
                )

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
