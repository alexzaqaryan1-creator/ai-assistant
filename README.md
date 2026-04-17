# Document AI Assistant

A small Flask app that lets users chat with **Google Gemini 2.0 Flash** (free tier). Optionally upload a document (PDF, DOCX, TXT, MD) and questions will be grounded in its contents.

## Run locally

```
pip install -r requirements.txt
echo GEMINI_API_KEY=your-key > .env
python main.py
```

Open <http://127.0.0.1:5000>. Get a free Gemini API key at <https://aistudio.google.com/apikey>.

## Deploy

Hosted on **Render**, auto-deployed via **GitHub Actions**.

### First-time setup

1. Push this repo to GitHub.
2. On <https://render.com>:
   - New → Blueprint → connect the repo.
   - Render reads `render.yaml` and creates the service.
   - In the service's **Environment** tab, paste your `GEMINI_API_KEY`. Optionally set `APP_PASSWORD` to gate access.
   - Under **Settings → Deploy Hook**, copy the hook URL.
3. On GitHub: **Settings → Secrets and variables → Actions → New repository secret**
   - Name: `RENDER_DEPLOY_HOOK_URL`
   - Value: the URL from step 2.

Every push to `main` runs the workflow in `.github/workflows/deploy.yml`, which imports-checks the app and pings Render to redeploy.

## Free tier limits

Gemini 2.0 Flash free tier: **1500 requests/day, ~15 requests/min, 1M tokens/min**. Very generous for small apps. Set `APP_PASSWORD` in Render if you want to restrict access further.
