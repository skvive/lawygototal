# LAWYGO Android Native — 소스 납품 / 빌드 전 단계

**2026-10-31 · Android 16(API 36) 대상 · Kotlin + Jetpack Compose · 원본 LAWYGO v6.1 백엔드 기반**

## 1. 무엇이 만들어졌나

- `app/` : 7개 Android 설치 변형으로 빌드할 수 있는 네이티브 안드로이드 프로젝트. `suite`, `journal`, `channel`, `pan`, `wiki`, `note`, `pro`.
- `backend_server/` : v6.1 FastAPI·SQLite 엔진 + **선택적 Google Credential Manager 서버 인증 브리지**. 원본 운영 GitHub/Neon DB를 대체하거나 자동 업데이트하지 않습니다.
- `qa/` : 모바일 API 16개, 프로젝트 구조 18개 신규 테스트. 기존 서버 회귀 92개 통과.
- `.github/workflows/` : SDK·Gradle을 설치해 debug APK와 release AAB를 빌드하는 CI 정의.
- `PLAY_STORE_ASSETS/` : 스토어 아이콘 초안. 실기기 스크린샷은 존재하지 않으므로 업로드 전에 촬영해야 합니다.
- `DESIGN_REFERENCES_WEB_ONLY/` : 웹 디자인 참고자료 (안드로이드에서 캡처한 이미지가 아님).

## 2. 중요한 검증 상태

이 환경에는 **Android SDK, Gradle 실행파일, 에뮬레이터, Android 실기기, Google Play Console 접근권한이 없습니다**. APK/AAB 실제 컴파일, 안드로이드 폰 설치, Play Console 등록은 하지 못했습니다. **유효한 APK/AAB 파일을 생성했다고 주장하지 않습니다.**

서버: v6.1 회귀 92개 + Android 서버 연동 16개 통과. Android 프로젝트의 XML·API·안전 설정은 18개 검사 통과. Kotlin CLI는 Android 의존성이 없어 전체 컴파일하지 못했습니다. 원본 인증 및 운영 데이터는 변경하지 않았습니다.

## 3. 빌드 (Windows)

1. Android Studio 최신 안정판, JDK 17, Android SDK API 36 / Build Tools 36.0.0, Gradle 8.13을 설치합니다.
2. `ANDROID_APP` 프로젝트 폴더를 Android Studio에서 엽니다. Gradle Sync를 진행합니다. 번들 Gradle Wrapper jar는 포함되어 있지 않습니다.
3. `BUILD_ANDROID_WINDOWS.cmd` 실행(Gradle CLI와 SDK 환경변수 필요). 또는 Android Studio > Build > Generate App Bundles / APKs.
4. 7개 앱 변형 중 `suiteDebug` 등 원하는 빌드 변형을 선택합니다.
5. 개인 소유 업로드 키를 등록해야 서명된 Release AAB를 만들 수 있습니다. 환경변수 `LAWYGO_UPLOAD_KEYSTORE`, `LAWYGO_UPLOAD_STORE_PASSWORD`, `LAWYGO_UPLOAD_KEY_ALIAS`, `LAWYGO_UPLOAD_KEY_PASSWORD`를 설정하고 **키를 저장소/채팅에 올리지 마세요**.
6. `app/build/outputs/apk/.../*.apk` 및 `app/build/outputs/bundle/.../*.aab` 확인. 스토어 등록 전 내부 테스트 필수.

## 4. 서버 연결

앱 설정에서 HTTPS로 서비스하는 **실제 v6.1 FastAPI API 주소**를 입력합니다. 로컬 Windows `http://127.0.0.1:8018`은 폰에서 접근할 수 없고 Release 앱은 HTTPS만 지원합니다.

- `backend_server/requirements.txt` 설치 후 운영용 HTTPS 리버스 프록시(Caddy/Nginx) 뒤에서 FastAPI 실행.
- 최초 관리자는 `backend_server/setup_admin.py`로 생성.
- Android 서버 계정 로그인의 `tenant` 기본값은 `demo`입니다. 조직별 실제 관리번호는 설정에 맞춰 변경.
- 배포 환경에서 `LAWYGO_SECURE_COOKIES=true`, 서비스 도메인 및 TLS 인증서를 설정.
- Google 로그인은 Google Cloud의 Android 패키지/SHA-1/SHA-256 등록, **웹 클라이언트 ID**, 서버 환경변수 `LAWYGO_GOOGLE_WEB_CLIENT_ID`가 필요. 최초에는 기존 회원으로 로그인해 Google `sub`를 연결하며, 이메일만으로 자동 합치지 않습니다.

## 5. 현 단계의 한계

- `PRO`: 네이티브 안내/연결 화면. **송무 사건·기일·문서 원본 서비스 전체는 미이식**. 실제 PRO GitHub 인증/법원 API 통합 필요.
- `NOTE`: 독립 v6.1의 노트·첨부·Gemini 분석 연동. 원본 LAWYGO 모든 AI 워크스페이스의 1:1 이식은 미완료.
- `WIKI`: 검수·공개된 로컬 지식 검색. 법령·판례 공식 API, 원본 벡터/온톨로지 엔진의 앱 1:1 이식은 미완료.
- `PAN`: 콘텐츠 피드/광고 표시/기초 편집 및 검색. 본인 YouTube/Blogger 계정 연결은 서버 API를 별도 이용하며 전체 네이티브 계정 관리 UI는 추가 필요.
- `JOURNAL`: RSS 기사는 **서버에서 수집**, 모바일 앱은 표시·공개 캐시만 수행. AI 일일 초안 및 SMTP 발송은 서버 편집실 권한으로 처리.
- Stripe 결제를 앱 안에서 직접 유도하지 않습니다. Google Play 인앱 디지털 구독 결제정책을 검토해 Play Billing 또는 적법한 예외를 적용해야 합니다.

## 6. 고객 납품 조건

`DOCS/QA_REPORT_ANDROID_KO.md`, `DOCS/PLAY_STORE_RELEASE_GUIDE_KO.md` 참고. 실기기 검증, 서명, Play Console 심사, 실계정 OAuth는 남았습니다.
