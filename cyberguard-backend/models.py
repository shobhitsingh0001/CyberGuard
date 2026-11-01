from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timezone
from database import Base


class RequestLog(Base):

    __tablename__ = "request_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        index=True,
    )

    ip = Column(String, index=True)
    method = Column(String)
    path = Column(String)
    query_string = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)

    risk_score = Column(Integer, default=0)
    risk_level = Column(String, default="Low")
    reasons = Column(String, nullable=True)
