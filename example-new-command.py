# cogs/example.py
from discord.ext import commands
from discord import app_commands
import logging

class ExampleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="ping", description="Verifica a latência do bot")
    async def ping(self, interaction):
        try:
            latency = round(self.bot.latency * 1000)
            await interaction.response.send_message(f"Pong! Latência: {latency}ms", ephemeral=True)
            logging.info(f"{interaction.user.name} executou o comando /ping")
        except Exception as e:
            logging.error(f"Erro ao executar comando ping: {str(e)}")
            await interaction.response.send_message(
                "Ocorreu um erro ao verificar a latência. Tente novamente mais tarde.",
                ephemeral=True
            )

    @app_commands.command(name="echo", description="Repete a mensagem do usuário")
    @app_commands.describe(mensagem="A mensagem que será repetida")
    async def echo(self, interaction, mensagem: str):
        try:
            await interaction.response.send_message(f"Você disse: {mensagem}", ephemeral=True)
            logging.info(f"{interaction.user.name} executou o comando /echo")
        except Exception as e:
            logging.error(f"Erro ao executar comando echo: {str(e)}")
            await interaction.response.send_message(
                "Ocorreu um erro ao executar o comando. Tente novamente mais tarde.",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(ExampleCog(bot))
