import discord
from discord.ext import commands
from discord import app_commands
import json
import paramiko
import os
import asyncio

def load_services():
    try:
        with open('services.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError as e:
        print(f"Erro: Arquivo 'services.json' não encontrado. {e}")
        return {}
    except json.JSONDecodeError as e:
        print(f"Erro: Falha ao decodificar JSON. {e}")
        return {}

SERVICES = load_services()

def create_instance_select_view():
    class GlassfishInstanceSelect(discord.ui.View):
        def __init__(self):
            super().__init__()
            options = [
                discord.SelectOption(label=key, description=value["nome"])
                for key, value in SERVICES.items() if "linux" in value.get("base_dir", {})
            ]
            self.select = discord.ui.Select(
                placeholder="Selecione uma instância",
                options=options,
            )
            self.select.callback = self.select_callback
            self.add_item(self.select)
            self.selected_instance = None
        
        async def select_callback(self, interaction: discord.Interaction):
            selected_instance = self.select.values[0]
            modal = GlassfishModal(selected_instance)
            await interaction.response.send_modal(modal)

    return GlassfishInstanceSelect()

class GlassfishModal(discord.ui.Modal, title="Gerenciar Instância Glassfish"):
    action = discord.ui.TextInput(
        label="Ação (start, stop, restart)", 
        placeholder="Exemplo: start", 
        required=True
    )

    def __init__(self, instance):
        super().__init__()
        self.instance = instance

    async def on_submit(self, interaction: discord.Interaction):
        bot = interaction.client
        cog = bot.get_cog("GlassfishManagementCog")
        if cog:
            await cog.execute_glassfish_command(interaction, self.action.value.strip(), self.instance)
        else:
            await interaction.response.send_message("Erro ao localizar o gerenciador de instâncias.", ephemeral=True)

class GlassfishManagementCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="glassfish_control", description="Gerencie instâncias do Glassfish - teste")
    async def glassfish_control(self, interaction: discord.Interaction):
        view = create_instance_select_view()
        await interaction.response.send_message("Selecione uma instância para continuar:", view=view, ephemeral=True)

    async def execute_glassfish_command(self, interaction: discord.Interaction, action: str, instance: str):
        try:
            # Verify interaction is still valid
            if interaction.response.is_done():
                return

            if instance not in SERVICES:
                await interaction.response.send_message(f"Instância '{instance}' não encontrada.", ephemeral=True)
                return
        
            service = SERVICES[instance]
            user_roles = [str(role.id) for role in interaction.user.roles]
            if not any(role in service["grupos_permitidos"] for role in user_roles):
                await interaction.response.send_message("Você não tem permissão para gerenciar essa instância.", ephemeral=True)
                return
        
            ssh_config = service.get("ssh")
            domain_name = service.get("domain_name", "domain1")
            glassfish_bin_dir = service["base_dir"].get("linux", "")
        
            # Verificar status do domínio antes de executar a ação
            status_command = f"cd {glassfish_bin_dir} && ./asadmin list-domains"
            status_result = await self._run_remote_linux_command(ssh_config, status_command, glassfish_bin_dir)
            
            # Verificar se o domínio já está no estado desejado
            domain_status = self._check_domain_status(status_result, domain_name, action)
            if domain_status == 'skip':
                await interaction.response.send_message(
                    f"Domínio '{domain_name}' já está no estado desejado.", 
                    ephemeral=True
                )
                return
        
            # Gerar comando principal
            main_command = self._generate_command(action, service["base_dir"], domain_name)
            result = await self._run_remote_linux_command(ssh_config, main_command, glassfish_bin_dir)
        
            # Se falhar, tentar comando forçado para stop/restart
            if not result.strip() and action in ['stop', 'restart']:
                force_command = f"cd {glassfish_bin_dir} && ./asadmin stop-domain --force {domain_name}"
                result = await self._run_remote_linux_command(ssh_config, force_command, glassfish_bin_dir)
        
            await interaction.response.send_message(
                f"Ação '{action}' executada na instância '{instance}'.\nResultado:\n```\n{result}\n```",
                ephemeral=True,
            )
        
        except discord.errors.NotFound:
            print(f"Interaction timeout for {instance}")
        except Exception as e:
            try:
                # Fallback error response if interaction is still valid
                if not interaction.response.is_done():
                    await interaction.response.send_message(f"Erro ao executar a ação: {e}", ephemeral=True)
            except:
                # Log error if even fallback fails
                print(f"Critical error processing Glassfish command: {e}")

    def _check_domain_status(self, status_output, domain_name, desired_action):
        lines = status_output.split('\n')
        for line in lines:
            if domain_name in line:
                current_status = line.split()[1]
                
                if desired_action == 'stop' and current_status == 'not running':
                    return 'skip'
                if desired_action == 'start' and current_status == 'running':
                    return 'skip'
        
        return 'proceed'
    
    def _generate_command(self, action, base_dir, domain_name):
        if action not in ["start", "stop", "restart"]:
            raise ValueError(f"Ação '{action}' não suportada.")

        glassfish_bin_dir = base_dir.get('linux', '')
        if not glassfish_bin_dir:
            raise ValueError("Caminho do diretório 'bin' no Glassfish não configurado corretamente para Linux.")

        command = f"cd {glassfish_bin_dir} && ./asadmin {action}-domain {domain_name}"

        return command

    async def _run_remote_linux_command(self, ssh_config, command, glassfish_bin_dir):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            print(f"Conectando ao servidor {ssh_config['host']}...")
            ssh.connect(
                hostname=ssh_config["host"],
                username=ssh_config["username"],
                password=ssh_config["password"],
            )
        
            # Adicione um log para verificar se a conexão foi bem-sucedida
            print("Conexão SSH estabelecida.")
    
            # Executar o comando de navegação para o diretório
            cd_command = f"cd {glassfish_bin_dir}"
            print(f"Executando comando de cd: {cd_command}")
            stdin, stdout, stderr = ssh.exec_command(cd_command, get_pty=True)
            error_cd = stderr.read().decode()
            if error_cd:
                raise RuntimeError(f"Erro ao executar o comando cd: {error_cd}")
        
            # Verifique se o comando de execução é válido
            full_command = f"cd {glassfish_bin_dir} && ./asadmin {command}-domain domain1"
            print(f"Executando comando principal: {full_command}")
            stdin, stdout, stderr = ssh.exec_command(full_command, get_pty=True)
    
            # Fornecer senha do sudo, se necessário
            if 'sudo_password' in ssh_config:
                stdin.write(ssh_config['sudo_password'] + '\n')
                stdin.flush()
    
            # Ler a saída e erro
            output = stdout.read().decode() if stdout else ""
            error = stderr.read().decode() if stderr else ""
            
            if error:
                print(f"Erro ao executar o comando principal: {error}")
                raise RuntimeError(f"Erro no comando SSH: {error}")
            
            print(f"Comando executado com sucesso. Resultado:\n{output}")
            return output
        
        except Exception as e:
            print(f"Erro ao executar o comando SSH: {str(e)}")
            raise RuntimeError(f"Erro ao executar o comando SSH: {str(e)}")
        
        finally:
            ssh.close()
