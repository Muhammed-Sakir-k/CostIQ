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

        response.raise_for_status()
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

            thumbnail = (
                item.get("thumbnail")
                or item.get("image")
                or ""
            )

            # Ensure required fields exist
            if not price_str or not source or not link:
                continue

            try:
                # Clean price string safely
                price = int(
                    price_str.replace("₹", "")
                    .replace(",", "")
                    .strip()
                )

                # Fix relative Google redirect links
                if link.startswith("/"):
                    link = "https://www.google.com" + link

                results.append({
                    "name": query,
                    "platform": source,
                    "price": price,
                    "link": link,
                    "thumbnail": thumbnail
                })

            except ValueError:
                continue

        return results

    except Exception as e:
        print("Google Shopping API error:", e)
        return []
