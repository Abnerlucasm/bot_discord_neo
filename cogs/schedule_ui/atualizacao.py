import logging
from datetime import datetime

import discord

from .components import CustomView
from .constants import (
    CANAL_NOTIFICACOES, EMOJI_CHAMADOS_ATUALIZACAO, EMOJI_CLIENTE_ATUALIZACAO,
    EMOJI_DATA_ATUALIZACAO, EMOJI_USER_ATUALIZACAO, EMOJI_VERS_CONT_ATUALIZACAO,
    EMOJI_VERS_CORP_ATUALIZACAO, EMOJI_VERS_WEB_ATUALIZACAO,
)

class AtualizacaoModal(discord.ui.Modal, title='Atualização'):
    def __init__(self, original_data=None):
        super().__init__(custom_id=f"atualizacao_{datetime.now().strftime('%Y%m%d%H%M%S')}")
        self.message_to_edit = None
        self.author_id = None
        self.selected_users = []
        self.original_data = original_data or {}

        self.cliente = discord.ui.TextInput(
            placeholder='Nome do cliente...',
            required=True,
            default=self.original_data.get('cliente', '')
        )

        self.versoes = discord.ui.TextInput(
            placeholder='NeoCorp: 1.2.3\nNeoWeb: 1.2.3\nNeoContábil: 1.2.3',
            default=self.original_data.get('versoes', 'NeoCorp: \nNeoWeb: \nNeoContábil: '),
            required=True,
            style=discord.TextStyle.paragraph,
        )

        self.chamados = discord.ui.TextInput(
            placeholder='Números dos chamados...',
            required=False,
            style=discord.TextStyle.paragraph,
            default=self.original_data.get('chamados', '')
        )

        self.data_atualizacao = discord.ui.TextInput(
            placeholder='DD/MM/AAAA',
            default=self.original_data.get('data_atualizacao', datetime.now().strftime('%d/%m/%Y')),
            required=True,
        )

        self.add_item(discord.ui.Label(text='Cliente', component=self.cliente))
        self.add_item(
            discord.ui.Label(
                text='Versões',
                description='Informe uma linha por sistema no formato Sistema: versão.',
                component=self.versoes,
            )
        )
        self.add_item(discord.ui.Label(text='Chamados', component=self.chamados))
        self.add_item(
            discord.ui.Label(
                text='Data da atualização',
                description='Use o formato DD/MM/AAAA.',
                component=self.data_atualizacao,
            )
        )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True, thinking=True)
            if self.data_atualizacao.value and self.data_atualizacao.value.strip():
                try:
                    datetime.strptime(self.data_atualizacao.value.strip(), '%d/%m/%Y')
                except ValueError:
                    await interaction.followup.send(
                        "Formato de data inválido. Use DD/MM/AAAA.",
                        ephemeral=True
                    )
                    return
            versoes_texto = self.versoes.value.strip()
            versao_neocorp = ""
            versao_neoweb = ""
            versao_neocontabil = ""

            for linha in versoes_texto.replace('|', '\n').split('\n'):
                linha = linha.strip()
                if "NeoCorp:" in linha:
                    versao_neocorp = linha.split("NeoCorp:")[1].strip()
                elif "NeoWeb:" in linha:
                    versao_neoweb = linha.split("NeoWeb:")[1].strip()
                elif "NeoContábil:" in linha:
                    versao_neocontabil = linha.split("NeoContábil:")[1].strip()

            data_atualizacao = self.data_atualizacao.value
            if data_atualizacao and data_atualizacao.strip():
                data = data_atualizacao.strip()
            else:
                data = datetime.now().strftime('%d/%m/%Y')

            mensagem = [
                "**ATUALIZAÇÃO**",
                f"**{EMOJI_CLIENTE_ATUALIZACAO} • Cliente:** {self.cliente.value}",
                f"**{EMOJI_VERS_CORP_ATUALIZACAO} • Versão NeoCorp:** {versao_neocorp}",
            ]

            if versao_neoweb:
                mensagem.append(f"**{EMOJI_VERS_WEB_ATUALIZACAO} • Versão NeoWeb:** {versao_neoweb}")
            if versao_neocontabil:
                mensagem.append(f"**{EMOJI_VERS_CONT_ATUALIZACAO} • Versão NeoContábil:** {versao_neocontabil}")
            if self.chamados.value and self.chamados.value.strip():
                mensagem.append(f"**{EMOJI_CHAMADOS_ATUALIZACAO} • Chamados:** {self.chamados.value}")

            mensagem.append(f"**{EMOJI_DATA_ATUALIZACAO} • Data:** {data}")

            responsaveis_texto = f"<@{interaction.user.id}>"

            for user in self.selected_users:
                if user.id != interaction.user.id:
                    responsaveis_texto += f", <@{user.id}>"

            mensagem.append(f"**{EMOJI_USER_ATUALIZACAO} • Atualizado por:** {responsaveis_texto}")

            mensagem_final = '\n'.join(mensagem)

            original_data = {
                "cliente": self.cliente.value,
                "versoes": self.versoes.value,
                "chamados": self.chamados.value,
                "data_atualizacao": data,
                "responsaveis": [user.id for user in self.selected_users],
            }

            view = CustomView("atualizacao", original_data, interaction.user.id)

            if self.message_to_edit:
                await self.message_to_edit.edit(content=mensagem_final, view=view)
                await interaction.followup.send(
                    "Atualização modificada com sucesso!",
                    ephemeral=True
                )
                logging.info("%s modificou uma atualização para %s", interaction.user.name, self.cliente.value)
            else:
                channel = interaction.client.get_channel(CANAL_NOTIFICACOES)
                if channel is None:
                    await interaction.followup.send(
                        "O canal de notificações não está disponível.",
                        ephemeral=True,
                    )
                    return

                message = await channel.send(content=mensagem_final, view=view)
                bot = interaction.client
                if hasattr(bot, "save_interactive_message"):
                    bot.save_interactive_message(
                        message.id,
                        channel.id,
                        "atualizacao",
                        interaction.user.id,
                        original_data,
                    )

                await interaction.followup.send("Atualização registrada com sucesso!", ephemeral=True)
                logging.info("%s registrou uma atualização para %s", interaction.user.name, self.cliente.value)

        except Exception as e:
            logging.exception("Erro ao registrar atualização: %s", e)
            await interaction.followup.send(
                "Ocorreu um erro ao registrar a atualização. Tente novamente mais tarde.",
                ephemeral=True,
            )

class ConfirmButton(discord.ui.Button):
    def __init__(self, modal: AtualizacaoModal):
        super().__init__(
            label="Continuar",
            style=discord.ButtonStyle.success,
            emoji="➡️"
        )
        self.modal = modal

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(self.modal)

class ResponsaveisSelect(discord.ui.UserSelect):
    def __init__(self, modal: AtualizacaoModal, current_user: discord.User):
        super().__init__(
            placeholder="Selecione os responsáveis adicionais...",
            min_values=0,
            max_values=25
        )
        self.modal = modal
        self.current_user = current_user

    async def callback(self, interaction: discord.Interaction):
        selected_users = [user for user in self.values if user.id != self.current_user.id]
        self.modal.selected_users = selected_users

        if selected_users:
            selected_users_text = "\n".join(f"- {user.mention}" for user in selected_users)
        else:
            selected_users_text = "Nenhum responsável adicional selecionado"
        await interaction.response.edit_message(
            content=f"**1ª Etapa: Selecione os responsáveis adicionais:**\n\n"
                   f"**⚠️ IMPORTANTE ⚠️**\n"
                   f"**Você já está listado como responsável principal desta atualização!**\n\n"
                   f"Responsáveis adicionais selecionados:\n{selected_users_text}\n\n"
                   f"Clique no botão 'Continuar' quando terminar a seleção.",
            view=self.view
        )

class AtualizacaoView(discord.ui.View):
    def __init__(self, modal: AtualizacaoModal, current_user: discord.User):
        super().__init__(timeout=None)
        self.modal = modal
        self.add_item(ResponsaveisSelect(modal, current_user))
        self.add_item(ConfirmButton(modal))

class NaoButton(discord.ui.Button):
    def __init__(self, modal: AtualizacaoModal):
        super().__init__(
            label="Não",
            style=discord.ButtonStyle.danger,
            emoji="❌"
        )
        self.modal = modal

    async def callback(self, interaction: discord.Interaction):
        self.modal.selected_users = [interaction.user]
        await interaction.response.send_modal(self.modal)

class SimButton(discord.ui.Button):
    def __init__(self, modal: AtualizacaoModal, current_user: discord.User):
        super().__init__(
            label="Sim",
            style=discord.ButtonStyle.success,
            emoji="✅"
        )
        self.modal = modal
        self.current_user = current_user

    async def callback(self, interaction: discord.Interaction):
        view = AtualizacaoView(self.modal, self.current_user)
        await interaction.response.edit_message(
            content="**1ª Etapa: Selecione os responsáveis adicionais:**\n\n"
                   "**⚠️ IMPORTANTE ⚠️**\n"
                   "**Você já está listado como responsável principal desta atualização!**\n\n"
                   "Use o menu abaixo para selecionar **outros responsáveis** pela atualização.\n"
                   "Após selecionar, clique no botão 'Continuar' para abrir o formulário de atualização.",
            view=view
        )

class InicialView(discord.ui.View):
    def __init__(self, modal: AtualizacaoModal, current_user: discord.User):
        super().__init__(timeout=None)
        self.modal = modal
        self.add_item(SimButton(modal, current_user))
        self.add_item(NaoButton(modal))
