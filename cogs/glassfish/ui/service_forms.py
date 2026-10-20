import logging
from typing import Any, Dict

import discord

from ..core import config as settings
from ..core.contracts import GlassfishServiceContract
from .role_permissions import RolePermissionView


class GlassfishAddModal(discord.ui.Modal, title='Adicionar Serviço Glassfish'):
    def __init__(self, service: GlassfishServiceContract, bot=None):
        super().__init__()
        self.service = service
        self.bot = bot

        self.servico_id = discord.ui.TextInput(
            placeholder='Ex: 97-1 (Padrão: Servidor-Instância)',
            required=True,
            min_length=2,
            max_length=30,
        )

        self.servico_nome = discord.ui.TextInput(
            placeholder='Ex: Glassfish 97 - Domain: Neosistemas - Porta: 4848',
            required=True,
            max_length=100,
        )

        self.add_item(
            discord.ui.Label(
                text='ID do serviço',
                description='Use apenas letras, números, hífens e sublinhados.',
                component=self.servico_id,
            )
        )
        self.add_item(
            discord.ui.Label(
                text='Nome do serviço',
                description='Informe o servidor, domínio ou porta para facilitar a identificação.',
                component=self.servico_nome,
            )
        )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            servico_id = self.servico_id.value.strip().lower()
            servico_nome = self.servico_nome.value.strip()

            if not servico_id or not all(c.isalnum() or c in "_-" for c in servico_id):
                await interaction.followup.send(
                    "❌ Informe um ID usando apenas letras, números, sublinhados ou hífens.",
                    ephemeral=True,
                )
                return

            if servico_id in self.service.load_services():
                await interaction.followup.send(
                    f"❌ Um serviço com o ID '{servico_id}' já existe. Escolha outro ID.",
                    ephemeral=True,
                )
                return

            service_data = {
                "nome": servico_nome,
                "status": "disponível",
                "usuario": None,
                "grupos_permitidos": [],
            }

            view = RolePermissionView(service_data, servico_id, self.bot, self.service)
            await interaction.followup.send(
                f"**Configuração de permissões para {servico_nome}**\n"
                "Selecione até dez cargos que poderão usar este serviço:",
                view=view,
                ephemeral=True,
            )
            logging.info("Formulário de permissões aberto para o serviço %s", servico_id)
        except Exception as e:
            logging.exception("Erro ao processar o formulário de adição do serviço")
            await interaction.followup.send(
                "❌ Não foi possível iniciar a configuração do serviço.",
                ephemeral=True,
            )


class GlassfishEditModal(discord.ui.Modal, title='Editar Serviço Glassfish'):
    def __init__(
        self,
        servico_id: str,
        servicos_config: Dict[str, Any],
        service: GlassfishServiceContract,
    ):
        super().__init__()
        self.servico_id = servico_id
        self.service = service
        self.servico_info = servicos_config[servico_id]

        self.servico_nome = discord.ui.TextInput(
            placeholder='Ex: Glassfish 250 - Domain: Neosistemas - Porta: 4848',
            required=True,
            max_length=100,
            default=self.servico_info.get('nome', ''),
        )
        self.add_item(
            discord.ui.Label(
                text='Nome do serviço',
                description='Informe um nome que identifique o servidor e o domínio.',
                component=self.servico_nome,
            )
        )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            servico_nome = self.servico_nome.value.strip()
            if not servico_nome:
                await interaction.followup.send(
                    "Informe um nome para o serviço.",
                    ephemeral=True,
                )
                return

            def update_name(service_info):
                old_name = service_info.get('nome', 'Desconhecido')
                service_info['nome'] = servico_nome
                return True, old_name

            saved, old_nome, service_info = await self.service.update_service(
                self.servico_id,
                update_name,
            )
            if not saved:
                await interaction.followup.send(
                    "Não foi possível salvar a alteração. Tente novamente.",
                    ephemeral=True,
                )
                return
            if old_nome == "not_found" or not service_info:
                await interaction.followup.send(
                    "Este serviço não está mais cadastrado.",
                    ephemeral=True,
                )
                return

            glassfish_cog = interaction.client.get_cog("GlassfishCog")
            if glassfish_cog:
                await glassfish_cog.refresh_persistent_message()

            channel = interaction.guild.get_channel(settings.LOGS_CHANNEL_ID)
            if channel:
                await channel.send(
                    f"📝 O serviço **{old_nome}** foi editado por <@{interaction.user.id}> para **{servico_nome}**."
                )

            if self.servico_id is not None:
                servico_id_str = str(self.servico_id)
            else:
                servico_id_str = "desconhecido"
            if old_nome:
                old_nome_str = old_nome
            else:
                old_nome_str = "Desconhecido"
            if interaction.user:
                user_name = interaction.user.name
            else:
                user_name = "Usuário desconhecido"
            logging.info(f"Serviço {servico_id_str} ({old_nome_str}) editado por {user_name} para {servico_nome}")

            await interaction.followup.send(
                f"Serviço **{servico_nome}** atualizado com sucesso!",
                ephemeral=True
            )

        except Exception as e:
            logging.error(f"Erro ao editar serviço: {str(e)}")
            await interaction.followup.send(
                f"Ocorreu um erro ao editar o serviço: {str(e)}",
                ephemeral=True
            )
