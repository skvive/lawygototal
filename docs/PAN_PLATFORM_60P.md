# PAN platform (`/p/pan`)

Design source: `LAWYGO_3판.zip` → `LAWYGO_PAN_60PAGES/` (60p 시안).

## Static assets

| Path | Origin |
|------|--------|
| `static/pan-ref/site.css` | PAN 60P `assets/site.css` |
| `static/pan-ref/pan-expansion.css` | `pan-expansion.css` |
| `static/pan-ref/site.js` | Mobile nav, i18n toggle, contact modal |
| `static/pan-ref/pan-features.js` | CMS forms + `[data-approved-feed]` |
| `static/pan-ref/pan-deploy.css` | Hero + image placeholders (ZIP webp optional) |

## Live data

| UI block | Script | API |
|----------|--------|-----|
| Lawyers, story row, tabs, shorts, blogs | `static/pan-platform.js` | `/api/pan/lawyers`, `/api/pan/content` |
| Approved feed cards | `pan-features.js` | `/api/feed?kind=all` |

Env: `LAWYGO_PAN_BLOGGER_SITES`, `LAWYGO_PAN_YOUTUBE_CHANNEL_IDS`.

To bundle AI hero webp from ZIP, copy `assets/*.webp` into `static/pan-ref/media/` and point thumbnails in CMS or env.
