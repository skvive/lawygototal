"""Foreground Windows/Linux launcher that waits for HTTP readiness before opening the browser."""
from __future__ import annotations
import os,sys,time,socket,subprocess,urllib.request,webbrowser
HOST='127.0.0.1';PORT=8018
URL=f'http://{HOST}:{PORT}/hub'

def port_open():
    with socket.socket() as s:
        s.settimeout(0.3)
        return s.connect_ex((HOST,PORT))==0

def main():
    if port_open():
        print(f'[LAWYGO] Port {PORT} is already used. Stop the existing service first.',file=sys.stderr)
        return 2
    args=[sys.executable,'-m','uvicorn','app:app','--host',HOST,'--port',str(PORT),'--log-level','info']
    process=subprocess.Popen(args)
    try:
        for _ in range(100):
            if process.poll() is not None:
                print('[LAWYGO] Server ended before HTTP readiness.',file=sys.stderr)
                return process.returncode or 1
            try:
                with urllib.request.urlopen(f'http://{HOST}:{PORT}/api/health',timeout=0.4) as r:
                    if r.status==200:
                        print('[LAWYGO] HTTP health OK:',URL)
                        webbrowser.open_new_tab(URL)
                        return process.wait()
            except (OSError,TimeoutError):
                time.sleep(0.2)
        print('[LAWYGO] Server readiness deadline exceeded.',file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('\n[LAWYGO] User requested shutdown.')
        return 0
    finally:
        if process.poll() is None:
            process.terminate()
            try: process.wait(timeout=6)
            except subprocess.TimeoutExpired:process.kill()
if __name__=='__main__':raise SystemExit(main())
