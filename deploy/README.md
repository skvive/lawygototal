# LAWYGO CMS — Neon + Vercel (rerand.lexid.site)

## Site purpose

LAWYGO CMS v3 is a **multi-product content engine** for the LAWYGO legal platform:

| Product | Role | Production domain (lawygo.com) |
|--------|------|--------------------------------|
| **CHANNEL** | 경제·법률 뉴스·영상·인사이트 | `channel.lawygo.com` → hub path `/p/channel` |
| **WIKI** | 법률백과·판례·법령 | `wiki.lawygo.com` → `/p/wiki` |
| **PAN** | 변호사 브랜딩·칼럼·광고(표시) | `pan.lawygo.com` → `/p/pan` |
| **NOTE** | 비공개 연구·초안(테넌트 격리) | `note.lawygo.com` → `/p/note` |
| **Hub / bridge** | 메인 SaaS·연동 API | `lawygo.com` | 

Staging on LexID maps the same four products to **one FastAPI deployment** at `https://rerand.lexid.site` (paths above). Newsletter and OG defaults use `LAWYGO_NEWSLETTER_BASE_URL`.

## Required Vercel environment variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Neon **pooled** connection string (`-pooler` host) |
| `LAWYGO_BOOTSTRAP_EMAIL` | First admin email (only when DB has zero users) |
| `LAWYGO_BOOTSTRAP_PASSWORD` | ≥12 chars; used once for bootstrap |
| `LAWYGO_TOKEN_ENCRYPTION_KEY` | Fernet key for OAuth tokens at rest |
| `LAWYGO_BILLING_WEBHOOK_KEY` | ≥32 chars HMAC for subscription events |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Optional; set `GOOGLE_REDIRECT_URI` to production callback |
| `GEMINI_API_KEY` | Optional; user opt-in only |

Local dev: omit `DATABASE_URL`, use `LAWYGO_DB_PATH=./data/lawygo.db`, run `RUN_WINDOWS.bat`.

## Deploy commands

```powershell
cd lawygototal
neonctl projects create --name lawygototal-rerand
neonctl connection-string --pooled
vercel link --yes
vercel env add DATABASE_URL production
vercel env add LAWYGO_BOOTSTRAP_EMAIL production
vercel env add LAWYGO_BOOTSTRAP_PASSWORD production
vercel --prod
vercel domains add rerand.lexid.site
```

After first deploy, open `/api/health` and sign in at `/dashboard`.
