"""
CyberGuard - lightweight request risk-monitoring service.

Ye service BharatStore (ya kisi bhi connected app) se aa rahe har request
ka metadata receive karta hai (cyberguard_logger.py wahan se bhejta hai),
usko detector.py se score karta hai, aur database me save kar deta hai.
Dashboard (cyberguard-dashboard/) isi API se data padh kar risk dashboard
dikhata hai.

Run: .venv\\Scripts\\python.exe -m uvicorn main:app --reload --port 9000
"""

from fastapi import FastAPI, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from database import engine, Base, get_db
from models import RequestLog
from schemas import RequestLogCreate, RequestLogResponse, StatsResponse, TopIP
from detector import analyze_request

app = FastAPI(title="CyberGuard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # dashboard aur BharatStore dono se access chahiye
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


@app.get("/")
def home():
    return {"message": "CyberGuard risk-monitoring API"}


# Ye endpoint BharatStore (cyberguard_logger.py) se call hota hai
@app.post("/api/log", response_model=RequestLogResponse)
def log_request(entry: RequestLogCreate, db: Session = Depends(get_db)):
    score, level, reasons = analyze_request(
        db=db,
        ip=entry.ip,
        method=entry.method,
        path=entry.path,
        query_string=entry.query_string or "",
        user_agent=entry.user_agent or "",
        sql_injection_suspected=entry.sql_injection_suspected,
    )

    new_log = RequestLog(
        ip=entry.ip,
        method=entry.method,
        path=entry.path,
        query_string=entry.query_string,
        user_agent=entry.user_agent,
        risk_score=score,
        risk_level=level,
        reasons=", ".join(reasons) if reasons else None,
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)

    return new_log


# Dashboard ke liye - recent logs, newest first
@app.get("/api/logs", response_model=List[RequestLogResponse])
def get_logs(limit: int = Query(default=100, ge=0), db: Session = Depends(get_db)):
    return (
        db.query(RequestLog)
        .order_by(RequestLog.timestamp.desc())
        .limit(limit)
        .all()
    )


# Dashboard ke liye - summary stats + top offending IPs
@app.get("/api/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    total = db.query(RequestLog).count()
    high = db.query(RequestLog).filter(RequestLog.risk_level == "High").count()
    medium = db.query(RequestLog).filter(RequestLog.risk_level == "Medium").count()
    low = db.query(RequestLog).filter(RequestLog.risk_level == "Low").count()

    top_ip_rows = (
        db.query(
            RequestLog.ip,
            func.count(RequestLog.id).label("count"),
            func.max(RequestLog.risk_score).label("max_score"),
        )
        .group_by(RequestLog.ip)
        .order_by(func.count(RequestLog.id).desc())
        .limit(10)
        .all()
    )

    top_ips = [TopIP(ip=row.ip, count=row.count, max_score=row.max_score) for row in top_ip_rows]

    return StatsResponse(
        total_requests=total,
        high_risk_count=high,
        medium_risk_count=medium,
        low_risk_count=low,
        top_ips=top_ips,
    )
