# Domain map — lawygo.com ↔ rerand.lexid.site

Production LAWYGO uses **subdomains per product**. Staging consolidates routes on `rerand.lexid.site` until split DNS is configured.

| Production | Staging (current) | App route |
|------------|-------------------|-----------|
| https://lawygo.com | https://rerand.lexid.site | `/` hub |
| https://lawygo.com/api/integrations/cms | https://rerand.lexid.site/api/… (bridge via `LAWYGO_NATIVE_BRIDGE_URL`) | API |
| https://channel.lawygo.com | https://rerand.lexid.site/p/channel | public feed |
| https://wiki.lawygo.com | https://rerand.lexid.site/p/wiki | public feed |
| https://pan.lawygo.com | https://rerand.lexid.site/p/pan | public feed + profiles |
| https://note.lawygo.com | https://rerand.lexid.site/p/note | author-scoped |
| https://pan.lawygo.com (newsletter links) | `LAWYGO_NEWSLETTER_BASE_URL=https://rerand.lexid.site` | `/api/newsletter/…` |

Optional future Vercel aliases (same deployment):

- `channel.rerand.lexid.site` → rewrite to `/p/channel`
- `wiki.rerand.lexid.site` → `/p/wiki`
- `pan.rerand.lexid.site` → `/p/pan`
- `note.rerand.lexid.site` → `/p/note`

OAuth redirect for Google: `https://rerand.lexid.site/api/google/callback` (see `vercel.json` default).
