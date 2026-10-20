import json
import logging
import os
import re
from datetime import datetime

import discord

class Persistence:
    def __init__(self, bot=None):
        self.bot = bot
        self.data_file = "data/mensagens_data.json"
        self.data = {}
        self.views = {}
        self._ensure_data_directory()
        self._load_data()

    def _ensure_data_directory(self):
        """Garante que o diretório de dados existe"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)

    def _load_data(self):
        """Carrega os dados de persistência do arquivo"""
        try:
            if os.path.exists(self.data_file):
                try:
                    with open(self.data_file, 'r', encoding='utf-8') as f:
                        content = f.read().strip()

                        if not content:
                            logging.warning(f"Arquivo {self.data_file} está vazio. Inicializando com dados vazios.")
                            self.data = {}
                            self._save_data()
                        else:
                            self.data = json.loads(content)

                            # Migração dos metadados das views persistidas.
                            updated = False
                            for key, value in self.data.items():

                                if "view_type" not in value and "type" in value:
                                    value["view_type"] = value["type"]
                                    updated = True

                                if "original_data" not in value:
                                    value["original_data"] = {}
                                    updated = True

                            if updated:
                                self._save_data()
                                logging.info("Estrutura de dados da persistência atualizada")

                            logging.info(f"Carregadas {len(self.data)} mensagens interativas do arquivo")
                except json.JSONDecodeError as e:
                    logging.error(f"Arquivo de mensagens interativas corrompido: {self.data_file}")

                    if os.path.exists(self.data_file):
                        backup_file = f"{self.data_file}.bak.{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
                        try:
                            os.rename(self.data_file, backup_file)
                            logging.info(f"Backup do arquivo corrompido criado: {backup_file}")
                        except Exception as bk_err:
                            logging.error(f"Não foi possível criar backup: {str(bk_err)}")

                    self.data = {}
                    self._save_data()
            else:

                logging.info(f"Arquivo {self.data_file} não encontrado. Criando um novo.")
                self.data = {}
                self._save_data()
        except Exception as e:
            logging.error(f"Erro ao carregar dados de persistência: {e}")
            self.data = {}

    def _save_data(self):
        """Salva os dados de persistência no arquivo"""
        try:

            self._ensure_data_directory()

            # Cria uma cópia horária antes de salvar.
            try:
                hour_mark = datetime.utcnow().strftime('%Y%m%d%H')
                backup_file = f"{self.data_file}.{hour_mark}.bak"
                if os.path.exists(self.data_file) and not os.path.exists(backup_file):
                    import shutil
                    shutil.copy2(self.data_file, backup_file)
                    logging.debug(f"Backup horário criado: {backup_file}")
            except Exception as bk_err:
                logging.debug(f"Não foi possível criar backup horário: {str(bk_err)}")

            temp_file = f"{self.data_file}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)

            # A substituição do arquivo é atômica.
            if os.path.exists(temp_file):
                # No Windows, remova o arquivo antigo antes da substituição.
                if os.name == 'nt' and os.path.exists(self.data_file):
                    os.remove(self.data_file)
                os.rename(temp_file, self.data_file)

            return True
        except Exception as e:
            logging.error(f"Erro ao salvar dados de persistência: {e}")
            return False

    def register_message(self, message_id, view_type, original_data, author_id, channel_id):
        """Registra uma mensagem com dados para persistência."""
        try:

            if not os.path.exists(self.data_file) or os.path.getsize(self.data_file) == 0:
                logging.warning(f"Arquivo {self.data_file} vazio ou inexistente. Reinicializando.")
                self.data = {}

            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        test_data = json.loads(content)

            except Exception as verify_err:
                logging.error(f"Verificação do arquivo falhou: {str(verify_err)}. Reinicializando dados.")
                self.data = {}

            if not view_type:
                logging.warning(f"view_type não fornecido para a mensagem {message_id}, usando 'agendamento' como padrão")
                view_type = "agendamento"

            if not isinstance(original_data, dict):
                logging.warning(f"original_data não é um dicionário para a mensagem {message_id}, usando um dicionário vazio")
                original_data = {}

            message_id_str = str(message_id)
            self.data[message_id_str] = {
                "view_type": view_type,
                "original_data": original_data,
                "author_id": str(author_id),
                "channel_id": str(channel_id),
                "timestamp": datetime.utcnow().isoformat()
            }

            if self._save_data():
                logging.info(f"Mensagem {message_id} registrada para persistência como tipo {view_type}")
                return True
            return False
        except Exception as e:
            logging.error(f"Erro ao registrar mensagem {message_id}: {str(e)}")
            return False

    def remove_message(self, message_id):
        """Remove uma mensagem do armazenamento persistente."""
        try:
            message_id_str = str(message_id)
            if message_id_str in self.data:
                del self.data[message_id_str]
                self._save_data()
                logging.info(f"Mensagem {message_id} removida da persistência")
                return True
            else:
                logging.warning(f"Tentativa de remover mensagem {message_id} que não existe na persistência")
                return False
        except Exception as e:
            logging.error(f"Erro ao remover mensagem {message_id}: {str(e)}")
            return False

    async def get_message_data(self, message_id):
        """Recupera os dados persistidos de uma mensagem pelo seu ID.

        Args:
            message_id: O ID da mensagem a ser buscada

        Returns:
            dict: Dados da mensagem ou None se não encontrada/erro
        """
        try:
            message_id_str = str(message_id)

            if message_id_str in self.data:
                logging.info(f"Dados recuperados para mensagem {message_id}")
                return self.data[message_id_str]

            self._load_data()

            if message_id_str in self.data:
                logging.info(f"Dados recuperados após recarga para mensagem {message_id}")
                return self.data[message_id_str]

            logging.warning(f"Dados não encontrados para mensagem {message_id}")
            return None
        except Exception as e:
            logging.error(f"Erro ao recuperar dados da mensagem {message_id}: {str(e)}")
            return None

    async def restore_views(self, bot):
        """Restaura todas as views quando o bot inicia."""
        try:
            try:
                from cogs.schedule_ui import CustomView
                logging.info("CustomView carregada do pacote schedule_ui")
            except ImportError:
                logging.error("Não foi possível carregar CustomView do pacote schedule_ui")
                return False

            restored_count = 0
            all_restored = True
            logging.info(f"Iniciando restauração de {len(self.data)} mensagens interativas")

            for message_id, data in list(self.data.items()):
                try:
                    channel_id = data.get('channel_id')
                    author_id = data.get('author_id')
                    view_type = data.get('view_type', '')
                    original_data = data.get('original_data', {})

                    if not channel_id:
                        logging.warning(f"Canal não encontrado para mensagem {message_id}")
                        all_restored = False
                        continue

                    if not author_id:
                        content = data.get("content", "")
                        if content:

                            author_match = re.search(r"(?:<@!?|<@|<@&)(\d+)(?:>)", content)
                            if author_match:
                                author_id = author_match.group(1)

                    if not author_id:
                        logging.warning(f"Autor não encontrado para mensagem {message_id}")
                        author_id = bot.user.id

                    try:
                        channel = bot.get_channel(int(channel_id))
                        if not channel:

                            try:
                                channel = await bot.fetch_channel(int(channel_id))
                            except (discord.HTTPException, TypeError, ValueError) as e:
                                logging.warning(f"Canal {channel_id} inválido ou indisponível: {e}")
                                all_restored = False
                                continue

                        try:
                            message = await channel.fetch_message(int(message_id))

                            if not view_type:

                                content = message.content
                                if "AGENDAMENTO" in content:
                                    view_type = "agendamento"
                                elif "ATUALIZAÇÃO" in content:
                                    view_type = "atualizacao"
                                elif "VERSÃO BETA 99" in content:
                                    view_type = "beta99"
                                else:
                                    view_type = "agendamento"
                                logging.info(f"Tipo de view inferido: {view_type}")

                            view = CustomView(
                                modal_type=view_type,
                                original_data=original_data,
                                author_id=int(author_id)
                            )

                            if not self.register_view(message_id, view):
                                all_restored = False

                            await message.edit(view=view)
                            restored_count += 1
                            logging.info(f"View restaurada com sucesso para a mensagem {message_id}")

                        except discord.NotFound:
                            logging.warning(f"Mensagem {message_id} não encontrada no canal {channel_id}")
                            self.remove_message(message_id)
                        except discord.Forbidden:
                            logging.warning(f"Sem permissão para acessar a mensagem {message_id}")
                            all_restored = False
                        except discord.HTTPException as e:
                            logging.error(f"Erro HTTP ao acessar a mensagem {message_id}: {str(e)}")
                            all_restored = False
                    except Exception as fetch_err:
                        logging.error(f"Erro ao processar canal/mensagem {message_id}: {str(fetch_err)}")
                        all_restored = False
                except Exception as inner_e:
                    logging.error(f"Erro ao processar dados da mensagem {message_id}: {str(inner_e)}")
                    all_restored = False

            logging.info(f"Restauradas {restored_count} views com sucesso")
            return all_restored
        except Exception as e:
            logging.error(f"Erro ao restaurar views: {str(e)}")
            return False

    def register_view(self, message_id, view):
        """Registra uma view para uma mensagem"""
        message_id_str = str(message_id)
        self.views[message_id_str] = view

        if self.bot:
            try:
                self.bot.add_view(view, message_id=int(message_id))
                logging.info(f"View da mensagem {message_id} registrada")
                return True
            except Exception as e:
                logging.error(f"Erro ao registrar view globalmente para mensagem {message_id}: {str(e)}")
                return False
        return True

_persistence_instance = None

def setup_persistence(bot=None):
    """Configura a instância global de persistência"""
    global _persistence_instance
    _persistence_instance = Persistence(bot)
    return _persistence_instance

def get_instance_persistence(bot=None):
    """Obtém a instância global de persistência"""
    global _persistence_instance
    if _persistence_instance is None:
        _persistence_instance = Persistence(bot)
    return _persistence_instance

async def restore_views(bot):
    """
    Restaura as views para as mensagens salvas na persistência.
    """
    persistence = get_instance_persistence(bot)
    return await persistence.restore_views(bot)
