import discord
from discord.ext import commands, tasks
from discord import app_commands
import logging
from .glassfish_service import GlassfishService
from .glassfish_commands import GlassfishCommands
from .glassfish_config import reload_config

class GlassfishCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.service = GlassfishService(bot)
        self.commands = GlassfishCommands(bot, self.service)
        
        # Atribui o servicos_config ao bot para compatibilidade
        self.bot.servicos_config = self.service.load_services()
        
        # Inicia o loop de verificação
        self.check_services_loop.start()

    def cog_unload(self):
        """Para o loop quando o cog for descarregado"""
        self.check_services_loop.cancel()

    @tasks.loop(minutes=15)  # Usa o valor padrão, mas será atualizado dinamicamente
    async def check_services_loop(self):
        """Loop para verificação de timeout dos serviços"""
        try:
            await self.service.check_services()
            # Atualiza o bot.servicos_config após verificação
            self.bot.servicos_config = self.service.load_services()
        except Exception as e:
            logging.error(f"Erro no loop de verificação de serviços: {str(e)}")

    @check_services_loop.before_loop
    async def before_check_services_loop(self):
        """Espera o bot estar pronto antes de iniciar o loop"""
        await self.bot.wait_until_ready()
        logging.info("Iniciando loop de verificação de serviços Glassfish")

    @commands.Cog.listener()
    async def on_ready(self):
        """Configura a mensagem persistente quando o bot iniciar"""
        # Recarrega as configurações do arquivo
        reload_config()
        
        # Configura a mensagem persistente
        await self.service.setup_persistent_message()

        # Atualiza o bot.servicos_config
        self.bot.servicos_config = self.service.load_services()

        # Sincroniza os comandos
        try:
            synced = await self.bot.tree.sync()
            logging.info(f"Comandos Glassfish sincronizados: {len(synced)} comandos")
        except Exception as e:
            logging.error(f"Erro ao sincronizar comandos Glassfish: {str(e)}")

    async def refresh_persistent_message(self):
        """Atualiza a mensagem persistente - método público para compatibilidade"""
        await self.service._refresh_persistent_message()
        # Atualiza também o bot.servicos_config
        self.bot.servicos_config = self.service.load_services()

    # === COMANDOS SLASH ===

    @app_commands.command(name="glassfish", description="Lista os serviços disponíveis")
    async def glassfish(self, interaction: discord.Interaction):
        """Lista os serviços disponíveis"""
        await self.commands.cmd_glassfish(interaction)

    @app_commands.command(name="recarregar_config_glassfish", description="Recarrega as configurações do Glassfish do arquivo (apenas TI)")
    async def recarregar_config_glassfish(self, interaction: discord.Interaction):
        """Recarrega as configurações do arquivo config.json"""
        await self.commands.cmd_recarregar_config_glassfish(interaction)

    @app_commands.command(name="verificacao_forcada_glassfish", description="Força a verificação de timeout dos serviços Glassfish (apenas TI)")
    async def verificacao_forcada_glassfish(self, interaction: discord.Interaction):
        """Força a verificação de timeout dos serviços"""
        await self.commands.cmd_verificacao_forcada_glassfish(interaction)

    @app_commands.command(name="configurar_timeout_glassfish", description="Configura o timeout para serviços Glassfish (apenas TI)")
    @app_commands.describe(
        horas="Número de horas para timeout (1-168)",
        intervalo_verificacao="Intervalo de verificação em minutos (5-60)",
        intervalo_lembrete="Intervalo de lembretes em horas (1-12)",
        max_extensoes="Número máximo de extensões permitidas (1-10)"
    )
    async def configurar_timeout_glassfish(
        self, 
        interaction: discord.Interaction, 
        horas: app_commands.Range[int, 1, 168] = None,
        intervalo_verificacao: app_commands.Range[int, 5, 60] = None,
        intervalo_lembrete: app_commands.Range[int, 1, 12] = None,
        max_extensoes: app_commands.Range[int, 1, 10] = None
    ):
        """Configura o timeout para serviços Glassfish"""
        await self.commands.cmd_configurar_timeout_glassfish(
            interaction, horas, intervalo_verificacao, intervalo_lembrete, max_extensoes
        )
        
        # Se o intervalo de verificação foi alterado, reinicia o loop
        if intervalo_verificacao is not None:
            self.check_services_loop.cancel()
            self.check_services_loop.change_interval(minutes=self.service.verificar_intervalo)
            self.check_services_loop.restart()

    @app_commands.command(name="obter_timeout_glassfish", description="Mostra as configurações atuais de timeout dos serviços Glassfish")
    async def obter_timeout_glassfish(self, interaction: discord.Interaction):
        """Mostra as configurações atuais de timeout"""
        await self.commands.cmd_obter_timeout_glassfish(interaction)

    @app_commands.command(name="relatorio_glassfish", description="Gera um relatório de uso e notificações dos serviços Glassfish (apenas TI)")
    async def relatorio_glassfish(self, interaction: discord.Interaction):
        """Gera um relatório detalhado de uso dos serviços"""
        await self.commands.cmd_relatorio_glassfish(interaction)

    @app_commands.command(name="adicionar_glassfish", description="Adiciona um novo serviço Glassfish (apenas TI)")
    async def adicionar_glassfish(self, interaction: discord.Interaction):
        """Adiciona um novo serviço Glassfish"""
        await self.commands.cmd_adicionar_glassfish(interaction)

    @app_commands.command(name="editar_glassfish", description="Edita um serviço Glassfish existente (apenas TI)")
    async def editar_glassfish(self, interaction: discord.Interaction):
        """Edita um serviço Glassfish existente"""
        await self.commands.cmd_editar_glassfish(interaction)

    @app_commands.command(name="remover_glassfish", description="Remove um serviço Glassfish (apenas TI)")
    async def remover_glassfish(self, interaction: discord.Interaction):
        """Remove um serviço Glassfish"""
        await self.commands.cmd_remover_glassfish(interaction)

    @app_commands.command(name="liberar_todos_glassfish", description="Libera todos os serviços Glassfish em uso (apenas TI)")
    async def liberar_todos_glassfish(self, interaction: discord.Interaction):
        """Libera todos os serviços Glassfish em uso"""
        await self.commands.cmd_liberar_todos_glassfish(interaction)

    @app_commands.command(name="testar_lembrete_glassfish", description="Envia um lembrete de teste para um serviço específico (apenas TI)")
    @app_commands.describe(
        simular_tempo="Simular quantas horas de uso do serviço"
    )
    async def testar_lembrete_glassfish(self, interaction: discord.Interaction, simular_tempo: int = 3):
        """Envia um lembrete de teste para um serviço específico"""
        await self.commands.cmd_testar_lembrete_glassfish(interaction, simular_tempo)

    @app_commands.command(name="modo_desenvolvimento_glassfish", description="Ativa/desativa modo de desenvolvimento para testes (apenas TI)")
    @app_commands.describe(
        ativar="True para ativar, False para desativar o modo de desenvolvimento"
    )
    async def modo_desenvolvimento_glassfish(self, interaction: discord.Interaction, ativar: bool):
        """Ativa/desativa o modo de desenvolvimento para testes"""
        await self.commands.cmd_modo_desenvolvimento_glassfish(interaction, ativar)

    @app_commands.command(name="simular_tempo_glassfish", description="Simula tempo de uso de um serviço para testes (apenas TI)")
    @app_commands.describe(
        servico_id="ID do serviço para simular (ex: 97-1)",
        horas_atras="Quantas horas atrás simular o início do uso"
    )
    async def simular_tempo_glassfish(self, interaction: discord.Interaction, servico_id: str, horas_atras: int):
        """Simula que um serviço está em uso há X horas"""
        await self.commands.cmd_simular_tempo_glassfish(interaction, servico_id, horas_atras)

    @app_commands.command(name="status_servico_glassfish", description="Mostra status detalhado de um serviço específico (apenas TI)")
    @app_commands.describe(
        servico_id="ID do serviço para verificar status (ex: 97-1)"
    )
    async def status_servico_glassfish(self, interaction: discord.Interaction, servico_id: str):
        """Mostra o status detalhado de um serviço específico"""
        await self.commands.cmd_status_servico_glassfish(interaction, servico_id)

    @app_commands.command(name="testar_envio_lembrete_glassfish", description="Testa o envio de lembrete direto (apenas TI)")
    async def testar_envio_lembrete_glassfish(self, interaction: discord.Interaction):
        """Testa o envio de lembrete diretamente"""
        await self.commands.cmd_testar_envio_lembrete_glassfish(interaction)

async def setup(bot):
    """Configuração do cog"""
    await bot.add_cog(GlassfishCog(bot))
