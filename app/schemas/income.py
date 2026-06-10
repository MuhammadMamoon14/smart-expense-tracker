from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class IncomeSource(str, Enum):
    salary = "salary"
    freelance = "freelance"
    business = "business"
    investment = "investment"
    rental = "rental"
    other = "other"


class IncomeCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    amount: float = Field(..., gt=0)
    source: IncomeSource
    date: str = Field(..., description="ISO date string YYYY-MM-DD")
    note: Optional[str] = None
    recurring: bool = False


class IncomeUpdate(BaseModel):
    title: Optional[str] = None
    amount: Optional[float] = Field(None, gt=0)
    source: Optional[IncomeSource] = None
    date: Optional[str] = None
    note: Optional[str] = None
    recurring: Optional[bool] = None


class IncomeOut(BaseModel):
    id: str
    user_id: str
    title: str
    amount: float
    source: str
    date: str
    note: Optional[str]
    recurring: bool
    created_at: str
    updated_at: str
