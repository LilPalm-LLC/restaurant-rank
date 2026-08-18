from statistics import mean
from typing import Iterable
from models.restaurant import Restaurant

DEFAULT_M = 50.0

def bayesian_score(rating: float | None, reviews: int, cohort_mean: float, m: float = DEFAULT_M) -> float:
    if rating is None:
        return 0.0
    v = max(int(reviews or 0), 0)
    r = float(rating)
    return (v / (v + m)) * r + (m / (v + m)) * cohort_mean

def rank_restaurants(restaurants: Iterable[Restaurant], mode: str = "Best Overall", m: float = DEFAULT_M) -> list[Restaurant]:
    items = list(restaurants)
    ratings = [r.rating for r in items if r.rating is not None]
    cohort = mean(ratings) if ratings else 0.0
    for r in items:
        r.rank_score = bayesian_score(r.rating, r.review_count, cohort, m)
    if mode == "Highest Rated":
        key = lambda r: (r.rating or 0, r.review_count)
        items.sort(key=key, reverse=True)
    elif mode == "Most Reviewed":
        items.sort(key=lambda r: r.review_count, reverse=True)
    elif mode == "Closest":
        items.sort(key=lambda r: r.distance_miles if r.distance_miles is not None else 10**9)
    elif mode == "Lowest Price":
        items.sort(key=lambda r: (price_num(r.price_level), -(r.rank_score or 0)))
    elif mode == "Premium":
        items.sort(key=lambda r: (-price_num(r.price_level), -(r.rank_score or 0)))
    elif mode == "Best Value":
        items.sort(key=lambda r: (value_score(r), r.review_count), reverse=True)
    elif mode == "Hidden Gems":
        items = [r for r in items if (r.rating or 0) >= 4.5 and r.review_count >= 25]
        items.sort(key=lambda r: hidden_gem_score(r), reverse=True)
    elif mode == "Best Rated + Most Reviewed":
        items.sort(key=lambda r: (((r.rating or 0) * 0.65) + (review_confidence(r.review_count) * 5 * 0.35)), reverse=True)
    else:
        items.sort(key=lambda r: (r.rank_score or 0, r.review_count), reverse=True)
    return items

def review_confidence(v: int) -> float:
    return min(1.0, (max(v, 0) / 1000) ** 0.5)

def price_num(price: str | None) -> int:
    return len(price or "") if price and price.startswith("$") else 2

def value_score(r: Restaurant) -> float:
    base = (r.rank_score or 0)
    p = price_num(r.price_level)
    return base * (1.25 - 0.15 * max(0, p - 1))

def hidden_gem_score(r: Restaurant) -> float:
    rating = r.rating or 0
    confidence = review_confidence(r.review_count)
    volume_bonus = 1 / (1 + max(r.review_count, 25) / 500)
    return rating * 0.7 + confidence * 5 * 0.15 + volume_bonus * 5 * 0.15

def top_pick_labels(restaurants: list[Restaurant]) -> dict[str, Restaurant]:
    if not restaurants:
        return {}
    best = rank_restaurants(restaurants, "Best Overall")
    out = {"Best Overall": best[0]} if best else {}
    hg = rank_restaurants(restaurants, "Hidden Gems")
    bv = rank_restaurants(restaurants, "Best Value")
    mr = rank_restaurants(restaurants, "Most Reviewed")
    hr = rank_restaurants(restaurants, "Highest Rated")
    if hg: out["Hidden Gem"] = hg[0]
    if bv: out["Best Value"] = bv[0]
    if mr: out["Most Reviewed"] = mr[0]
    if hr: out["Highest Rated"] = hr[0]
    return out
