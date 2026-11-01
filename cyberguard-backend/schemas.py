from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class RequestLogCreate(BaseModel):
    ip: str
    method: str
    path: str
    query_string: Optional[str] = ""
    user_agent: Optional[str] = ""
    sql_injection_suspected: bool = False


class RequestLogResponse(BaseModel):
    id: int
    timestamp: datetime
    ip: str
    method: str
    path: str
    query_string: Optional[str] = None
    user_agent: Optional[str] = None
    risk_score: int
    risk_level: str
    reasons: Optional[str] = None

    class Config:
        from_attributes = True


class TopIP(BaseModel):
    ip: str
    count: int
    max_score: int


class StatsResponse(BaseModel):
    total_requests: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    top_ips: List[TopIP]
