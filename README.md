# Document AI Assistant

A small Flask app that lets users upload a document (PDF, DOCX, TXT, MD) and chat with **Llama 3.3 70B via Groq's free API** about its contents.

## Run locally

```
pip install -r requirements.txt
echo GROQ_API_KEY=gsk_your-key > .env
python main.py
```

Open <http://127.0.0.1:5000>. Get a free Groq API key at <https://console.groq.com>.

## Deploy

Hosted on **Render**, auto-deployed via **GitHub Actions**.

### First-time setup

1. Push this repo to GitHub.
2. On <https://render.com>:
   - New → Blueprint → connect the repo.
   - Render reads `render.yaml` and creates the service.
   - In the service's **Environment** tab, paste your `GROQ_API_KEY`. Optionally set `APP_PASSWORD` to gate access.
   - Under **Settings → Deploy Hook**, copy the hook URL.
3. On GitHub: **Settings → Secrets and variables → Actions → New repository secret**
   - Name: `RENDER_DEPLOY_HOOK_URL`
   - Value: the URL from step 2.

Every push to `main` now runs the workflow in `.github/workflows/deploy.yml`, which imports-checks the app and pings Render to redeploy.

## Cost

Groq offers a generous **free tier** — rate-limited but doesn't cost anything. Set `APP_PASSWORD` in Render if you want to restrict access.
