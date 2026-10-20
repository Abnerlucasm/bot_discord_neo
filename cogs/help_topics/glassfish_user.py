import discord


def create_glassfish_help() -> discord.Embed:
    embed = discord.Embed(
        title="🔧 Comando: /glassfish",
        description="Gerencie os serviços do Glassfish de forma simples e eficiente.",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="📋 Como usar",
        value="Use `/glassfish` e selecione uma das opções disponíveis:",
        inline=False
    )
    embed.add_field(
        name="✅ Usar serviço",
        value="Registra que você está utilizando um serviço.\n"
              "• Selecione o ambiente desejado\n"
              "• Sistema bloqueará o uso por outros usuários\n"
              "• Você será notificado quando concluído",
        inline=False
    )
    embed.add_field(
        name="🔓 Liberar serviço",
        value="Libera um serviço que você estava usando.\n"
              "• Selecione o serviço que deseja liberar\n"
              "• Sistema notificará que está disponível",
        inline=False
    )
    embed.add_field(
        name="⚠️ Reportar problema",
        value="Registra um problema encontrado no serviço.\n"
              "• Descreva o problema encontrado\n"
              "• Equipe técnica será notificada",
        inline=False
    )
    embed.add_field(
        name="🔄 Outros comandos relacionados",
        value="• `/recarregar_config_glassfish` - Recarrega as configurações do Glassfish (apenas TI)\n"
              "• `/verificacao_forcada_glassfish` - Força verificação de timeout (apenas TI)\n"
              "• `/configurar_timeout_glassfish` - Configura tempo máximo de uso (apenas TI)\n"
              "• `/obter_timeout_glassfish` - Exibe configurações atuais de timeout\n"
              "• `/liberar_todos_glassfish` - Libera todos os serviços em uso (apenas TI)",
        inline=False
    )

    return embed



def create_obter_timeout_glassfish_help() -> discord.Embed:
    embed = discord.Embed(
        title="⏱️ Comando: /obter_timeout_glassfish",
        description="Mostra as configurações atuais de timeout dos serviços Glassfish.",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="📋 Como usar",
        value="Use `/obter_timeout_glassfish` para ver as configurações atuais.",
        inline=False
    )
    embed.add_field(
        name="📝 Observações",
        value="• Exibe o tempo máximo de uso sem confirmação\n"
              "• Mostra o intervalo entre lembretes\n"
              "• Informa a frequência de verificação automatizada",
        inline=False
    )

    return embed

