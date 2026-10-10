# Customer Feedback Analysis and Response Studio

A notebook and hosted web app for reviewing customer feedback, prioritizing potential problems, exploring sentiment, and drafting personalized support emails.

## What is included

- `app.py` is the GitHub-connected web app. It includes interactive charts, full-dataset search and filters, priority flags, CSV export, and optional Gemini email drafting.
- `Customer_Feedback_Analysis_AI_Response_Localhost.ipynb` contains the original local analysis notebook and Flask dashboard.
- `sample_reviews.csv` is a small illustrative dataset so the web app works immediately after deployment.
- `Reviews.csv` is the full local dataset. It is intentionally excluded from GitHub because it is about 300 MB.

The sample records are examples for demonstrating the app. The sentiment and priority labels are rule-based estimates intended to help triage feedback; they do not replace reading a review.

## Run locally

1. Install Python 3.10 or later.
2. Create and activate a virtual environment, then install dependencies:

   ```bash
   python -m venv .venv
   # Windows PowerShell
   .venv\Scripts\Activate.ps1
   # macOS or Linux: source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Start the web app:

   ```bash
   streamlit run app.py
   ```

The sample review data loads by default. To analyze your local full dataset, place `Reviews.csv` beside `app.py`; it will be detected automatically. You can also upload a CSV from the sidebar. The CSV needs `Text` and `Score` columns; `ProfileName` and `ProductId` are optional.

To run the notebook dashboard, open the notebook in JupyterLab, run its setup and data-loading cells, and then run the final **Localhost Dashboard and Email Studio** cell. That Flask dashboard is for local use.

## Deploy from GitHub

GitHub stores the code, but GitHub Pages cannot run the Python app. To publish the interactive app, connect the repository to [Streamlit Community Cloud](https://share.streamlit.io/):

1. Create a GitHub repository and push this project. Keep `Reviews.csv`, `.env`, Jupyter runtime files, and API keys out of the repository.
2. Sign in to Streamlit Community Cloud with GitHub and create an app from the repository.
3. Select the repository branch and set the app file to `app.py`, then deploy.
4. The hosted app opens with the included sample reviews. Upload a smaller CSV through the sidebar to analyze it.

The full local dataset is too large for a regular GitHub file and may exceed hosted app memory or upload limits. Keep it locally or use a data store suitable for production; do not add it to Git history.

## Optional Gemini email drafts

AI drafting is disabled until a key is configured. Create a local `.env` file (it is ignored by Git):

```text
GEMINI_API_KEY=your-key-here
GEMINI_MODEL=gemini-3.8-flash
```

For Streamlit Community Cloud, add the values in the app's **Settings → Secrets** rather than committing them. Example secrets:

```toml
GEMINI_API_KEY = "your-key-here"
GEMINI_MODEL = "gemini-3.8-flash"
```

When a draft is requested, the selected review and provided resolution context are sent to Google's Gemini API. Confirm that your organization permits sharing the review text with that service. The app creates a draft; it does not send email. A verified customer email can be entered to open the draft in the user's email application.

## Filters and flags

The queue supports search across review text, customer, product, and issue, plus filters for priority, severity, sentiment, rating, and flag reason. It includes all levels: **Urgent**, **High**, **Watch**, and **Normal**. Export downloads the currently filtered reviews.

- **Urgent:** 1-star rating or a detected safety/health term.
- **High:** 2-star rating or strongly negative language on a 3-star review.
- **Watch:** negative wording without a higher priority trigger.
- **Normal:** no elevated priority rule matched.

## Data and privacy

The demo app is publicly reachable when deployed with a public repository. Do not upload confidential or personal customer information to a public app. Uploaded data is processed in the app session; this project does not implement user accounts, durable storage, or access controls. Gemini receives review text only when a user explicitly generates a response.

## License

Add a license file before redistributing the project or dataset. The sample data is illustrative; check the source and license of any real review dataset before sharing it.
