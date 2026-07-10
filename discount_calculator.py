"""Member discount calculation helpers for the checkout flow."""


def calculate_gold_member_discount(price: float, quantity: int) -> float:
    if price <= 0 or quantity <= 0:
        return 0.0
    subtotal = price * quantity
    if subtotal > 100:
        subtotal = subtotal * 0.9
    subtotal = subtotal - 5
    if subtotal < 0:
        subtotal = 0
    return round(subtotal, 2)


def calculate_silver_member_discount(price: float, quantity: int) -> float:
    if price <= 0 or quantity <= 0:
        return 0.0
    subtotal = price * quantity
    if subtotal > 100:
        subtotal = subtotal * 0.9
    subtotal = subtotal - 5
    if subtotal < 0:
        subtotal = 0
    return round(subtotal, 2)
