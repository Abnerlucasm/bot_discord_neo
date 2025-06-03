import datetime
from typing import Optional, Dict, Any


class UsageData:
    def __init__(self, usuario: str, user_id: int, timestamp: Optional[datetime.datetime] = None):
        self.usuario = usuario
        self.user_id = user_id
        self.timestamp = timestamp or datetime.datetime.now()
        self.last_check: Optional[datetime.datetime] = None
        self.last_reminder: Optional[datetime.datetime] = None
        self.extension_count = 0  # Contador de extensões de tempo solicitadas
        
    def update_timestamp(self):
        """Atualiza o timestamp para o momento atual"""
        self.timestamp = datetime.datetime.now()
        
    def update_check(self):
        """Registra que uma verificação foi feita"""
        self.last_check = datetime.datetime.now()
        
    def update_reminder(self):
        """Registra que um lembrete foi enviado"""
        self.last_reminder = datetime.datetime.now()
        
    def increment_extension(self):
        """Incrementa o contador de extensões de tempo"""
        self.extension_count += 1
        return self.extension_count
        
    def to_dict(self) -> Dict[str, Any]:
        """Converte os dados para um dicionário para salvar em JSON"""
        return {
            "usuario": self.usuario,
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat(),
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "last_reminder": self.last_reminder.isoformat() if self.last_reminder else None,
            "extension_count": self.extension_count
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UsageData':
        """Cria uma instância a partir de um dicionário"""
        instance = cls(data["usuario"], data["user_id"])
        instance.timestamp = datetime.datetime.fromisoformat(data["timestamp"])
        if data.get("last_check"):
            instance.last_check = datetime.datetime.fromisoformat(data["last_check"])
        if data.get("last_reminder"):
            instance.last_reminder = datetime.datetime.fromisoformat(data["last_reminder"])
        instance.extension_count = data.get("extension_count", 0)
        return instance 