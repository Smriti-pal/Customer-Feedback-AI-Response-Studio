from __future__ import annotations

import html
import os
from urllib.parse import quote

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Customer Feedback Studio", page_icon="💬", layout="wide")

POSITIVE_TERMS = {
    "amazing", "best", "delight", "easy", "excellent", "fast", "good", "great",
    "happy", "love", "perfect", "recommend", "reliable", "satisfied", "thank", "wonderful",
}
NEGATIVE_TERMS = {
    "awful", "bad", "broken", "complaint", "damage", "disappointed", "fail", "faulty",
    "hate", "issue", "leak", "missing", "poor", "problem", "refund", "return", "terrible",
    "unhappy", "waste", "wrong",
}
SAFETY_TERMS = {"allergy", "allergic", "burn", "choke", "contamination", "injury", "rash", "sick", "unsafe"}
ISSUES = {
    "Safety / Health": SAFETY_TERMS,
    "Product / Quality": {"broken", "damage", "defect", "faulty", "quality", "work"},
    "Delivery / Shipping": {"arrive", "delivery", "late", "package", "ship", "shipping"},
    "Service / Support": {"agent", "service", "support", "response", "reply"},
    "Refund / Return / Billing": {"bill", "charge", "refund", "return"},
    "Pricing / Value": {"expensive", "price", "value", "cost"},
    "Website / App": {"app", "checkout", "site", "website"},
}


def text_sentiment(value: str) -> tuple[str, int, int]:
    words = str(value).lower().split()
    positive = sum(word.strip(".,!?;:'\"()[]{}") in POSITIVE_TERMS for word in words)
    negative = sum(word.strip(".,!?;:'\"()[]{}") in NEGATIVE_TERMS for word in words)
    score = positive - negative
    label = "Positive" if score > 0 else "Negative" if score < 0 else "Neutral"
    confidence = round(abs(score) / max(1, positive + negative) * 100)
    return label, score, confidence


def analyze_reviews(frame: pd.DataFrame) -> pd.DataFrame:
    if "Text" not in frame.columns or "Score" not in frame.columns:
        raise ValueError("The CSV needs at least these columns: Text and Score.")
    data = frame.copy()
    data["Text"] = data["Text"].fillna("").astype(str)
    data["Score"] = pd.to_numeric(data["Score"], errors="coerce")
    data = data.dropna(subset=["Score"])
    data["Score"] = data["Score"].clip(1, 5).round().astype(int)
    data["Customer"] = data.get("ProfileName", pd.Series("", index=data.index)).fillna("").astype(str)
    data["Product"] = data.get("ProductId", pd.Series("", index=data.index)).fillna("").astype(str)
    sentiment = data["Text"].map(text_sentiment)
    data["Sentiment"] = sentiment.map(lambda item: item[0])
    data["Sentiment score"] = sentiment.map(lambda item: item[1])
    data["Confidence"] = sentiment.map(lambda item: item[2])

    lower_text = data["Text"].str.lower()
    data["Issue"] = "General Complaint"
    for issue, terms in ISSUES.items():
        pattern = r"\b(?:" + "|".join(sorted(terms)) + r")\b"
        matches = lower_text.str.contains(pattern, regex=True, na=False)
        data.loc[matches & data["Issue"].eq("General Complaint"), "Issue"] = issue

    negative_words = lower_text.str.count(r"\b(?:" + "|".join(sorted(NEGATIVE_TERMS)) + r")\b")
    strong_negative = (negative_words >= 2) & data["Sentiment"].eq("Negative")
    safety = lower_text.str.contains(r"\b(?:" + "|".join(sorted(SAFETY_TERMS)) + r")\b", regex=True, na=False)
    data["Priority"] = "Normal"
    data.loc[data["Sentiment"].eq("Negative"), "Priority"] = "Watch"
    data.loc[(data["Score"].eq(2)) | (data["Score"].eq(3) & strong_negative), "Priority"] = "High"
    data.loc[data["Score"].eq(1) | safety, "Priority"] = "Urgent"
    data["Severity"] = data["Score"].map({1: "Critical", 2: "High", 3: "Moderate", 4: "Low", 5: "Positive feedback"})
    data["Flag reason"] = "No elevated risk detected"
    data.loc[data["Score"].eq(1), "Flag reason"] = "1-star rating"
    data.loc[data["Score"].eq(2), "Flag reason"] = "2-star rating"
    data.loc[data["Score"].ge(3) & data["Sentiment"].eq("Negative"), "Flag reason"] = "Negative text sentiment"
    data.loc[data["Score"].eq(3) & strong_negative, "Flag reason"] = "Strong negative wording"
    data.loc[safety, "Flag reason"] = "Safety or health language"
    data["Priority score"] = (
        data["Score"].map({1: 70, 2: 55, 3: 35, 4: 15, 5: 5}).fillna(0)
        + (negative_words * 4).clip(upper=20)
        + safety.astype(int) * 30
    ).clip(upper=100).astype(int)
    return data


def get_api_key() -> str:
    try:
        secret = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        secret = ""
    return str(secret or os.getenv("GEMINI_API_KEY", "")).strip()


def generate_response(row: pd.Series, tone: str, resolution: str) -> str:
    api_key = get_api_key()
    if not api_key:
        raise ValueError("Gemini is not configured. Add GEMINI_API_KEY to .env or app secrets.")
    from google import genai

    model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    try:
        model = str(st.secrets.get("GEMINI_MODEL", model))
    except Exception:
        pass
    review = str(row["Text"])[:5000]
    prompt = f"""Write a concise, ready-to-review customer support email. Be specific to the customer's issue and do not invent actions, refunds, replacements, timelines, or facts. Acknowledge the customer's feelings and the review's {row['Sentiment'].lower()} sentiment. Account for severity: {row['Severity']}; priority: {row['Priority']}; detected issue: {row['Issue']}. If a resolution was provided, state it accurately: {resolution or 'No resolution provided; ask a helpful next question instead.'}. Tone: {tone}. Rating: {row['Score']}/5. Customer name: {row['Customer'] or 'not provided'}. Product: {row['Product'] or 'not provided'}. Review: {review}. Include a useful subject line and sign off as Customer Support. Do not include placeholders."""
    client = genai.Client(api_key=api_key)
    result = client.models.generate_content(model=model, contents=prompt)
    response = getattr(result, "text", None)
    if not response:
        raise RuntimeError("Gemini returned an empty response.")
    return response.strip()


st.title("Customer Feedback Studio")
st.caption("Explore review trends, prioritize customer issues, and draft tailored responses.")

with st.sidebar:
    st.header("Review data")
    uploaded = st.file_uploader("Upload a review CSV", type=["csv"], help="Required columns: Text and Score. ProfileName and ProductId are optional.")
    st.caption("A small sample is loaded by default. The full local dataset is intentionally excluded from GitHub.")

try:
    if uploaded is not None:
        raw = pd.read_csv(uploaded, low_memory=False)
        source_label = uploaded.name
    elif os.path.exists("Reviews.csv"):
        raw = pd.read_csv("Reviews.csv", low_memory=False)
        source_label = "Local Reviews.csv"
    else:
        raw = pd.read_csv("sample_reviews.csv")
        source_label = "Sample reviews"
    data = analyze_reviews(raw)
except Exception as error:
    st.error(f"Could not load or analyze this file: {error}")
    st.stop()

if data.empty:
    st.warning("No rows with a valid rating were found.")
    st.stop()

st.caption(f"Data source: **{source_label}** · {len(data):,} reviews analyzed")
urgent = int(data["Priority"].eq("Urgent").sum())
flagged = int(data["Priority"].ne("Normal").sum())
negative = int(data["Sentiment"].eq("Negative").sum())
k1, k2, k3, k4 = st.columns(4)
k1.metric("Reviews", f"{len(data):,}")
k2.metric("Flagged", f"{flagged:,}", help="Urgent, High, and Watch feedback")
k3.metric("Urgent", f"{urgent:,}")
k4.metric("Negative sentiment", f"{negative:,}")

chart1, chart2, chart3 = st.columns(3)
with chart1:
    rating_counts = data["Score"].value_counts().reindex([1, 2, 3, 4, 5], fill_value=0).rename_axis("Rating").reset_index(name="Reviews")
    st.plotly_chart(px.bar(rating_counts, x="Rating", y="Reviews", title="Ratings", color="Rating", color_continuous_scale="Blues"), use_container_width=True)
with chart2:
    priority_counts = data["Priority"].value_counts().reindex(["Urgent", "High", "Watch", "Normal"], fill_value=0).rename_axis("Priority").reset_index(name="Reviews")
    st.plotly_chart(px.bar(priority_counts, x="Priority", y="Reviews", title="Priority flags", color="Priority", color_discrete_map={"Urgent": "#b63c3c", "High": "#d87e32", "Watch": "#d2a23a", "Normal": "#8994a6"}), use_container_width=True)
with chart3:
    sentiment_counts = data["Sentiment"].value_counts().reindex(["Positive", "Neutral", "Negative"], fill_value=0).rename_axis("Sentiment").reset_index(name="Reviews")
    st.plotly_chart(px.pie(sentiment_counts, names="Sentiment", values="Reviews", title="Sentiment mix", color="Sentiment", color_discrete_map={"Positive": "#23845c", "Neutral": "#8792a1", "Negative": "#b63c3c"}), use_container_width=True)

st.subheader("Priority feedback queue")
st.caption("Search and filter the complete dataset. Priority and severity are triage estimates; review the source feedback before acting.")
filters = st.columns([2, 1, 1, 1, 1, 1, 1])
query = filters[0].text_input("Search", placeholder="Review, customer, product")
priority_filter = filters[1].multiselect("Priority", ["Urgent", "High", "Watch", "Normal"], default=["Urgent", "High", "Watch"])
severity_filter = filters[2].multiselect("Severity", sorted(data["Severity"].dropna().unique().tolist()))
sentiment_filter = filters[3].multiselect("Sentiment", ["Positive", "Neutral", "Negative"])
rating_filter = filters[4].multiselect("Rating", [1, 2, 3, 4, 5])
reason_filter = filters[5].multiselect("Flag reason", sorted(data["Flag reason"].unique().tolist()))

filtered = data[data["Priority"].isin(priority_filter)]
if severity_filter:
    filtered = filtered[filtered["Severity"].isin(severity_filter)]
if sentiment_filter:
    filtered = filtered[filtered["Sentiment"].isin(sentiment_filter)]
if rating_filter:
    filtered = filtered[filtered["Score"].isin(rating_filter)]
if reason_filter:
    filtered = filtered[filtered["Flag reason"].isin(reason_filter)]
if query:
    match = filtered["Text"].str.contains(query, case=False, regex=False, na=False)
    match |= filtered["Customer"].str.contains(query, case=False, regex=False, na=False)
    match |= filtered["Product"].str.contains(query, case=False, regex=False, na=False)
    match |= filtered["Issue"].str.contains(query, case=False, regex=False, na=False)
    filtered = filtered[match]
priority_order = pd.CategoricalDtype(["Urgent", "High", "Watch", "Normal"], ordered=True)
filtered = filtered.assign(_priority_order=filtered["Priority"].astype(priority_order)).sort_values(["_priority_order", "Priority score"], ascending=[True, False]).drop(columns="_priority_order")
st.caption(f"Showing {len(filtered):,} matching reviews")
show_columns = ["Priority", "Priority score", "Score", "Severity", "Sentiment", "Issue", "Flag reason", "Customer", "Product", "Text"]
st.dataframe(filtered[show_columns], use_container_width=True, hide_index=True, height=480)
st.download_button("Download filtered reviews", filtered[show_columns].to_csv(index=False).encode("utf-8-sig"), "filtered_feedback.csv", "text/csv")

st.subheader("Draft a personalized response")
options = filtered.index.tolist()
if options:
    def label_for(index: int) -> str:
        row = data.loc[index]
        snippet = " ".join(str(row["Text"]).split())[:85]
        return f"{row['Priority']} · {row['Score']} stars · {row['Customer'] or 'Customer'} · {snippet}"

    chosen = st.selectbox("Choose a review", options, format_func=label_for)
    selected = data.loc[chosen]
    st.info(f"**{selected['Issue']}** · {selected['Sentiment']} sentiment · {selected['Severity']} severity · Flag: {selected['Flag reason']}")
    with st.form("response_form"):
        tone = st.selectbox("Response tone", ["Warm and professional", "Concise and formal", "Friendly but professional"])
        resolution = st.text_input("Confirmed resolution, if any", placeholder="Leave blank if no resolution has been confirmed")
        st.caption("The review text is sent to Google Gemini when you generate a draft. Verify your organization permits this before using customer data.")
        generate = st.form_submit_button("Generate email draft", type="primary", disabled=not bool(get_api_key()))
    if not get_api_key():
        st.caption("AI drafting is optional. Configure GEMINI_API_KEY to enable it.")
    if generate:
        try:
            with st.spinner("Writing a response based on this review…"):
                st.session_state[f"response_{chosen}"] = generate_response(selected, tone, resolution.strip())
        except Exception as error:
            st.error(f"Could not generate a response: {error}")
    draft_key = f"response_{chosen}"
    if draft_key in st.session_state:
        draft = st.text_area("Editable email draft", value=st.session_state[draft_key], height=240, key=f"draft_{chosen}")
        recipient = st.text_input("Customer email address (optional)", key=f"recipient_{chosen}", placeholder="Enter a verified email address")
        if recipient:
            mailto = "mailto:" + quote(recipient.strip()) + "?body=" + quote(draft)
            st.markdown(f"[Open draft in your email app]({html.escape(mailto, quote=True)})")

with st.expander("How flags and sentiment work"):
    st.markdown("""
    - **Urgent:** 1-star rating or a safety and health term.
    - **High:** 2-star rating or strongly negative wording on a 3-star review.
    - **Watch:** negative wording without a higher-priority trigger.
    - **Normal:** no elevated priority rule matched.

    Sentiment and issue types use simple word matching. They are estimates to help sort the queue, not a replacement for reading the review.
    """)
