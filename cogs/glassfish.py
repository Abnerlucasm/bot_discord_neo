import discord
from discord.ext import commands, tasks
from discord import app_commands
import logging
import json
import datetime
import asyncio
import re
import os

# Carrega as configurações do arquivo JSON
config_file = "config.json"
try:
    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    # Carrega as configurações de cargos e canais
    CARGO_TI_ID = config["cargos"]["ti_id"]
    LOGS_CHANNEL_ID = config["canais"]["logs_id"]
    PERSISTENT_CHANNEL_ID = config["canais"]["persistent_id"]
    
    # Carrega as configurações de timeout
    TEMPO_MAXIMO_USO = config["timeout"]["tempo_maximo_uso"]
    VERIFICAR_INTERVALO = config["timeout"]["verificar_intervalo"]
    LEMBRETE_INTERVALO = config["timeout"]["lembrete_intervalo"]
    
    logging.info(f"Configurações carregadas com sucesso do arquivo {config_file}")
except Exception as e:
    # Valores padrão caso não consiga carregar do arquivo
    logging.error(f"Erro ao carregar configurações do arquivo {config_file}: {str(e)}")
    logging.warning("Usando valores padrão para as configurações")
    

# Classe para manter os dados de uso dos serviços
class UsageData:
    def __init__(self, usuario, user_id, timestamp=None):
        self.usuario = usuario
        self.user_id = user_id
        self.timestamp = timestamp or datetime.datetime.now()
        self.last_check = None
        self.last_reminder = None
        
    def update_timestamp(self):
        """Atualiza o timestamp para o momento atual"""
        self.timestamp = datetime.datetime.now()
        
    def update_check(self):
        """Registra que uma verificação foi feita"""
        self.last_check = datetime.datetime.now()
        
    def update_reminder(self):
        """Registra que um lembrete foi enviado"""
        self.last_reminder = datetime.datetime.now()
        
    def to_dict(self):
        """Converte os dados para um dicionário para salvar em JSON"""
        return {
            "usuario": self.usuario,
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat(),
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "last_reminder": self.last_reminder.isoformat() if self.last_reminder else None
        }
        
    @classmethod
    def from_dict(cls, data):
        """Cria uma instância a partir de um dicionário"""
        instance = cls(data["usuario"], data["user_id"])
        instance.timestamp = datetime.datetime.fromisoformat(data["timestamp"])
        if data.get("last_check"):
            instance.last_check = datetime.datetime.fromisoformat(data["last_check"])
        if data.get("last_reminder"):
            instance.last_reminder = datetime.datetime.fromisoformat(data["last_reminder"])
        return instance

class ProblemReportModal(discord.ui.Modal, title="Reportar Problema"):
    def __init__(self, servico, servicos_config):
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
    def __init__(self, user_roles, servicos_config, check_permissions=True):
        super().__init__(timeout=None)
        self.add_item(ServiceSelect(user_roles, servicos_config, check_permissions))

class ServiceSelect(discord.ui.Select):
    def __init__(self, user_roles, servicos_config, check_permissions=True):
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
            usage_data = None
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
    def __init__(self, servico, servicos_config):
        super().__init__(timeout=None)
        self.servico = servico
        self.servicos_config = servicos_config
        self.add_item(self.create_button("Usar", "❎", discord.ButtonStyle.primary, f"usar_{servico}"))
        self.add_item(self.create_button("Liberar", "✅", discord.ButtonStyle.success, f"liberar_{servico}"))
        self.add_item(self.create_button("Reportar problema", "⚠️", discord.ButtonStyle.danger, f"reportar_{servico}"))

    def create_button(self, label, emoji, style, custom_id):
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
        
        self.salvar_em_json()
        channel = interaction.guild.get_channel(LOGS_CHANNEL_ID)
        if channel:
            await channel.send(
                f"O serviço **{config['nome']}** está sendo usado por <@{interaction.user.id}> <:stop:1328441358188417025>"
            )
            
        # Obtém as configurações de timeout do cog
        cog = interaction.client.get_cog("GlassfishCog")
        tempo_maximo = TEMPO_MAXIMO_USO  # Valor padrão
        intervalo_lembrete = LEMBRETE_INTERVALO  # Valor padrão
        
        if cog:
            tempo_maximo = cog.tempo_maximo_uso
            intervalo_lembrete = cog.lembrete_intervalo
            
        await interaction.response.send_message(
            f"O serviço **{config['nome']}** está sendo usado por <@{interaction.user.id}> <:stop:1328441358188417025>\n\n" +
            f"⚠️ **Importante**:\n" +
            f"- Você receberá lembretes a cada {intervalo_lembrete} horas para confirmar que ainda está usando o serviço\n" +
            f"- Se não houver confirmação por {tempo_maximo} horas, o serviço será liberado automaticamente\n" +
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
    def __init__(self, servico, servicos_config):
        super().__init__(
            label="Continuar usando o serviço",
            style=discord.ButtonStyle.primary,
            emoji="✅"
        )
        self.servico = servico
        self.servicos_config = servicos_config
        
    async def callback(self, interaction: discord.Interaction):
        config = self.servicos_config[self.servico]
        
        if config["status"] != "em uso" or config["usuario"] != interaction.user.name:
            await interaction.response.send_message(
                "Este serviço não está mais associado ao seu usuário.",
                ephemeral=True
            )
            return
        
        # Atualiza os dados de uso
        if "usage_data" in config:
            try:
                usage_data = UsageData.from_dict(config["usage_data"])
                usage_data.update_check()
                config["usage_data"] = usage_data.to_dict()
            except Exception as e:
                logging.error(f"Erro ao atualizar dados de uso: {str(e)}")
                # Cria novo objeto de uso se houver erro
                usage_data = UsageData(interaction.user.name, interaction.user.id)
                config["usage_data"] = usage_data.to_dict()
        else:
            # Cria novo objeto de uso se não existir
            usage_data = UsageData(interaction.user.name, interaction.user.id)
            config["usage_data"] = usage_data.to_dict()
        
        # Salva as alterações
        try:
            with open("services.json", "w", encoding="utf-8") as file:
                json.dump(self.servicos_config, file, indent=4)
            logging.info(f"Uso confirmado para o serviço {self.servico} por {interaction.user.name}")
        except Exception as e:
            logging.error(f"Erro ao salvar serviços: {str(e)}")
        
        await interaction.response.send_message(
            f"✅ Você confirmou que ainda está usando o serviço **{config['nome']}**. Obrigado!",
            ephemeral=True
        )

class LiberarButton(discord.ui.Button):
    def __init__(self, servico, servicos_config):
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
    def __init__(self, servico, servicos_config):
        super().__init__(timeout=None)
        self.add_item(ConfirmUseButton(servico, servicos_config))
        self.add_item(LiberarButton(servico, servicos_config))

class GlassfishCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.persistent_message = None
        
        # Configurações de timeout - carregadas das variáveis globais
        self.tempo_maximo_uso = TEMPO_MAXIMO_USO
        self.verificar_intervalo = VERIFICAR_INTERVALO
        self.lembrete_intervalo = LEMBRETE_INTERVALO
        
        # Inicia o loop de verificação de timeout
        self.check_services_loop.start()
    
    @app_commands.command(name="liberar_todos_glassfish", description="Libera todos os serviços Glassfish em uso (apenas TI)")
    async def liberar_todos_glassfish(self, interaction: discord.Interaction):
        """
        Libera todos os serviços Glassfish que estão em uso.
        Este comando só pode ser executado por usuários com o cargo de TI.
        """
        try:
            # Verifica se o usuário tem permissão (cargo de TI)
            is_ti = any(role.id == CARGO_TI_ID for role in interaction.user.roles)
            if not is_ti:
                await interaction.response.send_message(
                    "❌ Apenas usuários com cargo de TI podem executar este comando.",
                    ephemeral=True
                )
                logging.warning(f"{interaction.user.name} tentou liberar todos os serviços sem permissão")
                return
            
            # Carrega os serviços do arquivo
            await interaction.response.defer(ephemeral=True)
            servicos_liberados = 0
            servicos_em_uso = []
            
            # Obtém a lista de serviços em uso
            for servico_id, config in self.bot.servicos_config.items():
                if config["status"] == "em uso":
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
                config = self.bot.servicos_config[servico_id]
                
                # Remove dados de uso
                if "usage_data" in config:
                    del config["usage_data"]
                
                config["status"] = "disponível"
                config["usuario"] = None
                servicos_liberados += 1
            
            # Salva as alterações
            with open("services.json", "w", encoding="utf-8") as file:
                json.dump(self.bot.servicos_config, file, indent=4)
            
            # Atualiza a mensagem persistente
            await self.refresh_persistent_message()
            
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
    
    @app_commands.command(name="testar_lembrete_glassfish", description="Envia um lembrete de teste para um serviço específico (apenas desenvolvimento)")
    @app_commands.describe(
        simular_tempo="Simular quantas horas de uso do serviço"
    )
    async def testar_lembrete_glassfish(self, interaction: discord.Interaction, simular_tempo: int = 3):
        """
        Envia um lembrete de teste para um serviço específico.
        Este comando só pode ser executado por usuários com o cargo de TI.
        Útil para testar o sistema de lembretes sem precisar esperar o tempo real.
        """
        try:
            logging.info(f"Comando testar_lembrete_glassfish executado por {interaction.user.name}")
            
            # Verifica se o usuário tem permissão (cargo de TI)
            is_ti = any(role.id == CARGO_TI_ID for role in interaction.user.roles)
            if not is_ti:
                await interaction.response.send_message(
                    "❌ Apenas usuários com cargo de TI podem executar este comando.",
                    ephemeral=True
                )
                logging.warning(f"Usuário {interaction.user.name} tentou executar testar_lembrete_glassfish sem permissão")
                return
        
            # Mostra o seletor de serviços
            view = TestarLembreteView(self.bot.servicos_config, simular_tempo)
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
    
    def cog_unload(self):
        # Para o loop quando o cog for descarregado
        self.check_services_loop.cancel()
        
    def reload_config(self):
        """Recarrega as configurações do arquivo config.json"""
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            # Atualiza as configurações de timeout
            self.tempo_maximo_uso = config["timeout"].get("tempo_maximo_uso", TEMPO_MAXIMO_USO)
            self.verificar_intervalo = config["timeout"].get("verificar_intervalo", VERIFICAR_INTERVALO)
            self.lembrete_intervalo = config["timeout"].get("lembrete_intervalo", LEMBRETE_INTERVALO)
            
            logging.info(f"Configurações recarregadas com sucesso do arquivo {config_file}")
            return True
        except Exception as e:
            logging.error(f"Erro ao recarregar configurações do arquivo {config_file}: {str(e)}")
            return False
        
    def _save_config_to_file(self):
        """Salva as configurações atuais no arquivo config.json"""
        try:
            # Carrega o arquivo atual para não sobrescrever outras configurações
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                config = {
                    "cargos": {"ti_id": CARGO_TI_ID},
                    "canais": {
                        "logs_id": LOGS_CHANNEL_ID,
                        "persistent_id": PERSISTENT_CHANNEL_ID
                    },
                    "timeout": {}
                }
            
            # Atualiza as configurações de timeout
            config["timeout"]["tempo_maximo_uso"] = self.tempo_maximo_uso
            config["timeout"]["verificar_intervalo"] = self.verificar_intervalo
            config["timeout"]["lembrete_intervalo"] = self.lembrete_intervalo
            
            # Salva o arquivo
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
                
            logging.info(f"Configurações de timeout salvas no arquivo {config_file}")
            return True
        except Exception as e:
            logging.error(f"Erro ao salvar configurações no arquivo {config_file}: {str(e)}")
            return False
        
    @tasks.loop(minutes=15)  # Verifica a cada 15 minutos em vez de 1 hora
    async def check_services_loop(self):
        """Loop para verificar o timeout dos serviços"""
        try:
            logging.info("Iniciando verificação de timeout de serviços Glassfish")
            
            # Carrega os serviços
            try:
                with open("services.json", "r", encoding="utf-8") as file:
                    servicos_config = json.load(file)
            except Exception as e:
                logging.error(f"Erro ao carregar services.json: {str(e)}")
                return

            agora = datetime.datetime.now()
            alteracoes = False
            servicos_verificados = 0
            servicos_liberados = 0
            
            # Verifica cada serviço
            for servico_id, config in servicos_config.items():
                if config["status"] == "em uso" and "usage_data" in config:
                    servicos_verificados += 1
                    try:
                        # Converte os dados de uso
                        usage_data_dict = config["usage_data"]
                        ultimo_uso = datetime.datetime.fromisoformat(usage_data_dict["timestamp"])
                        user_id = usage_data_dict.get("user_id")
                        
                        # Calcula o tempo em uso
                        horas_em_uso = (agora - ultimo_uso).total_seconds() / 3600
                        
                        # Formatação para exibir horas e minutos
                        segundos_em_uso = (agora - ultimo_uso).total_seconds()
                        horas_formatadas = int(segundos_em_uso / 3600)
                        minutos_formatados = int((segundos_em_uso % 3600) / 60)
                        tempo_formatado = f"{horas_formatadas} horas e {minutos_formatados} minutos"
                        
                        # Verifica último check se existir
                        ultima_verificacao = None
                        if usage_data_dict.get("last_check"):
                            try:
                                ultima_verificacao = datetime.datetime.fromisoformat(usage_data_dict["last_check"])
                                horas_desde_verificacao = (agora - ultima_verificacao).total_seconds() / 3600
                            except (ValueError, TypeError) as e:
                                logging.error(f"Erro ao processar última verificação: {str(e)}")
                                horas_desde_verificacao = horas_em_uso
                        else:
                            horas_desde_verificacao = horas_em_uso
                            
                        # Verifica último lembrete se existir
                        ultimo_lembrete = None
                        if usage_data_dict.get("last_reminder"):
                            try:
                                ultimo_lembrete = datetime.datetime.fromisoformat(usage_data_dict["last_reminder"])
                                horas_desde_lembrete = (agora - ultimo_lembrete).total_seconds() / 3600
                            except (ValueError, TypeError) as e:
                                logging.error(f"Erro ao processar último lembrete: {str(e)}")
                                horas_desde_lembrete = horas_em_uso
                        else:
                            horas_desde_lembrete = horas_em_uso
                        
                        logging.info(f"Serviço {servico_id} em uso por {config['usuario']} há {horas_em_uso:.1f} horas")
                        
                        # Timeout automático após tempo_maximo_uso horas sem verificação
                        # OU após lembrete_intervalo horas sem resposta ao lembrete
                        deve_liberar = False
                        motivo_liberacao = ""
                        
                        # Formatação do tempo de verificação
                        segundos_verificacao = horas_desde_verificacao * 3600
                        verificacao_horas = int(segundos_verificacao / 3600)
                        verificacao_minutos = int((segundos_verificacao % 3600) / 60)
                        verificacao_formatado = f"{verificacao_horas} horas e {verificacao_minutos} minutos"
                        
                        # Formatação do tempo desde o lembrete
                        segundos_lembrete = horas_desde_lembrete * 3600
                        lembrete_horas = int(segundos_lembrete / 3600)
                        lembrete_minutos = int((segundos_lembrete % 3600) / 60)
                        lembrete_formatado = f"{lembrete_horas} horas e {lembrete_minutos} minutos"
                        
                        if horas_desde_verificacao > self.tempo_maximo_uso:
                            deve_liberar = True
                            motivo_liberacao = f"após {verificacao_formatado} sem verificação"
                        elif ultimo_lembrete and not ultima_verificacao:
                            # Se há lembrete mas nunca houve verificação
                            if horas_desde_lembrete > self.lembrete_intervalo:
                                deve_liberar = True
                                motivo_liberacao = f"após {lembrete_formatado} sem resposta ao lembrete"
                        elif ultimo_lembrete and ultima_verificacao:
                            # Se o último lembrete é mais recente que a última verificação
                            if ultimo_lembrete > ultima_verificacao and horas_desde_lembrete > self.lembrete_intervalo:
                                deve_liberar = True
                                motivo_liberacao = f"após {lembrete_formatado} sem resposta ao lembrete"
                        
                        if deve_liberar:
                            # Formatação para exibir horas e minutos do tempo total de uso
                            segundos_em_uso = (agora - ultimo_uso).total_seconds()
                            horas_formatadas = int(segundos_em_uso / 3600)
                            minutos_formatados = int((segundos_em_uso % 3600) / 60)
                            tempo_uso = f"{horas_formatadas} horas e {minutos_formatados} minutos"
                            
                            # Libera o serviço automaticamente
                            logging.warning(f"Timeout automático para o serviço {servico_id} - {config['nome']} {motivo_liberacao}")
                            
                            # Notifica no canal de logs
                            channel = self.bot.get_channel(LOGS_CHANNEL_ID)
                            if channel:
                                await channel.send(
                                    f"⏰ **Timeout Automático**: O serviço **{config['nome']}** foi liberado automaticamente {motivo_liberacao}. " +
                                    f"Estava sendo usado por **{config['usuario']}** por {tempo_uso}."
                                )
                            
                            # Atualiza o estado do serviço
                            config["status"] = "disponível"
                            config["usuario"] = None
                            if "usage_data" in config:
                                del config["usage_data"]
                            
                            alteracoes = True
                        
                        # Envia lembretes para verificação a cada lembrete_intervalo horas
                        elif horas_desde_lembrete > self.lembrete_intervalo and user_id:
                            # Tenta obter o usuário para enviar DM
                            try:
                                user = await self.bot.fetch_user(int(user_id))
                                
                                # Cria uma view com botões para confirmar o uso ou liberar
                                view = CheckView(servico_id, self.bot.servicos_config)
                                
                                # Calcula tempo em horas e minutos para exibição mais precisa
                                segundos_em_uso = (agora - ultimo_uso).total_seconds()
                                horas_formatadas = int(segundos_em_uso / 3600)
                                minutos_formatados = int((segundos_em_uso % 3600) / 60)
                                tempo_formatado = f"{horas_formatadas} horas e {minutos_formatados} minutos"
                                
                                # Envia mensagem para o usuário
                                await user.send(
                                    f"⚠️ **Lembrete de uso do Glassfish**\n" +
                                    f"Você está usando o serviço **{config['nome']}** há {tempo_formatado}.\n" +
                                    f"Por favor, confirme se ainda está utilizando este serviço ou libere-o se não estiver mais usando.",
                                    view=view
                                )
                                
                                logging.info(f"Lembrete enviado para {config['usuario']} (ID: {user_id}) sobre o serviço {servico_id}")
                                
                                # Atualiza o timestamp do último lembrete
                                usage_data = UsageData.from_dict(usage_data_dict)
                                usage_data.update_reminder()
                                config["usage_data"] = usage_data.to_dict()
                                alteracoes = True
                                
                            except Exception as e:
                                logging.error(f"Erro ao enviar lembrete para o usuário {user_id}: {str(e)}")
                    
                    except Exception as e:
                        logging.error(f"Erro ao processar verificação para o serviço {servico_id}: {str(e)}")
            
            # Log do resultado da verificação
            if servicos_verificados > 0:
                logging.info(f"Verificação concluída: {servicos_verificados} serviços verificados, {servicos_liberados} liberados")
            
            # Salva as alterações se houver mudanças
            if alteracoes:
                try:
                    with open("services.json", "w", encoding="utf-8") as file:
                        json.dump(servicos_config, file, indent=4)
                    logging.info("Alterações em serviços salvas após verificação de timeout")
                    
                    # Atualiza a mensagem persistente
                    await self.refresh_persistent_message()
                except Exception as e:
                    logging.error(f"Erro ao salvar alterações em services.json: {str(e)}")
            
        except Exception as e:
            logging.error(f"Erro geral na verificação de timeout: {str(e)}")
            
    @check_services_loop.before_loop
    async def before_check_services_loop(self):
        """Espera o bot estar pronto antes de iniciar o loop"""
        await self.bot.wait_until_ready()
        
        # Executa uma verificação imediata ao iniciar
        logging.info("Executando verificação inicial de serviços")
        await self.check_services_loop()
        
        # Espera 15 minutos antes de começar o loop regular
        await asyncio.sleep(900)  # 15 minutos em segundos

    @commands.Cog.listener()
    async def on_ready(self):
        """Configura a mensagem persistente quando o bot iniciar"""
        # Recarrega as configurações do arquivo
        self.reload_config()
        
        await self.setup_persistent_message()

        # Sincroniza os comandos para garantir que apareçam
        try:
            # Lista de todos os comandos que devem ser registrados
            app_commands_list = [
                self.recarregar_config_glassfish,
                self.glassfish,
                self.verificacao_forcada_glassfish,
                self.configurar_timeout_glassfish,
                self.obter_timeout_glassfish,
                self.relatorio_glassfish,
                self.adicionar_glassfish,
                self.editar_glassfish,
                self.remover_glassfish,
                self.liberar_todos_glassfish,
                self.testar_lembrete_glassfish
            ]
            
            # Adiciona explicitamente cada comando que não esteja já registrado
            added_commands = []
            for cmd in app_commands_list:
                cmd_name = cmd.qualified_name
                
                # Verifica se o comando já existe na árvore principal
                cmd_exists = any(registered_cmd.name == cmd_name for registered_cmd in self.bot.tree.get_commands())
                
                if not cmd_exists:
                    try:
                        # Se não existe, adiciona à árvore de comandos
                        self.bot.tree.add_command(cmd)
                        added_commands.append(cmd_name)
                        logging.info(f"Comando {cmd_name} adicionado à árvore de comandos")
                    except Exception as cmd_err:
                        logging.error(f"Erro ao adicionar comando {cmd_name}: {str(cmd_err)}")
            
            # Sincroniza a árvore de comandos
            sync_result = await self.bot.tree.sync()
            sync_names = [cmd.name for cmd in sync_result]
            
            if added_commands:
                logging.info(f"Comandos adicionados: {', '.join(added_commands)}")
            
            logging.info(f"Comandos sincronizados com sucesso: {', '.join(sync_names)}")
        except Exception as e:
            logging.error(f"Erro ao sincronizar comandos: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
    
    @app_commands.command(name="glassfish", description="Lista os serviços disponíveis")
    async def glassfish(self, interaction: discord.Interaction):
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
            
            # Verificar permissões para cada serviço
            servicos_permitidos = {}
            for key, config in self.bot.servicos_config.items():
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
            
            view = ServiceDropdown(user_roles, self.bot.servicos_config)
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
    
    @app_commands.command(name="recarregar_config_glassfish", description="Recarrega as configurações do Glassfish do arquivo (apenas TI)")
    async def recarregar_config_glassfish(self, interaction: discord.Interaction):
        """Recarrega as configurações do arquivo config.json"""
        # Verifica se o usuário tem permissão (equipe de TI)
        is_ti = any(role.id == CARGO_TI_ID for role in interaction.user.roles)
        if not is_ti:
            await interaction.response.send_message(
                "Apenas o setor de TI pode recarregar as configurações.",
                ephemeral=True
            )
            return
            
        success = self.reload_config()
        
        if success:
            await interaction.response.send_message(
                f"✅ Configurações recarregadas com sucesso:\n" +
                f"- Tempo máximo de uso: {self.tempo_maximo_uso} horas\n" +
                f"- Intervalo de lembretes: {self.lembrete_intervalo} horas\n" +
                f"- Verificação de serviços: a cada {self.verificar_intervalo} hora(s)",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "❌ Ocorreu um erro ao recarregar as configurações. Verifique os logs para mais detalhes.",
                ephemeral=True
            )

    @app_commands.command(name="verificacao_forcada_glassfish", description="Força a verificação de timeout dos serviços Glassfish (apenas TI)")
    async def verificacao_forcada_glassfish(self, interaction: discord.Interaction):
        """Comando para forçar a verificação dos serviços (apenas TI)"""
        # Verifica se o usuário tem permissão
        is_ti = any(role.id == CARGO_TI_ID for role in interaction.user.roles)
        if not is_ti:
            await interaction.response.send_message(
                "Apenas o setor de TI pode executar este comando.",
                ephemeral=True
            )
            return
        
        await interaction.response.send_message(
            "Iniciando verificação forçada dos serviços Glassfish...",
            ephemeral=True
        )
        
        # Executa a verificação
        try:
            await self.check_services_loop()
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
    
    @app_commands.command(name="configurar_timeout_glassfish", description="Configura o tempo máximo de uso dos serviços Glassfish (apenas TI)")
    @app_commands.describe(
        horas="Número de horas após o qual o serviço será liberado automaticamente se não for confirmado",
        lembrete="Intervalo em horas entre lembretes para o usuário"
    )
    async def configurar_timeout_glassfish(self, interaction: discord.Interaction, horas: int, lembrete: int = None):
        """Configura o tempo máximo de uso dos serviços Glassfish"""
        # Verifica se o usuário tem permissão (equipe de TI)
        is_ti = any(role.id == CARGO_TI_ID for role in interaction.user.roles)
        if not is_ti:
            await interaction.response.send_message(
                "Apenas o setor de TI pode configurar o tempo máximo de uso dos serviços.",
                ephemeral=True
            )
            return
            
        # Valida os parâmetros
        if horas < 1 or horas > 72:
            await interaction.response.send_message(
                "O tempo máximo de uso deve estar entre 1 e 72 horas.",
                ephemeral=True
            )
            return
            
        if lembrete is not None:
            if lembrete < 1 or lembrete >= horas:
                await interaction.response.send_message(
                    f"O intervalo entre lembretes deve estar entre 1 e {horas-1} horas.",
                    ephemeral=True
                )
                return
            self.lembrete_intervalo = lembrete
            
        # Atualiza as configurações
        old_timeout = self.tempo_maximo_uso
        self.tempo_maximo_uso = horas
        self.verificar_intervalo = max(1, horas // 4)  # Ajusta automaticamente o intervalo de verificação
        
        # Se o lembrete não foi especificado, ajustamos proporcionalmente
        if lembrete is None:
            self.lembrete_intervalo = max(1, horas // 2)
            
        # Salva as configurações atualizadas no arquivo
        self._save_config_to_file()
            
        # Log da alteração
        logging.info(f"Configurações de timeout alteradas por {interaction.user.name}: Tempo máximo = {horas}h, Lembrete = {self.lembrete_intervalo}h")
        
        # Atualiza a mensagem persistente para refletir a nova configuração
        await self.setup_persistent_message()
        
        # Notifica no canal de logs
        channel = interaction.guild.get_channel(LOGS_CHANNEL_ID)
        if channel:
            await channel.send(
                f"⚙️ **Configuração de Timeout**: <@{interaction.user.id}> alterou o tempo máximo de uso dos serviços Glassfish de {old_timeout}h para {horas}h."
            )
            
        await interaction.response.send_message(
            f"✅ Configurações de timeout atualizadas:\n" +
            f"- Tempo máximo de uso: {horas} horas\n" +
            f"- Intervalo de lembretes: {self.lembrete_intervalo} horas\n" +
            f"Os serviços em uso serão verificados a cada {self.verificar_intervalo} hora(s).",
            ephemeral=True
        )
    
    @app_commands.command(name="obter_timeout_glassfish", description="Mostra as configurações atuais de timeout dos serviços Glassfish")
    async def obter_timeout_glassfish(self, interaction: discord.Interaction):
        """Mostra as configurações atuais de timeout dos serviços Glassfish"""
        await interaction.response.send_message(
            f"**Configurações atuais de timeout dos serviços Glassfish:**\n" +
            f"- Tempo máximo sem confirmação: {self.tempo_maximo_uso} horas\n" +
            f"- Intervalo de lembretes: {self.lembrete_intervalo} horas\n" +
            f"- Verificação de serviços: a cada {self.verificar_intervalo} hora(s)",
            ephemeral=True
        )
        
    @app_commands.command(name="relatorio_glassfish", description="Gera um relatório de uso e notificações dos serviços Glassfish (apenas TI)")
    async def relatorio_glassfish(self, interaction: discord.Interaction):
        """Gera um relatório detalhado de uso e notificações dos serviços Glassfish"""
        # Verifica se o usuário tem permissão (equipe de TI)
        is_ti = any(role.id == CARGO_TI_ID for role in interaction.user.roles)
        if not is_ti:
            await interaction.response.send_message(
                "Apenas o setor de TI pode gerar relatórios dos serviços.",
                ephemeral=True
            )
            return
        
        # Indica que está processando
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Carrega os serviços
            with open("services.json", "r", encoding="utf-8") as file:
                servicos_config = json.load(file)
            
            # Cria listas para organizar os dados
            em_uso = []
            notificados = []
            liberados_auto = []  # Vamos buscar nos logs do último dia
            
            # Data atual para cálculos
            agora = datetime.datetime.now()
            
            # Processa serviços em uso
            for servico_id, config in servicos_config.items():
                if config["status"] == "em uso":
                    # Calcula o tempo de uso mesmo sem usage_data disponível
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
                                
                                # Se recebeu lembrete mas não confirmou, ou se a última confirmação é anterior ao último lembrete
                                if not usage_data.get("last_check") or (
                                    last_reminder > datetime.datetime.fromisoformat(usage_data["last_check"])
                                ):
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
            
            # Serviços liberados automaticamente
            resposta.append("\n**⏰ Serviços Liberados Automaticamente (últimas 24h):**")
            if liberados_auto:
                for servico in liberados_auto:
                    if "erro" not in servico:
                        resposta.append(f"• **{servico['nome']}** - Usuário: {servico['usuario']} | Quando: {servico['quando']}")
                    else:
                        resposta.append(f"• {servico['erro']}")
            else:
                resposta.append("• Nenhum serviço foi liberado automaticamente nas últimas 24 horas.")
            
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

    async def setup_persistent_message(self):
        """Configura ou atualiza a mensagem persistente no canal específico"""
        channel = self.bot.get_channel(PERSISTENT_CHANNEL_ID)
        if not channel:
            logging.error(f"Canal {PERSISTENT_CHANNEL_ID} não encontrado")
            return

        # Procura por mensagem existente do bot
        async for message in channel.history(limit=100):
            if message.author == self.bot.user and "**Serviços Glassfish**" in message.content:
                self.persistent_message = message
                break

        view = ServiceDropdown(None, self.bot.servicos_config, check_permissions=False)
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

    async def refresh_persistent_message(self):
        """Atualiza a mensagem persistente quando houver mudanças"""
        if self.persistent_message:
            view = ServiceDropdown(None, self.bot.servicos_config, check_permissions=False)
            await self.persistent_message.edit(view=view)
            logging.info("Mensagem persistente do Glassfish atualizada")

    @app_commands.command(name="adicionar_glassfish", description="Adiciona um novo serviço Glassfish (apenas TI)")
    async def adicionar_glassfish(self, interaction: discord.Interaction):
        """Adiciona um novo serviço Glassfish usando um modal"""
        # Verifica se o usuário tem permissão (equipe de TI)
        is_ti = any(role.id == CARGO_TI_ID for role in interaction.user.roles)
        if not is_ti:
            await interaction.response.send_message(
                "Apenas o setor de TI pode gerenciar os serviços.",
                ephemeral=True
            )
            return
        
        # Abre um modal para adicionar o serviço
        await interaction.response.send_modal(GlassfishAddModal(self.bot.servicos_config, self.bot))
    
    @app_commands.command(name="editar_glassfish", description="Edita um serviço Glassfish existente (apenas TI)")
    async def editar_glassfish(self, interaction: discord.Interaction):
        """Exibe uma lista de serviços para editar"""
        # Verifica se o usuário tem permissão (equipe de TI)
        is_ti = any(role.id == CARGO_TI_ID for role in interaction.user.roles)
        if not is_ti:
            await interaction.response.send_message(
                "Apenas o setor de TI pode gerenciar os serviços.",
                ephemeral=True
            )
            return
            
        try:
            # Carrega os serviços
            with open("services.json", "r", encoding="utf-8") as file:
                servicos_config = json.load(file)
                
            # Cria uma view com um dropdown para selecionar o serviço
            view = GlassfishSelectView(servicos_config, "editar")
            
            # Se não houver serviços, informa ao usuário
            if not servicos_config:
                await interaction.response.send_message(
                    "Não há serviços configurados para editar.",
                    ephemeral=True
                )
                return
                
            # Envia a mensagem com o dropdown
            await interaction.response.send_message(
                "Selecione o serviço que deseja editar:",
                view=view,
                ephemeral=True
            )
            
        except Exception as e:
            logging.error(f"Erro ao preparar edição de serviço Glassfish: {str(e)}")
            await interaction.response.send_message(
                f"Ocorreu um erro ao selecionar o serviço: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="remover_glassfish", description="Remove um serviço Glassfish (apenas TI)")
    async def remover_glassfish(self, interaction: discord.Interaction):
        """Exibe uma lista de serviços para remover"""
        # Verifica se o usuário tem permissão (equipe de TI)
        is_ti = any(role.id == CARGO_TI_ID for role in interaction.user.roles)
        if not is_ti:
            await interaction.response.send_message(
                "Apenas o setor de TI pode gerenciar os serviços.",
                ephemeral=True
            )
            return
            
        try:
            # Carrega os serviços
            with open("services.json", "r", encoding="utf-8") as file:
                servicos_config = json.load(file)
                
            # Cria uma view com um dropdown para selecionar o serviço
            view = GlassfishSelectView(servicos_config, "remover")
            
            # Se não houver serviços, informa ao usuário
            if not servicos_config:
                await interaction.response.send_message(
                    "Não há serviços configurados para remover.",
                    ephemeral=True
                )
                return
                
            # Envia a mensagem com o dropdown
            await interaction.response.send_message(
                "Selecione o serviço que deseja remover:",
                view=view,
                ephemeral=True
            )
            
        except Exception as e:
            logging.error(f"Erro ao preparar remoção de serviço Glassfish: {str(e)}")
            await interaction.response.send_message(
                f"Ocorreu um erro ao selecionar o serviço: {str(e)}",
                ephemeral=True
            )

# Novo modal para adicionar serviço
class GlassfishAddModal(discord.ui.Modal, title='Adicionar Serviço Glassfish'):
    def __init__(self, servicos_config, bot=None):
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

# View com dropdown para selecionar um serviço
class GlassfishSelectView(discord.ui.View):
    def __init__(self, servicos_config, action_type):
        super().__init__(timeout=180)  # 3 minutos
        self.add_item(GlassfishSelect(servicos_config, action_type))

class GlassfishSelect(discord.ui.Select):
    def __init__(self, servicos_config, action_type):
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

# Classe para solicitar os cargos permitidos ao adicionar um serviço
class RolePermissionView(discord.ui.View):
    def __init__(self, service_data, serv_id, bot):
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
    def __init__(self, parent_view):
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

class ConfirmRemoveView(discord.ui.View):
    def __init__(self, servico_id, servicos_config):
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

# Adicionar a classe GlassfishEditModal após a classe GlassfishAddModal
class GlassfishEditModal(discord.ui.Modal, title='Editar Serviço Glassfish'):
    def __init__(self, servico_id, servicos_config):
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
    # Comando liberar_todos_glassfish já foi definido no início da classe GlassfishCog
    # Esta duplicação foi removida para evitar conflitos

    @app_commands.command(name="testar_lembrete_glassfish", description="Envia um lembrete de teste para um serviço específico (apenas desenvolvimento)")
    @app_commands.describe(
        servico_id="ID do serviço para testar (ex: 97-1)",
        simular_tempo="Simular quantas horas de uso do serviço"
    )
    async def testar_lembrete_glassfish(self, interaction: discord.Interaction, servico_id: str, simular_tempo: int = 3):
        """
        Envia um lembrete de teste para um serviço específico.
        Este comando só pode ser executado por usuários com o cargo de TI.
        Útil para testar o sistema de lembretes sem precisar esperar o tempo real.
        """
        try:
            logging.info(f"Comando testar_lembrete_glassfish executado por {interaction.user.name} para serviço {servico_id}")
            
            # Verifica se o usuário tem permissão (cargo de TI)
            is_ti = any(role.id == CARGO_TI_ID for role in interaction.user.roles)
            if not is_ti:
                await interaction.response.send_message(
                    "❌ Apenas usuários com cargo de TI podem executar este comando.",
                    ephemeral=True
                )
                logging.warning(f"Usuário {interaction.user.name} tentou executar testar_lembrete_glassfish sem permissão")
                return
            
            # Verifica se o serviço existe
            if servico_id not in self.bot.servicos_config:
                await interaction.response.send_message(
                    f"❌ Serviço com ID '{servico_id}' não encontrado.",
                    ephemeral=True
                )
                return
                
            config = self.bot.servicos_config[servico_id]
            
            # Verifica se o serviço está em uso
            if config["status"] != "em uso":
                await interaction.response.send_message(
                    f"❌ O serviço **{config['nome']}** não está em uso. Para testar, use o serviço primeiro.",
                    ephemeral=True
                )
                return
                
            # Prepara os dados para o teste
            usage_data_dict = config.get("usage_data", {})
            if not usage_data_dict:
                await interaction.response.send_message(
                    f"❌ O serviço **{config['nome']}** não tem dados de uso. Use o serviço normalmente primeiro.",
                    ephemeral=True
                )
                return
                
            # Obtem o user_id
            user_id = usage_data_dict.get("user_id")
            if not user_id:
                await interaction.response.send_message(
                    f"❌ Não foi possível identificar o usuário do serviço **{config['nome']}**.",
                    ephemeral=True
                )
                return
                
            # Prepara para enviar o lembrete
            await interaction.response.defer(ephemeral=True)
            
            try:
                # Tenta obter o usuário para enviar DM
                user = await self.bot.fetch_user(int(user_id))
                
                # Cria uma view com botões para confirmar o uso ou liberar
                view = CheckView(servico_id, self.bot.servicos_config)
                
                # Calcula tempo simulado em horas e minutos
                horas_formatadas = simular_tempo
                minutos_formatados = 0
                tempo_uso = f"{horas_formatadas} horas e {minutos_formatados} minutos (simulação)"
                
                # Envia mensagem para o usuário
                await user.send(
                    f"⚠️ **Lembrete de uso do Glassfish (TESTE)**\n" +
                    f"Você está usando o serviço **{config['nome']}** há {tempo_uso}.\n" +
                    f"Por favor, confirme se ainda está utilizando este serviço ou libere-o se não estiver mais usando.\n\n" +
                    f"**NOTA**: Este é um lembrete de TESTE enviado por {interaction.user.name}.",
                    view=view
                )
                
                # Atualiza o timestamp do último lembrete
                usage_data = UsageData.from_dict(usage_data_dict)
                usage_data.update_reminder()
                config["usage_data"] = usage_data.to_dict()
                
                # Salva as alterações
                with open("services.json", "w", encoding="utf-8") as file:
                    json.dump(self.bot.servicos_config, file, indent=4)
                
                # Confirma para o usuário que o lembrete foi enviado
                await interaction.followup.send(
                    f"✅ Lembrete de teste enviado com sucesso para o usuário `{config['usuario']}` sobre o serviço **{config['nome']}**.\n"
                    f"Tempo simulado: {simular_tempo} horas",
                    ephemeral=True
                )
                
                # Log
                logging.info(f"Lembrete de teste enviado por {interaction.user.name} para {config['usuario']} sobre o serviço {servico_id}")
                
            except Exception as e:
                logging.error(f"Erro ao enviar lembrete de teste para o usuário {user_id}: {str(e)}")
                await interaction.followup.send(
                    f"❌ Erro ao enviar lembrete de teste: {str(e)}",
                    ephemeral=True
                )
                
        except Exception as e:
            logging.error(f"Erro ao testar lembrete: {str(e)}")
            await interaction.followup.send(
                f"❌ Ocorreu um erro ao testar lembrete: {str(e)}",
                ephemeral=True
            )

# Adicionar antes da definição do comando testar_lembrete_glassfish
class TestarLembreteSelect(discord.ui.Select):
    def __init__(self, servicos_config, simular_tempo: int):
        self.servicos_config = servicos_config
        self.simular_tempo = simular_tempo
        
        # Prepara as opções apenas com serviços em uso
        options = []
        for key, config in servicos_config.items():
            if config["status"] == "em uso":
                # Calcula o tempo em uso para mostrar na descrição
                tempo_uso = "Tempo desconhecido"
                if "usage_data" in config:
                    try:
                        usage_data = config["usage_data"]
                        timestamp = datetime.datetime.fromisoformat(usage_data["timestamp"])
                        segundos_em_uso = (datetime.datetime.now() - timestamp).total_seconds()
                        horas_em_uso = int(segundos_em_uso / 3600)
                        minutos_em_uso = int((segundos_em_uso % 3600) / 60)
                        tempo_uso = f"Em uso há {horas_em_uso}h{minutos_em_uso}m"
                    except:
                        pass
                
                options.append(
                    discord.SelectOption(
                        label=f"{config['nome']}",
                        value=key,
                        description=f"Em uso por: {config['usuario']} | {tempo_uso}",
                        emoji="🔴"
                    )
                )
        
        # Se não houver serviços em uso, adiciona uma opção informativa
        if not options:
            options = [discord.SelectOption(
                label="Nenhum serviço em uso",
                value="none",
                description="Não há serviços disponíveis para testar",
                emoji="ℹ️"
            )]
        
        super().__init__(
            placeholder="Selecione um serviço para testar o lembrete...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "none":
            await interaction.response.send_message(
                "Não há serviços em uso para testar o lembrete.",
                ephemeral=True
            )
            return
        
        servico_id = self.values[0]
        config = self.servicos_config[servico_id]
        
        try:
            # Prepara os dados para o teste
            usage_data_dict = config.get("usage_data", {})
            if not usage_data_dict:
                await interaction.response.send_message(
                    f"❌ O serviço **{config['nome']}** não tem dados de uso. Use o serviço normalmente primeiro.",
                    ephemeral=True
                )
                return
            
            # Obtem o user_id
            user_id = usage_data_dict.get("user_id")
            if not user_id:
                await interaction.response.send_message(
                    f"❌ Não foi possível identificar o usuário do serviço **{config['nome']}**.",
                    ephemeral=True
                )
                return
            
            # Prepara para enviar o lembrete
            await interaction.response.defer(ephemeral=True)
            
            try:
                # Tenta obter o usuário para enviar DM
                user = await interaction.client.fetch_user(int(user_id))
                
                # Cria uma view com botões para confirmar o uso ou liberar
                view = CheckView(servico_id, self.servicos_config)
                
                # Calcula tempo simulado em horas e minutos
                horas_formatadas = self.simular_tempo
                minutos_formatados = 0
                tempo_uso = f"{horas_formatadas} horas e {minutos_formatados} minutos (simulação)"
                
                # Envia mensagem para o usuário
                await user.send(
                    f"⚠️ **Lembrete de uso do Glassfish (TESTE)**\n" +
                    f"Você está usando o serviço **{config['nome']}** há {tempo_uso}.\n" +
                    f"Por favor, confirme se ainda está utilizando este serviço ou libere-o se não estiver mais usando.\n\n" +
                    f"**NOTA**: Este é um lembrete de TESTE enviado por {interaction.user.name}.",
                    view=view
                )
                
                # Atualiza o timestamp do último lembrete
                usage_data = UsageData.from_dict(usage_data_dict)
                usage_data.update_reminder()
                config["usage_data"] = usage_data.to_dict()
                
                # Salva as alterações
                with open("services.json", "w", encoding="utf-8") as file:
                    json.dump(self.servicos_config, file, indent=4)
                
                # Confirma para o usuário que o lembrete foi enviado
                await interaction.followup.send(
                    f"✅ Lembrete de teste enviado com sucesso para o usuário `{config['usuario']}` sobre o serviço **{config['nome']}**.\n" +
                    f"Tempo simulado: {self.simular_tempo} horas",
                    ephemeral=True
                )
                
                # Log
                logging.info(f"Lembrete de teste enviado por {interaction.user.name} para {config['usuario']} sobre o serviço {servico_id}")
                
            except Exception as e:
                logging.error(f"Erro ao enviar lembrete de teste para o usuário {user_id}: {str(e)}")
                await interaction.followup.send(
                    f"❌ Erro ao enviar lembrete de teste: {str(e)}",
                    ephemeral=True
                )
                
        except Exception as e:
            logging.error(f"Erro ao testar lembrete: {str(e)}")
            await interaction.followup.send(
                f"❌ Ocorreu um erro ao testar lembrete: {str(e)}",
                ephemeral=True
            )

class TestarLembreteView(discord.ui.View):
    def __init__(self, servicos_config, simular_tempo: int):
        super().__init__(timeout=None)
        self.add_item(TestarLembreteSelect(servicos_config, simular_tempo))
