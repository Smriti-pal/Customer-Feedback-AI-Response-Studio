"""Low-memory CSV importer and SQLite-backed feedback queries."""
import csv
import json
import re
import shutil
import sqlite3
import urllib.request
from collections import Counter
from pathlib import Path


POSITIVE_TERMS = {
    "amazing", "awesome", "best", "brilliant", "comfortable", "easy", "excellent",
    "fantastic", "fast", "good", "great", "happy", "helpful", "love", "perfect",
    "recommend", "reliable", "satisfied", "smooth", "thank", "useful", "wonderful",
}
NEGATIVE_TERMS = {
    "awful", "bad", "broken", "complaint", "damaged", "defective", "disappointed",
    "disappointing", "failure", "faulty", "hate", "horrible", "late", "missing",
    "poor", "problem", "refund", "return", "rude", "slow", "terrible", "unusable",
    "waste", "worst", "wrong",
}
NEGATORS = {"no", "not", "never", "hardly"}
ISSUE_RULES = {
    "Safety / Health": {"allergic", "allergy", "injury", "injured", "unsafe", "safety", "fire", "smoke", "shock", "burn", "poison", "contamination", "contaminated", "choking"},
    "Product / Quality": {"broken", "damaged", "defective", "faulty", "stale", "rotten", "leak", "leaking", "quality", "wrong", "size", "expired"},
    "Delivery / Shipping": {"late", "delay", "delayed", "shipping", "shipped", "delivery", "package", "packaging", "missing", "courier", "arrived"},
    "Service / Support": {"rude", "support", "service", "complaint", "response", "help", "agent", "staff", "unhelpful"},
    "Refund / Return / Billing": {"refund", "return", "billing", "charge", "charged", "overcharged", "cancellation", "replacement", "payment"},
    "Pricing / Value": {"price", "pricing", "expensive", "cost", "discount", "overpriced"},
    "Website / App": {"website", "app", "login", "technical", "error", "bug", "crash"},
}
SAFETY_TERMS = ISSUE_RULES["Safety / Health"]
SEVERITY = {1: "Critical", 2: "High", 3: "Moderate", 4: "Low", 5: "Positive feedback"}
PRIORITY_RANK = {"Urgent": 0, "High": 1, "Watch": 2, "Normal": 3}
PRIORITY_BASE = {1: 70, 2: 55, 3: 35, 4: 15, 5: 5}


def _analyze(text, rating):
    tokens = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    words = re.sub(r"\s+", " ", tokens).strip().split()
    word_set = set(words)
    positive = sum(word in POSITIVE_TERMS for word in words)
    negative = sum(word in NEGATIVE_TERMS for word in words)
    negated_positive = sum(word in POSITIVE_TERMS and i > 0 and words[i - 1] in NEGATORS for i, word in enumerate(words))
    negated_negative = sum(word in NEGATIVE_TERMS and i > 0 and words[i - 1] in NEGATORS for i, word in enumerate(words))
    positive = max(0, positive - negated_positive + negated_negative)
    negative = max(0, negative - negated_negative + negated_positive)
    score = positive - negative
    cues = positive + negative
    sentiment = "Positive" if score > 0 else "Negative" if score < 0 else "Neutral"
    confidence = round(abs(score) / cues * 100) if cues else 0
    issues = [name for name, terms in ISSUE_RULES.items() if word_set.intersection(terms)] or ["General Complaint"]
    safety = any(word in SAFETY_TERMS for word in words)
    strong_negative = negative >= 2 and negative > positive
    priority = "Urgent" if rating == 1 or safety else "High" if rating == 2 or (rating == 3 and strong_negative) else "Watch" if sentiment == "Negative" else "Normal"
    reason = "No elevated risk detected"
    if rating == 1:
        reason = "1-star rating"
    elif rating == 2:
        reason = "2-star rating"
    if rating >= 3 and sentiment == "Negative":
        reason = "Negative text sentiment"
    if rating == 3 and strong_negative:
        reason = "Strong negative wording"
    if safety:
        reason = "Safety or health language"
    priority_score = min(100, PRIORITY_BASE[rating] + min(20, negative * 4) + (30 if safety else 0))
    return {
        "issues": issues,
        "sentiment": sentiment,
        "sentiment_score": score,
        "confidence": confidence,
        "severity": SEVERITY[rating],
        "priority": priority,
        "priority_rank": PRIORITY_RANK[priority],
        "priority_score": priority_score,
        "reason": reason,
    }


def ensure_csv(path, source_url):
    path = Path(path)
    if path.is_file():
        return path
    if not source_url:
        raise FileNotFoundError(f"Reviews.csv was not found at {path} and REVIEWS_CSV_URL is not set.")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".download")
    request = urllib.request.Request(source_url, headers={"User-Agent": "CustomerFeedbackStudio/1.0"})
    with urllib.request.urlopen(request, timeout=600) as response, temporary.open("wb") as output:
        shutil.copyfileobj(response, output, length=1024 * 1024)
    temporary.replace(path)
    return path


def _connect(path):
    connection = sqlite3.connect(str(path), timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA cache_size=-8192")
    connection.execute("PRAGMA temp_store=FILE")
    return connection


def _summary(connection, version):
    counts = {row["name"]: int(row["count"]) for row in connection.execute(
        "SELECT 'rating_' || rating AS name, COUNT(*) AS count FROM reviews GROUP BY rating "
        "UNION ALL SELECT 'sentiment_' || sentiment, COUNT(*) FROM reviews GROUP BY sentiment "
        "UNION ALL SELECT 'priority_' || priority, COUNT(*) FROM reviews GROUP BY priority"
    )}
    total = int(connection.execute("SELECT COUNT(*) FROM reviews").fetchone()[0])
    if not total:
        raise ValueError("Reviews.csv contains no valid 1–5 star reviews with review text.")
    rating_counts = [counts.get(f"rating_{rating}", 0) for rating in range(1, 6)]
    priority_names = ["Urgent", "High", "Watch", "Normal"]
    priority_counts = [counts.get(f"priority_{priority}", 0) for priority in priority_names]
    rating_max, priority_max = max(rating_counts or [0], default=0), max(priority_counts or [0], default=0)
    rating_chart = [
        {"label": str(rating), "value": count, "percent": round(count / total * 100, 1), "height": max(2, round(count / max(1, rating_max) * 100))}
        for rating, count in enumerate(rating_counts, start=1)
    ]
    priority_chart = [
        {"label": priority, "value": count, "percent": round(count / total * 100, 1), "height": max(2, round(count / max(1, priority_max) * 100))}
        for priority, count in zip(priority_names, priority_counts)
    ]
    critical = counts.get("rating_1", 0) + counts.get("rating_2", 0)
    return {
        "ready": True,
        "version": version,
        "total": total,
        "critical": critical,
        "critical_percent": round(critical / total * 100, 1),
        "positive": counts.get("sentiment_Positive", 0),
        "neutral": counts.get("sentiment_Neutral", 0),
        "negative": counts.get("sentiment_Negative", 0),
        "flagged": total - counts.get("priority_Normal", 0),
        "urgent": counts.get("priority_Urgent", 0),
        "rating_chart": rating_chart,
        "priority_chart": priority_chart,
        "sentiment_chart": [
            {"label": name, "value": counts.get(f"sentiment_{name}", 0), "percent": round(counts.get(f"sentiment_{name}", 0) / total * 100, 1)}
            for name in ("Positive", "Neutral", "Negative")
        ],
        "flagged_rows": [],
        "top_keywords": [],
    }


def prepare_store(csv_path, database_path, source_url):
    csv_path = ensure_csv(csv_path, source_url)
    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    source_version = f"{csv_path.stat().st_size}:{csv_path.stat().st_mtime_ns}"

    if database_path.exists():
        existing = _connect(database_path)
        try:
            stored = existing.execute("SELECT value FROM metadata WHERE key='source_version'").fetchone()
            if stored and stored[0] == source_version:
                return _summary(existing, source_version)
        except sqlite3.Error:
            pass
        finally:
            existing.close()
        database_path.unlink(missing_ok=True)

    connection = _connect(database_path)
    try:
        connection.execute("PRAGMA journal_mode=OFF")
        connection.execute("PRAGMA synchronous=OFF")
        connection.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        connection.execute(
            "CREATE TABLE reviews ("
            "id INTEGER PRIMARY KEY, rating INTEGER NOT NULL, customer TEXT, product TEXT, review TEXT NOT NULL, "
            "issue TEXT NOT NULL, issues TEXT NOT NULL, sentiment TEXT NOT NULL, sentiment_score INTEGER NOT NULL, "
            "confidence INTEGER NOT NULL, severity TEXT NOT NULL, priority TEXT NOT NULL, priority_rank INTEGER NOT NULL, "
            "priority_score INTEGER NOT NULL, reason TEXT NOT NULL)"
        )
        with csv_path.open("r", encoding="utf-8-sig", errors="replace", newline="") as source:
            reader = csv.DictReader(source)
            columns = set(reader.fieldnames or ())
            missing = {"Score", "Text"} - columns
            if missing:
                raise ValueError(f"Reviews.csv is missing required columns: {sorted(missing)}")
            batch = []
            for index, row in enumerate(reader):
                try:
                    rating_value = float(row.get("Score", ""))
                    if not rating_value.is_integer() or not 1 <= rating_value <= 5:
                        continue
                    rating = int(rating_value)
                except (TypeError, ValueError):
                    continue
                review = (row.get("Text") or "").strip()
                if not review:
                    continue
                context = _analyze(review, rating)
                batch.append((
                    index, rating, (row.get("ProfileName") or "")[:100],
                    (row.get("ProductId") or "")[:70], review,
                    context["issues"][0], ", ".join(context["issues"]),
                    context["sentiment"], context["sentiment_score"], context["confidence"],
                    context["severity"], context["priority"], context["priority_rank"],
                    context["priority_score"], context["reason"],
                ))
                if len(batch) >= 2000:
                    connection.executemany("INSERT INTO reviews VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", batch)
                    connection.commit()
                    batch.clear()
            if batch:
                connection.executemany("INSERT INTO reviews VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", batch)
                connection.commit()
        connection.execute("CREATE INDEX idx_review_priority ON reviews(priority_rank, priority_score DESC, confidence DESC)")
        connection.execute("CREATE INDEX idx_review_rating ON reviews(rating)")
        connection.execute("CREATE INDEX idx_review_issue ON reviews(issue)")
        connection.execute("CREATE INDEX idx_review_sentiment ON reviews(sentiment)")
        connection.execute("CREATE INDEX idx_review_severity ON reviews(severity)")
        connection.execute("CREATE INDEX idx_review_reason ON reviews(reason)")
        connection.execute("INSERT INTO metadata(key,value) VALUES('source_version',?)", (source_version,))
        connection.commit()
        return _summary(connection, source_version)
    finally:
        connection.close()


def fetch_queue(database_path, params):
    connection = _connect(database_path)
    try:
        conditions, values = [], []
        for field, column in (
            ("priority", "priority"), ("severity", "severity"), ("sentiment", "sentiment"),
            ("rating", "rating"), ("issue", "issue"), ("reason", "reason"),
        ):
            value = params.get(field, "").strip()
            if value:
                conditions.append(f"{column} = ?")
                values.append(int(value) if column == "rating" else value)
        query = params.get("q", "").strip()[:160]
        if query:
            conditions.append("(instr(lower(review),lower(?)) > 0 OR instr(lower(customer),lower(?)) > 0 OR instr(lower(product),lower(?)) > 0 OR instr(lower(reason),lower(?)) > 0 OR instr(lower(issues),lower(?)) > 0)")
            values.extend([query] * 5)
        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        total = int(connection.execute("SELECT COUNT(*) FROM reviews" + where, values).fetchone()[0])
        try:
            page_size = int(params.get("page_size", "50"))
        except ValueError:
            page_size = 50
        if page_size not in (25, 50, 100, 200):
            page_size = 50
        pages = max(1, (total + page_size - 1) // page_size)
        try:
            page = min(max(1, int(params.get("page", "1"))), pages)
        except ValueError:
            page = 1
        offset = (page - 1) * page_size
        rows = connection.execute(
            "SELECT * FROM reviews" + where + " ORDER BY priority_rank, priority_score DESC, confidence DESC LIMIT ? OFFSET ?",
            [*values, page_size, offset],
        ).fetchall()
        output = []
        for row in rows:
            full_review = " ".join(row["review"].split())[:6000]
            output.append({
                "priority": row["priority"], "priority_score": int(row["priority_score"]),
                "rating": int(row["rating"]), "severity": row["severity"], "sentiment": row["sentiment"],
                "sentiment_score": int(row["sentiment_score"]), "confidence": int(row["confidence"]),
                "issues": row["issues"], "issue_value": row["issue"], "reason": row["reason"],
                "customer": row["customer"], "product": row["product"],
                "review": full_review[:300] + ("..." if len(full_review) > 300 else ""),
                "full_review": full_review,
            })
        return {
            "rows": output, "total": total, "page": page, "pages": pages,
            "start": offset + 1 if total else 0, "end": offset + len(output),
        }
    finally:
        connection.close()
