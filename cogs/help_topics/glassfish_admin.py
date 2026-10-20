import discord


def create_recarregar_config_glassfish_help() -> discord.Embed:
    embed = discord.Embed(
        title="🔄 Comando: /recarregar_config_glassfish",
        description="Recarrega as configurações do Glassfish do arquivo.",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="📋 Como usar",
        value="Use `/recarregar_config_glassfish` para atualizar as configurações de timeout e outros parâmetros.",
        inline=False
    )
    embed.add_field(
        name="🔒 Permissões",
        value="• Este comando está disponível apenas para usuários com o cargo de TI",
        inline=False
    )
    embed.add_field(
        name="📝 Observações",
        value="• As configurações são carregadas do arquivo de configuração\n"
              "• Afeta as configurações de timeout e intervalos de verificação",
        inline=False
    )

    return embed



def create_verificacao_forcada_glassfish_help() -> discord.Embed:
    embed = discord.Embed(
        title="🔍 Comando: /verificacao_forcada_glassfish",
        description="Força a verificação de timeout dos serviços Glassfish imediatamente.",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="📋 Como usar",
        value="Use `/verificacao_forcada_glassfish` para executar manualmente o processo de verificação.",
        inline=False
    )
    embed.add_field(
        name="🔒 Permissões",
        value="• Este comando está disponível apenas para usuários com o cargo de TI",
        inline=False
    )
    embed.add_field(
        name="📝 Observações",
        value="• Verifica serviços em uso por muito tempo\n"
              "• Libera automaticamente serviços cujo timeout expirou\n"
              "• Envia notificações para os usuários quando necessário",
        inline=False
    )

    return embed



def create_configurar_timeout_glassfish_help() -> discord.Embed:
    embed = discord.Embed(
        title="⚙️ Comando: /configurar_timeout_glassfish",
        description="Configura o tempo máximo de uso dos serviços Glassfish.",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="📋 Como usar",
        value="Use `/configurar_timeout_glassfish horas:<tempo> intervalo_verificacao:<minutos> intervalo_lembrete:<horas> max_extensoes:<quantidade>`\n"
              "• `horas`: Tempo máximo de uso, entre 1 e 168 horas\n"
              "• `intervalo_verificacao`: Intervalo de verificação, entre 5 e 60 minutos\n"
              "• `intervalo_lembrete`: Intervalo entre lembretes, entre 1 e 12 horas\n"
              "• `max_extensoes`: Limite de extensões, entre 1 e 10",
        inline=False
    )
    embed.add_field(
        name="🔒 Permissões",
        value="• Este comando está disponível apenas para usuários com o cargo de TI",
        inline=False
    )
    embed.add_field(
        name="📝 Observações",
        value="• Informe ao menos um parâmetro para alterar as configurações\n"
              "• As alterações são salvas permanentemente",
        inline=False
    )

    return embed



def create_liberar_todos_glassfish_help() -> discord.Embed:
    embed = discord.Embed(
        title="🔄 Comando: /liberar_todos_glassfish",
        description="Libera todos os serviços Glassfish que estão em uso de uma só vez.",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="📋 Como usar",
        value="Use `/liberar_todos_glassfish` para liberar todos os serviços em uso.",
        inline=False
    )
    embed.add_field(
        name="🔒 Permissões",
        value="• Este comando está disponível apenas para usuários com o cargo de TI",
        inline=False
    )
    embed.add_field(
        name="📝 Observações",
        value="• Libera todos os serviços Glassfish que estão em uso\n"
              "• Útil para situações de manutenção ou reinicialização dos servidores\n"
              "• Registra automaticamente quais serviços foram liberados e quem os estava usando",
        inline=False
    )

    return embed



def create_relatorio_glassfish_help() -> discord.Embed:
    embed = discord.Embed(
        title="📋 Comando: /relatorio_glassfish",
        description="Resume o uso atual dos serviços Glassfish.",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="📋 Como usar",
        value="Use `/relatorio_glassfish`\n"
              "• Comando simples sem parâmetros\n"
              "• Resume uso, confirmações e lembretes pendentes",
        inline=False
    )
    embed.add_field(
        name="🔒 Permissões",
        value="• Este comando está disponível apenas para usuários com o cargo de TI",
        inline=False
    )
    embed.add_field(
        name="📝 Informações do Relatório",
        value="• **Serviços em uso**: Lista detalhada com tempos\n"
              "• **Lembretes pendentes**: Usuários que não responderam\n"
              "• **Estatísticas**: Percentuais de uso e disponibilidade\n"
              "• **Dados**: Último check e último lembrete",
        inline=False
    )

    return embed



def create_adicionar_glassfish_help() -> discord.Embed:
    embed = discord.Embed(
        title="➕ Comando: /adicionar_glassfish",
        description="Adiciona um novo serviço Glassfish ao sistema.",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="📋 Como usar",
        value="Use `/adicionar_glassfish`\n"
              "• Abre um formulário para preenchimento\n"
              "• Solicita ID e nome do serviço\n"
              "• Permite configurar permissões de cargos",
        inline=False
    )
    embed.add_field(
        name="🔒 Permissões",
        value="• Este comando está disponível apenas para usuários com o cargo de TI",
        inline=False
    )
    embed.add_field(
        name="📝 Processo de Adição",
        value="• **Passo 1**: Preencher ID do serviço (ex: 97-1)\n"
              "• **Passo 2**: Definir nome descritivo\n"
              "• **Passo 3**: Selecionar cargos com permissão\n"
              "• **Resultado**: Serviço adicionado e disponível",
        inline=False
    )

    return embed



def create_editar_glassfish_help() -> discord.Embed:
    embed = discord.Embed(
        title="✏️ Comando: /editar_glassfish",
        description="Edita as informações de um serviço Glassfish existente.",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="📋 Como usar",
        value="Use `/editar_glassfish`\n"
              "• Exibe lista de serviços existentes\n"
              "• Selecione o serviço para editar\n"
              "• Modifique as informações desejadas",
        inline=False
    )
    embed.add_field(
        name="🔒 Permissões",
        value="• Este comando está disponível apenas para usuários com o cargo de TI",
        inline=False
    )
    embed.add_field(
        name="📝 Informações Editáveis",
        value="• **Nome**: Descrição do serviço\n"
              "• O ID do serviço não pode ser alterado\n"
              "• **Segurança**: Alterações são registradas nos logs",
        inline=False
    )

    return embed



def create_remover_glassfish_help() -> discord.Embed:
    embed = discord.Embed(
        title="🗑️ Comando: /remover_glassfish",
        description="Remove um serviço Glassfish do sistema.",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="📋 Como usar",
        value="Use `/remover_glassfish`\n"
              "• Exibe lista de serviços existentes\n"
              "• Selecione o serviço para remover\n"
              "• Confirme a remoção",
        inline=False
    )
    embed.add_field(
        name="🔒 Permissões",
        value="• Este comando está disponível apenas para usuários com o cargo de TI",
        inline=False
    )
    embed.add_field(
        name="📝 Processo de Remoção",
        value="• **Verificação**: Sistema verifica se está em uso\n"
              "• **Confirmação**: Solicitada para serviços em uso\n"
              "• **Segurança**: Ação é registrada nos logs\n"
              "• **Irreversível**: Remoção é permanente",
        inline=False
    )

    return embed

