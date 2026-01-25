import requests
import os

SERP_API_KEY = os.getenv("SERPAPI_KEY")

def fetch_google_shopping_prices(query):
    if not SERP_API_KEY or not query:
        return []

    try:
        params = {
            "engine": "google_shopping",
            "q": query,
            "api_key": SERP_API_KEY,
            "hl": "en",
            "gl": "in"
        }

        response = requests.get(
            "https://serpapi.com/search",
            params=params,
            timeout=10
        )

        data = response.json()
        results = []

        for item in data.get("shopping_results", []):
            price_str = item.get("price")
            source = item.get("source")

            link = (
                item.get("link")
                or item.get("product_link")
                or item.get("redirect_link")
            )

            if price_str and source and link:
                try:
                    price = int(
                        price_str.replace("₹", "")
                        .replace(",", "")
                        .strip()
                    )

                    if link.startswith("/"):
                        link = "https://www.google.com" + link

                    results.append({
                        "name": query,
                        "platform": source,
                        "price": price,
                        "link": link
                    })

                except ValueError:
                    continue

        return results

    except Exception as e:
        print("Google Shopping API error:", e)
        return []
