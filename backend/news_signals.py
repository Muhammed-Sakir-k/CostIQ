import requests

# Simple keyword groups
DOWN_KEYWORDS = [
    "sale", "discount", "festival", "offer", "price cut",
    "deal", "clearance", "black friday", "big billion", "great indian"
]

UP_KEYWORDS = [
    "launch", "shortage", "supply issue", "price hike",
    "tax", "import duty", "limited stock"
]

def analyze_news_signal(product):
    """
    Returns: signal ("DOWN" / "UP" / "NEUTRAL") and reason
    """

    try:
        # Using Google News RSS (no API key needed)
        url = f"https://news.google.com/rss/search?q={product}+price"
        response = requests.get(url, timeout=5)

        text = response.text.lower()

        for word in DOWN_KEYWORDS:
            if word in text:
                return {
                    "signal": "DOWN",
                    "reason": f"News indicates upcoming sale or discount ({word})"
                }

        for word in UP_KEYWORDS:
            if word in text:
                return {
                    "signal": "UP",
                    "reason": f"News indicates possible price increase ({word})"
                }

        return {
            "signal": "NEUTRAL",
            "reason": "No strong price-related news detected"
        }

    except Exception:
        return {
            "signal": "NEUTRAL",
            "reason": "Unable to analyze news signals"
        }
