from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class BackupEnvelope:
    format: str
    version: int
    created_at: str
    profile: Dict[str, Any]
    settings: Dict[str, Any]
    favorite_lists: list
