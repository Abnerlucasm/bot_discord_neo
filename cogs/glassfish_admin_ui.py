import discord
import json
import logging
from typing import Dict, Any, List
from .glassfish_config import CARGO_TI_ID, LOGS_CHANNEL_ID


class GlassfishAddModal(discord.ui.Modal, title='Adicionar Serviço Glassfish'):
    def __init__(self, servicos_config: Dict[str, Any], bot=None):
        super().__init__()
        self.servicos_config = servicos_config
        self.bot = bot
        
        # Campo para o ID do serviço
        self.servico_id = discord.ui.TextInput(
            label='ID do Serviço',
            placeholder='Ex: 97-1 (Padrão: Servidor-Instância)',
            required=True,
            min_length=2,
            max_length=30
        )
        self.add_item(self.servico_id)
        
        # Campo para o nome do serviço
        self.servico_nome = discord.ui.TextInput(
            label='Nome do Serviço',
            placeholder='Ex: Glassfish 97 - Domain: Neosistemas - Porta: 4848',
            required=True,
            max_length=100
        )
        self.add_item(self.servico_nome)
        
    async def on_submit(self, interaction: discord.Interaction):
        try:
            servico_id = self.servico_id.value.strip().lower()
            servico_nome = self.servico_nome.value.strip()
            
            # Log para diagnóstico
            logging.info(f"Tentativa de adicionar serviço - ID: {servico_id}, Nome: {servico_nome}")
            
            # Valida ID do serviço
            if not all(c.isalnum() or c in "_-" for c in servico_id):
                await interaction.response.send_message(
                    "❌ ID do serviço deve conter apenas letras, números, underlines ou hífens.",
                    ephemeral=True
                )
                return
                
            # Verifica se o ID já existe
            if servico_id in self.servicos_config:
                await interaction.response.send_message(
                    f"❌ Um serviço com o ID '{servico_id}' já existe. Escolha outro ID.",
                    ephemeral=True
                )
                return
            
            # Criar estrutura para o novo serviço
            service_data = {
                "nome": servico_nome,
                "status": "disponível",
                "usuario": None,
                "grupos_permitidos": []
            }
            
            # Log para diagnóstico
            logging.info(f"Criando RolePermissionView para o serviço {servico_id}")    
            
            # Abre view para selecionar cargos permitidos
            try:
                view = RolePermissionView(service_data, servico_id, self.bot)
                await interaction.response.send_message(
                    f"**Configuração de Permissões para {servico_nome}**\n"
                    f"Selecione os cargos que poderão usar este serviço:",
                    view=view,
                    ephemeral=True
                )
                logging.info(f"RolePermissionView enviado com sucesso para o serviço {servico_id}")
            except Exception as view_error:
                logging.error(f"Erro ao criar ou enviar RolePermissionView: {str(view_error)}")
                await interaction.response.send_message(
                    f"❌ Ocorreu um erro ao configurar permissões: {str(view_error)}",
                    ephemeral=True
                )
            
        except Exception as e:
            logging.error(f"Erro ao processar formulário de adição: {str(e)}")
            try:
                await interaction.response.send_message(
                    f"❌ Ocorreu um erro ao adicionar o serviço: {str(e)}",
                    ephemeral=True
                )
            except discord.InteractionResponded:
                await interaction.followup.send(
                    f"❌ Ocorreu um erro ao adicionar o serviço: {str(e)}",
                    ephemeral=True
                )
            except Exception as final_err:
                logging.error(f"Erro fatal ao responder interação de adição: {str(final_err)}")


class GlassfishEditModal(discord.ui.Modal, title='Editar Serviço Glassfish'):
    def __init__(self, servico_id: str, servicos_config: Dict[str, Any]):
        super().__init__()
        self.servico_id = servico_id
        self.servicos_config = servicos_config
        self.servico_info = servicos_config[servico_id]
        
        # Campo para o nome do serviço
        self.servico_nome = discord.ui.TextInput(
            label='Nome do Serviço',
            placeholder='Ex: Glassfish 250 - Domain: Neosistemas - Porta: 4848',
            required=True,
            max_length=100,
            default=self.servico_info.get('nome', '')
        )
        self.add_item(self.servico_nome)
        
    async def on_submit(self, interaction: discord.Interaction):
        try:
            servico_nome = self.servico_nome.value.strip()
            
            # Atualiza o nome do serviço
            old_nome = self.servico_info.get('nome', 'Desconhecido')
            self.servicos_config[self.servico_id]['nome'] = servico_nome
            
            # Salva a configuração atualizada
            with open("services.json", "w", encoding="utf-8") as file:
                json.dump(self.servicos_config, file, indent=4)
                
            # Atualiza a mensagem persistente
            glassfish_cog = interaction.client.get_cog("GlassfishCog")
            if glassfish_cog:
                await glassfish_cog.refresh_persistent_message()
                
            # Notifica no canal de logs
            channel = interaction.guild.get_channel(LOGS_CHANNEL_ID)
            if channel:
                await channel.send(
                    f"📝 O serviço **{old_nome}** foi editado por <@{interaction.user.id}> para **{servico_nome}**."
                )
                
            # Registra o log
            servico_id_str = str(self.servico_id) if self.servico_id is not None else "desconhecido"
            old_nome_str = old_nome if old_nome else "Desconhecido"
            user_name = interaction.user.name if interaction.user else "Usuário desconhecido"
            logging.info(f"Serviço {servico_id_str} ({old_nome_str}) editado por {user_name} para {servico_nome}")
            
            # Envia mensagem de sucesso
            await interaction.response.send_message(
                f"Serviço **{servico_nome}** atualizado com sucesso!",
                ephemeral=True
            )
            
        except Exception as e:
            logging.error(f"Erro ao editar serviço: {str(e)}")
            await interaction.response.send_message(
                f"Ocorreu um erro ao editar o serviço: {str(e)}",
                ephemeral=True
            )


class GlassfishSelectView(discord.ui.View):
    def __init__(self, servicos_config: Dict[str, Any], action_type: str):
        super().__init__(timeout=180)  # 3 minutos
        self.add_item(GlassfishSelect(servicos_config, action_type))


class GlassfishSelect(discord.ui.Select):
    def __init__(self, servicos_config: Dict[str, Any], action_type: str):
        self.servicos_config = servicos_config
        self.action_type = action_type  # "editar" ou "remover"
        self.bot = None  # Será definido quando a view for associada a um bot
        
        # Prepara as opções do dropdown
        options = []
        for key, config in servicos_config.items():
            # Adiciona status e usuário à descrição se estiver em uso
            if config["status"] == "em uso":
                desc = f"Em uso por: {config['usuario']}"
                emoji = "🔴"
            else:
                desc = "Disponível"
                emoji = "🟢"
                
            options.append(
                discord.SelectOption(
                    label=f"{key}: {config['nome'][:40]}", 
                    value=key,
                    description=desc,
                    emoji=emoji
                )
            )
        
        super().__init__(
            placeholder="Selecione um serviço", 
            min_values=1, 
            max_values=1,
            options=options
        )
        
    async def callback(self, interaction: discord.Interaction):
        servico_id = self.values[0]
        
        # Define o bot a partir da interação se não estiver definido
        if self.bot is None:
            self.bot = interaction.client
            
        try:
            if self.action_type == "editar":
                # Abre o modal de edição
                await interaction.response.send_modal(GlassfishEditModal(servico_id, self.servicos_config))
            elif self.action_type == "remover":
                # Verifica se o serviço está em uso
                servico_info = self.servicos_config[servico_id]
                if servico_info["status"] == "em uso":
                    # Pede confirmação antes de remover
                    view = ConfirmRemoveView(servico_id, self.servicos_config)
                    await interaction.response.send_message(
                        f"⚠️ **ATENÇÃO**: O serviço **{servico_info['nome']}** está atualmente em uso por **{servico_info['usuario']}**.\n\n"
                        f"Tem certeza que deseja remover este serviço?",
                        view=view,
                        ephemeral=True
                    )
                else:
                    # Remove o serviço diretamente
                    del self.servicos_config[servico_id]
                    
                    # Salva a configuração atualizada
                    with open("services.json", "w", encoding="utf-8") as file:
                        json.dump(self.servicos_config, file, indent=4)
                        
                    # Atualiza a mensagem persistente
                    glassfish_cog = interaction.client.get_cog("GlassfishCog")
                    if glassfish_cog:
                        await glassfish_cog.refresh_persistent_message()
                        logging.info(f"Mensagem persistente do Glassfish atualizada após remoção do serviço {servico_id}")
                    
                    # Notifica no canal de logs
                    try:
                        channel = interaction.guild.get_channel(LOGS_CHANNEL_ID)
                        if channel:
                            await channel.send(
                                f"🗑️ O serviço **{servico_info['nome']}** foi removido por <@{interaction.user.id}>"
                            )
                    except Exception as log_err:
                        logging.error(f"Erro ao enviar log de remoção: {str(log_err)}")
                    
                    await interaction.response.send_message(
                        f"✅ Serviço **{servico_info['nome']}** removido com sucesso!",
                        ephemeral=True
                    )
                    
                    logging.info(f"Serviço {servico_id} ({servico_info['nome']}) removido por {interaction.user.name}")
        except Exception as e:
            logging.error(f"Erro ao processar seleção de serviço: {str(e)}")
            try:
                await interaction.response.send_message(
                    f"❌ Ocorreu um erro ao processar o serviço: {str(e)}",
                    ephemeral=True
                )
            except discord.InteractionResponded:
                await interaction.followup.send(
                    f"❌ Ocorreu um erro ao processar o serviço: {str(e)}",
                    ephemeral=True
                )
            except Exception as final_err:
                logging.error(f"Erro fatal ao responder interação de seleção: {str(final_err)}")


class ConfirmRemoveView(discord.ui.View):
    def __init__(self, servico_id: str, servicos_config: Dict[str, Any]):
        super().__init__(timeout=60)  # 1 minuto para timeout
        self.servico_id = servico_id
        self.servicos_config = servicos_config
        self.servico_data = servicos_config[servico_id]
        
    @discord.ui.button(label="Sim, remover mesmo em uso", style=discord.ButtonStyle.danger)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            servico_nome = self.servico_data["nome"]
            usuario = self.servico_data["usuario"]
            
            # Remove o serviço
            del self.servicos_config[self.servico_id]
            
            # Salva a configuração atualizada
            with open("services.json", "w", encoding="utf-8") as file:
                json.dump(self.servicos_config, file, indent=4)
                
            # Atualiza a mensagem persistente
            glassfish_cog = interaction.client.get_cog("GlassfishCog")
            if glassfish_cog:
                await glassfish_cog.refresh_persistent_message()
                
            # Notifica no canal de logs
            channel = interaction.guild.get_channel(LOGS_CHANNEL_ID)
            if channel:
                await channel.send(
                    f"⚠️ **ATENÇÃO**: O serviço **{servico_nome}** foi removido por <@{interaction.user.id}> "
                    f"enquanto estava em uso por **{usuario}**."
                )
                
            # Desabilita todos os botões
            for item in self.children:
                item.disabled = True
            
            await interaction.response.edit_message(
                content=f"✅ Serviço **{servico_nome}** removido com sucesso!",
                view=self
            )
            
            logging.info(f"Serviço {self.servico_id} ({servico_nome}) removido por {interaction.user.name} enquanto em uso por {usuario}")
            
        except Exception as e:
            logging.error(f"Erro ao remover serviço: {str(e)}")
            await interaction.response.send_message(
                f"Ocorreu um erro ao remover o serviço: {str(e)}",
                ephemeral=True
            )
            
    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.secondary)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Desabilita todos os botões
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(
            content="Operação cancelada!",
            view=self
        )


class RolePermissionView(discord.ui.View):
    def __init__(self, service_data: Dict[str, Any], serv_id: str, bot):
        super().__init__(timeout=180)  # Aumenta o timeout para 3 minutos
        self.selected_roles = []
        self.service_data = service_data
        self.serv_id = serv_id
        self.bot = bot
        
        # Adicionar o select de cargos ao view
        self.add_item(RolePermissionSelect(self))
        
    @discord.ui.button(label="Confirmar", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.selected_roles:
            await interaction.response.send_message("⚠️ Por favor, selecione pelo menos um cargo antes de confirmar.", ephemeral=True)
            return
            
        try:
            # Carregar configuração existente
            services_file = "services.json"
            
            try:
                with open(services_file, "r", encoding="utf-8") as f:
                    services = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                services = {}
                
            # Adicionar dados do serviço
            services[self.serv_id] = {
                "nome": self.service_data["nome"],
                "status": "disponível",
                "usuario": None,
                "grupos_permitidos": self.selected_roles
            }
            
            # Salvar configuração atualizada
            with open(services_file, "w", encoding="utf-8") as f:
                json.dump(services, f, ensure_ascii=False, indent=4)
                
            # Atualizar a mensagem persistente
            if self.bot:
                glassfish_cog = self.bot.get_cog("GlassfishCog")
                if glassfish_cog:
                    await glassfish_cog.refresh_persistent_message()
            else:
                glassfish_cog = interaction.client.get_cog("GlassfishCog")
                if glassfish_cog:
                    await glassfish_cog.refresh_persistent_message()
                
            # Preparar menções dos cargos
            cargo_mentions = []
            cargo_names = []
            for role_id in self.selected_roles:
                role = interaction.guild.get_role(int(role_id))
                if role:
                    cargo_mentions.append(role.mention)
                    cargo_names.append(role.name)
            
            cargos_texto = ", ".join(cargo_mentions) if cargo_mentions else "Nenhum"
            cargos_nomes = ", ".join(cargo_names) if cargo_names else "Nenhum"
            
            # Tenta editar a mensagem original com tratamento de erro
            message_edited = False
            try:
                # Desabilita todos os botões
                for child in self.children:
                    child.disabled = True
                
                # Tenta editar a mensagem original
                await interaction.message.edit(
                    content=f"✅ **Configuração Concluída**\nServiço **{self.service_data['nome']}** configurado com sucesso!",
                    view=self
                )
                message_edited = True
            except discord.NotFound:
                logging.warning(f"Não foi possível editar a mensagem - ela pode ter sido excluída ou o bot não tem mais acesso a ela")
            except Exception as edit_error:
                logging.error(f"Erro ao editar mensagem: {str(edit_error)}")
            
            # Envia a resposta com tratamento para interação já respondida
            try:
                # Se não conseguiu editar a mensagem, provavelmente a interação já foi respondida
                if message_edited:
                    await interaction.response.send_message(
                        f"✅ Serviço **{self.service_data['nome']}** adicionado com sucesso!\n"
                        f"**Cargos permitidos:** {cargos_nomes}",
                        ephemeral=True
                    )
                else:
                    # Se a mensagem não foi editada, pode ser que a interação já tenha sido respondida
                    try:
                        await interaction.response.send_message(
                            f"✅ Serviço **{self.service_data['nome']}** adicionado com sucesso!\n"
                            f"**Cargos permitidos:** {cargos_nomes}",
                            ephemeral=True
                        )
                    except discord.InteractionResponded:
                        # Se a interação já foi respondida, usa followup
                        await interaction.followup.send(
                            f"✅ Serviço **{self.service_data['nome']}** adicionado com sucesso!\n"
                            f"**Cargos permitidos:** {cargos_nomes}",
                            ephemeral=True
                        )
            except Exception as resp_error:
                logging.error(f"Erro ao responder à interação: {str(resp_error)}")
            
            # Tentar registrar a ação no canal de logs
            try:
                log_channel = interaction.guild.get_channel(LOGS_CHANNEL_ID) or await interaction.guild.fetch_channel(LOGS_CHANNEL_ID)
                if log_channel:
                    await log_channel.send(
                        f"🆕 **Novo serviço Glassfish adicionado**\n"
                        f"**ID:** {self.serv_id}\n"
                        f"**Nome:** {self.service_data['nome']}\n"
                        f"**Cargos permitidos:** {cargos_texto}\n"
                        f"**Adicionado por:** {interaction.user.mention}"
                    )
                    
                    logging.info(f"Novo serviço {self.serv_id} ({self.service_data['nome']}) adicionado por {interaction.user.name} com cargos: {cargos_nomes}")
            except Exception as e:
                logging.error(f"Erro ao enviar log de novo serviço: {str(e)}")
                
            # Fechar o menu
            self.stop()
            
        except Exception as e:
            logging.error(f"Erro ao adicionar serviço: {str(e)}")
            # Tenta responder à interação, com tratamento para caso já tenha sido respondida
            try:
                await interaction.response.send_message(
                    f"❌ Erro ao adicionar serviço: {e}",
                    ephemeral=True
                )
            except discord.InteractionResponded:
                await interaction.followup.send(
                    f"❌ Erro ao adicionar serviço: {e}",
                    ephemeral=True
                )
            except Exception as final_err:
                logging.error(f"Erro fatal ao responder interação: {str(final_err)}")
                
    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            # Desabilita todos os botões
            for item in self.children:
                item.disabled = True
            
            # Tenta editar a mensagem original
            try:
                await interaction.response.edit_message(
                    content="🚫 Operação cancelada!",
                    view=self
                )
            except discord.NotFound:
                logging.warning("Não foi possível editar a mensagem de cancelamento - ela pode ter sido excluída")
            except Exception as edit_error:
                logging.error(f"Erro ao editar mensagem de cancelamento: {str(edit_error)}")
            
            # Envia uma mensagem adicional
            try:
                await interaction.followup.send(
                    "Operação cancelada. Nenhum serviço foi adicionado.",
                    ephemeral=True
                )
            except Exception as followup_error:
                logging.error(f"Erro ao enviar followup de cancelamento: {str(followup_error)}")
            
            self.stop()
        except Exception as e:
            logging.error(f"Erro ao processar cancelamento: {str(e)}")
            try:
                await interaction.response.send_message("Erro ao cancelar operação.", ephemeral=True)
            except:
                pass


class RolePermissionSelect(discord.ui.Select):
    def __init__(self, parent_view: RolePermissionView):
        self.parent_view = parent_view
        # Criar opção padrão inicial
        options = [
            discord.SelectOption(
                label="Clique para carregar os cargos",
                value="placeholder",
                description="Selecione para carregar os cargos disponíveis"
            )
        ]
        super().__init__(
            placeholder="Selecione os cargos permitidos",
            min_values=1,
            max_values=1,  # Inicialmente apenas 1, será atualizado após carregar os cargos
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        # Se a opção selecionada for o placeholder, carregamos os cargos
        if "placeholder" in self.values:
            try:
                # Limpa as opções
                self.options.clear()
                
                # Carrega os cargos do servidor
                guild_roles = interaction.guild.roles
                
                # Adiciona cada cargo como uma opção, excluindo cargos do sistema
                role_count = 0
                for role in guild_roles:
                    if not role.is_default() and not role.is_integration() and not role.is_bot_managed():
                        self.options.append(
                            discord.SelectOption(
                                label=role.name,
                                value=str(role.id),
                                description=f"ID: {role.id}"
                            )
                        )
                        role_count += 1
                
                # Log para diagnóstico
                logging.info(f"Carregados {role_count} cargos no select")
                
                if role_count == 0:
                    # Nenhum cargo encontrado, adiciona opção informativa
                    self.options.append(
                        discord.SelectOption(
                            label="Nenhum cargo disponível",
                            value="no_roles",
                            description="Não há cargos disponíveis para seleção"
                        )
                    )
                    self.max_values = 1
                    try:
                        await interaction.response.send_message(
                            "Não foram encontrados cargos disponíveis no servidor.",
                            ephemeral=True
                        )
                    except discord.InteractionResponded:
                        await interaction.followup.send(
                            "Não foram encontrados cargos disponíveis no servidor.",
                            ephemeral=True
                        )
                    return
                
                # Atualiza o número máximo de valores selecionáveis
                # Permite selecionar múltiplos cargos, até 10 no máximo
                self.max_values = min(10, len(self.options))
                
                # Importante: define min_values para 0 para permitir desfazer seleções
                self.min_values = 0
                
                # Limpa a seleção atual
                self.parent_view.selected_roles = []
                
                # Tenta atualizar a mensagem com a view atualizada
                edit_successful = False
                try:
                    # Atualiza a mensagem com a view atualizada e um texto explicativo
                    await interaction.response.edit_message(
                        content=f"**Configuração de Permissões**\nSelecione até {self.max_values} cargos que terão acesso a este serviço.\nDepois de selecionar, clique em **Confirmar**.",
                        view=self.parent_view
                    )
                    edit_successful = True
                except discord.NotFound:
                    logging.warning("Não foi possível editar a mensagem do select - ela pode ter sido excluída")
                except Exception as edit_error:
                    logging.error(f"Erro ao editar mensagem do select: {str(edit_error)}")
                
                # Se não conseguiu editar, tenta enviar uma nova mensagem
                if not edit_successful:
                    try:
                        await interaction.response.send_message(
                            f"**Configuração de Permissões**\nSelecione até {self.max_values} cargos que terão acesso a este serviço.\nDepois de selecionar, clique em **Confirmar**.",
                            view=self.parent_view,
                            ephemeral=True
                        )
                    except discord.InteractionResponded:
                        await interaction.followup.send(
                            f"⚠️ Não foi possível atualizar a mensagem original. Por favor, tente novamente.",
                            ephemeral=True
                        )
                
                # Envia uma mensagem adicional para informar o usuário
                try:
                    await interaction.followup.send(
                        f"✅ Cargos carregados! Agora você pode selecionar até {self.max_values} cargos.",
                        ephemeral=True
                    )
                except Exception as followup_error:
                    logging.error(f"Erro ao enviar followup de cargos carregados: {str(followup_error)}")
                
            except Exception as e:
                logging.error(f"Erro ao carregar cargos: {str(e)}")
                try:
                    await interaction.response.send_message(
                        f"❌ Ocorreu um erro ao carregar os cargos: {str(e)}",
                        ephemeral=True
                    )
                except discord.InteractionResponded:
                    await interaction.followup.send(
                        f"❌ Ocorreu um erro ao carregar os cargos: {str(e)}",
                        ephemeral=True
                    )
                except Exception as final_err:
                    logging.error(f"Erro fatal ao responder interação de cargos: {str(final_err)}")
            return
            
        try:
            # Atualiza a lista de cargos selecionados
            self.parent_view.selected_roles = self.values
            
            # Nomes dos cargos selecionados para exibição
            selected_roles_names = []
            for role_id in self.values:
                role = interaction.guild.get_role(int(role_id))
                if role:
                    selected_roles_names.append(role.name)
            
            role_names_str = ", ".join(selected_roles_names) if selected_roles_names else "nenhum"
            
            # Responde à interação
            try:
                await interaction.response.send_message(
                    f"✅ Selecionado(s) {len(self.parent_view.selected_roles)} cargo(s): {role_names_str}",
                    ephemeral=True
                )
            except discord.InteractionResponded:
                await interaction.followup.send(
                    f"✅ Selecionado(s) {len(self.parent_view.selected_roles)} cargo(s): {role_names_str}",
                    ephemeral=True
                )
        except Exception as e:
            logging.error(f"Erro ao processar seleção de cargos: {str(e)}")
            try:
                await interaction.response.send_message(
                    f"❌ Ocorreu um erro ao processar sua seleção: {str(e)}",
                    ephemeral=True
                )
            except discord.InteractionResponded:
                await interaction.followup.send(
                    f"❌ Ocorreu um erro ao processar sua seleção: {str(e)}",
                    ephemeral=True
                )
            except Exception as final_err:
                logging.error(f"Erro fatal ao responder interação de seleção: {str(final_err)}")


# View para testar lembretes
class TestarLembreteView(discord.ui.View):
    def __init__(self, servicos_config: Dict[str, Any], simular_tempo: int):
        super().__init__(timeout=None)
        self.add_item(TestarLembreteSelect(servicos_config, simular_tempo))


class TestarLembreteSelect(discord.ui.Select):
    def __init__(self, servicos_config: Dict[str, Any], simular_tempo: int):
        self.servicos_config = servicos_config
        self.simular_tempo = simular_tempo
        
        # Prepara as opções do dropdown apenas com serviços em uso
        options = []
        for key, config in servicos_config.items():
            if config["status"] == "em uso":
                options.append(
                    discord.SelectOption(
                        label=f"{key}: {config['nome'][:40]}", 
                        value=key,
                        description=f"Em uso por: {config['usuario']}"
                    )
                )
        
        if not options:
            options = [discord.SelectOption(label="Nenhum serviço em uso", value="none")]
        
        super().__init__(
            placeholder="Selecione um serviço para testar", 
            min_values=1, 
            max_values=1,
            options=options
        )
        
    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "none":
            await interaction.response.send_message(
                "Não há serviços em uso para testar.",
                ephemeral=True
            )
            return
            
        servico_id = self.values[0]
        config = self.servicos_config[servico_id]
        
        try:
            # Simula o tempo passado
            import datetime
            agora = datetime.datetime.now()
            tempo_simulado = agora - datetime.timedelta(hours=self.simular_tempo)
            
            # Atualiza os dados de uso
            if "usage_data" in config:
                usage_data = config["usage_data"]
                usage_data["timestamp"] = tempo_simulado.isoformat()
                usage_data["last_check"] = None
                usage_data["last_reminder"] = None
                usage_data["extension_count"] = 0
                config["usage_data"] = usage_data
            else:
                config["usage_data"] = {
                    "usuario": config["usuario"],
                    "user_id": interaction.user.id,
                    "timestamp": tempo_simulado.isoformat(),
                    "last_check": None,
                    "last_reminder": None,
                    "extension_count": 0
                }
            
            # Salva as alterações
            with open("services.json", "w", encoding="utf-8") as file:
                json.dump(self.servicos_config, file, indent=4)
            
            await interaction.response.send_message(
                f"✅ Tempo simulado para o serviço **{config['nome']}**.\n" +
                f"Simulando uso de {self.simular_tempo} horas atrás.",
                ephemeral=True
            )
            
        except Exception as e:
            logging.error(f"Erro ao simular tempo para o serviço {servico_id}: {str(e)}")
            await interaction.response.send_message(
                f"❌ Ocorreu um erro ao simular o tempo: {str(e)}",
                ephemeral=True
            ) 