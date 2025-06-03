import discord
import json
import logging
import datetime
from typing import Dict, Any, Optional, List
from .glassfish_models import UsageData
from .glassfish_config import CARGO_TI_ID, LOGS_CHANNEL_ID, MAX_EXTENSOES


class ProblemReportModal(discord.ui.Modal, title="Reportar Problema"):
    def __init__(self, servico: str, servicos_config: Dict[str, Any]):
        super().__init__()
        self.servico = servico
        self.servicos_config = servicos_config
        
        self.problema = discord.ui.TextInput(
            label="Descrição do Problema",
            style=discord.TextStyle.paragraph,
            placeholder="Descreva o problema encontrado...",
            required=True,
            max_length=1000
        )
        self.add_item(self.problema)
    
    async def on_submit(self, interaction: discord.Interaction):
        config = self.servicos_config[self.servico]
        try:
            guild = interaction.guild
            role = guild.get_role(CARGO_TI_ID)
            if role:
                mensagem = (
                    f"⚠️ Problema reportado no serviço **{config['nome']}** por <@{interaction.user.id}>\n"
                    f"**Descrição:** {self.problema.value}\n"
                    f"Aviso para o setor de TI: <@&{CARGO_TI_ID}>"
                )
                channel = guild.get_channel(LOGS_CHANNEL_ID)
                if channel:
                    await channel.send(mensagem)
                await interaction.response.send_message(
                    f"Problema reportado para o setor de TI.",
                    ephemeral=True
                )
                logging.info(f"{interaction.user.name} reportou um problema com {config['nome']}")
        except Exception as e:
            logging.error(f"Erro ao reportar problema: {str(e)}")
            await interaction.response.send_message(
                "Ocorreu um erro ao reportar o problema. Tente novamente mais tarde.",
                ephemeral=True
            )


class ServiceDropdown(discord.ui.View):
    def __init__(self, user_roles: Optional[List[int]], servicos_config: Dict[str, Any], check_permissions: bool = True):
        super().__init__(timeout=None)
        self.add_item(ServiceSelect(user_roles, servicos_config, check_permissions))


class ServiceSelect(discord.ui.Select):
    def __init__(self, user_roles: Optional[List[int]], servicos_config: Dict[str, Any], check_permissions: bool = True):
        self.servicos_config = servicos_config
        
        if check_permissions and user_roles:
            servicos_permitidos = {}
            for key, config in servicos_config.items():
                # Converter grupos_permitidos para inteiros
                grupos_permitidos = []
                for grupo in config["grupos_permitidos"]:
                    try:
                        grupos_permitidos.append(int(grupo))
                    except (ValueError, TypeError):
                        logging.error(f"ID de grupo inválido em {key}: {grupo}")
                
                # Verificar se o usuário tem algum dos cargos permitidos
                for role in user_roles:
                    if role in grupos_permitidos:
                        servicos_permitidos[key] = config
                        logging.info(f"Usuário tem permissão para o serviço {key} pelo cargo {role}")
                        break
                    else:
                        logging.debug(f"Cargo {role} não tem permissão para {key}. Grupos permitidos: {grupos_permitidos}")
        else:
            servicos_permitidos = servicos_config
        
        options = [
            discord.SelectOption(
                label=config["nome"],
                value=key,
                description=(f"Em uso por: {config['usuario']}" if config["status"] == "em uso" else "Disponível"),
                emoji="🔴" if config["status"] == "em uso" else "🟢"
            )
            for key, config in servicos_permitidos.items()
        ]
        
        if not options:
            options = [discord.SelectOption(label="Sem serviços disponíveis", value="none")]
        
        super().__init__(
            placeholder="Selecione um serviço...",
            min_values=1,
            max_values=1,
            options=options,
        )
    
    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "none":
            await interaction.response.send_message("Não há serviços disponíveis para você.", ephemeral=True)
            return
        
        user_roles = [role.id for role in interaction.user.roles]
        servico_selecionado = self.values[0]
        config = self.servicos_config[servico_selecionado]
        
        # Verifica permissões - Corrigido para usar inteiros diretamente
        grupos_permitidos = [int(x) for x in config["grupos_permitidos"]]
        tem_permissao = any(role in grupos_permitidos for role in user_roles)
        
        if not tem_permissao:
            logging.warning(f"Usuário {interaction.user.name} (cargos: {user_roles}) tentou acessar {servico_selecionado} sem permissão. Grupos permitidos: {grupos_permitidos}")
            await interaction.response.send_message(
                "Você não tem permissão para acessar este serviço.",
                ephemeral=True
            )
            return
        
        status_emoji = "🔴" if config["status"] == "em uso" else "🟢"
        usuario_atual = ""
        
        if config["status"] == "em uso":
            # Verifica informações de uso
            if "usage_data" in config:
                try:
                    usage_data_dict = config["usage_data"]
                    ultimo_uso = datetime.datetime.fromisoformat(usage_data_dict["timestamp"])
                    horas_em_uso = (datetime.datetime.now() - ultimo_uso).total_seconds() / 3600
                    
                    usuario_atual = f" (Em uso por: {config['usuario']} há {int(horas_em_uso)} horas)"
                except (KeyError, ValueError) as e:
                    logging.error(f"Erro ao processar dados de uso: {str(e)}")
                    usuario_atual = f" (Em uso por: {config['usuario']})"
            else:
                usuario_atual = f" (Em uso por: {config['usuario']})"
        
        logging.info(f"{interaction.user.name} selecionou o serviço: {config['nome']} (Status: {config['status']})")
        view = ActionButtons(servico_selecionado, self.servicos_config)
        await interaction.response.send_message(
            f"{status_emoji} Você selecionou o serviço **{config['nome']}**. Status atual: **{config['status']}**{usuario_atual}. Escolha uma ação:",
            view=view,
            ephemeral=True,
        )


class ActionButtons(discord.ui.View):
    def __init__(self, servico: str, servicos_config: Dict[str, Any]):
        super().__init__(timeout=None)
        self.servico = servico
        self.servicos_config = servicos_config
        self.add_item(self.create_button("Usar", "❎", discord.ButtonStyle.primary, f"usar_{servico}"))
        self.add_item(self.create_button("Liberar", "✅", discord.ButtonStyle.success, f"liberar_{servico}"))
        self.add_item(self.create_button("Reportar problema", "⚠️", discord.ButtonStyle.danger, f"reportar_{servico}"))

    def create_button(self, label: str, emoji: str, style: discord.ButtonStyle, custom_id: str):
        button = discord.ui.Button(label=label, emoji=emoji, style=style, custom_id=custom_id)
        button.callback = self.handle_callback
        return button

    async def handle_callback(self, interaction: discord.Interaction):
        custom_id = interaction.data["custom_id"]
        action_type = custom_id.split("_")[0]
        
        result = False
        if action_type == "usar":
            result = await self.usar(interaction)
        elif action_type == "liberar":
            result = await self.liberar(interaction)
        elif action_type == "reportar":
            await self.reportar_problema(interaction)
            return
            
        if result:
            # Atualiza o dropdown persistente
            cog = interaction.client.get_cog("GlassfishCog")
            if cog:
                await cog.refresh_persistent_message()

    async def usar(self, interaction: discord.Interaction):
        from .glassfish_config import TEMPO_MAXIMO_USO, LEMBRETE_INTERVALO
        
        config = self.servicos_config[self.servico]
        if config["status"] == "em uso":
            await interaction.response.send_message(
                f"O serviço **{config['nome']}** já está em uso por {config['usuario']}.",
                ephemeral=True,
            )
            logging.info(f"{interaction.user.name} tentou usar {config['nome']}, mas já está em uso")
            return False
            
        config["status"] = "em uso"
        config["usuario"] = interaction.user.name
        
        # Adiciona dados de uso
        usage_data = UsageData(interaction.user.name, interaction.user.id)
        config["usage_data"] = usage_data.to_dict()
        
        # Limpa a flag de notificação de timeout para permitir novas notificações
        if "notificacao_timeout" in config:
            del config["notificacao_timeout"]
            logging.info(f"Flag de notificação de timeout removida para {config['nome']}")
        
        self.salvar_em_json()
        channel = interaction.guild.get_channel(LOGS_CHANNEL_ID)
        if channel:
            await channel.send(
                f"O serviço **{config['nome']}** está sendo usado por <@{interaction.user.id}> <:stop:1328441358188417025>"
            )
            
        await interaction.response.send_message(
            f"O serviço **{config['nome']}** está sendo usado por <@{interaction.user.id}> <:stop:1328441358188417025>\n\n" +
            f"⚠️ **Importante**:\n" +
            f"- Você receberá lembretes a cada {LEMBRETE_INTERVALO} horas para confirmar que ainda está usando o serviço\n" +
            f"- Se não houver confirmação por {TEMPO_MAXIMO_USO} horas, o serviço será liberado automaticamente\n" +
            f"- Por favor, libere o serviço quando terminar de usá-lo",
            ephemeral=True,
        )
        logging.info(f"{interaction.user.name} começou a usar o serviço {config['nome']}")
        return True

    async def liberar(self, interaction: discord.Interaction):
        config = self.servicos_config[self.servico]
        if config["status"] == "disponível":
            await interaction.response.send_message(
                f"O serviço **{config['nome']}** já está disponível.",
                ephemeral=True,
            )
            logging.info(f"{interaction.user.name} tentou liberar {config['nome']}, mas já está disponível")
            return False
        elif config["usuario"] != interaction.user.name:
            # Verificação para TI ou administradores
            is_admin = any(role.id == CARGO_TI_ID for role in interaction.user.roles)
            
            if not is_admin:
                await interaction.response.send_message(
                    f"Apenas {config['usuario']} pode liberar este serviço. Se precisar de ajuda, contate o setor de TI.",
                    ephemeral=True,
                )
                logging.warning(f"{interaction.user.name} tentou liberar {config['nome']}, mas não tem permissão")
                return False
            else:
                # Administrador liberando o serviço de outro usuário
                logging.info(f"Admin {interaction.user.name} está liberando o serviço {config['nome']} que estava sendo usado por {config['usuario']}")
        
        # Remove dados de uso
        if "usage_data" in config:
            del config["usage_data"]
            
        # Limpa a flag de notificação de timeout
        if "notificacao_timeout" in config:
            del config["notificacao_timeout"]
            logging.info(f"Flag de notificação de timeout removida para {config['nome']}")
            
        config["status"] = "disponível"
        config["usuario"] = None
        self.salvar_em_json()
        channel = interaction.guild.get_channel(LOGS_CHANNEL_ID)
        if channel:
            await channel.send(
                f"O serviço **{config['nome']}** foi liberado por <@{interaction.user.id}> <:start:1328441356682793062>"
            )
        await interaction.response.send_message(
            f"O serviço **{config['nome']}** foi liberado por <@{interaction.user.id}> <:start:1328441356682793062>",
            ephemeral=True,
        )
        logging.info(f"{interaction.user.name} liberou o serviço {config['nome']}")
        return True

    async def reportar_problema(self, interaction: discord.Interaction):
        modal = ProblemReportModal(self.servico, self.servicos_config)
        await interaction.response.send_modal(modal)

    def salvar_em_json(self):
        try:
            with open("services.json", "w", encoding="utf-8") as file:
                json.dump(self.servicos_config, file, indent=4)
            logging.info("Configurações salvas com sucesso em services.json")
        except Exception as e:
            logging.error(f"Erro ao salvar em services.json: {str(e)}")


# Botão e modal para verificar o uso
class ConfirmUseButton(discord.ui.Button):
    def __init__(self, servico: str, servicos_config: Dict[str, Any]):
        super().__init__(
            label="Continuar usando o serviço",
            style=discord.ButtonStyle.primary,
            emoji="✅"
        )
        self.servico = servico
        self.servicos_config = servicos_config
        
    async def callback(self, interaction: discord.Interaction):
        from .glassfish_config import TEMPO_MAXIMO_USO
        
        config = self.servicos_config[self.servico]
        
        if config["status"] != "em uso" or config["usuario"] != interaction.user.name:
            await interaction.response.send_message(
                "Este serviço não está mais associado ao seu usuário.",
                ephemeral=True
            )
            return
        
        # Obtém o objeto de cog para acessar as configurações
        cog = interaction.client.get_cog("GlassfishCog")
        max_extensoes = MAX_EXTENSOES  # Valor padrão de segurança
        tempo_maximo = TEMPO_MAXIMO_USO  # Valor padrão de segurança
        
        if cog and hasattr(cog, 'service'):
            max_extensoes = cog.service.max_extensoes
            tempo_maximo = cog.service.tempo_maximo_uso
        
        # Atualiza os dados de uso
        if "usage_data" in config:
            try:
                usage_data = UsageData.from_dict(config["usage_data"])
                
                # Verifica se já passou do tempo máximo desde a última verificação
                ultima_verificacao = usage_data.last_check
                agora = datetime.datetime.now()
                
                # Se não houver verificação anterior, ou se a última verificação for muito antiga,
                # conta como uma extensão (exceto na primeira verificação)
                if ultima_verificacao:
                    horas_desde_verificacao = (agora - ultima_verificacao).total_seconds() / 3600
                    
                    # Se já passou do prazo, conta como uma extensão
                    if horas_desde_verificacao > tempo_maximo:
                        current_count = usage_data.increment_extension()
                        
                        # Verifica se excedeu o limite de extensões
                        if current_count > max_extensoes:
                            await interaction.response.send_message(
                                f"❌ Você já utilizou {current_count-1}/{max_extensoes} extensões permitidas e não pode mais estender o tempo de uso.\n" +
                                f"O serviço será liberado automaticamente em breve.\n" +
                                f"Por favor, libere o serviço manualmente ou solicite uma exceção ao setor de TI.",
                                ephemeral=True
                            )
                            return
                        else:
                            # Informa quantas extensões já foram usadas
                            await interaction.response.send_message(
                                f"✅ Tempo de uso estendido! Você utilizou {current_count}/{max_extensoes} extensões permitidas.\n" +
                                f"O prazo para uso do serviço **{config['nome']}** foi renovado. Obrigado!",
                                ephemeral=True
                            )
                    else:
                        # Confirmação normal, sem contar como extensão
                        await interaction.response.send_message(
                            f"✅ Você confirmou que ainda está usando o serviço **{config['nome']}**. Obrigado!",
                            ephemeral=True
                        )
                else:
                    # Primeira verificação, não conta como extensão
                    await interaction.response.send_message(
                        f"✅ Você confirmou que ainda está usando o serviço **{config['nome']}**. Obrigado!",
                        ephemeral=True
                    )
                
                # Atualiza o timestamp de verificação em todos os casos
                usage_data.update_check()
                config["usage_data"] = usage_data.to_dict()
                
            except Exception as e:
                logging.error(f"Erro ao atualizar dados de uso: {str(e)}")
                # Cria novo objeto de uso se houver erro
                usage_data = UsageData(interaction.user.name, interaction.user.id)
                usage_data.update_check()
                config["usage_data"] = usage_data.to_dict()
                
                await interaction.response.send_message(
                    f"✅ Você confirmou que ainda está usando o serviço **{config['nome']}**. Obrigado!",
                    ephemeral=True
                )
        else:
            # Cria novo objeto de uso se não existir
            usage_data = UsageData(interaction.user.name, interaction.user.id)
            usage_data.update_check()
            config["usage_data"] = usage_data.to_dict()
            
            await interaction.response.send_message(
                f"✅ Você confirmou que ainda está usando o serviço **{config['nome']}**. Obrigado!",
                ephemeral=True
            )
        
        # Notifica no canal de logs sobre a confirmação
        try:
            channel = interaction.guild.get_channel(LOGS_CHANNEL_ID)
            if channel and "usage_data" in config:
                extension_count = config["usage_data"].get("extension_count", 0)
                if extension_count > 0:
                    await channel.send(
                        f"🔄 **Extensão de Uso**: <@{interaction.user.id}> confirmou o uso do serviço **{config['nome']}** " +
                        f"({extension_count}/{max_extensoes} extensões utilizadas)"
                    )
                else:
                    await channel.send(
                        f"✅ **Confirmação de Uso**: <@{interaction.user.id}> confirmou que ainda está usando o serviço **{config['nome']}**"
                    )
        except Exception as e:
            logging.error(f"Erro ao enviar mensagem para o canal de logs: {str(e)}")
        
        # Salva as alterações
        try:
            with open("services.json", "w", encoding="utf-8") as file:
                json.dump(self.servicos_config, file, indent=4)
            logging.info(f"Uso confirmado para o serviço {self.servico} por {interaction.user.name}")
        except Exception as e:
            logging.error(f"Erro ao salvar serviços: {str(e)}")


class LiberarButton(discord.ui.Button):
    def __init__(self, servico: str, servicos_config: Dict[str, Any]):
        super().__init__(
            label="Liberar o serviço",
            style=discord.ButtonStyle.danger,
            emoji="🔄"
        )
        self.servico = servico
        self.servicos_config = servicos_config
        
    async def callback(self, interaction: discord.Interaction):
        config = self.servicos_config[self.servico]
        
        if config["status"] != "em uso":
            await interaction.response.send_message(
                "Este serviço já está disponível.",
                ephemeral=True
            )
            return
            
        if config["usuario"] != interaction.user.name:
            await interaction.response.send_message(
                f"Apenas {config['usuario']} pode liberar este serviço.",
                ephemeral=True
            )
            return
        
        # Remove dados de uso
        if "usage_data" in config:
            del config["usage_data"]
            
        # Limpa a flag de notificação de timeout
        if "notificacao_timeout" in config:
            del config["notificacao_timeout"]
            logging.info(f"Flag de notificação de timeout removida para {config['nome']} durante reset")
            
        config["status"] = "disponível"
        config["usuario"] = None
        
        # Salva as alterações
        try:
            with open("services.json", "w", encoding="utf-8") as file:
                json.dump(self.servicos_config, file, indent=4)
            logging.info(f"Serviço {self.servico} liberado por {interaction.user.name}")
        except Exception as e:
            logging.error(f"Erro ao salvar serviços: {str(e)}")
        
        # Notifica no canal de logs
        try:
            channel = interaction.guild.get_channel(LOGS_CHANNEL_ID)
            if channel:
                await channel.send(
                    f"O serviço **{config['nome']}** foi liberado por <@{interaction.user.id}> <:start:1328441356682793062>"
                )
        except Exception as e:
            logging.error(f"Erro ao enviar mensagem para o canal de logs: {str(e)}")
        
        await interaction.response.send_message(
            f"✅ Você liberou o serviço **{config['nome']}**.",
            ephemeral=True
        )


class CheckView(discord.ui.View):
    def __init__(self, servico: str, servicos_config: Dict[str, Any]):
        super().__init__(timeout=None)
        self.add_item(ConfirmUseButton(servico, servicos_config))
        self.add_item(LiberarButton(servico, servicos_config)) 