# Windows 실행 안내

1. Python 3.11 이상 설치, 설치 중 `Add Python to PATH` 선택.
2. `LAWYGO_ENGINE/RUN_WINDOWS.bat` 더블 클릭.
3. 실행기가 `requirements.txt`를 설치하고 최초 관리자 계정을 만들도록 안내.
4. 브라우저에서 `http://127.0.0.1:8018/dashboard` 접속.
5. Google 로그인과 실제 외부 채널 동기화를 사용하려면 `LAWYGO_ENGINE/.env`에 Google OAuth 정보·Fernet 암호화 키를 넣고 서버를 재시작.
6. Google API에 대한 권한이 확인되면 관리자 메뉴에서 Blogger·YouTube 계정 연결.
7. 자동 수집을 원하는 경우 Windows 작업 스케줄러에서 `RUN_SYNC_ONCE_WINDOWS.bat`를 **6시간 간격**으로 실행.
8. 운영 서버 HTTPS 배포 전 `LAWYGO_SECURE_COOKIES=true` 활성화.

**주의:** `LAWYGO_ENGINE/.env`에는 실제 비밀키가 들어가므로 ZIP을 재압축해 다른 사람에게 전달하지 마세요. 이 패키지에는 비밀키가 빈 `.env.example`만 있습니다.
