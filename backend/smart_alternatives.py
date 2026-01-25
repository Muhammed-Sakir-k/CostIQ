# smart_alternatives.py

DEVICES = [
    {
        "name": "Samsung Galaxy S23",
        "category": "smartphone",
        "price": 69999,
        "camera": 9,
        "performance": 9,
        "battery": 8.5,
        "display": 9
    },
    {
        "name": "Google Pixel 7",
        "category": "smartphone",
        "price": 59999,
        "camera": 9.5,
        "performance": 8.5,
        "battery": 8,
        "display": 8.5
    },
    {
        "name": "OnePlus 11",
        "category": "smartphone",
        "price": 56999,
        "camera": 8.5,
        "performance": 9.5,
        "battery": 9,
        "display": 9
    }
]

TARGET_PRODUCTS = {
    "iphone 14": {
        "category": "smartphone",
        "price": 59999,
        "camera": 9.5,
        "performance": 9,
        "battery": 8,
        "display": 9
    }
}

def recommend_alternatives(product_name, current_price):
    key = product_name.lower()
    if key not in TARGET_PRODUCTS:
        return []

    target = TARGET_PRODUCTS[key]
    alternatives = []

    for d in DEVICES:
        if d["category"] != target["category"]:
            continue

        # cheaper than current price
        if d["price"] >= current_price:
            continue

        # similarity score
        score = (
            abs(target["camera"] - d["camera"]) +
            abs(target["performance"] - d["performance"]) +
            abs(target["display"] - d["display"])
        )

        alternatives.append({
            "name": d["name"],
            "price": d["price"],
            "match": round(100 - score * 5),  # % similarity
            "reason": "Similar specs at a lower price"
        })

    return sorted(alternatives, key=lambda x: x["price"])
print("✅ smart_alternatives loaded")
