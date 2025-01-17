# main.py
import discord
from discord.ext import commands
import logging
import json
import os
from cogs.glassfish import GlassfishCog
from cogs.help import HelpCog
from cogs.schedule_update import ScheduleUpdateCog

# Configuração do sistema de log
logging.basicConfig(
    filename="glassfish.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

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
        await self.add_cog(GlassfishCog(self))
        await self.add_cog(HelpCog(self))
        await self.add_cog(ScheduleUpdateCog(self))
        
    async def on_ready(self):
        print(f'{self.user} está pronto!')
        logging.info(f'Bot iniciado como {self.user}')
        await self.change_presence(activity=discord.Game("Neo Chamados"))
        await self.tree.sync()
        print("Comandos sincronizados globalmente.")
        logging.info("Comandos sincronizados globalmente com sucesso")

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
