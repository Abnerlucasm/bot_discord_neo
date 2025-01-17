# cogs/help.py
from discord.ext import commands
from discord import app_commands
import discord
import logging

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="ajuda",
        description="Mostra informações sobre os comandos disponíveis"
    )
    async def ajuda(self, interaction: discord.Interaction):
        try:
            embed = discord.Embed(
                title="🤖 Ajuda do Bot",
                description="Aqui estão os comandos disponíveis:",
                color=discord.Color.blue()
            )

            # Comando Glassfish
            embed.add_field(
                name="/glassfish",
                value="Lista os serviços disponíveis e permite gerenciá-los.\n"
                      "- Usar serviço\n"
                      "- Liberar serviço\n"
                      "- Reportar problema\n",
                inline=False
            )

            # Comando Ajuda
            embed.add_field(
                name="/ajuda",
                value="Mostra esta mensagem de ajuda com todos os comandos disponíveis.",
                inline=False
            )

            # Você pode adicionar mais campos conforme adiciona novos comandos

            embed.set_footer(text="Para mais detalhes sobre um comando específico, use /ajuda <comando>")

            await interaction.response.send_message(embed=embed, ephemeral=True)
            logging.info(f"{interaction.user.name} executou o comando /ajuda")

        except Exception as e:
            logging.error(f"Erro ao executar comando ajuda: {str(e)}")
            await interaction.response.send_message(
                "Ocorreu um erro ao mostrar a ajuda. Tente novamente mais tarde.",
                ephemeral=True
            )

    @app_commands.command(
        name="sobre",
        description="Mostra informações sobre o bot"
    )
    async def sobre(self, interaction: discord.Interaction):
        try:
            embed = discord.Embed(
                title="Sobre o Bot",
                description="Bot desenvolvido para gerenciamento de serviços do Glassfish.",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="Funcionalidades",
                value="- Gerenciamento de serviços\n"
                      "- Sistema de permissões por cargo\n"
                      "- Notificações de uso\n"
                      "- Reporte de problemas",
                inline=False
            )
            
            embed.add_field(
            name="/agendamento",
            value="Abre um formulário para registrar um novo agendamento com cliente.",
            inline=False
            )       

            embed.add_field(
                name="/atualizacao",
                value="Abre um formulário para registrar uma nova atualização de versão.",
                inline=False
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)
            logging.info(f"{interaction.user.name} executou o comando /sobre")

        except Exception as e:
            logging.error(f"Erro ao executar comando sobre: {str(e)}")
            await interaction.response.send_message(
                "Ocorreu um erro ao mostrar as informações. Tente novamente mais tarde.",
                ephemeral=True
            )