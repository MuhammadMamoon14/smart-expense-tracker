from typing import Optional
from pydantic import BaseModel, Field


class SavingsCreate(BaseModel):
    goal_name: str = Field(..., min_length=1, max_length=200)
    target_amount: float = Field(..., gt=0)
    current_amount: float = Field(default=0.0, ge=0)
    target_date: Optional[str] = None
    note: Optional[str] = None


class SavingsUpdate(BaseModel):
    goal_name: Optional[str] = None
    target_amount: Optional[float] = Field(None, gt=0)
    current_amount: Optional[float] = Field(None, ge=0)
    target_date: Optional[str] = None
    note: Optional[str] = None


class SavingsDeposit(BaseModel):
    amount: float = Field(..., gt=0)


class SavingsOut(BaseModel):
    id: str
    user_id: str
    goal_name: str
    target_amount: float
    current_amount: float
    remaining: float
    progress_pct: float
    target_date: Optional[str]
    note: Optional[str]
    is_completed: bool
    created_at: str
    updated_at: str
