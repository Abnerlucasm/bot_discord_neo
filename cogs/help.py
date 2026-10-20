import logging

import discord
from discord import app_commands
from discord.ext import commands

from .help_topics import HELP_TOPICS, create_general_help


class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="ajuda",
        description="Mostra informações sobre os comandos disponíveis",
    )
    @app_commands.describe(comando="Nome do comando para ver ajuda específica (opcional)")
    async def ajuda(self, interaction: discord.Interaction, comando: str = None):
        try:
            if comando:
                comando = comando.lower()
                create_topic = HELP_TOPICS.get(comando)
                if create_topic is None:
                    await interaction.response.send_message(
                        f"❌ Comando '{comando}' não encontrado. Use `/ajuda` para ver a lista de comandos disponíveis.",
                        ephemeral=True,
                    )
                    return
                embed = create_topic()
                embed.set_footer(text="💡 Use /ajuda para ver todos os comandos disponíveis")
            else:
                embed = create_general_help(interaction.user.name)

            embed.set_image(url="attachment://logo.jpg")
            image_file = discord.File("assets/logo.jpg", filename="logo.jpg")
            await interaction.response.send_message(
                file=image_file,
                embed=embed,
                ephemeral=True,
            )
            if comando:
                comando_executado = f"/ajuda {comando}"
            else:
                comando_executado = "/ajuda"
            logging.info(f"{interaction.user.name} executou o comando {comando_executado}")
        except Exception as e:
            logging.error(f"Erro ao executar comando ajuda: {str(e)}")
            await interaction.response.send_message(
                "Ocorreu um erro ao mostrar a ajuda. Tente novamente mais tarde.",
                ephemeral=True,
            )

    @app_commands.command(
        name="sobre",
        description="Mostra informações sobre o bot",
    )
    async def sobre(self, interaction: discord.Interaction):
        try:
            embed = discord.Embed(
                title="💫 Sobre o Bot da Neo",
                description=f"Olá **{interaction.user.name}**! Que bom ter você por aqui!\n\n"
                            f"Sou o assistente virtual da Neo Sistemas, desenvolvido para tornar "
                            f"seu trabalho mais ágil e organizado. Estou aqui para ajudar com "
                            f"várias tarefas importantes do seu dia a dia!",
                color=discord.Color.blue(),
            )
            embed.set_image(url="attachment://logo.jpg")
            embed.add_field(
                name="✨ Principais Funcionalidades",
                value="• 🔧 Gerenciamento inteligente de serviços\n"
                      "• 👥 Sistema avançado de permissões\n"
                      "• 🔔 Notificações em tempo real\n"
                      "• ⚠️ Sistema de reporte de problemas\n"
                      "• 📅 Gerenciamento de Agendamentos\n"
                      "• 🔄 Controle de Atualizações",
                inline=False,
            )
            embed.add_field(
                name="🔗 Links Importantes",
                value="• 📚 Documentação completa: https://github.com/Abnerlucasm/bot_discord_neo\n"
                      "• ❓ Precisa de ajuda? Use /ajuda para ver todos os comandos\n"
                      "• 💡 Sugestões são sempre bem-vindas!",
                inline=False,
            )
            embed.set_footer(text="Neo Sistemas • Inovando para facilitar seu trabalho")
            image_file = discord.File("assets/logo.jpg", filename="logo.jpg")
            await interaction.response.send_message(
                file=image_file,
                embed=embed,
                ephemeral=True,
            )
            logging.info(f"{interaction.user.name} executou o comando /sobre")
        except Exception as e:
            logging.error(f"Erro ao executar comando sobre: {str(e)}")
            await interaction.response.send_message(
                "Ocorreu um erro ao mostrar as informações. Tente novamente mais tarde.",
                ephemeral=True,
            )
