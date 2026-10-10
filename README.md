# Customer Feedback AI Response Studio

A Flask dashboard based on **section 14** of the Jupyter notebook. It keeps that dashboard's HTML, styling, charts, queue, filters, and response studio. The app reads `Reviews.csv`; it does not replace the requested dataset with sample data.

## Files

- `app.py` runs the Flask dashboard and email response studio.
- `Customer_Feedback_Analysis_AI_Response_Localhost.ipynb` is the original notebook and UI source.
- `render.yaml` configures a free Render web service deployed from this GitHub repository.
- `.env.example` documents optional local Gemini settings. Do not commit a real API key.

`Reviews.csv` is about 300 MB, so it is intentionally not stored in the Git repository. GitHub blocks regular Git files over 100 MiB. For a public deployment, the service can download the CSV from a GitHub Release asset at startup. A public release asset is downloadable by anyone, so only use this with data you are permitted to publish.

## Deploy free from GitHub

1. Push this project to the `main` branch of your GitHub repository.
2. In GitHub, open **Releases > Draft a new release**. Create a tag such as `reviews-data-v1`, attach `Reviews.csv`, and publish the release. Each release asset must be under 2 GiB, so this 300 MB CSV fits.
3. Copy the asset's **download URL**. It should look like:

   ```text
   https://github.com/Smriti-pal/Customer-Feedback-AI-Response-Studio/releases/download/reviews-data-v1/Reviews.csv
   ```

4. In Render, choose **New > Blueprint**, connect this repository, and keep the `free` plan from `render.yaml`.
5. When Render asks for `REVIEWS_CSV_URL`, paste the release download URL. Do not add `Reviews.csv` to the Git repository.
6. Let the first deploy finish, then open the Render URL and select **Open Feedback Dashboard**.
7. To enable Gemini email drafts, add `GEMINI_API_KEY` under the Render service's environment variables. This is optional; the dashboard works without it.

The browser interface is the notebook's section 14 UI. The loader reads only the columns used by the dashboard to reduce memory use. Render's free plan has 512 MB RAM and sleeps after inactivity; startup can be slow while it downloads and analyzes the CSV, and this dataset may still exceed the free memory limit. Its filesystem is temporary, so the release asset is downloaded again after the service sleeps, restarts, or redeploys. This is a no-cost demo setup, not an always-on service.

## Run locally

1. Install Python 3.10 or newer.
2. Install dependencies:

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. Place `Reviews.csv` beside `app.py`.
4. Start the app:

   ```powershell
   python app.py
   ```

5. Open `http://127.0.0.1:10000` and select **Open Feedback Dashboard**.

## Optional Gemini configuration

Copy `.env.example` to `.env` and enter your Gemini key, or configure `GEMINI_API_KEY` in the hosting service's environment settings. Keep `.env` private and out of GitHub. Review text is sent to Google's Gemini API only when a user requests an AI draft.

The service has no login or access controls. Do not publish private or sensitive customer information in a public website or public release asset.

## Flag definitions

- **Urgent:** 1-star rating or safety/health language.
- **High:** 2-star rating or strongly negative wording on a 3-star review.
- **Watch:** other negative text sentiment.
- **Normal:** no elevated flag rule matched.

Sentiment and issue labels are transparent word-list estimates for triage. Review the original feedback before responding.
