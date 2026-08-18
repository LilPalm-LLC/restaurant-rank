from utils.cuisine import normalize_cuisine, normalize_many

def test_aliases():
    assert normalize_cuisine('Iranian')=='Persian'
    assert normalize_cuisine('Barbecue')=='BBQ'

def test_multi_unique(): assert normalize_many(['Persa','Persian'])==['Persian']
