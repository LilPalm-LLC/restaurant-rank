import json, pytest
from utils.validation import validate_backup_bytes, validate_pin, clean_name

def test_pin():
    assert validate_pin('1234')=='1234'
    with pytest.raises(ValueError): validate_pin('123')

def test_name():
    assert clean_name(' Hadi ')=='Hadi'

def test_backup():
    obj={'format':'restaurant-rank-backup','version':1,'created_at':'x','profile':{},'settings':{},'favorite_lists':[]}
    assert validate_backup_bytes(json.dumps(obj).encode())['version']==1
    with pytest.raises(ValueError): validate_backup_bytes(b'{}')
