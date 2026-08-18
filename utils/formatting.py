def price_label(value: str | None) -> str:
    return value or "—"

def short_address(address: str) -> str:
    return address or "Address unavailable"
