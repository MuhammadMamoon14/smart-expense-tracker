from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class BillFrequency(str, Enum):
    once = "once"
    monthly = "monthly"
    quarterly = "quarterly"
    yearly = "yearly"


class BillCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    amount: float = Field(..., gt=0)
    due_date: str = Field(..., description="ISO date string YYYY-MM-DD")
    category: str = Field(default="Utilities")
    frequency: BillFrequency = BillFrequency.monthly
    note: Optional[str] = None


class BillUpdate(BaseModel):
    title: Optional[str] = None
    amount: Optional[float] = Field(None, gt=0)
    due_date: Optional[str] = None
    category: Optional[str] = None
    frequency: Optional[BillFrequency] = None
    note: Optional[str] = None


class BillOut(BaseModel):
    id: str
    user_id: str
    title: str
    amount: float
    due_date: str
    category: str
    frequency: str
    note: Optional[str]
    is_paid: bool
    paid_date: Optional[str]
    created_at: str
    updated_at: str
