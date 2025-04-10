# main.py
import discord
from discord.ext import commands
import logging
import json
import os
from cogs.glassfish import GlassfishCog
from cogs.help import HelpCog
from cogs.schedule_update import ScheduleUpdateCog
# from cogs.glassfish_gerenciador import GlassfishManagementCog
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

# Criar pasta logs se não existir
if not os.path.exists('logs'):
    os.makedirs('logs')

# Configuração do sistema de log
log_file = os.path.join('logs', 'bot.log')
handler = TimedRotatingFileHandler(
    filename=log_file,
    when='midnight',
    interval=1,
    backupCount=30,  # Mantém logs dos últimos 30 dias
    encoding='utf-8'
)
handler.suffix = '%Y-%m-%d.log'  # Formato do arquivo: bot.2024-02-21.log

# Formato do log
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Configuração do logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)

class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix=".", intents=intents)
        
    async def setup_hook(self):
        # Carrega as configurações
        try:
            with open("services.json", "r", encoding="utf-8") as file:
                self.servicos_config = json.load(file)
            logging.info("Arquivo services.json carregado com sucesso")
        except Exception as e:
            logging.error(f"Erro ao carregar services.json: {str(e)}")
            self.servicos_config = {}
        
        # Carrega os cogs
        try:
            await self.add_cog(GlassfishCog(self))
            await self.add_cog(HelpCog(self))
            
            # Criamos manualmente o cog e os comandos
            schedule_cog = ScheduleUpdateCog(self)
            await self.add_cog(schedule_cog)
            
            # Registra explicitamente os comandos principais
            self.tree.add_command(discord.app_commands.Command(
                name="beta99",
                description="Registra uma nova versão beta 99",
                callback=schedule_cog.beta99
            ))
            
            self.tree.add_command(discord.app_commands.Command(
                name="agendamento",
                description="Registra um novo agendamento",
                callback=schedule_cog.agendamento
            ))
            
            self.tree.add_command(discord.app_commands.Command(
                name="atualizacao",
                description="Registra uma nova atualização",
                callback=schedule_cog.atualizacao
            ))
            
            logging.info("Todos os cogs foram carregados com sucesso")
        except Exception as e:
            logging.error(f"Erro ao carregar cogs: {str(e)}")
        
    async def on_ready(self):
        print(f'{self.user} está pronto!')
        logging.info(f'Bot iniciado como {self.user}')
        await self.change_presence(activity=discord.Game("Neo Chamados"))
        
        try:
            # Sincroniza comandos com reset completo
            commands = await self.tree.sync()
            command_names = [cmd.name for cmd in commands]
            logging.info(f"Comandos sincronizados: {', '.join(command_names)}")
            print(f"Comandos sincronizados: {', '.join(command_names)}")
        except Exception as e:
            logging.error(f"Erro ao sincronizar comandos: {str(e)}")
            print(f"Erro ao sincronizar comandos: {str(e)}")

def main():
    try:
        with open("token.txt", "r") as file:
            token = file.read().strip()
        logging.info("Token carregado com sucesso")
        
        bot = Bot()
        bot.run(token)
    except Exception as e:
        logging.error(f"Erro ao carregar/executar o bot: {str(e)}")

if __name__ == "__main__":
    main()
