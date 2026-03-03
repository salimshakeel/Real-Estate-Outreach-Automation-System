# Deploy to Render (Free Tier)

This guide walks you through deploying the **Real Estate Outreach Automation System** (backend + frontend monorepo) on [Render](https://render.com) using the free tier.

## What Gets Deployed

| Service        | Tech       | Free tier behavior                          |
|----------------|------------|---------------------------------------------|
| **PostgreSQL** | Render DB  | 1 GB, 90-day expiry (can extend)           |
| **Backend**    | FastAPI    | Spins down after ~15 min inactivity         |
| **Frontend**   | Next.js   | Spins down after ~15 min inactivity         |

After spin-down, the first request may take 30–60 seconds to wake the service.

---

## Prerequisites

- GitHub account
- Code pushed to a **public** GitHub repo (e.g. `salimshakeel/Real-Estate-Outreach-Automation-System`)
- Render account (free at [render.com](https://render.com))

---

## Step 1: Connect Repository to Render

1. Go to [dashboard.render.com](https://dashboard.render.com) and sign in (or sign up with GitHub).
2. Click **New** → **Blueprint**.
3. Connect your GitHub account if needed, then select the repository **Real-Estate-Outreach-Automation-System**.
4. Render will detect `render.yaml` in the repo root. Click **Apply**.

---

## Step 2: Set Required Environment Variables

Render will create three resources: one PostgreSQL database and two web services. You **must** set one variable for the frontend:

### Frontend: `NEXT_PUBLIC_API_URL`

1. In the Render dashboard, open the **realestate-frontend** service.
2. Go to **Environment**.
3. Find **NEXT_PUBLIC_API_URL** (it was added from the Blueprint with `sync: false`).
4. Set its value to your backend URL:
   - **URL format:** `https://realestate-backend.onrender.com`
   - Replace with your actual backend URL if Render gave it a different hostname (e.g. `https://realestate-backend-xxxx.onrender.com`).
5. Save. Render will redeploy the frontend so the build picks up this value.

### Backend (optional)

- **CORS_ORIGINS** – Only needed if your frontend URL is different from `https://realestate-frontend.onrender.com`. Add that URL (comma-separated if you have several).
- **SENDGRID_API_KEY**, **OPENAI_API_KEY**, etc. – Optional; the app runs in “demo” mode without them.

---

## Step 3: Deploy

1. After applying the Blueprint, Render starts building and deploying all three resources.
2. Wait for all services to show **Live** (green). First deploy can take 5–10 minutes.
3. Note the URLs:
   - **Frontend:** `https://realestate-frontend.onrender.com` (or the URL Render shows)
   - **Backend:** `https://realestate-backend.onrender.com` (or the URL Render shows)
   - **API docs:** `https://realestate-backend.onrender.com/docs`

---

## Step 4: Use the App

1. Open the **frontend** URL in your browser (e.g. `https://realestate-frontend.onrender.com`).
2. Use the dashboard to manage leads, campaigns, and templates.
3. If the frontend was deployed **before** you set `NEXT_PUBLIC_API_URL`, trigger a **Manual Deploy** on the frontend service after saving the env var so the new value is used at build time.

---

## Troubleshooting

### Frontend shows “Network Error” or can’t reach API

- Confirm **NEXT_PUBLIC_API_URL** is set to the **backend** URL (e.g. `https://realestate-backend.onrender.com`) with no trailing slash.
- Redeploy the frontend after changing `NEXT_PUBLIC_API_URL` (it’s baked in at build time).

### Backend returns CORS errors

- In the backend service **Environment**, set **CORS_ORIGINS** to include your frontend URL, e.g. `https://realestate-frontend.onrender.com`. Defaults already include this; add any other origins you use.

### Backend or frontend “spins down”

- Free tier services sleep after inactivity. The first request after that may take 30–60 seconds. This is expected.

### Database connection errors

- The Blueprint wires **DATABASE_URL** from the Render Postgres instance to the backend. The app converts `postgresql://` to `postgresql+asyncpg://` automatically. If you use a different DB name in `render.yaml`, ensure the backend service’s **DATABASE_URL** still comes from the correct database in the Blueprint.

---

## Changing the Setup Later

- **Env vars:** Change them in each service’s **Environment** tab and save; Render will redeploy that service if needed.
- **Blueprint (render.yaml):** Edit in your repo and push. In Render, open the Blueprint and click **Apply** to sync changes. New env vars with `sync: false` must be set manually in the Dashboard.

You’re done. Your app is live on Render’s free tier.
