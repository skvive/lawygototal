# LAWYGO 공개 UI — 디자인 검증·재작성 기획 (2026-10-29)

## 1. 검증 결론 (디자이너 관점)

| 구분 | 현재 `lawygo.lexid.site` (/p/*) | 문제 | 정본 시안 (ZIP) |
|------|----------------------------------|------|------------------|
| **채널** | 4제품 공통 `pagehead` + `product-banner` + 3열 동일 `post` 카드 | 여백 과다(hero급 배너·단조 webp 1장), **신문/저널 톤 없음** | `LAWYGO_ATLAS_35PAGES/journal/*` — LAWYGO **JOURNAL** 편집국·호(issue)·editorial-grid |
| **판** | 채널과 **동일 레이아웃** | 블로그형 **대표 이미지·칩·그리드** 없음 | `LAWYGO_PAN_60PAGES/blog.html`, `blogger-feed.html` — image-card + 분야 chip |
| **위키** | 동일 카드 | 백과/검색·목차 UI 미적용 | `LAWYGO_ATLAS_35PAGES/wiki/*` |
| **노트** | 동일 카드 | 연구 노트·비공개 톤 미적용 | `LAWYGO_ATLAS_35PAGES/note/*` |
| **허브** | 단일 hero + 4 tile 동일 비율 | 채널만 channel.webp 반복 | `LAWYGO_ATLAS_35PAGES/index.html`, `01_REFERENCES` 마케팅 시안 |

**근본 원인:** runnable CMS(`static/product.html` + `product.js`)가 ZIP 내부 **마케팅 Atlas 35p / PAN 60p**와 연결되지 않고, API 목록만 공통 카드로 렌더링함.

---

## 2. ZIP 자산 인덱스 (재학습 경로)

마스터: `LAWYGO_SESSION_COMPLETE_MASTER_ZIP_20261029.zip`

| 아카이브 | 용도 | 핵심 경로 |
|----------|------|-----------|
| `LAWYGO_CHANNEL_WIKI_PAN_NOTE_ENGINE_INTEGRATED_20261029.zip` | **제품별 UI 정본** | `03_DESIGN_REFERENCES/LAWYGO_ATLAS_35PAGES/` (JOURNAL·WIKI·NOTE·PRO·PAN 허브) |
| 동일 | PAN 블로그·쇼츠 | `03_DESIGN_REFERENCES/LAWYGO_PAN_60PAGES/blog.html` 등 60p |
| `LAWYGO_ALL_SESSION_FINAL_CONSOLIDATED_20261029.zip` | 뉴스레터·브랜딩 | `05_로이고뉴스레터_초기시안/` |
| `LAWYGO_V3_FULL_FUNCTIONAL_QA_20261029.zip` | 실행 엔진(현재 배포) | `LAWYGO_ENGINE/static/*` — **디자인 최소 공통형** |
| `01_REFERENCES/` | 2026-10-29 세션 이미지 | 저널·PAN 홍보용 PNG/JPG → `static/img/editorial/` 반영 |

Atlas README: 채널 브랜드명은 **LAWYGO JOURNAL(로이고 저널)**, 4데스크(워싱턴/서울/판례/인사이트), 호(issue) 아카이브 구조.

---

## 3. 제품별 디자인 목표 (Must)

### A. 채널 = 로이고 저널 (신문·편집국)

- **Must:** utility bar, masthead `LAWYGO JOURNAL`, dateline, 1+2 **editorial-grid**(리드 기사 + 보조), 하단 **호(issue) 리스트** 또는 섹션 라벨(뉴스/클립/인사이트 = API board slug).
- **Must not:** 단일 230×140 배너, 3열 동일 높이 카드만.
- **참조 HTML:** `journal/index.html`, `journal/issue-01.html`, `assets/site.css` (`.editorial-grid`, `.issue-cover`, `.issue-row`).
- **이미지:** 기사별 썸네일(업로드 media 또는 editorial 풀 순환), 단일 `channel.webp` 금지.

### B. 판 = 변호사 블로그 허브

- **Must:** `page-hero` + **filter chip** + **image-card** (썸네일·meta·제목·요약·readmore).
- **참조:** `LAWYGO_PAN_60PAGES/blog.html`, `assets/site.css` + `pan-expansion.css`.
- **광고:** `is_sponsored` → sponsor ribbon (기존 tag 유지).

### C. 위키 (Phase 2)

- `wiki/index.html` — knowledge-search, facet, result-card.
- D. NOTE (Phase 2) — workspace 톤, 공개 피드 최소화.

---

## 4. 구현 단계

| Phase | 범위 | 산출 |
|-------|------|------|
| **1 (즉시)** | `/p/channel`, `/p/pan` | `product-themes.css`, `product.js` 테마 렌더, editorial 이미지 풀 |
| **2** | `/p/wiki`, `/p/note` | Atlas 위키·노트 레이아웃 이식 |
| **3** | `/`, `/dashboard` | 허브·관리자 Atlas 토큰(site.css 변수) 정렬 |
| **4** | 에셋 | Atlas/PAN zip 내 hero·law-books.webp 등 누락 파일 CDN 또는 ALLCHA 파이프라인 생성 |

---

## 5. QA 체크리스트 (디자인)

- [ ] 채널: 첫 화면에서 **신문 masthead + 리드 기사 1건**이 3초 안에 인지되는가
- [ ] 채널: 섹션 간 **여백 95px급 Atlas padding**이 아닌 **편집면 밀도**(32–48px)인가
- [ ] 판: 카드마다 **서로 다른 썸네일**이 보이는가 (클론 1장 반복 없음)
- [ ] 모바일 720px: editorial-grid 1열, pan g3→1열
- [ ] 접근성: focus-visible, 광고 표시 유지

---

## 6. 이번 커밋 범위 (Phase 1)

- `static/product-themes.css` — JOURNAL / PAN 전용
- `static/product.js` — product별 DOM·렌더 분기
- `static/product.html` — 공통 배너 제거, `#product-stage` 셸
- `static/img/editorial/*` — ZIP `01_REFERENCES` 이관
- 본 문서

운영 URL: https://lawygo.lexid.site/p/channel · `/p/pan`
