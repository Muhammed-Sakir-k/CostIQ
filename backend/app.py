print("🔥 app.py loaded")
from flask import Flask, jsonify, request
from flask_cors import CORS
import json
from flask import render_template
from services.google_shopping import fetch_google_shopping_prices
from db import init_db
import sqlite3
from db import get_conn
from intelligence import combined_intelligence
from models.price_prediction import predict_trend
from flask import session, redirect, url_for
from werkzeug.security import check_password_hash
from config import ADMIN_USERNAME, ADMIN_PASSWORD_HASH
from datetime import timedelta, datetime ,timezone
from collections import defaultdict
from datetime import date
from smart_alternatives import recommend_alternatives

visitor_log = defaultdict(set)  # date -> set of IPs



app = Flask(__name__, template_folder="../frontend/templates", static_folder="../frontend/static")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax"
)
app.secret_key = "smartprice-secret"   # 🔐 REQUIRED FOR LOGIN
app.config["SESSION_PERMANENT"] = False
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=10)
init_db()

from db import create_default_admin

init_db()
create_default_admin()



# 🔐 ADMIN GUARD (ADD IT HERE)
def admin_required():
    if not session.get("admin_logged_in"):
        return False
    return True


CORS(app) 
# Load demo data
with open("backend/data/demo_data.json") as f:
    products = json.load(f)

    





@app.route("/")
def home():
    return jsonify({"message": "SmartPrice API Running"})


@app.route("/app")
def app_home():
    return render_template("index.html")



@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify([])

    real_results = fetch_google_shopping_prices(query)

    if real_results:
        # 🔥 SAVE TO DB
        conn = get_conn()
        cur = conn.cursor()
        for item in real_results:
            cur.execute(
                "INSERT INTO price_history (product, platform, price) VALUES (?, ?, ?)",
                (item["name"], item["platform"], item["price"])
            )
        conn.commit()
        conn.close()

        return jsonify(real_results)

    # fallback (optional)
    filtered = [p for p in products if query.lower() in p["name"].lower()]
    return jsonify(filtered)



@app.route("/history")
def history():
    product = request.args.get("name", "").strip()
    if not product:
        return jsonify({})

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT platform, price, ts
        FROM price_history
        WHERE product = ?
        ORDER BY ts ASC
    """, (product,))

    rows = cur.fetchall()
    conn.close()

    history = {}
    for platform, price, ts in rows:
        history.setdefault(platform, []).append({
            "price": price,
            "ts": ts
        })

    return jsonify(history)


@app.route("/predict", methods=["GET"])
def predict_price():
    product_name = request.args.get("name", "").lower()

    predictions = {}

    for p in products:
        if p["name"].lower() == product_name:
            trend = predict_trend(p["history"])
            predictions[p["platform"]] = trend

    return jsonify(predictions)

@app.route("/recommend", methods=["GET"])
def recommend_buy():
    product_name = request.args.get("name", "").lower()
    recommendations = {}

    for p in products:
        if p["name"].lower() == product_name:
            trend = predict_trend(p["history"])
            if trend == "DOWN":
                recommendations[p["platform"]] = "WAIT"
            else:
                recommendations[p["platform"]] = "BUY NOW"

    return jsonify(recommendations)

@app.route("/alternatives", methods=["GET"])
def alternatives():
    product_name = request.args.get("name", "").lower()
    alternatives = []

    for p in products:
        if product_name in p["name"].lower():
            alternatives.append({
                "platform": p["platform"],
                "price": p["price"]
            })

    return jsonify(alternatives)

@app.route("/app")
def frontend():
    return render_template("index.html")

@app.route("/intelligence")
def intelligence():
    product = request.args.get("name", "").strip()
    if not product:
        return jsonify({})

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT platform, price
        FROM price_history
        WHERE product = ?
        ORDER BY ts ASC
    """, (product,))
    rows = cur.fetchall()
    conn.close()

    # 1️⃣ Collect price history per platform
    platform_prices = {}
    for platform, price in rows:
        platform_prices.setdefault(platform, []).append(price)

    # ❌ No data yet → tracking state
    if not platform_prices:
        return jsonify({
            "status": "tracking",
            "message": "Not enough price data yet. We’ve started tracking this product.",
            "advice": "Check back later or explore smart alternatives."
        })

    # 2️⃣ 🔥 ADD THIS PART HERE (BEST PRICE LOGIC)
    best_platform, prices = min(
        platform_prices.items(),
        key=lambda x: min(x[1])
    )
    best_price = min(prices)

    # 3️⃣ Run AI analysis per platform (you already have this)
    analysis = {}
    for platform, prices in platform_prices.items():
        analysis[platform] = combined_intelligence(product, prices)

    # 4️⃣ Global decision (simple & user-friendly)
    buy_votes = sum(1 for v in analysis.values() if v["decision"] == "BUY")

    global_decision = "BUY" if best_price else "WAIT"

    # 5️⃣ FINAL RESPONSE (THIS is what frontend should use)
    return jsonify({
        "global_decision": global_decision,
        "best_platform": best_platform,
        "best_price": best_price,
        "confidence": 72,
        "reason": "Lowest available price across all tracked platforms",
        "platform_analysis": analysis
    })


@app.route("/track-click", methods=["POST"])
def track_click():
    data = request.json

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO click_events (product, platform, price) VALUES (?, ?, ?)",
        (data["product"], data["platform"], data["price"])
    )
    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})

@app.route("/admin/click-stats")
def click_stats():
    if not admin_required():
        return jsonify({"error": "Unauthorized"}), 401
    conn = get_conn()
    cur = conn.cursor()

    # Platform-wise clicks
    cur.execute("""
        SELECT platform, COUNT(*) as clicks
        FROM click_events
        GROUP BY platform
        ORDER BY clicks DESC
    """)
    platform_rows = cur.fetchall()

    # Total clicks
    cur.execute("SELECT COUNT(*) FROM click_events")
    total_clicks = cur.fetchone()[0]

    # Cheapest price click count
    cur.execute("""
        SELECT COUNT(*)
        FROM click_events
        WHERE price = (
            SELECT MIN(price) FROM click_events
        )
    """)
    cheapest_clicks = cur.fetchone()[0]

    conn.close()

    return jsonify({
        "total_clicks": total_clicks,
        "platform_stats": [
            {"platform": p, "clicks": c} for p, c in platform_rows
        ],
        "cheapest_clicks": cheapest_clicks
    })

from flask import make_response

@app.route("/admin")
def admin():
    if not admin_required():
        return redirect("/admin/login")

    response = make_response(render_template("admin.html"))
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return response

    



@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT password_hash FROM admin_user WHERE username=? LIMIT 1",
            (username,)
        )
        row = cur.fetchone()
        conn.close()

        if row and check_password_hash(row[0], password):
            # ✅ LOGIN SUCCESS — ADD IT HERE
            session["admin_logged_in"] = True
            session.permanent = False   # 🔥 THIS LINE GOES HERE

            return redirect("/admin")

        # ❌ LOGIN FAILED
        return render_template(
            "login.html",
            error="Invalid username or password"
        )

    # GET request
    return render_template("login.html")


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect("/admin/login")


import csv
from flask import Response

@app.route("/admin/export/csv")
def export_csv():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT product, platform, price, ts FROM click_events")
    rows = cur.fetchall()
    conn.close()

    def generate():
        yield "Product,Platform,Price,Time\n"
        for r in rows:
            yield f"{r[0]},{r[1]},{r[2]},{r[3]}\n"

    return Response(generate(), mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=click_analytics.csv"})

@app.route("/admin/daily-clicks")
def daily_clicks():
    if not session.get("admin_logged_in"):
        return jsonify({})

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT DATE(ts) as day, COUNT(*)
        FROM click_events
        GROUP BY day
        ORDER BY day
    """)
    rows = cur.fetchall()
    conn.close()

    return jsonify({
        "days": [r[0] for r in rows],
        "counts": [r[1] for r in rows]
    })

from werkzeug.security import generate_password_hash, check_password_hash

@app.route("/admin/change-password", methods=["POST"])
def change_password():
    if not admin_required():
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    old = data.get("old_password")
    new = data.get("new_password")

    if not old or not new:
        return jsonify({"error": "Missing fields"}), 400

    conn = get_conn()
    cur = conn.cursor()

    # Always fetch EXACTLY ONE admin
    cur.execute(
        "SELECT password_hash FROM admin_user WHERE username=? LIMIT 1",
        ("admin",)
    )
    row = cur.fetchone()

    if not row:
        conn.close()
        return jsonify({"error": "Admin not found"}), 500

    current_hash = row[0]

    # Verify old password
    if not check_password_hash(current_hash, old):
        conn.close()
        return jsonify({"error": "Wrong old password"}), 400

    # Update password
    new_hash = generate_password_hash(new)
    cur.execute(
        "UPDATE admin_user SET password_hash=? WHERE username=?",
        (new_hash, "admin")
    )
    conn.commit()
    conn.close()

    return jsonify({"status": "Password updated successfully"})



@app.before_request
def enforce_admin_timeout():
    if session.get("admin_logged_in"):
        now = datetime.now(timezone.utc)

        last_activity = session.get("last_activity")

        # Convert last_activity safely
        if isinstance(last_activity, str):
            last_activity = datetime.fromisoformat(last_activity)
        elif not isinstance(last_activity, datetime):
            last_activity = None

        # Timeout check (10 minutes = 600 seconds)
        if last_activity:
            if (now - last_activity).total_seconds() > 600:
                session.clear()
                return redirect("/admin/login")

        # Always store as ISO string (safe for sessions)
        session["last_activity"] = now.isoformat()

@app.route("/admin/visitor-stats")
def visitor_stats():
    if not admin_required():
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT SUM(count) FROM visitors")
    total = cur.fetchone()[0] or 0

    today = str(date.today())
    cur.execute("SELECT count FROM visitors WHERE day = ?", (today,))
    row = cur.fetchone()
    today_count = row[0] if row else 0

    conn.close()

    return jsonify({
        "total": total,
        "today": today_count
    })



@app.route("/admin/click-heatmap")
def click_heatmap():
    if not admin_required():
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT strftime('%H', ts) as hour, COUNT(*) as clicks
        FROM click_events
        GROUP BY hour
        ORDER BY hour
    """)

    rows = cur.fetchall()
    conn.close()

    return jsonify({
        "hours": [r[0] for r in rows],
        "counts": [r[1] for r in rows]
    })




@app.route("/track-visit", methods=["POST"])
def track_visit():
    today = str(date.today())

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "INSERT OR IGNORE INTO visitors (day, count) VALUES (?, 0)",
        (today,)
    )
    cur.execute(
        "UPDATE visitors SET count = count + 1 WHERE day = ?",
        (today,)
    )

    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})

@app.route("/smart-alternatives")
def smart_alternatives():
    product = request.args.get("name", "").strip()
    price = request.args.get("price", type=int)

    if not product or not price:
        return jsonify([])

    alternatives = recommend_alternatives(product, price)
    return jsonify(alternatives)


if __name__ == "__main__":
    app.run(debug=True)


