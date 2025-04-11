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
    @app_commands.describe(comando="Nome do comando para ver ajuda específica (opcional)")
    async def ajuda(self, interaction: discord.Interaction, comando: str = None):
        try:
            if comando:
                # Converte para minúsculo para facilitar a comparação
                comando = comando.lower()
                
                # Ajuda específica para cada comando
                if comando == "glassfish":
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
                              "• Equipe técnica será notificada\n"
                              "• Acompanhe o status do seu reporte",
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

                elif comando == "agendamento":
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
                              "• Data e hora do agendamento\n"
                              "• Tipo de atendimento\n"
                              "• Observações (opcional)",
                        inline=False
                    )
                    embed.add_field(
                        name="🔔 Notificações",
                        value="• Você receberá lembretes do agendamento\n"
                              "• Cliente será notificado da confirmação\n"
                              "• Equipe será informada do compromisso",
                        inline=False
                    )

                elif comando == "atualizacao":
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
                    
                elif comando == "beta99":
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

                elif comando == "sobre":
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
                
                elif comando == "recarregar_config_glassfish":
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
                
                elif comando == "verificacao_forcada_glassfish":
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
                
                elif comando == "configurar_timeout_glassfish":
                    embed = discord.Embed(
                        title="⚙️ Comando: /configurar_timeout_glassfish",
                        description="Configura o tempo máximo de uso dos serviços Glassfish.",
                        color=discord.Color.blue()
                    )
                    embed.add_field(
                        name="📋 Como usar",
                        value="Use `/configurar_timeout_glassfish horas:<tempo> lembrete:<intervalo>`\n"
                              "• `horas`: Número de horas após o qual o serviço será liberado automaticamente\n"
                              "• `lembrete`: (Opcional) Intervalo em horas entre lembretes para o usuário",
                        inline=False
                    )
                    embed.add_field(
                        name="🔒 Permissões",
                        value="• Este comando está disponível apenas para usuários com o cargo de TI",
                        inline=False
                    )
                    embed.add_field(
                        name="📝 Observações",
                        value="• O tempo máximo deve estar entre 1 e 72 horas\n"
                              "• O intervalo de lembretes deve ser menor que o tempo máximo\n"
                              "• As configurações são salvas permanentemente",
                        inline=False
                    )
                
                elif comando == "obter_timeout_glassfish":
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

                elif comando == "liberar_todos_glassfish":
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

                elif comando == "testar_lembrete_glassfish":
                    embed = discord.Embed(
                        title="⏱️ Comando: /testar_lembrete_glassfish",
                        description="Envia um lembrete de teste para um serviço específico.",
                        color=discord.Color.blue()
                    )
                    embed.add_field(
                        name="📋 Como usar",
                        value="Use `/testar_lembrete_glassfish servico_id:<id> simular_tempo:<horas>`\n"
                              "• `servico_id`: ID do serviço para testar (ex: 97-1)\n"
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
                        value="• O serviço precisa estar em uso para o teste funcionar\n"
                              "• Envia uma mensagem direta para o usuário que está usando o serviço\n"
                              "• Útil para testar o sistema de lembretes sem esperar o tempo real\n"
                              "• Apenas para fins de desenvolvimento e testes",
                        inline=False
                    )

                else:
                    await interaction.response.send_message(
                        f"❌ Comando '{comando}' não encontrado. Use `/ajuda` para ver a lista de comandos disponíveis.",
                        ephemeral=True
                    )
                    return

                embed.set_footer(text="💡 Use /ajuda para ver todos os comandos disponíveis")
                
            else:
                # Mantém o embed original de ajuda geral
                embed = discord.Embed(
                    title="🤖 Bem-vindo(a) à Central de Ajuda!",
                    description=f"Olá **{interaction.user.name}**! Sou o bot da Neo Sistemas, "
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
                    name="🔗 Links Úteis",
                    value="• 📚 Documentação: https://github.com/Abnerlucasm/bot_discord_neo\n"
                          "• 💡 Sugestões? Entre em contato com a equipe\n"
                          "• ❓ Dúvidas? Use /ajuda <comando> para mais detalhes\n"
                          "• 🛠️ Comandos administrativos:\n"
                          "  - `/recarregar_config_glassfish` - Recarrega configurações\n"
                          "  - `/verificacao_forcada_glassfish` - Força verificação de timeout\n"
                          "  - `/configurar_timeout_glassfish` - Configura tempo máximo de uso\n"
                          "  - `/obter_timeout_glassfish` - Exibe configurações de timeout\n"
                          "  - `/liberar_todos_glassfish` - Libera todos os serviços em uso",
                    inline=False
                )

                embed.set_footer(text="Neo Sistemas • Facilitando seu dia a dia")

            # Adiciona a imagem para ambos os casos
            embed.set_image(url="attachment://logo.jpg")
            
            # Envia a mensagem com o arquivo da imagem
            file = discord.File("assets/logo.jpg", filename="logo.jpg")
            await interaction.response.send_message(file=file, embed=embed, ephemeral=True)
            logging.info(f"{interaction.user.name} executou o comando /ajuda {comando if comando else ''}")

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
                title="💫 Sobre o Bot da Neo",
                description=f"Olá **{interaction.user.name}**! Que bom ter você por aqui!\n\n"
                          f"Sou o assistente virtual da Neo Sistemas, desenvolvido para tornar "
                          f"seu trabalho mais ágil e organizado. Estou aqui para ajudar com "
                          f"várias tarefas importantes do seu dia a dia!",
                color=discord.Color.blue()
            )
            
            # Adiciona a imagem
            embed.set_image(url="attachment://logo.jpg")
            
            embed.add_field(
                name="✨ Principais Funcionalidades",
                value="• 🔧 Gerenciamento inteligente de serviços\n"
                      "• 👥 Sistema avançado de permissões\n"
                      "• 🔔 Notificações em tempo real\n"
                      "• ⚠️ Sistema de reporte de problemas\n"
                      "• 📅 Gerenciamento de Agendamentos\n"
                      "• 🔄 Controle de Atualizações",
                inline=False
            )
            
            embed.add_field(
                name="🔗 Links Importantes",
                value="• 📚 Documentação completa: https://github.com/Abnerlucasm/bot_discord_neo\n"
                      "• ❓ Precisa de ajuda? Use /ajuda para ver todos os comandos\n"
                      "• 💡 Sugestões são sempre bem-vindas!",
                inline=False
            )
            
            embed.set_footer(text="Neo Sistemas • Inovando para facilitar seu trabalho")
            
            # Envia a mensagem com o arquivo da imagem
            file = discord.File("assets/logo.jpg", filename="logo.jpg")
            await interaction.response.send_message(file=file, embed=embed, ephemeral=True)
            logging.info(f"{interaction.user.name} executou o comando /sobre")

        except Exception as e:
            logging.error(f"Erro ao executar comando sobre: {str(e)}")
            await interaction.response.send_message(
                "Ocorreu um erro ao mostrar as informações. Tente novamente mais tarde.",
                ephemeral=True
            )