# SpiderGPT production deployment

The repository uses a vanilla Vite frontend and a FastAPI backend. The frontend reads frontend/.env at build time; the backend reads backend/.env at runtime.

## 1. Environment files

Windows PowerShell:

    Copy-Item backend/.env.example backend/.env
    Copy-Item frontend/.env.example frontend/.env

Do not commit either file.

### Backend .env

Put real secrets here: PostgreSQL credentials, JWT secret, Supabase service role key, AI provider keys, Redis URL, Razorpay/Stripe secrets, webhook secrets, and similar server-only values.

For production set ENVIRONMENT=production, DEBUG=false, a PostgreSQL DATABASE_URL, STORAGE_PROVIDER=supabase, Supabase credentials, REDIS_URL, explicit ALLOWED_CORS_ORIGINS, an AI provider key, a real payment provider configuration, and ADMIN_EMAILS.

### Frontend .env

Only browser-visible configuration belongs here:

    VITE_API_URL=https://api.your-domain.com/api/v1
    VITE_SUPABASE_URL=https://YOUR_PROJECT.supabase.co
    VITE_SUPABASE_ANON_KEY=YOUR_SUPABASE_ANON_KEY

Never put a Supabase service-role key, JWT secret, AI key, payment secret, database password, or webhook secret in the frontend. The Supabase anon/publishable key is browser-visible; server-side authorization and data access must remain protected.

## 2. Local run

Terminal 1:

    python -m venv .venv
    .venv\Scripts\Activate.ps1
    pip install -r backend/requirements.txt
    uvicorn backend.app.main:app --reload --port 8000

Terminal 2:

    npm install
    npm run dev

Open http://localhost:3000.

## 3. Production backend

Use managed PostgreSQL, Redis, Supabase Storage/Auth, and real AI/payment providers.

Run migrations before the web process:

    alembic upgrade head
    uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT

Run Deep Research as a persistent worker:

    python scripts/research_worker.py

The included backend/Dockerfile can be used for both services; change only the start command for the worker.

## 4. Production frontend

Build the static frontend:

    npm install
    npm run build

The output directory is dist/. On Vercel, Netlify, or another static host, use npm run build and dist as the output directory. Define the three VITE_* variables in the hosting provider's environment settings.

## 5. Supabase / Google OAuth

After the frontend has a real HTTPS URL, add that exact URL to Supabase Auth URL configuration and Google OAuth redirect configuration. Keep local and production URLs separate.

The application flow is: Google -> Supabase Auth -> Supabase access token -> SpiderGPT /auth/google -> SpiderGPT session token.

## 6. Payments

Create recurring plans in the selected provider and copy their IDs/secrets into backend/.env. Configure provider webhooks to the backend webhook endpoints. Frontend state is never treated as payment authority.

Before launch test monthly Pro, yearly Pro, monthly Plus, yearly Plus, successful payment, failed payment, renewal, cancellation, immediate cancellation, and duplicate webhook delivery.

## 7. GoDaddy domain

The GoDaddy registrar does not need to host the application. A simple layout is:

    https://your-domain.com       -> frontend host
    https://www.your-domain.com  -> frontend host
    https://api.your-domain.com  -> backend host

After HTTPS is active, put the final frontend origins in backend ALLOWED_CORS_ORIGINS and the final API URL in VITE_API_URL. Then update Google OAuth and Supabase allowed URLs.

## 8. Pre-launch checklist

- [ ] Production PostgreSQL connected and migrations applied
- [ ] Redis connected
- [ ] Supabase Auth/Storage configured
- [ ] Google OAuth redirect URLs configured
- [ ] AI provider configured and tested
- [ ] Search provider configured if enabled
- [ ] Image provider configured if enabled
- [ ] Razorpay/Stripe recurring plans tested
- [ ] Payment webhooks verified
- [ ] Deep Research worker running continuously
- [ ] Production CORS contains only real frontend origins
- [ ] No real secrets committed to Git
- [ ] HTTPS enabled on frontend and API
- [ ] Mobile browser QA completed
- [ ] Account deletion/privacy/terms/support pages published before public launch
- [ ] Monitoring, logs, database backups, and provider alerts configured

The code is deployment-ready from an application/configuration perspective once these external services and launch requirements are configured. Buying the GoDaddy domain is the DNS step; do not store backend secrets at the registrar.