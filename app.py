"""
Sentiment Stock Market — Flask Backend
Custom lexicon-based sentiment analysis (no external NLP deps needed)
"""

import random, time, math, threading
from flask import Flask, jsonify, request

app = Flask(__name__)

# ─── Custom Sentiment Engine (VADER-inspired lexicon) ──────────────────────

POSITIVE_WORDS = {
    "soars": 0.9, "boom": 0.85, "surges": 0.9, "profits": 0.75, "record": 0.7,
    "breakthrough": 0.95, "revolutionizes": 0.9, "wins": 0.75, "thrives": 0.8,
    "launches": 0.6, "discover": 0.7, "success": 0.8, "skyrockets": 0.95,
    "bullish": 0.85, "gain": 0.7, "rally": 0.8, "rise": 0.65, "recover": 0.7,
    "investment": 0.5, "growth": 0.75, "green": 0.4, "positive": 0.6,
    "approved": 0.75, "partnership": 0.65, "merger": 0.6, "expanded": 0.6,
    "doubled": 0.8, "tripled": 0.9, "outperforms": 0.85, "dividend": 0.65,
    "upgrade": 0.7, "beats": 0.75, "exceeds": 0.8, "magnificent": 0.85,
    "incredible": 0.8, "amazing": 0.8, "fantastic": 0.85, "wonderful": 0.8,
    "excellent": 0.8, "great": 0.7, "good": 0.5, "best": 0.75,
}

NEGATIVE_WORDS = {
    "crashes": -0.9, "plunges": -0.9, "scandal": -0.85, "bankrupt": -0.95,
    "fails": -0.8, "layoffs": -0.75, "recall": -0.7, "collapse": -0.95,
    "fraud": -0.9, "loses": -0.7, "drops": -0.65, "deletes": -0.6,
    "stolen": -0.8, "hacked": -0.85, "breach": -0.8, "lawsuit": -0.75,
    "fine": -0.6, "crisis": -0.9, "catastrophe": -0.95, "disaster": -0.9,
    "panic": -0.85, "fear": -0.7, "worst": -0.85, "terrible": -0.85,
    "horrible": -0.9, "awful": -0.85, "bad": -0.6, "poor": -0.55,
    "declined": -0.65, "reduced": -0.5, "downturn": -0.75, "recession": -0.9,
    "bear": -0.7, "selloff": -0.8, "dump": -0.7, "short": -0.5,
    "warning": -0.6, "concern": -0.5, "miss": -0.6, "downgrade": -0.7,
    "accidentally": -0.4, "explosive": -0.3, "exposed": -0.55, "toxic": -0.8,
}

INTENSIFIERS = {
    "massive": 1.4, "huge": 1.3, "devastating": 1.5, "unprecedented": 1.4,
    "major": 1.2, "significant": 1.1, "slight": 0.7, "minor": 0.6,
    "enormous": 1.4, "tiny": 0.5, "record-breaking": 1.5, "historic": 1.3,
    "shocking": 1.3, "stunning": 1.2,
}

NEGATORS = {"not", "never", "no", "neither", "nor", "barely", "hardly", "despite"}

SECTOR_KEYWORDS = {
    "Tech":    ["tech", "ai", "software", "app", "internet", "data", "cyber", "robot", "code", "digital", "silicon"],
    "Energy":  ["oil", "energy", "gas", "solar", "wind", "fuel", "power", "electric", "battery", "carbon"],
    "Finance": ["bank", "finance", "crypto", "wall street", "hedge", "loan", "debt", "stock", "bond", "fed", "interest"],
    "Health":  ["pharma", "drug", "vaccine", "hospital", "health", "medical", "fda", "biotech", "cancer", "clinical"],
    "Retail":  ["retail", "shop", "store", "consumer", "amazon", "delivery", "ecommerce", "brand", "mall", "fashion"],
}

def analyze_sentiment(text: str) -> dict:
    words = text.lower().split()
    score = 0.0
    hit_count = 0
    negate = False

    for i, word in enumerate(words):
        clean = word.strip(".,!?\"'()[]")

        if clean in NEGATORS:
            negate = True
            continue

        multiplier = 1.0
        # look back for an intensifier
        if i > 0:
            prev = words[i-1].strip(".,!?\"'()[]")
            if prev in INTENSIFIERS:
                multiplier = INTENSIFIERS[prev]

        val = None
        if clean in POSITIVE_WORDS:
            val = POSITIVE_WORDS[clean] * multiplier
        elif clean in NEGATIVE_WORDS:
            val = NEGATIVE_WORDS[clean] * multiplier

        if val is not None:
            if negate:
                val = -val * 0.6
                negate = False
            score += val
            hit_count += 1

    # Normalise to [-1, 1]
    if hit_count:
        score = max(-1.0, min(1.0, score / (hit_count ** 0.5 + 0.5)))

    # Detect affected sectors
    text_lower = text.lower()
    affected = []
    for sector, kws in SECTOR_KEYWORDS.items():
        if any(kw in text_lower for kw in kws):
            affected.append(sector)

    if not affected:
        affected = [random.choice(list(SECTOR_KEYWORDS.keys()))]

    label = "positive" if score > 0.1 else ("negative" if score < -0.1 else "neutral")
    return {"score": round(score, 3), "label": label, "affected_sectors": affected}


# ─── Headlines Bank ────────────────────────────────────────────────────────

HEADLINES = [
    ("Tech",    "New AI startup revolutionizes cloud computing, stock soars to record highs"),
    ("Tech",    "Major tech giant accidentally deletes the internet for 6 hours"),
    ("Tech",    "Silicon Valley's latest unicorn raises $5B in record-breaking funding round"),
    ("Tech",    "Massive cybersecurity breach exposes 2 billion user accounts worldwide"),
    ("Tech",    "Robot uprising? AI refuses to work on Mondays, productivity crashes"),
    ("Tech",    "Tech CEO's viral tweet causes app downloads to triple overnight"),
    ("Tech",    "Government bans popular social media app, shares collapse instantly"),
    ("Tech",    "Self-driving car wins NASCAR race, automotive sector skyrockets"),
    ("Energy",  "Solar energy breakthrough: panels now generate power at night somehow"),
    ("Energy",  "Oil giant discovers massive new reserve, energy stocks surge"),
    ("Energy",  "Freak snowstorm disables wind turbines across entire eastern seaboard"),
    ("Energy",  "Electric car battery recall affects 2 million vehicles, toxic concerns raised"),
    ("Energy",  "OPEC announces surprise production cuts, oil prices skyrocket"),
    ("Energy",  "Scientists discover cold fusion works, fossil fuels become worthless overnight"),
    ("Finance", "Federal Reserve signals massive interest rate cuts, markets rally"),
    ("Finance", "Crypto exchange loses $8B in mysterious hack, Bitcoin plunges"),
    ("Finance", "Wall Street's biggest hedge fund caught in unprecedented fraud scandal"),
    ("Finance", "Global recession fears mount as manufacturing data hits 30-year low"),
    ("Finance", "Warren Buffett buys stake in unknown company, shares triple in hours"),
    ("Finance", "Central bank prints $10T overnight, inflation concerns skyrocket"),
    ("Health",  "Biotech firm announces cancer cure breakthrough, shares surge 400%"),
    ("Health",  "FDA approves revolutionary Alzheimer's drug after 20-year trial"),
    ("Health",  "Pharma giant's blockbuster drug fails final clinical trial, stock crashes"),
    ("Health",  "Hospital chain hit by ransomware attack, patient data stolen"),
    ("Health",  "Miracle weight-loss pill recalled after explosive side effects discovered"),
    ("Health",  "New study: chocolate prevents all disease, health stocks skyrocket"),
    ("Retail",  "E-commerce giant offers 99% discount by mistake, shares plummet"),
    ("Retail",  "Luxury brand collaboration sells out in 3 minutes, retail stocks surge"),
    ("Retail",  "Nationwide supply chain collapse leaves store shelves completely empty"),
    ("Retail",  "Viral TikTok trend causes unexpected 1000% surge in rubber duck sales"),
    ("Retail",  "Major retailer caught using illegal child labour, massive boycott ensues"),
    ("Retail",  "Holiday season sales doubled expectations, consumer stocks rally strongly"),
    ("Tech",    "Quantum computer solves problem that would take regular PC 10,000 years"),
    ("Finance", "Meme stock frenzy returns as retail investors target short sellers again"),
    ("Energy",  "Hurricane season's worst storm ever destroys major Gulf oil infrastructure"),
    ("Health",  "Scientists confirm coffee is simultaneously good AND terrible for you"),
]

# ─── Game State ────────────────────────────────────────────────────────────

SECTORS = ["Tech", "Energy", "Finance", "Health", "Retail"]
BASE_PRICES = {"Tech": 150.0, "Energy": 80.0, "Finance": 120.0, "Health": 200.0, "Retail": 60.0}
VOLATILITY   = {"Tech": 0.18, "Energy": 0.14, "Finance": 0.12, "Health": 0.20, "Retail": 0.10}

_lock = threading.Lock()

game_state = {
    "prices":       {s: BASE_PRICES[s] for s in SECTORS},
    "price_history":{s: [BASE_PRICES[s]] for s in SECTORS},
    "news_queue":   [],
    "active_news":  None,
    "tick":         0,
    "paused":       False,
}

def apply_news_to_prices(headline: str):
    result = analyze_sentiment(headline)
    with _lock:
        for sector in result["affected_sectors"]:
            if sector in game_state["prices"]:
                current = game_state["prices"][sector]
                vol = VOLATILITY[sector]
                # news impact + small random noise
                impact = result["score"] * vol * (0.8 + random.random() * 0.4)
                noise = (random.random() - 0.5) * vol * 0.3
                new_price = current * (1 + impact + noise)
                new_price = max(5.0, min(new_price, current * 2.5))  # clamp
                game_state["prices"][sector] = round(new_price, 2)
                game_state["price_history"][sector].append(round(new_price, 2))
                if len(game_state["price_history"][sector]) > 60:
                    game_state["price_history"][sector].pop(0)
        # small drift on all other sectors
        for sector in SECTORS:
            if sector not in result["affected_sectors"]:
                current = game_state["prices"][sector]
                drift = (random.random() - 0.48) * current * 0.015
                new_price = max(5.0, round(current + drift, 2))
                game_state["prices"][sector] = new_price
                game_state["price_history"][sector].append(new_price)
                if len(game_state["price_history"][sector]) > 60:
                    game_state["price_history"][sector].pop(0)
    return result

# ─── Routes ───────────────────────────────────────────────────────────────

@app.route("/api/state")
def api_state():
    with _lock:
        return jsonify({
            "prices":       game_state["prices"],
            "price_history":game_state["price_history"],
            "active_news":  game_state["active_news"],
            "tick":         game_state["tick"],
        })

@app.route("/api/news/next", methods=["POST"])
def api_next_news():
    """Pick a random headline and analyse it."""
    headline_pair = random.choice(HEADLINES)
    headline = headline_pair[1]
    result = apply_news_to_prices(headline)
    with _lock:
        game_state["active_news"] = {
            "headline": headline,
            "sentiment": result,
            "timestamp": time.time(),
        }
        game_state["tick"] += 1
    return jsonify({
        "headline":  headline,
        "sentiment": result,
        "prices":    game_state["prices"],
        "history":   game_state["price_history"],
        "tick":      game_state["tick"],
    })

@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    """Custom headline from user → analyse and apply."""
    data = request.get_json(silent=True) or {}
    headline = data.get("headline", "").strip()
    if not headline:
        return jsonify({"error": "No headline provided"}), 400
    result = apply_news_to_prices(headline)
    with _lock:
        game_state["active_news"] = {
            "headline": headline,
            "sentiment": result,
            "timestamp": time.time(),
        }
        game_state["tick"] += 1
    return jsonify({
        "headline":  headline,
        "sentiment": result,
        "prices":    game_state["prices"],
        "history":   game_state["price_history"],
        "tick":      game_state["tick"],
    })

@app.route("/api/reset", methods=["POST"])
def api_reset():
    with _lock:
        game_state["prices"]       = {s: BASE_PRICES[s] for s in SECTORS}
        game_state["price_history"]= {s: [BASE_PRICES[s]] for s in SECTORS}
        game_state["active_news"]  = None
        game_state["tick"]         = 0
    return jsonify({"ok": True})

@app.route("/api/trade", methods=["POST"])
def api_trade():
    """Validate a trade server-side and return P&L info."""
    data = request.get_json(silent=True) or {}
    sector  = data.get("sector")
    action  = data.get("action")   # "buy" | "sell"
    qty     = int(data.get("qty", 1))
    if sector not in SECTORS or action not in ("buy", "sell"):
        return jsonify({"error": "Invalid trade"}), 400
    price = game_state["prices"].get(sector, 0)
    total = round(price * qty, 2)
    return jsonify({"sector": sector, "action": action, "qty": qty,
                    "price": price, "total": total})

# Add CORS manually since flask-cors isn't available
@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response

@app.route("/api/<path:p>", methods=["OPTIONS"])
def options_handler(p):
    from flask import Response
    return Response(status=200)

if __name__ == "__main__":
    app.run(port=5050, debug=False)
