# Google Play Console 등록 실행 체크리스트

**아직 실제 Google Play 등록/게시/심사는 수행하지 않았습니다.** 연결된 Play Console 계정, 앱 서명 업로드 키, 개인정보 URL, Android SDK 및 기기가 있어야 합니다.

1. `site.lexid.lawygo` 앱 ID가 Play Console에서 비어 있는지 확인. 앱 이름 LAWYGO, 카테고리 비즈니스/생산성 검토. 회사 명의의 법률광고 심의 필요.
2. Android SDK API 36 / targetSdk 36으로 빌드. Debug APK는 Play 출시용이 아님. **서명된 AAB** 제출.
3. Play App Signing 등록, 소유자가 생성한 **업로드 키(keystore)를 비공개 보관**. 앱 서명 키를 ChatGPT나 GitHub에 업로드하지 않기.
4. Play Console 앱 액세스 테스트 계정/가이드, 개인정보 처리방침의 공개 URL, 회원 데이터 삭제 요청 URL, 데이터 안전 양식, 광고 신고, AI 법률정보 면책 표기, 스토어 콘텐츠 검증.
5. `PLAY_STORE_ASSETS/lawygo_store_icon_512.png` 로고 초안. feature graphic 1024x500, Android 기기 실제 화면 캡처(폰 2장 이상), 태블릿 추가 자료 필요. **웹페이지 시안은 안드로이드 실행 스크린샷이 아닙니다.**
6. 통합앱을 내부 테스트 트랙에 먼저 배포, QA 보고 검토. 신규 개인 개발자 계정 조건에 해당하면 **12명 14일 연속 참여 비공개 테스트**가 필요할 수 있음.
7. Android 디지털 구독/업무 SaaS의 인앱 구매는 원칙적으로 Google Play Billing 요건을 검토해야 함. Stripe 웹 결제로 앱 내부에서 유도하지 말 것. 가능한 예외는 법률·플랫폼 정책 전문가 검토.
8. Play Console 앱 서명·검토·등록·게시 버튼은 사용자 본인 권한과 최종 승인 후 수행. 현재는 **승인 대기 코드베이스**입니다.

확인된 공식 출처:
- https://support.google.com/googleplay/android-developer/answer/11926878?hl=ko
- https://support.google.com/googleplay/android-developer/answer/9844279
- https://support.google.com/googleplay/android-developer/answer/14151465
- https://support.google.com/googleplay/android-developer/answer/9858738

## 스토어 설명 초안 (운영 사실로 과장하지 않음)

**짧은 설명:** 경제·법률 뉴스, 전문가 콘텐츠, 법률백과와 개인 업무 노트를 한곳에서

**상세 설명:** LAWYGO는 경제·법률 저널, 전문가 채널, 변호사 콘텐츠 플랫폼 PAN, 법률백과 WIKI, 비공개 NOTE 및 송무 PRO 진입 기능을 통합하는 서비스입니다. 무료 공개 콘텐츠를 탐색하고, 가입 이용자는 권한에 따라 게시물과 개인 문서를 관리할 수 있습니다. 법률정보 및 AI 결과는 참고자료이며 실제 법률 자문·최신 법령 검토를 대체하지 않습니다. 일부 전문 기능은 별도 계정·구독이 필요할 수 있습니다.

## 수동 내부 테스트 업로드 자동화 (선택)

`.github/workflows/google-play-internal.yml`은 실제 GitHub 저장소에 소스가 반영되고 서명키·Play 서비스 계정 비밀값이 **GitHub Secrets**에 등록된 경우에만 실행할 수 있습니다. 실패 방지를 위해 별도 승인 없이 운영 트랙으로 업로드하지 않으며 `track: internal`, `status: draft`로 제한합니다.

**필수 Secrets:** `LAWYGO_UPLOAD_KEYSTORE_BASE64`, `LAWYGO_UPLOAD_STORE_PASSWORD`, `LAWYGO_UPLOAD_KEY_ALIAS`, `LAWYGO_UPLOAD_KEY_PASSWORD`, `LAWYGO_PLAY_SERVICE_ACCOUNT_JSON`.

코드만 포함된 이 ZIP에서는 워크플로를 실행하거나 실제 Play Console 앱을 생성하지 않았습니다. 연결된 Play Console 계정의 서비스 계정에 Publishing API 업로드 권한과 앱이 미리 등록되어 있어야 합니다.
