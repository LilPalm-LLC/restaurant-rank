from utils.security import valid_pin, generate_recovery_code, valid_recovery_code, hash_secret, verify_secret

def test_pin_validation(): assert valid_pin('4827') and not valid_pin('12a4')

def test_recovery():
    c=generate_recovery_code(); assert valid_recovery_code(c)

def test_hashing():
    h=hash_secret('1234'); assert h!='1234' and verify_secret('1234',h) and not verify_secret('9999',h)
