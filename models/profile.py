from dataclasses import dataclass, field
from typing import Dict, List

@dataclass
class UserSettings:
    language: str = "en"
    distance_unit: str = "auto"
    default_radius: int = 5
    theme: str = "ocean"
    appearance: str = "system"

@dataclass
class UserProfile:
    profile_id: str
    name: str
    pin_hash: str
    recovery_code_hash: str
    created_at: str
    settings: UserSettings = field(default_factory=UserSettings)
    failed_attempts: int = 0
    locked_until: int = 0
