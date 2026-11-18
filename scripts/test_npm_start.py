import subprocess
import time
import urllib.request
import os
import signal

print("[*] Iniciando 'npm run start:dev'...")
proc = subprocess.Popen(
    ["npm.cmd", "run", "start:dev"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    shell=True
)

try:
    time.sleep(4)
    # Probar endpoint raiz
    req = urllib.request.Request("http://127.0.0.1:8000/")
    with urllib.request.urlopen(req, timeout=5) as res:
        print(f"[OK] GET http://localhost:8000/ -> Status {res.status}")
        print(f"     Body: {res.read().decode('utf-8')[:100]}...")

    # Probar endpoint docs
    req_docs = urllib.request.Request("http://127.0.0.1:8000/docs")
    with urllib.request.urlopen(req_docs, timeout=5) as res_docs:
        print(f"[OK] GET http://localhost:8000/docs -> Status {res_docs.status}")

    print("\n[ÉXITO] 'npm run start:dev' arrancó FastAPI y respondió en todos los endpoints requeridos.")
finally:
    # Terminar proceso y subprocesos
    subprocess.call(["taskkill", "/F", "/T", "/PID", str(proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
