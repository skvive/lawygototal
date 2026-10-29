# Domain map — lawygo.com ↔ lawygo.lexid.site

Production LAWYGO uses **subdomains per product**. LexID staging consolidates routes on `lawygo.lexid.site` until split DNS is configured.

| Production | Staging (current) | App route |
|------------|-------------------|-----------|
| https://lawygo.com | https://lawygo.lexid.site | `/` hub |
| https://lawygo.com/api/integrations/cms | https://lawygo.lexid.site/api/… (bridge via `LAWYGO_NATIVE_BRIDGE_URL`) | API |
| https://channel.lawygo.com | https://lawygo.lexid.site/p/channel | public feed |
| https://wiki.lawygo.com | https://lawygo.lexid.site/p/wiki | public feed |
| https://pan.lawygo.com | https://lawygo.lexid.site/p/pan | public feed + profiles |
| https://note.lawygo.com | https://lawygo.lexid.site/p/note | author-scoped |
| https://pan.lawygo.com (newsletter links) | `LAWYGO_NEWSLETTER_BASE_URL=https://lawygo.lexid.site` | `/api/newsletter/…` |

Optional future Vercel aliases (same deployment):

- `channel.lawygo.lexid.site` → rewrite to `/p/channel`
- `wiki.lawygo.lexid.site` → `/p/wiki`
- `pan.lawygo.lexid.site` → `/p/pan`
- `note.lawygo.lexid.site` → `/p/note`

Legacy alias: `rerand.lexid.site` may remain on the same project until removed.

OAuth redirect for Google: `https://lawygo.lexid.site/api/google/callback` (see `vercel.json` default).
