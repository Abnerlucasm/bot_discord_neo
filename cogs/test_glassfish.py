import discord
from discord.ext import commands
from discord import app_commands
import logging
import json
import datetime

class TestarLembreteSelect(discord.ui.Select):
    def __init__(self, servicos_config, simular_tempo: int):
        self.servicos_config = servicos_config
        self.simular_tempo = simular_tempo
        
        # Prepara as opções do dropdown apenas com serviços em uso
        options = []
        for key, config in servicos_config.items():
            if config["status"] == "em uso":
                options.append(
                    discord.SelectOption(
                        label=f"{key}: {config['nome'][:40]}", 
                        value=key,
                        description=f"Em uso por: {config['usuario']}"
                    )
                )
        
        if not options:
            options = [discord.SelectOption(label="Nenhum serviço em uso", value="none")]
        
        super().__init__(
            placeholder="Selecione um serviço para testar", 
            min_values=1, 
            max_values=1,
            options=options
        )
        
    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "none":
            await interaction.response.send_message(
                "Não há serviços em uso para testar.",
                ephemeral=True
            )
            return
            
        servico_id = self.values[0]
        config = self.servicos_config[servico_id]
        
        try:
            # Simula o tempo passado
            agora = datetime.datetime.now()
            tempo_simulado = agora - datetime.timedelta(hours=self.simular_tempo)
            
            # Atualiza os dados de uso
            if "usage_data" in config:
                usage_data = config["usage_data"]
                usage_data["timestamp"] = tempo_simulado.isoformat()
                usage_data["last_check"] = None
                usage_data["last_reminder"] = None
                usage_data["extension_count"] = 0
                config["usage_data"] = usage_data
            else:
                config["usage_data"] = {
                    "usuario": config["usuario"],
                    "user_id": interaction.user.id,
                    "timestamp": tempo_simulado.isoformat(),
                    "last_check": None,
                    "last_reminder": None,
                    "extension_count": 0
                }
            
            # Salva as alterações
            with open("services.json", "w", encoding="utf-8") as file:
                json.dump(self.servicos_config, file, indent=4)
            
            await interaction.response.send_message(
                f"✅ Tempo simulado para o serviço **{config['nome']}**.\n" +
                f"Simulando uso de {self.simular_tempo} horas atrás.",
                ephemeral=True
            )
            
        except Exception as e:
            logging.error(f"Erro ao simular tempo para o serviço {servico_id}: {str(e)}")
            await interaction.response.send_message(
                f"❌ Ocorreu um erro ao simular o tempo: {str(e)}",
                ephemeral=True
            )

class TestarLembreteView(discord.ui.View):
    def __init__(self, servicos_config, simular_tempo: int):
        super().__init__(timeout=None)
        self.add_item(TestarLembreteSelect(servicos_config, simular_tempo)) 