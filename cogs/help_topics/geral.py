import discord


def create_sobre_help() -> discord.Embed:
    embed = discord.Embed(
        title="ℹ️ Comando: /sobre",
        description="Conheça mais sobre o bot e suas funcionalidades.",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="📋 Como usar",
        value="Simplesmente digite `/sobre` para ver:\n"
              "• Informações gerais sobre o bot\n"
              "• Lista de funcionalidades\n"
              "• Links importantes\n"
              "• Documentação do projeto",
        inline=False
    )

    return embed
