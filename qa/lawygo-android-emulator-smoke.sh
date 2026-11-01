#!/usr/bin/env bash
# Emulated LAWYGO UI QA; always run as ONE command inside android-emulator-runner.
set -Eeuo pipefail
APK="android_native/LAWYGO_ANDROID_NATIVE_20261031/app/build/outputs/apk/suite/debug/app-suite-debug.apk"
PKG="site.lexid.lawygo"
mkdir -p lawygo-emulator-screens
collect_diagnostics() {
  adb logcat -d -v brief -t 3000 > lawygo-emulator-logcat.txt 2>&1 || true
  adb shell dumpsys activity activities > lawygo-emulator-activity.txt 2>&1 || true
  adb shell pm list packages > lawygo-emulator-packages.txt 2>&1 || true
  adb exec-out screencap -p > lawygo-emulator-last.png 2>/dev/null || true
}
trap collect_diagnostics EXIT
echo "=== Emulator / APK ==="
adb wait-for-device
adb devices -l
adb shell getprop sys.boot_completed
test -s "$APK"
adb install -r "$APK"
adb shell pm path "$PKG" || true
adb shell pm list packages | grep -i lawygo || true
echo "=== Launch LAWYGO ==="
adb shell am force-stop "$PKG" || true
adb shell am start -W -n "$PKG/.MainActivity" 2>&1 | tee lawygo-emulator-launch.txt
sleep 10
adb exec-out screencap -p > lawygo-emulator-first-launch.png
test -s lawygo-emulator-first-launch.png
PID="$(adb shell pidof "$PKG" | tr -d '\r' || true)"
echo "LAWYGO app PID: $PID"
if [[ -z "$PID" ]]; then echo "FAIL: app process exited on first launch" >&2; exit 1; fi
SIZE="$(adb shell wm size | tr -d '\r' | awk '/Physical size:/ {print $3; exit}')"
WIDTH="$(echo "$SIZE" | cut -d x -f1)"
HEIGHT="$(echo "$SIZE" | cut -d x -f2)"
if [[ ! "$WIDTH" =~ ^[0-9]+$ || ! "$HEIGHT" =~ ^[0-9]+$ ]]; then echo "FAIL: screen size $SIZE"; exit 1; fi
NAV_Y=$((HEIGHT * 93 / 100))
TABS=(home journal pan wiki note)
for idx in 0 1 2 3 4; do
  TAB="${TABS[$idx]}"
  TAP_X=$((WIDTH * (10 + 20 * idx) / 100))
  adb shell input tap "$TAP_X" "$NAV_Y"
  sleep 3
  adb exec-out screencap -p > "lawygo-emulator-screens/${TAB}.png"
  test -s "lawygo-emulator-screens/${TAB}.png"
  echo "Captured $TAB"
done
adb shell input tap "$((WIDTH * 94 / 100))" "$((HEIGHT * 5 / 100))"
sleep 2
adb exec-out screencap -p > lawygo-emulator-screens/settings.png
test -s lawygo-emulator-screens/settings.png
PID="$(adb shell pidof "$PKG" | tr -d '\r' || true)"
test -n "$PID"
echo "PASS: emulator installation, first launch, app PID and 6 UI screenshots."
