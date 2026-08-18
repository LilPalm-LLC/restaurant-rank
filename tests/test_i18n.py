from i18n.translations import TRANSLATIONS, missing_keys

def test_i18n_complete():
    a,b=missing_keys(); assert not a and not b
    assert TRANSLATIONS['es']['nav.search']=='Buscar'
