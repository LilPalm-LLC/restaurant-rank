CANONICAL_CUISINES = [
    "American","BBQ","Mexican","Italian","Indian","Chinese","Japanese","Korean","Thai","Vietnamese",
    "Persian","Turkish","Mediterranean","Middle Eastern","Greek","French","Spanish","Brazilian","Colombian",
    "Peruvian","Argentine","Caribbean","Seafood","Steakhouse","Pizza","Burger","Sandwich","Bakery","Cafe",
    "Dessert","Sushi","Ramen","Vegan","Vegetarian","Halal","Kosher","Fast Food","Fine Dining"
]
ALIASES = {
    "iranian":"Persian","persa":"Persian","persian cuisine":"Persian","persian":"Persian",
    "barbecue":"BBQ","bar-b-q":"BBQ","bbq":"BBQ",
    "italiana":"Italian","italian":"Italian","mexicana":"Mexican","mexican":"Mexican",
    "turca":"Turkish","turkish":"Turkish","india":"Indian","indian":"Indian",
    "japonesa":"Japanese","japanese":"Japanese","china":"Chinese","chinese":"Chinese",
    "coreana":"Korean","korean":"Korean","vegetariana":"Vegetarian","vegetarian":"Vegetarian",
    "vegana":"Vegan","vegan":"Vegan","mariscos":"Seafood","seafood":"Seafood","parrilla":"Steakhouse"
}

def normalize_cuisine(value: str) -> str:
    s = " ".join((value or "").strip().lower().split())
    return ALIASES.get(s, value.strip() if value else "")

def normalize_many(values: list[str]) -> list[str]:
    out=[]
    for v in values:
        n=normalize_cuisine(v)
        if n and n not in out: out.append(n)
    return out

def translate_cuisine(cuisine: str, lang: str) -> str:
    if lang != "es": return cuisine
    mapping={"Persian":"Persa","Turkish":"Turca","Indian":"India","Mexican":"Mexicana","Italian":"Italiana","Chinese":"China","Japanese":"Japonesa","Korean":"Coreana","Vegetarian":"Vegetariana","Vegan":"Vegana","Seafood":"Mariscos","BBQ":"Barbacoa","Greek":"Griega","French":"Francesa","Spanish":"Española","Mediterranean":"Mediterránea","Middle Eastern":"Medio Oriente"}
    return mapping.get(cuisine,cuisine)
