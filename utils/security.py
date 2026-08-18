import hashlib, hmac, secrets, re, base64
from datetime import datetime, timezone
try:
    import bcrypt  # type: ignore
except ImportError:  # local validation environments may not have dependencies installed; production requirements include bcrypt
    bcrypt = None

PIN_RE = re.compile(r"^\d{4}$")
RECOVERY_RE = re.compile(r"^[A-Z0-9]{4}(?:-[A-Z0-9]{4}){2}$")

def valid_pin(pin: str) -> bool: return bool(PIN_RE.fullmatch(pin or ""))

def hash_secret(value: str) -> str:
    if bcrypt is not None:
        return bcrypt.hashpw(value.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    # Fallback is only for dependency-missing local validation; deployed builds use bcrypt from requirements.txt.
    salt=secrets.token_bytes(16); digest=hashlib.scrypt(value.encode(),salt=salt,n=2**14,r=8,p=1)
    return "scrypt$"+base64.urlsafe_b64encode(salt).decode()+"$"+base64.urlsafe_b64encode(digest).decode()

def verify_secret(value: str, hashed: str) -> bool:
    try:
        if hashed.startswith("scrypt$"):
            _,s,d=hashed.split("$"); salt=base64.urlsafe_b64decode(s); expected=base64.urlsafe_b64decode(d)
            actual=hashlib.scrypt(value.encode(),salt=salt,n=2**14,r=8,p=1)
            return hmac.compare_digest(actual,expected)
        if bcrypt is None:return False
        return bcrypt.checkpw(value.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError): return False

def generate_recovery_code() -> str:
    alphabet="ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "-".join("".join(secrets.choice(alphabet) for _ in range(4)) for _ in range(3))

def normalize_recovery_code(code: str) -> str: return (code or "").strip().upper()
def valid_recovery_code(code: str) -> bool: return bool(RECOVERY_RE.fullmatch(normalize_recovery_code(code)))
def now_utc_iso() -> str: return datetime.now(timezone.utc).isoformat()
def secure_token() -> str: return secrets.token_urlsafe(24)
def fingerprint(value: str) -> str: return hashlib.sha256(value.encode("utf-8")).hexdigest()
