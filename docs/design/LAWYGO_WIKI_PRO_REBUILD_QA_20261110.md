# LAWYGO WIKI + PRO / Design Rebuild QA · 2026-11-10

## Source-of-truth
- Repository: `skvive/lawygototal`, base `master@ecd33151c3d1651d15db8c5dcafed13e399f6861`.
- Development branch: `design/wiki-pro-rebuild-20261110`.
- Existing code reused: `static/wiki.html`, `static/pro.html`, `static/lawygo-service-integration-20261105.js`, `static/wiki-page.js`, `static/brand-shell.js`, `static/pro-program-linked-20261108.css`.
- Source references: Drive `legal-encyclopedia-unified-architecture.md`, `lawygo-pro-engine.md`; public `https://www.lawygo.com/`.
- Shared development repositories `ChatGPT_Library` and `렉시드개발자료/공통개발스킬` inspected before authoring; reuse prior brand QA and assets.
- Baseline brand: navy `#0c2439`, ivory `#f6f4ed`, gold `#c99c5c`. No wholesale framework rewrite.

## Changes
| Route | Change | Dependency | Safety |
|---|---|---|---|
| `/p/wiki` | Editorial research-dashboard introduction, actionable four-item nav, new vector dashboard illustration | Public research `/api/wiki/search`, existing `lawygo-service-integration-20261105.js` | Search results remain public-only, no private case data imported |
| `/p/wiki` | Responsive refinement of existing 3-column source reader | Existing `lnw-*` selectors and article detail endpoint | No API contract changed |
| `/pro` | Detailed PRO operations preview + linked source/service gateway | `www.lawygo.com` and existing portal subroutes | Concept UI labeled; no fake case counts or authentication |
| Both | New scoped CSS + 1100×720 SVG | Existing styles, no new third-party package | Desktop/tablet/mobile and reduced-motion rules |

## Page-by-page review (static code)
- [x] HOME `/`: intentionally unchanged; JOURNAL-centric design remains.
- [x] JOURNAL `/journal`: unchanged; retained editorial structure.
- [x] CHANNEL `/channel`: unchanged.
- [x] WIKI `/p/wiki`: new editorial bridge, route-level anchors, 3-column research UI and source separation.
- [x] NOTE `/p/note`: unchanged, links to existing workspace anchors.
- [x] PRO `/pro`: source-linked overview, workflow preview, entry points.
- [x] PAN `/p/pan`: unchanged.
- [x] Pricing, Payment, Partnerships, Strategy, Dashboard: unchanged.

## Verification
- [x] Source repository permissions: GitHub connector reports admin/push access.
- [x] Original repository preserved; changes isolated on feature branch and no file deleted.
- [x] After-commit source readback completed for both HTML pages, CSS, and SVG.
- [x] Both HTML files contain matching numbers of `section` open/close tags.
- [x] Responsive CSS breakpoints for 1100 / 800 / 500 widths, focus-visible, reduced motion.
- [x] Reuse of actual public search endpoint; no synthetic search results.
- [ ] GitHub Actions 52-screenshot website QA from pull request.
- [ ] Vercel staging/preview deployment READY and URL confirmed.
- [ ] Real mobile/desktop visual inspection at 360 / 390 / 768 / 1440.
- [ ] Validate external LAWYGO /login and /platform availability in authenticated browser.
- [ ] Production promotion only after passing gates.

## Known constraints
- Private `shinkangteam/lawygo` Next.js source, AI prompt logs, personal cases and customer files were not copied into the public `skvive/lawygototal` repository.
- Existing public WIKI search is not a substitute for patent ontology/ranking inside a secured AI engine.
- `lawygo.com` product page content was source-mapped, not directly scraped and pasted with any false operational/QA metrics.
- Current branch does **not** change Neon/Auth migrations, OAuth callback, payment, server APIs or live data.
- New SVG is an editable UI visualization; it is a concept, not a screenshot or a legally verified document.
