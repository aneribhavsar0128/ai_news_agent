from pydantic import BaseModel

class ProcessedNews(BaseModel):
    category: str
    summary: str
    importance_score: int
    why_it_matters: str
    who_is_affected: str
    future_impact: str
    should_email: bool