@echo off
setlocal
cd /d "%~dp0"
where java >nul 2>&1 || (echo [ERROR] JDK 17 or newer required & exit /b 1)
where gradle >nul 2>&1 || (echo [ERROR] Gradle 8.13 is not installed. Open project in Android Studio to sync Gradle. & exit /b 2)
if "%ANDROID_HOME%"=="" (echo [ERROR] Set ANDROID_HOME to Android SDK path & exit /b 3)
call gradle --no-daemon :app:testSuiteDebugUnitTest :app:assembleDebug :app:bundleRelease || exit /b 4
echo APK: app\build\outputs\apk
 echo AAB: app\build\outputs\bundle (unsigned unless configured)
