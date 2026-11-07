# LAWYGO workspace-first redesign QA checklist — 2026-11-08

## Original sources
- Frontend: `skvive/lawygototal`, base master `a7909f14e3e64149288bfd81d3dc7d6001040185`.
- Authenticated backend: `shinkangteam/lawygo`, original Next routes `/board/ai/legal_encyclopedia`, `/board/ai/ai_search` and related legal AI detail modules.
- Shared Drive: `ChatGPT_Library` and `렉시드개발자료/공통개발스킬`; current docs describe iframe restrictions and the current Neon/Auth isolation.

## Critical findings fixed
1. Journal/newsletter-first homepage incorrectly obscured legal product entry.
2. WIKI and NOTE required scrolling past marketing before reaching real on-page workspace interfaces.
3. Duplicated shell/platform navigation and five products caused poor hierarchy.
4. Public WIKI inline reader lacked a reloadable detail URL.
5. Authenticated AI is cross-origin with frame restrictions; never pretend it can be embedded or share credentials.

## New IA
- HOME: WIKI, WORKSPACE, PRO, PAN; no journal navigation.
- WIKI: inline original public API-powered 3-column research frame first, optional `?post=<id>` permalink to detailed reader, backend legal encyclopedia direct link.
- WORKSPACE: local draft dashboard first, authenticated AI modules retain their real original URL/credentials.
- Existing CMS, auth, Neon data, billing, PAN and PRO modules unchanged.

## Verification gates
- HTML shell and main/H1 on all updated pages.
- Mobile at 360/390, tablet at 768, desktop at 1440.
- No horizontal overflow, broken assets, JS errors; all controls keyboard reachable.
- WIKI search → public result → detailed article → reload deep link → NOTE citation, and NOTE draft/edit/copy/export.
- AI engine direct links must require the original login; private workspaces are NOT iframed.
- Run existing `.github/workflows/lawygo-web-qa.yml` against this branch and inspect Vercel preview, then release only if checks pass.
