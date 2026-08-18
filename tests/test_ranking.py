from models.restaurant import Restaurant
from utils.ranking import rank_restaurants, bayesian_score

def test_bayesian_prefers_confident_rating_over_tiny_sample():
    low_conf=bayesian_score(5.0,3,4.6)
    strong=bayesian_score(4.8,2000,4.6)
    assert strong > low_conf

def test_hidden_gem_excludes_too_few_reviews():
    items=[Restaurant('1','Tiny',5.0,2),Restaurant('2','Gem',4.7,40)]
    out=rank_restaurants(items,'Hidden Gems')
    assert [x.place_id for x in out]==['2']
