import discord


def create_general_help(user_name: str) -> discord.Embed:
    embed = discord.Embed(
        title="🤖 Bem-vindo(a) à Central de Ajuda!",
        description=f"Olá **{user_name}**! Sou o bot da Neo Sistemas, "
                  f"estou aqui para ajudar você a gerenciar suas rotinas de forma simples e eficiente!\n\n"
                  f"**📋 Aqui está o que posso fazer por você:**\n\n"
                  f"Para ver detalhes de cada comando, use `/ajuda <comando>`",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="🔧 /glassfish",
        value="Gerencie seus serviços facilmente:\n"
              "• ✅ Usar serviço\n"
              "• 🔓 Liberar serviço\n"
              "• ⚠️ Reportar problema\n",
        inline=False
    )

    embed.add_field(
        name="📅 /agendamento",
        value="Organize seus compromissos! Registre e gerencie agendamentos com clientes.",
        inline=False
    )

    embed.add_field(
        name="🔄 /atualizacao",
        value="Mantenha tudo atualizado! Registre e acompanhe as atualizações de versão.",
        inline=False
    )

    embed.add_field(
        name="🔄 /beta99",
        value="Registre os clientes que estão utilizando a versão 99 em acesso antecipado.",
        inline=False
    )

    embed.add_field(
        name="ℹ️ /sobre",
        value="Conheça mais sobre mim e minhas funcionalidades!",
        inline=False
    )

    embed.add_field(
        name="🔗 Links Úteis e Comandos Administrativos",
        value="• 📚 Documentação: https://github.com/Abnerlucasm/bot_discord_neo\n"
              "• 🧪 Guia de Desenvolvimento: docs/desenvolvimento.md (para testes)\n"
              "• 💡 Sugestões? Entre em contato com a equipe\n"
              "• ❓ Dúvidas? Use /ajuda <comando> para mais detalhes\n\n"
              "**🛠️ Comandos administrativos (TI):**\n"
              "• `/obter_timeout_glassfish` - Configurações de timeout\n"
              "• `/relatorio_glassfish` - Relatório de uso\n"
              "• `/recarregar_config_glassfish` - Recarrega configurações\n"
              "• `/verificacao_forcada_glassfish` - Força verificação\n"
              "• `/configurar_timeout_glassfish` - Configura timeouts\n"
              "• `/liberar_todos_glassfish` - Libera todos os serviços\n"
              "• `/adicionar_glassfish` - Adiciona serviço\n"
              "• `/editar_glassfish` - Edita serviço\n"
              "• `/remover_glassfish` - Remove serviço\n\n"
              "**🧪 Comandos de desenvolvimento (TI):**\n"
              "• `/modo_desenvolvimento_glassfish` - Modo de teste\n"
              "• `/simular_tempo_glassfish` - Simula tempo de uso\n"
              "• `/status_servico_glassfish` - Status detalhado\n"
              "• `/testar_lembrete_glassfish` - Testa lembretes\n"
              "• `/testar_envio_lembrete_glassfish` - Teste direto de DM",
        inline=False
    )

    embed.set_footer(text="Neo Sistemas • Facilitando seu dia a dia")
    return embed
