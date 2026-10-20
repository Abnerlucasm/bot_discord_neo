
import logging
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

import discord
from discord.ext import commands

from cogs.glassfish import GlassfishCog
from cogs.help import HelpCog
from cogs.schedule_update import ScheduleUpdateCog
from cogs.utils import setup_interaction_handler, setup_persistence

if not os.path.exists('logs'):
    os.makedirs('logs')

if not os.path.exists('data'):
    os.makedirs('data')

log_file = os.path.join('logs', 'bot.log')
handler = TimedRotatingFileHandler(
    filename=log_file,
    when='midnight',
    interval=1,
    backupCount=30,
    encoding='utf-8'
)
handler.suffix = '%Y-%m-%d.log'

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)

class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix=".", intents=intents)

        self.interactive_messages = {}

    @staticmethod
    def _create_guild_command(name, description, callback):
        command = discord.app_commands.Command(
            name=name,
            description=description,
            callback=callback,
        )
        command.guild_only = True
        return command

    async def setup_hook(self):
        try:
            glassfish_cog = GlassfishCog(self)
            await self.add_cog(glassfish_cog)
            await self.add_cog(HelpCog(self))

            schedule_cog = ScheduleUpdateCog(self)
            await self.add_cog(schedule_cog)

            self.tree.add_command(self._create_guild_command(
                "beta99",
                "Registra uma nova versão beta 99",
                schedule_cog.beta99,
            ))
            self.tree.add_command(self._create_guild_command(
                "agendamento",
                "Registra um novo agendamento",
                schedule_cog.agendamento,
            ))
            self.tree.add_command(self._create_guild_command(
                "atualizacao",
                "Registra uma nova atualização",
                schedule_cog.atualizacao,
            ))
            setup_persistence(self)
            setup_interaction_handler(self)
            try:
                await self.tree.sync()
                logging.info("Comandos sincronizados no setup_hook")
            except Exception as sync_error:
                logging.error(f"Erro ao sincronizar comandos no setup_hook: {str(sync_error)}")

            logging.info("Todos os cogs foram carregados com sucesso")
        except Exception as e:
            logging.error(f"Erro ao carregar cogs: {str(e)}")
            raise

    async def on_ready(self):
        print(f'{self.user} está pronto!')
        logging.info(f'Bot iniciado como {self.user}')
        await self.change_presence(activity=discord.Game("Neo Chamados"))

    def save_interactive_message(self, message_id, channel_id, message_type, author_id, original_data=None):
        """Salva uma mensagem interativa para persistência"""
        try:

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

            # Mantém a referência em memória por compatibilidade.
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

            from cogs.persistence import get_instance_persistence
            persistence = get_instance_persistence(self)

            success = persistence.remove_message(message_id)

            if success:
                logging.info(f"Mensagem {message_id} removida com sucesso da persistência")
            else:
                logging.warning(f"Mensagem {message_id} não encontrada na persistência ou erro ao remover")

            # Mantém o dicionário em memória por compatibilidade.
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
