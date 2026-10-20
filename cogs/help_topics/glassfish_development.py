import discord


def create_testar_lembrete_glassfish_help() -> discord.Embed:
    embed = discord.Embed(
        title="⏱️ Comando: /testar_lembrete_glassfish",
        description="Prepara a simulação de uso para testar um lembrete.",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="📋 Como usar",
        value="Use `/testar_lembrete_glassfish simular_tempo:<horas>`\n"
              "• `simular_tempo`: (Opcional) Tempo simulado de uso em horas. Padrão: 3",
        inline=False
    )
    embed.add_field(
        name="🔒 Permissões",
        value="• Este comando está disponível apenas para usuários com o cargo de TI",
        inline=False
    )
    embed.add_field(
        name="📝 Observações",
        value="• Exibe uma lista de serviços em uso para testar\n"
              "• Simula tempo de uso conforme especificado\n"
              "• Rode `/verificacao_forcada_glassfish` para processar o teste imediatamente\n"
              "• Apenas para fins de desenvolvimento e testes",
        inline=False
    )

    return embed



def create_modo_desenvolvimento_glassfish_help() -> discord.Embed:
    embed = discord.Embed(
        title="🧪 Comando: /modo_desenvolvimento_glassfish",
        description="Ativa ou desativa o modo de desenvolvimento para testes.",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="📋 Como usar",
        value="Use `/modo_desenvolvimento_glassfish ativar:<true/false>`\n"
              "• `ativar`: True para ativar, False para desativar",
        inline=False
    )
    embed.add_field(
        name="🔒 Permissões",
        value="• Este comando está disponível apenas para usuários com o cargo de TI",
        inline=False
    )
    embed.add_field(
        name="📝 Observações",
        value="• **Modo ativado**: Tempo máximo de uso reduzido (1 hora vs 24 horas)\n"
              "• **Verificações**: Mais frequentes (1 minuto vs 15 minutos)\n"
              "• **Ideal para**: Testes rápidos e desenvolvimento\n"
              "• **Atenção**: Não usar em produção - apenas para testes",
        inline=False
    )

    return embed



def create_simular_tempo_glassfish_help() -> discord.Embed:
    embed = discord.Embed(
        title="⏰ Comando: /simular_tempo_glassfish",
        description="Simula que um serviço está em uso há X horas atrás.",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="📋 Como usar",
        value="Use `/simular_tempo_glassfish servico_id:<id> horas_atras:<horas>`\n"
              "• `servico_id`: ID do serviço para simular (ex: 97-1)\n"
              "• `horas_atras`: Quantas horas atrás simular o início do uso",
        inline=False
    )
    embed.add_field(
        name="🔒 Permissões",
        value="• Este comando está disponível apenas para usuários com o cargo de TI",
        inline=False
    )
    embed.add_field(
        name="📝 Observações",
        value="• **Pré-requisito**: O serviço deve estar em uso\n"
              "• **Funcionalidade**: Altera o timestamp de início de uso\n"
              "• **Uso**: Testar cenários de timeout sem esperar tempo real\n"
              "• **Cuidado**: Use apenas em ambiente de testes",
        inline=False
    )

    return embed



def create_status_servico_glassfish_help() -> discord.Embed:
    embed = discord.Embed(
        title="📊 Comando: /status_servico_glassfish",
        description="Mostra os dados atuais de um serviço específico.",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="📋 Como usar",
        value="Use `/status_servico_glassfish servico_id:<id>`\n"
              "• `servico_id`: ID do serviço para verificar (ex: 97-1)",
        inline=False
    )
    embed.add_field(
        name="🔒 Permissões",
        value="• Este comando está disponível apenas para usuários com o cargo de TI",
        inline=False
    )
    embed.add_field(
        name="📝 Informações Exibidas",
        value="• **Status**: Disponível ou em uso\n"
              "• **Usuário**: Quem está usando (se aplicável)\n"
              "• **Tempo de uso**: Há quanto tempo está em uso\n"
              "• **Extensões**: Quantas foram utilizadas\n"
              "• **Timestamps**: Último check e lembrete\n"
              "• **Próximas ações**: Previsão de lembretes e timeout",
        inline=False
    )

    return embed



def create_testar_envio_lembrete_glassfish_help() -> discord.Embed:
    embed = discord.Embed(
        title="📧 Comando: /testar_envio_lembrete_glassfish",
        description="Envia um lembrete de teste ao usuário vinculado a um serviço em uso.",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="📋 Como usar",
        value="Use `/testar_envio_lembrete_glassfish`\n"
              "• Comando simples sem parâmetros\n"
              "• Seleciona automaticamente um serviço em uso e envia a DM ao usuário associado",
        inline=False
    )
    embed.add_field(
        name="🔒 Permissões",
        value="• Este comando está disponível apenas para usuários com o cargo de TI",
        inline=False
    )
    embed.add_field(
        name="📝 Observações",
        value="• **Função**: Testa o sistema de DM de lembretes\n"
              "• **Destinatário**: Usuário associado ao serviço selecionado\n"
              "• **Propósito**: Verificar se mensagens diretas estão funcionando\n"
              "• **Requer**: Um serviço em uso com dados de usuário válidos",
        inline=False
    )

    return embed

