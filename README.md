# Customer Feedback Analysis and AI Response Studio

A Flask web app built from the dashboard and email studio already in the Jupyter notebook. The web interface uses the notebook's existing HTML, CSS, charts, queue, filters, and response drafting flow. The app uses **Reviews.csv only**; it does not substitute a sample file or accept another dataset.

## Files

- `app.py` serves the notebook's existing interface and loads `Reviews.csv`.
- `Customer_Feedback_Analysis_AI_Response_Localhost.ipynb` contains the original analysis notebook and source UI.
- `render.yaml` configures a Flask web service and persistent data disk on Render.
- `.env.example` shows optional local Gemini settings. Never commit a real key.

The 300 MB `Reviews.csv` stays out of GitHub. GitHub enforces a 100 MB maximum for a single Git object, and keeping the data outside source control also avoids publishing customer review data.

## Run locally

1. Install Python 3.10 or newer.
2. Install the packages:

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. Put `Reviews.csv` beside `app.py`.
4. Start the app:

   ```powershell
   python app.py
   ```

5. Open `http://127.0.0.1:10000` and choose **Open Feedback Dashboard**.

The dashboard route is `/dashboard`. If the CSV is absent, the app displays a clear missing-data message instead of silently loading sample data.

## Deploy the same UI

This is a Flask application. Streamlit Community Cloud only runs Streamlit apps, so it cannot serve this notebook's Flask UI unchanged. Use Render to deploy the GitHub repository:

1. In Render, choose **New > Blueprint** and connect this repository on the `main` branch. Render reads `render.yaml` to configure the service.
2. The blueprint uses a paid Standard web service and a persistent 1 GB disk at `/var/data`. Render's free service filesystem is ephemeral, and persistent disks are available for paid services.
3. After the service is created, transfer your local `Reviews.csv` to `/var/data/Reviews.csv` on the service disk using the Render dashboard's SSH/SCP instructions. The file must be available at this path; it is not downloaded from GitHub.
4. Restart or redeploy the service after the transfer. Open the Render URL and select **Open Feedback Dashboard**.
5. If you want AI drafts, set `GEMINI_API_KEY` in the Render service environment settings and redeploy. The dashboard works without Gemini.

Render deployment documentation: [Flask apps](https://render.com/docs/deploy-flask) and [persistent disks and file transfer](https://render.com/docs/disks).

## Gemini and customer data

The email studio sends review text and response context to Google's Gemini API only when someone requests a draft. Configure the key outside GitHub. Before using real customer data on a public service, confirm your organization's privacy and data-sharing requirements. The service does not have user accounts or access controls.

## Review flags

- **Urgent:** 1-star rating or safety/health language.
- **High:** 2-star rating or strongly negative wording on a 3-star review.
- **Watch:** other negative text sentiment.
- **Normal:** no elevated flag rule matched.

Sentiment and issue types are word-list estimates for triage. Read the review before taking action.
