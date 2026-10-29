# Brand hub (ALL SESSION ZIP alignment)

Source of truth when the full ZIP is unavailable locally:

- Atlas 35p hub layout + QA text corrections (`_design_ref/.../LAWYGO_KOREAN_TEXT_IMAGE_QA_REPORT.md`)
- Payment plans from `add_payment_lawygo.py` in consolidated bundle scripts
- Partnership/MOU copy from PAN 60p `partnership.html`

## Live routes

| Path | File |
|------|------|
| `/` | `static/index.html` — 5-product grid, CMS feed, newsletter API |
| `/pricing` | `static/pricing.html` |
| `/payment` | `static/payment.html` — marketing only; Stripe PR #14, billing disabled |
| `/partnership` | `static/partnership.html` |

Shared chrome: `static/brand-shell.js`, styles `static/atlas/site.css`.

## ZIP path (user machine)

`LAWYGO_ALL_SESSION_PROJECT_FILES_20261029.zip` → `01_최종완성_웹사이트_Partnership_MOU/`

Extract into `_design_ref/extracted/all_session/` to diff future updates. MOU PDF/DOCX stay out of git (size).
