# main.py
import discord
from discord.ext import commands
import logging
import json
import os
from cogs.glassfish import GlassfishCog
from cogs.help import HelpCog
from cogs.schedule_update import ScheduleUpdateCog
# from cogs.glassfish_gerenciador import GlassfishManagementCog
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from cogs.utils import setup_interaction_handler, setup_persistence

# Criar pasta logs se não existir
if not os.path.exists('logs'):
    os.makedirs('logs')

# Criar pasta data se não existir
if not os.path.exists('data'):
    os.makedirs('data')

# Arquivo de persistência para mensagens interativas
MESSAGES_DB_FILE = os.path.join('data', 'mensagens_data.json')

# Configuração do sistema de log
log_file = os.path.join('logs', 'bot.log')
handler = TimedRotatingFileHandler(
    filename=log_file,
    when='midnight',
    interval=1,
    backupCount=30,  # Mantém logs dos últimos 30 dias
    encoding='utf-8'
)
handler.suffix = '%Y-%m-%d.log'  # Formato do arquivo: bot.2024-02-21.log

# Formato do log
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Configuração do logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)

class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix=".", intents=intents)
        
        # Dicionário para armazenar mensagens interativas
        self.interactive_messages = {}
        
    async def setup_hook(self):
        # Carrega as configurações
        try:
            with open("services.json", "r", encoding="utf-8") as file:
                self.servicos_config = json.load(file)
            logging.info("Arquivo services.json carregado com sucesso")
        except Exception as e:
            logging.error(f"Erro ao carregar services.json: {str(e)}")
            self.servicos_config = {}
        
        # Carrega os cogs
        try:
            glassfish_cog = GlassfishCog(self)
            await self.add_cog(glassfish_cog)
            await self.add_cog(HelpCog(self))
            
            # Criamos manualmente o cog e os comandos
            schedule_cog = ScheduleUpdateCog(self)
            await self.add_cog(schedule_cog)
            
            # Registra explicitamente os comandos principais
            self.tree.add_command(discord.app_commands.Command(
                name="beta99",
                description="Registra uma nova versão beta 99",
                callback=schedule_cog.beta99
            ))
            
            self.tree.add_command(discord.app_commands.Command(
                name="agendamento",
                description="Registra um novo agendamento",
                callback=schedule_cog.agendamento
            ))
            
            self.tree.add_command(discord.app_commands.Command(
                name="atualizacao",
                description="Registra uma nova atualização",
                callback=schedule_cog.atualizacao
            ))
            
            # Garantir que todos os comandos do GlassfishCog estão registrados
            glassfish_commands = [
                glassfish_cog.glassfish,
                glassfish_cog.recarregar_config_glassfish,
                glassfish_cog.verificacao_forcada_glassfish,
                glassfish_cog.configurar_timeout_glassfish,
                glassfish_cog.obter_timeout_glassfish,
                glassfish_cog.relatorio_glassfish,
                glassfish_cog.adicionar_glassfish,
                glassfish_cog.editar_glassfish,
                glassfish_cog.remover_glassfish,
                glassfish_cog.liberar_todos_glassfish,
                glassfish_cog.testar_lembrete_glassfish
            ]
            
            # Registra explicitamente cada comando do Glassfish
            for cmd in glassfish_commands:
                try:
                    cmd_name = cmd.qualified_name
                    cmd_exists = any(registered_cmd.name == cmd_name for registered_cmd in self.tree.get_commands())
                    
                    if not cmd_exists:
                        self.tree.add_command(cmd)
                        logging.info(f"Comando {cmd_name} registrado manualmente")
                except Exception as cmd_error:
                    logging.error(f"Erro ao registrar comando: {str(cmd_error)}")
            
            # Tenta sincronizar logo no início
            try:
                await self.tree.sync()
                logging.info("Comandos sincronizados no setup_hook")
            except Exception as sync_error:
                logging.error(f"Erro ao sincronizar comandos no setup_hook: {str(sync_error)}")
            
            logging.info("Todos os cogs foram carregados com sucesso")
        except Exception as e:
            logging.error(f"Erro ao carregar cogs: {str(e)}")
        
        # Adicionar perto do final do arquivo bot.py, após as outras inicializações
        setup_persistence(self)  # Se ainda não estiver chamando isso
        setup_interaction_handler(self)  # Configura o handler global de interações
        
    async def on_ready(self):
        print(f'{self.user} está pronto!')
        logging.info(f'Bot iniciado como {self.user}')
        await self.change_presence(activity=discord.Game("Neo Chamados"))
        
        try:
            # Sincroniza comandos com reset completo
            commands = await self.tree.sync()
            command_names = [cmd.name for cmd in commands]
            logging.info(f"Comandos sincronizados: {', '.join(command_names)}")
            print(f"Comandos sincronizados: {', '.join(command_names)}")
        except Exception as e:
            logging.error(f"Erro ao sincronizar comandos: {str(e)}")
            print(f"Erro ao sincronizar comandos: {str(e)}")
            
        # Inicializa o sistema de persistência com o caminho correto
        try:
            # Carrega e reconecta mensagens interativas anteriores
            await self.load_interactive_messages()
        except Exception as e:
            logging.error(f"Erro ao carregar mensagens interativas: {str(e)}")
    
    async def load_interactive_messages(self):
        """Carrega as mensagens interativas anteriores e reconecta os botões"""
        try:
            # Inicializa o módulo de persistência
            from cogs.persistence import setup_persistence
            persistence = setup_persistence(self)
            
            # Verifica se o arquivo de mensagens existe
            if not os.path.exists(MESSAGES_DB_FILE):
                logging.info(f"Arquivo de mensagens interativas não encontrado: {MESSAGES_DB_FILE}")
                return
                
            # Carrega as mensagens do arquivo
            try:
                with open(MESSAGES_DB_FILE, 'r') as f:
                    messages_data = json.load(f)
                    
                logging.info(f"Carregadas {len(messages_data)} mensagens interativas do arquivo")
                
                # Restaura todas as views usando o módulo de persistência
                from cogs.persistence import restore_views
                success = await restore_views(self)
                
                if success:
                    logging.info(f"Views restauradas com sucesso usando o novo sistema modular")
                else:
                    logging.error(f"Erro ao restaurar views usando o novo sistema modular")
                
            except json.JSONDecodeError:
                logging.error(f"Arquivo de mensagens interativas corrompido: {MESSAGES_DB_FILE}")
                
        except Exception as e:
            import traceback
            logging.error(f"Erro ao carregar mensagens interativas: {str(e)}")
            logging.error(traceback.format_exc())
    
    def save_interactive_message(self, message_id, channel_id, message_type, author_id, original_data=None):
        """Salva uma mensagem interativa para persistência"""
        try:
            # Usa o sistema de persistência para registrar a mensagem
            from cogs.persistence import get_instance_persistence
            persistence = get_instance_persistence(self)
            
            success = persistence.register_message(
                message_id=message_id,
                view_type=message_type,
                original_data=original_data or {},
                author_id=author_id,
                channel_id=channel_id
            )
            
            if success:
                logging.info(f"Mensagem {message_id} registrada com sucesso na persistência")
            else:
                logging.error(f"Falha ao registrar mensagem {message_id} na persistência")
            
            # Mantém a referência no dicionário de memória para compatibilidade
            self.interactive_messages[str(message_id)] = {
                'channel_id': str(channel_id),
                'type': message_type,
                'author_id': str(author_id),
                'original_data': original_data or {},
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Erro ao salvar mensagem interativa: {str(e)}")

    def remove_interactive_message(self, message_id):
        """Remove uma mensagem interativa do registro de persistência"""
        try:
            # Usa o sistema de persistência para remover a mensagem
            from cogs.persistence import get_instance_persistence
            persistence = get_instance_persistence(self)
            
            success = persistence.remove_message(message_id)
            
            if success:
                logging.info(f"Mensagem {message_id} removida com sucesso da persistência")
            else:
                logging.warning(f"Mensagem {message_id} não encontrada na persistência ou erro ao remover")
            
            # Mantém o dicionário de memória atualizado para compatibilidade
            if str(message_id) in self.interactive_messages:
                del self.interactive_messages[str(message_id)]
                
        except Exception as e:
            logging.error(f"Erro ao remover mensagem interativa: {str(e)}")
          
def main():
    try:
        with open("token.txt", "r") as file:
            token = file.read().strip()
        logging.info("Token carregado com sucesso")
        
        bot = Bot()
        bot.run(token)
    except Exception as e:
        logging.error(f"Erro ao carregar/executar o bot: {str(e)}")

if __name__ == "__main__":
    main()
