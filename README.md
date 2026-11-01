# BharatStore + CyberGuard — Full Project

Do alag services hain, dono alag ports pe chalengi:

| Project             | Folder                  | Port | Run command                                                          |
|---------------------|-------------------------|------|----------------------------------------------------------------------|
| BharatStore backend | `ecommerce-backend/`    | 8000 | `.venv\\Scripts\\python.exe -m uvicorn main:app --reload --port 8000` |
| CyberGuard backend  | `cyberguard-backend/`   | 9000 | `.venv\\Scripts\\python.exe -m uvicorn main:app --reload --port 9000` |
| BharatStore frontend| `ecommerce-frontend/`   | 5500 | `py -3.13 -m http.server 5500`                                      |
| CyberGuard dashboard| `cyberguard-dashboard/` | 5600 | `py -3.13 -m http.server 5600`                                      |

## Setup — step by step

### 1. BharatStore backend
```bash
cd ecommerce-backend
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```
Ye `http://127.0.0.1:8000` pe chalega. Products daalne ke liye (ek baar):
```bash
.\.venv\Scripts\python.exe seeddata.py
```

### 2. CyberGuard backend (optional, monitoring ke liye)
Naya terminal:
```bash
cd cyberguard-backend
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 9000
```
Ye `http://127.0.0.1:9000` pe chalega. Agar ye chalta nahi rehta,
BharatStore chalna band nahi hoga — logging chup-chaap skip ho jayegi
(`cyberguard_logger.py` isko already handle karta hai).

### 3. BharatStore frontend
Naya terminal:
```bash
cd ecommerce-frontend
py -3.13 -m http.server 5500 --bind 127.0.0.1
```
Browser me kholo:
- `http://127.0.0.1:5500/Home.html` — store
- `http://127.0.0.1:5500/login.html` — sign in
- `http://127.0.0.1:5500/signup.html` — create account

### 4. CyberGuard dashboard (optional)
Naya terminal:
```bash
cd cyberguard-dashboard
py -3.13 -m http.server 5600 --bind 127.0.0.1
```
Browser me kholo: `http://127.0.0.1:5600/dashboard.html`

## Kya fix kiya gaya tha

- `models.py` (ecommerce) me `UserSession` aur `LoginActivity` tables
  missing the — `auth.py` inhe use karta tha, isliye backend crash ho
  jata. Dono add kar diye.
- `login.html` / `signup.html` port `8001` use kar rahe the, lekin
  BharatStore backend `8000` pe chalta hai (`script.js` isi port ko
  use karta hai) — dono files me port `8000` kar diya.
- `cyberguard_logger.py` ka port CyberGuard ke actual port (`9000`)
  se match karaya, taaki BharatStore (`8000`) aur CyberGuard (`9000`)
  ek doosre se clash na karein.
- CyberGuard ka `main.py` pehle diya hi nahi gaya tha (sirf models,
  schemas, detector the) — naya likh diya: `POST /api/log` (jahan
  BharatStore requests bhejta hai), `GET /api/logs` aur `GET /api/stats`
  (dashboard ke liye).
- CyberGuard ka `dashboard.html` + `dashboard.js` bhi naye bana diye
  (stat cards + recent requests table, auto-refresh har 10 second).

## Login/Signup ka data kaha jaata hai

`ecommerce-backend/store.db` me — `users` table me. Password kabhi
plain text me save nahi hota (PBKDF2-SHA256 hash + random salt).
Har login attempt (success/fail dono) `login_activities` table me
record hoti hai.

# agar serveer error de pichla band na kiya gya ho to
powershell

# check krne ke liye
Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Get-Process -Id $_.OwningProcess }

# band krne ke liye
Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }

# same as 9000 port for cyberguard
Get-NetTCPConnection -LocalPort 9000 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Get-Process -Id $_.OwningProcess }

Get-NetTCPConnection -LocalPort 9000 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
