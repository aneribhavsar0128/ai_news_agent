from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Date
from datetime import datetime
from app.database import Base

class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    source = Column(String)
    url = Column(Text, unique=True, index=True)
    summary = Column(Text)
    category = Column(String, default="General")
    importance_score = Column(Integer, default=0)
    # AI Insights
    why_it_matters = Column(Text)
    who_is_affected = Column(Text)
    future_impact = Column(Text)
    historical_context = Column(Text)
    trend_analysis = Column(Text)
    email_reason = Column(Text)
    tags = Column(Text)
    estimated_read_time = Column(String)
    embedding_id = Column(String)
    email_reason = Column(Text)
    should_email = Column(Boolean, default=False)
    sent_email = Column(Boolean, default=False)
    processed_at = Column(DateTime)
    published_at = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class DailyBrief(Base): 
    __tablename__ = "daily_briefs"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, nullable=False)
    html = Column(Text, nullable=False)
    json = Column(Text, nullable=False)
    articles_used = Column(Integer, default=0)
    created_at = Column(DateTime,default=datetime.utcnow)

class Subscriber(Base):
    __tablename__ = "subscribers"

    id = Column(Integer,primary_key=True,index=True,)
    name = Column(String(100),nullable=True,)
    email = Column(String(255),unique=True,index=True,nullable=False,)
    is_active = Column(Boolean,default=True,nullable=False,)
    created_at = Column(DateTime,default=datetime.utcnow,nullable=False,)
    unsubscribed_at = Column(DateTime,nullable=True,)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer,primary_key=True,index=True,)
    name = Column(String(100),nullable=False,)
    email = Column(String(255),unique=True,index=True,nullable=False,)
    password_hash = Column(String(500),nullable=False,)
    is_active = Column(Boolean,default=True,nullable=False,)
    is_admin = Column(Boolean,default=False,nullable=False,)
    created_at = Column(DateTime,default=datetime.utcnow,nullable=False,)
    updated_at = Column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow,nullable=False,)


