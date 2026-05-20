# Deploy to Google Cloud Run

This game is a Streamlit app. On Google Cloud, there are two workable paths:

1. Run the app on **Cloud Run**
2. Use either **Gemini API** or **Vertex AI** as the hosted LLM backend
3. Store the API key as an environment variable, or prefer **Vertex AI credentials** on Cloud Run

> [!IMPORTANT]
> If your Google AI Studio project still shows **Free tier**, a `GEMINI_API_KEY`
> may continue to hit free-tier Gemini quotas even when the Cloud project has a
> billing account attached. In that case, prefer the **Vertex AI** path below.

## 1) Create the Gemini API key

The app supports Google-hosted models with SDialog model strings such as:

```text
google:gemini-2.5-flash
```

Create a Gemini API key in Google AI Studio and bind it to the Google Cloud
project you want to bill:

- Open `https://aistudio.google.com/app/apikey`
- Select or create the Google Cloud project you want to use
- Create an API key
- Restrict the key to the Gemini API if prompted

Google's current Gemini API documentation says unrestricted Gemini API keys
will stop being supported on **June 19, 2026**, so it is worth applying the
restriction immediately.

Set the key locally before testing:

```bash
export GEMINI_API_KEY="YOUR_GEMINI_KEY"
```

Once `GEMINI_API_KEY` is present, the game setup screen defaults to
`google:gemini-2.5-flash`.

## 2) Test locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt streamlit
pip install . --no-deps --no-build-isolation
streamlit run examples/swm_roleplay/streamlit_app.py
```

## 3) Fastest path: use Cloud Shell

If `gcloud` is not installed on your Mac, open **Cloud Shell** from the Google
Cloud Console. Cloud Shell already includes `gcloud`, so you can deploy without
installing anything locally.

In Cloud Shell:

```bash
git clone YOUR_REPOSITORY_URL deploy
cd deploy
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
gcloud run deploy city-x-game \
  --source . \
  --region europe-west1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=YOUR_GEMINI_KEY
```

If the code is only on your Mac and not in Git yet, use the local install path
below instead.

## 4) Vertex AI path (recommended for billed Google Cloud usage)

Vertex AI uses your Google Cloud project credentials directly instead of an AI
Studio API key.

Enable the required services:

```bash
gcloud config set project YOUR_PROJECT_ID
gcloud services enable aiplatform.googleapis.com run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
```

Then deploy without `GEMINI_API_KEY` and tell the app which project/location to
use:

```bash
gcloud run deploy city-x-game \
  --source . \
  --region europe-west1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID,VERTEX_AI_LOCATION=europe-west1
```

In the app setup screen, use:

```text
vertexai:gemini-2.5-flash
```

## 5) Gemini API path

If you intentionally want the Gemini API key path, keep using the steps below.

## 6) Enable the required Google Cloud services

Replace `YOUR_PROJECT_ID` with your Google Cloud project id:

```bash
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
```

## 7) Quick deploy to Cloud Run

This uses the `Dockerfile` in this folder:

```bash
gcloud run deploy city-x-game \
  --source . \
  --region europe-west1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=YOUR_GEMINI_KEY
```

After deployment, open the Cloud Run service URL in your browser.

## 8) Safer deploy with Secret Manager

Instead of passing the API key directly on the command line:

```bash
printf '%s' "YOUR_GEMINI_KEY" | gcloud secrets create GEMINI_API_KEY --data-file=-
```

If the secret already exists, create a new version instead:

```bash
printf '%s' "YOUR_GEMINI_KEY" | gcloud secrets versions add GEMINI_API_KEY --data-file=-
```

Grant the Cloud Run runtime service account access to the secret, then deploy:

```bash
gcloud run deploy city-x-game \
  --source . \
  --region europe-west1 \
  --allow-unauthenticated \
  --update-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest
```

## Notes on billing

- Cloud Run usage can consume normal Google Cloud billing credits.
- Gemini API billing is handled through the Google Cloud project linked to the
  key.
- If your credit is a standard billing-account credit usable for "Any service
  on this billing account", it is likely usable for Cloud Run and other Google
  Cloud services. Check the exact credit restrictions in **Cloud Billing >
  Credits**.
