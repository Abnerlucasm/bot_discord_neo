import discord


def create_agendamento_help() -> discord.Embed:
    embed = discord.Embed(
        title="📅 Comando: /agendamento",
        description="Gerencie agendamentos com clientes de forma organizada.",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="📋 Como usar",
        value="Use `/agendamento` e preencha as informações solicitadas:",
        inline=False
    )
    embed.add_field(
        name="ℹ️ Informações necessárias",
        value="• Nome do cliente\n"
              "• Número do chamado (opcional)\n"
              "• Data e hora previstas\n"
              "• Observações (opcional)",
        inline=False
    )
    embed.add_field(
        name="📣 Notificação",
        value="O agendamento é publicado no canal configurado e pode mencionar um cargo responsável.",
        inline=False
    )

    return embed


def create_atualizacao_help() -> discord.Embed:
    embed = discord.Embed(
        title="🔄 Comando: /atualizacao",
        description="Registre e acompanhe atualizações de versão do sistema.",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="📋 Como usar",
        value="Use `/atualizacao` e forneça os detalhes da atualização:",
        inline=False
    )
    embed.add_field(
        name="ℹ️ Informações necessárias",
        value="• Versão da atualização\n"
              "• Descrição das mudanças\n"
              "• Impacto nos usuários\n"
              "• Data de implementação",
        inline=False
    )
    embed.add_field(
        name="📝 Notas importantes",
        value="• Documente todas as alterações relevantes\n"
              "• Inclua instruções para usuários se necessário\n"
              "• Mencione correções de bugs importantes",
        inline=False
    )

    return embed


def create_beta99_help() -> discord.Embed:
    embed = discord.Embed(
        title="🔄 Comando: /beta99",
        description="Registre e acompanhe atualizações de versão em acesso antecipado do sistema.",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="📋 Como usar",
        value="Use `/beta99` e forneça os detalhes da versão e cliente da atualização:",
        inline=False
    )
    embed.add_field(
        name="ℹ️ Informações necessárias",
        value="• Nome do Cliente\n"
              "• Número da versão beta\n"
              "• Número do chamado onde houve a solicitação / motivo\n"
              "• Data de implementação",
        inline=False
    )
    embed.add_field(
        name="📝 Notas importantes",
        value="• Documente todas as alterações relevantes\n"
              "• Inclua instruções para usuários se necessário\n",
        inline=False
    )

    return embed
