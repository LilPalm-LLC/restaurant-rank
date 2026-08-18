import json
from typing import Any
from utils.security import valid_pin, valid_recovery_code

MAX_BACKUP_BYTES = 1_500_000

def clean_name(name: str) -> str:
    value = " ".join((name or "").strip().split())
    if not 1 <= len(value) <= 50: raise ValueError("Name must be 1-50 characters.")
    return value

def clean_collection_name(name: str) -> str:
    value = " ".join((name or "").strip().split())
    if not 1 <= len(value) <= 60: raise ValueError("Collection name must be 1-60 characters.")
    return value

def validate_backup_bytes(data: bytes) -> dict[str, Any]:
    if len(data) > MAX_BACKUP_BYTES: raise ValueError("Backup file is too large.")
    try: obj = json.loads(data.decode("utf-8"))
    except Exception as e: raise ValueError("Backup is not valid JSON.") from e
    if not isinstance(obj, dict) or obj.get("format") != "restaurant-rank-backup": raise ValueError("Unsupported backup format.")
    if obj.get("version") != 1: raise ValueError("Unsupported backup version.")
    if not isinstance(obj.get("profile"), dict) or not isinstance(obj.get("settings"), dict) or not isinstance(obj.get("favorite_lists"), list):
        raise ValueError("Backup structure is invalid.")
    return obj

def validate_pin(pin: str) -> str:
    if not valid_pin(pin): raise ValueError("PIN must be exactly 4 digits.")
    return pin

def validate_recovery_code(code: str) -> str:
    if not valid_recovery_code(code): raise ValueError("Recovery code format is invalid.")
    return code.strip().upper()
