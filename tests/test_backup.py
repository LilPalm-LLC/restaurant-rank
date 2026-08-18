import json
from utils.validation import validate_backup_bytes

def test_backup_never_needs_secrets():
    obj={'format':'restaurant-rank-backup','version':1,'created_at':'x','profile':{'name':'Hadi'},'settings':{},'favorite_lists':[]}
    out=validate_backup_bytes(json.dumps(obj).encode()); assert 'pin' not in json.dumps(out).lower()
