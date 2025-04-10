import discord
import logging
import re
import asyncio
from cogs.persistence import get_instance_persistence

# Emoji para status de agendamento
EMOJI_STATUS_AGEND = "<:discotoolsxyzicon1:1331628487202705554>"

# Importa as classes necessárias de schedule_update.py
try:
    from cogs.schedule_update import (
        AgendamentoModal, 
        AtualizacaoModal, 
        Beta99Modal, 
        ConfirmarAgendamentoModal,
        StatusButton,
        ConfirmarButton,
        EditButton,
        DeleteButton,
        CustomView,
        ConfirmarAgendamentoButton,
        PularButton
    )
    CLASSES_IMPORTADAS = True
    logging.info("Classes de schedule_update.py carregadas com sucesso")
except ImportError as e:
    CLASSES_IMPORTADAS = False
    logging.error(f"Erro ao importar classes de schedule_update.py: {str(e)}")

async def handle_button_interactions(interaction: discord.Interaction, bot):
    """
    Processa as interações de botões delegando para as classes de schedule_update.py
    """
    if not CLASSES_IMPORTADAS:
        await interaction.response.send_message(
            "Ocorreu um erro de configuração no bot. Por favor, contacte o administrador.",
            ephemeral=True
        )
        return

    try:
        # FASE 1: Extração de dados da interação
        logging.info(f"Interação de botão recebida de {interaction.user} (ID: {interaction.user.id})")
        
        # Obtém o ID personalizado do botão
        button_id = interaction.data.get('custom_id', '')
        message = interaction.message
        message_id = str(message.id)
        content = message.content if message else ""
        components = message.components if message else []
        
        # FASE 2: Recuperação de dados da persistência
        persistence = get_instance_persistence(bot)
        message_data = await persistence.get_message_data(message_id)
        
        # Identifica o tipo de visualização com base no conteúdo da mensagem
        view_type = None
        if "AGENDAMENTO" in content:
            view_type = "agendamento"
            logging.info(f"Tipo de visualização inferido: {view_type}")
        elif "ATUALIZAÇÃO" in content:
            view_type = "atualizacao"
            logging.info(f"Tipo de visualização inferido: {view_type}")
        elif "VERSÃO BETA 99" in content:
            view_type = "beta99"
            logging.info(f"Tipo de visualização inferido: {view_type}")
        
        # FASE 3: Verificação de botão pelo texto do rótulo ou custom_id
        button_type = None
        button_label = None
        
        # Procura pelo botão nos componentes da mensagem
        if components:
            for action_row in components:
                try:
                    # Tenta acessar os componentes usando children
                    components_list = action_row.children
                except AttributeError:
                    # Se children não existir, tenta usar outra abordagem
                    try:
                        # Tenta acessar diretamente como se fosse um item iterável
                        components_list = action_row
                    except:
                        logging.error(f"Não foi possível acessar os componentes da linha de ação: {action_row}")
                        continue
                
                if isinstance(components_list, list):
                    # Se for uma lista, itera normalmente
                    for component in components_list:
                        if hasattr(component, 'custom_id') and component.custom_id == button_id:
                            button_label = component.label.lower() if hasattr(component, 'label') else None
                            logging.info(f"Botão encontrado: {button_label} (ID: {button_id})")
                            
                            # Identifica o tipo de botão pelo rótulo
                            if button_label:
                                if "receber" in button_label or "aguardando" in button_label:
                                    button_type = "rcv"
                                elif "confirmar data" in button_label or "data" in button_label:
                                    button_type = "dat"
                                elif "editar" in button_label:
                                    button_type = "edt"
                                elif "excluir" in button_label or "deletar" in button_label:
                                    button_type = "del" 
                                elif "finalizar" in button_label:
                                    button_type = "fin"
                                elif "concluir" in button_label:
                                    button_type = "con"
                            break
                elif hasattr(components_list, 'custom_id') and components_list.custom_id == button_id:
                    # Se for um único componente que corresponde ao botão
                    button_label = components_list.label.lower() if hasattr(components_list, 'label') else None
                    logging.info(f"Botão único encontrado: {button_label} (ID: {button_id})")
                    
                    # Identifica o tipo de botão pelo rótulo
                    if button_label:
                        if "receber" in button_label or "aguardando" in button_label:
                            button_type = "rcv"
                        elif "confirmar data" in button_label or "data" in button_label:
                            button_type = "dat"
                        elif "editar" in button_label:
                            button_type = "edt"
                        elif "excluir" in button_label or "deletar" in button_label:
                            button_type = "del" 
                        elif "finalizar" in button_label:
                            button_type = "fin"
                        elif "concluir" in button_label:
                            button_type = "con"
                    
                if button_type:
                    break

        # Se ainda não encontrou o tipo do botão, tenta identificar pelo custom_id
        if not button_type:
            logging.info(f"Tentando identificar botão pelo custom_id: {button_id}")
            
            # Detecta pelo prefixo do custom_id
            if button_id.startswith("rcv"):
                button_type = "rcv"
            elif button_id.startswith("dat"):
                button_type = "dat"
            elif button_id.startswith("edt"):
                button_type = "edt"
            elif button_id.startswith("del"):
                button_type = "del"
            elif button_id.startswith("fin"):
                button_type = "fin"
            elif button_id.startswith("con"):
                button_type = "con"
            # Botões da segunda etapa de criação de agendamento
            elif "confirm" in button_id.lower():
                button_type = "confirm_role"
            elif "pular" in button_id.lower() or "skip" in button_id.lower():
                button_type = "skip_role"
        
        if not button_type:
            logging.warning(f"Tipo de botão não identificado para ID: {button_id}")
            await interaction.response.send_message(
                "Este botão não pôde ser identificado. Por favor, tente outra ação.",
                ephemeral=True
            )
            return

        # Define valores padrão
        author_id = None
        original_data = {}
        
        # Carrega dados da persistência
        if message_data:
            author_id = message_data.get('author_id')
            original_data = message_data.get('original_data', {})
            view_type = message_data.get('view_type', view_type)
        
        # Se não temos author_id, tenta extrair da mensagem
        if author_id is None:
            author_match_patterns = [
                r"Solicitado por: <@(\d+)>",  # Para agendamentos
                r"Atualizado por: <@(\d+)>"   # Para atualizações
            ]
            
            for pattern in author_match_patterns:
                author_mention_match = re.search(pattern, content)
                if author_mention_match:
                    author_id = author_mention_match.group(1)
                    logging.info(f"Autor ID {author_id} extraído da mensagem {message_id}")
                    break
        
        # Verificações de permissão para botões de edição/exclusão
        if button_type in ["edt", "del"]:
            # Verifica se o usuário atual é o autor da mensagem original
            if author_id and str(author_id) != str(interaction.user.id):
                logging.warning(f"Permissão negada: Usuário {interaction.user.id} tentou {button_type} mensagem de {author_id}")
                await interaction.response.send_message(
                    "Você não tem permissão para editar/excluir esta mensagem. Apenas o autor original pode fazer isso.",
                    ephemeral=True
                )
                return

        # Se não estiver na persistência e conseguimos extrair dados, registra
        if not message_data and view_type and author_id:
            persistence.register_message(
                message_id=message_id,
                view_type=view_type,
                original_data=original_data,
                author_id=author_id,
                channel_id=interaction.channel_id
            )
            logging.info(f"Dados inferidos registrados na persistência para mensagem {message_id}")

        # FASE 4: Processamento do botão
        try:
            # Delega para a classe apropriada com base no tipo de botão
            if button_type == "rcv":
                try:
                    # Em vez de criar um StatusButton, vamos extrair a view da mensagem
                    # e gerenciar diretamente o conteúdo da mensagem
                    logging.info(f"Processando botão de recebimento")
                    
                    # Verifica o status atual através do conteúdo da mensagem
                    status_atual = "Pendente"
                    if "Recebido por" in content:
                        status_atual = "Recebido"
                    
                    # Inverte o status
                    novo_status = "Recebido" if status_atual == "Pendente" else "Pendente"
                    
                    # Obtém a view original da mensagem
                    view = CustomView(
                        modal_type=view_type, 
                        original_data=original_data, 
                        author_id=int(author_id) if author_id else interaction.user.id
                    )
                    
                    # Processa as linhas de conteúdo
                    content_lines = content.split('\n')
                    new_lines = []
                    
                    # Verifica se já está agendado
                    is_agendado = any("Data Confirmada:" in line for line in content_lines)
                    status_complement = "Agendado" if is_agendado else (
                        "Aguardando Agendamento" if novo_status == "Recebido" else "Aguardando Recebimento"
                    )
                    
                    # Informação de quem recebeu
                    recebido_por = f"<@{interaction.user.id}>" if novo_status == "Recebido" else ""
                    confirmado_por = None
                    
                    # Processa as linhas para atualizar o status
                    instrucoes_encontradas = False
                    for line in content_lines:
                        # Ignora linhas de instruções e histórico anteriores, serão recriadas
                        if line.startswith("**INSTRUÇÕES PARA OS RESPONSÁVEIS") or \
                           line.startswith("**Histórico de Ações") or \
                           line.startswith("1️⃣") or line.startswith("2️⃣") or \
                           line.startswith("✅ **Status Atual") or \
                           line.startswith("📋 Solicitação recebida") or \
                           line.startswith("🗓️ Data confirmada") or \
                           line == "":
                            instrucoes_encontradas = True
                            continue
                            
                        # Captura informação de quem confirmou a data, se existir
                        if "Data Confirmada:" in line:
                            if "por" in line:
                                confirmado_por = line.split("por")[1].strip()
                            
                        # Atualiza a linha de status
                        if "**• Status:**" in line:
                            status_line = f"**{EMOJI_STATUS_AGEND} • Status: **{novo_status}{' por ' + recebido_por if recebido_por else ''} | {status_complement}"
                            new_lines.append(status_line)
                        else:
                            new_lines.append(line)
                    
                    # Adiciona instruções e histórico após todas as outras informações
                    if novo_status == "Recebido":
                        # Adiciona quebra de linha antes das instruções
                        new_lines.append("")
                        new_lines.append("**INSTRUÇÕES PARA OS RESPONSÁVEIS:**")
                        if is_agendado:
                            new_lines.append("✅ **Status Atual**: Agendamento confirmado")
                        else:
                            new_lines.append("✅ **Status Atual**: Solicitação recebida, aguardando confirmação da data")
                            new_lines.append("2️⃣ Clique em \"🗓️ Confirmar Data do Agendamento\" para definir a data confirmada")
                            
                        # Adiciona o histórico de ações
                        new_lines.append("")
                        new_lines.append("**Histórico de Ações:**")
                        new_lines.append(f"📋 Solicitação recebida por {recebido_por}")
                        if confirmado_por:
                            new_lines.append(f"🗓️ Data confirmada por {confirmado_por}")
                    else:
                        # Se o status voltou para Pendente, restaura as instruções originais
                        new_lines.append("")
                        new_lines.append("**INSTRUÇÕES PARA OS RESPONSÁVEIS:**")
                        new_lines.append("1️⃣ Clique em \"📋 Aguardando Recebimento\" para indicar que você recebeu a solicitação")
                        new_lines.append("2️⃣ Clique em \"🗓️ Confirmar Data do Agendamento\" para definir a data confirmada")
                    
                    # Atualiza a view com o novo status nos botões
                    for child in view.children:
                        if isinstance(child, StatusButton):
                            child.status = novo_status
                            child.style = discord.ButtonStyle.success if novo_status == "Recebido" else discord.ButtonStyle.danger
                            child.label = "✅ Solicitação Recebida" if novo_status == "Recebido" else "⚠️ Aguardando Recebimento"
                    
                    # Atualiza a mensagem com o novo conteúdo e a view atualizada
                    await interaction.message.edit(content='\n'.join(new_lines), view=view)
                    await interaction.response.send_message(f"Você alterou o status para: **{novo_status}**", ephemeral=True)
                    
                except Exception as e:
                    logging.error(f"Erro ao processar botão de recebimento: {str(e)}", exc_info=True)
                    if not interaction.response.is_done():
                        await interaction.response.send_message(
                            "Ocorreu um erro ao processar o botão de recebimento. Por favor, tente novamente.",
                            ephemeral=True
                        )
                
            elif button_type == "dat":
                # Botão de confirmar data
                # Cria um modal de confirmação de agendamento
                modal = ConfirmarAgendamentoModal(original_data)
                modal.message = interaction.message
                modal.view = CustomView(
                    modal_type=view_type, 
                    original_data=original_data, 
                    author_id=int(author_id) if author_id else interaction.user.id
                )
                await interaction.response.send_modal(modal)
                
            elif button_type == "edt":
                # Botão de editar
                # Cria um botão de edição e invoca seu callback
                edit_button = EditButton(
                    modal_type=view_type, 
                    original_data=original_data, 
                    author_id=int(author_id) if author_id else interaction.user.id
                )
                await edit_button.callback(interaction)
                
            elif button_type == "del":
                # Botão de deletar
                # Cria um botão de exclusão e invoca seu callback
                delete_button = DeleteButton(
                    author_id=int(author_id) if author_id else interaction.user.id
                )
                await delete_button.callback(interaction)
                
            elif button_type == "fin":
                try:
                    # Implementação direta para finalizar agendamento
                    logging.info(f"Processando botão de finalizar")
                    
                    # Verifica se o agendamento já foi finalizado
                    if "AGENDAMENTO FINALIZADO" in content:
                        await interaction.response.send_message(
                            "Este agendamento já foi finalizado.",
                            ephemeral=True
                        )
                        return
                    
                    # Verifica se tem data confirmada
                    if not any("Data Confirmada:" in line for line in content):
                        await interaction.response.send_message(
                            "Você precisa primeiro confirmar a data do agendamento antes de finalizar.",
                            ephemeral=True
                        )
                        return
                    
                    # Obtém a view original da mensagem
                    view = CustomView(
                        modal_type=view_type, 
                        original_data=original_data, 
                        author_id=int(author_id) if author_id else interaction.user.id
                    )
                    
                    # Processa as linhas de conteúdo
                    content_lines = content.split('\n')
                    new_lines = []
                    
                    # Adiciona cabeçalho de finalizado
                    new_lines.append("**AGENDAMENTO FINALIZADO** ✅")
                    
                    # Processa as linhas para manter informações importantes
                    for line in content_lines[1:]:  # Pula o título original
                        if (line.startswith("**INSTRUÇÕES PARA OS RESPONSÁVEIS") or 
                            line.startswith("**Histórico de Ações") or 
                            line == ""):
                            continue
                        elif "**• Status:**" in line:
                            new_lines.append(f"**{EMOJI_STATUS_AGEND} • Status: **Finalizado por <@{interaction.user.id}> | Concluído")
                        else:
                            new_lines.append(line)
                    
                    # Adiciona nova seção de histórico
                    new_lines.append("\n**Histórico de Ações:**")
                    # Procura quem recebeu e confirmou no conteúdo original
                    recebido_por = None
                    confirmado_por = None
                    for line in content_lines:
                        if "Recebido por" in line and "Status:" in line:
                            recebido_match = re.search(r"Recebido por <@(\d+)>", line)
                            if recebido_match:
                                recebido_por = f"<@{recebido_match.group(1)}>"
                        if "Data Confirmada:" in line and "por" in line:
                            confirmado_match = re.search(r"por <@(\d+)>", line)
                            if confirmado_match:
                                confirmado_por = f"<@{confirmado_match.group(1)}>"
                    
                    if recebido_por:
                        new_lines.append(f"📋 Solicitação recebida por {recebido_por}")
                    if confirmado_por:
                        new_lines.append(f"🗓️ Data confirmada por {confirmado_por}")
                    new_lines.append(f"✅ Agendamento finalizado por <@{interaction.user.id}>")
                    
                    # Atualiza a view: desativa ou esconde botões
                    for child in view.children:
                        # Desativa todos os botões exceto o de excluir
                        if not isinstance(child, DeleteButton):
                            # Atualiza estilo para mostrar como concluído
                            if isinstance(child, StatusButton):
                                child.style = discord.ButtonStyle.success
                                child.label = "✅ Agendamento Finalizado"
                                child.disabled = True
                            else:
                                child.disabled = True
                    
                    # Atualiza a mensagem
                    await interaction.message.edit(content='\n'.join(new_lines), view=view)
                    await interaction.response.send_message("Agendamento finalizado com sucesso!", ephemeral=True)
                
                except Exception as e:
                    logging.error(f"Erro ao processar botão de finalizar: {str(e)}", exc_info=True)
                    if not interaction.response.is_done():
                        await interaction.response.send_message(
                            "Ocorreu um erro ao finalizar o agendamento. Por favor, tente novamente.",
                            ephemeral=True
                        )
            
            elif button_type == "con":
                try:
                    # Implementação direta para concluir atualização
                    logging.info(f"Processando botão de concluir")
                    
                    # Verifica se a atualização já foi concluída
                    if "ATUALIZAÇÃO CONCLUÍDA" in content:
                        await interaction.response.send_message(
                            "Esta atualização já foi concluída.",
                            ephemeral=True
                        )
                        return
                    
                    # Obtém a view original da mensagem
                    view = CustomView(
                        modal_type=view_type, 
                        original_data=original_data, 
                        author_id=int(author_id) if author_id else interaction.user.id
                    )
                    
                    # Processa as linhas de conteúdo
                    content_lines = content.split('\n')
                    new_lines = []
                    
                    # Adiciona cabeçalho de concluído
                    new_lines.append("**ATUALIZAÇÃO CONCLUÍDA** ✅")
                    
                    # Processa as linhas para manter informações importantes
                    for line in content_lines[1:]:  # Pula o título original
                        if not "**ATUALIZAÇÃO**" in line:
                            new_lines.append(line)
                    
                    # Adiciona informação de quem concluiu
                    new_lines.append(f"\n**• Concluído por:** <@{interaction.user.id}>")
                    
                    # Atualiza a view: desativa ou esconde botões
                    for child in view.children:
                        # Desativa todos os botões exceto o de excluir
                        if not isinstance(child, DeleteButton):
                            # Atualiza estilo para mostrar como concluído
                            if isinstance(child, StatusButton):
                                child.style = discord.ButtonStyle.success
                                child.label = "✅ Atualização Concluída"
                                child.disabled = True
                            else:
                                child.disabled = True
                    
                    # Atualiza a mensagem
                    await interaction.message.edit(content='\n'.join(new_lines), view=view)
                    await interaction.response.send_message("Atualização concluída com sucesso!", ephemeral=True)
                
                except Exception as e:
                    logging.error(f"Erro ao processar botão de concluir: {str(e)}", exc_info=True)
                    if not interaction.response.is_done():
                        await interaction.response.send_message(
                            "Ocorreu um erro ao concluir a atualização. Por favor, tente novamente.",
                            ephemeral=True
                        )
            
            elif button_type == "confirm_role" or button_type == "skip_role":
                # Botões de confirmação/pular na seleção de cargos
                # Extrai dados do modal inicial da mensagem
                modal = AgendamentoModal(original_data)
                modal.author_id = interaction.user.id
                
                if button_type == "confirm_role":
                    # Extrai o cargo selecionado da mensagem
                    selected_role_id = None
                    role_mention_match = re.search(r"Cargo selecionado: <@&(\d+)>", interaction.message.content)
                    if role_mention_match:
                        selected_role_id = role_mention_match.group(1)
                        role = interaction.guild.get_role(int(selected_role_id))
                        if role:
                            modal.selected_role = role
                    
                    # Usa o botão confirmar
                    confirmar_button = ConfirmarAgendamentoButton(modal)
                    await confirmar_button.callback(interaction)
                else:
                    # Usa o botão pular
                    pular_button = PularButton(modal)
                    await pular_button.callback(interaction)
                
        except Exception as e:
            logging.error(f"Erro ao processar botão tipo {button_type}: {str(e)}", exc_info=True)
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "Ocorreu um erro ao processar sua solicitação. Por favor, tente novamente.",
                    ephemeral=True
                )
            
    except Exception as e:
        logging.error(f"Erro geral no processamento de interação: {str(e)}", exc_info=True)
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "Ocorreu um erro inesperado. Por favor, tente novamente ou contate o administrador.",
                ephemeral=True
            )

def setup_interaction_handler(bot):
    """Configura o handler global para todas as interações de botões"""
    
    from cogs.persistence import restore_views
    
    # Restaura as views quando o bot inicia
    @bot.event
    async def on_ready():
        # Dá um pequeno delay para garantir que tudo esteja carregado
        await asyncio.sleep(1)
        await restore_views(bot)
    
    @bot.event
    async def on_interaction(interaction):
        try:
            # Verifica se é uma interação de componente (botão)
            if interaction.type != discord.InteractionType.component:
                return

            # Log para diagnóstico
            logging.info(f"Interação detectada - custom_id: {interaction.data.get('custom_id')}")
            
            # Checagem para botões específicos do agendamento e notificações
            custom_id = interaction.data.get('custom_id', '')
            
            # Verifica se é um botão da seleção de role
            if custom_id and (custom_id.startswith('confirm_role_') or custom_id.startswith('skip_role_')):
                logging.info(f"Delegando interação de seleção de role para manipulador: {custom_id}")
                await handle_button_interactions(interaction, bot)
                return
            
            # Verifica se é um botão de mensagem persistida
            if interaction.message:
                persistence = get_instance_persistence(bot)
                
                # Verifica se a mensagem está nos dados de persistência
                message_id = str(interaction.message.id)
                if message_id in persistence.data:
                    logging.info(f"Mensagem {message_id} encontrada na persistência - processando")
                    await handle_button_interactions(interaction, bot)
                    return
                
                # Verifica se é uma mensagem de agendamento/notificação baseada no conteúdo
                message_content = interaction.message.content if interaction.message.content else ""
                is_notification = (
                    "**AGENDAMENTO**" in message_content or 
                    "**ATUALIZAÇÃO**" in message_content or
                    "**BETA99**" in message_content or
                    "**AGENDAMENTO FINALIZADO**" in message_content or
                    "**ATUALIZAÇÃO CONCLUÍDA**" in message_content
                )
                
                if is_notification:
                    logging.info(f"Mensagem {message_id} identificada como notificação pelo conteúdo - processando")
                    await handle_button_interactions(interaction, bot)
                    return
            
            # Se chegou aqui, deixa o discord.py lidar normalmente
            logging.info(f"Permitindo que o discord.py processe a interação normalmente")
            
        except Exception as e:
            logging.error(f"Erro ao processar interação: {str(e)}", exc_info=True)
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "Ocorreu um erro ao processar esta interação. Por favor, tente novamente.",
                    ephemeral=True
                ) 