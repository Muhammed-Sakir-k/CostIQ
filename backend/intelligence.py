from news_signals import analyze_news_signal

def analyze_price_trend(price_list):
    if len(price_list) < 3:
        return {
            "decision": "WATCH",
            "confidence": 40,
            "reason": "Not enough historical data"
        }

    diffs = []
    for i in range(1, len(price_list)):
        diffs.append(price_list[i] - price_list[i - 1])

    avg_diff = sum(diffs) / len(diffs)

    if avg_diff < 0:
        confidence = min(90, int(abs(avg_diff) / price_list[-1] * 1000))
        return {
            "decision": "WAIT",
            "confidence": max(60, confidence),
            "reason": "Prices are consistently decreasing"
        }

    if avg_diff > 0:
        confidence = min(90, int(avg_diff / price_list[-1] * 1000))
        return {
            "decision": "BUY",
            "confidence": max(60, confidence),
            "reason": "Prices are increasing over time"
        }

    return {
        "decision": "WATCH",
        "confidence": 50,
        "reason": "Prices are stable"
    }


def combined_intelligence(product, price_list):
    base = analyze_price_trend(price_list)
    news = analyze_news_signal(product)

    decision = base["decision"]
    confidence = base["confidence"]
    reasons = [base["reason"]]

    if news["signal"] == "DOWN":
        confidence = min(95, confidence + 15)
        decision = "WAIT"
        reasons.append(news["reason"])

    elif news["signal"] == "UP":
        confidence = min(95, confidence + 15)
        decision = "BUY"
        reasons.append(news["reason"])

    return {
        "decision": decision,
        "confidence": confidence,
        "reason": " | ".join(reasons)
    }
