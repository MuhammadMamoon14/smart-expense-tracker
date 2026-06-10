from typing import Optional
from datetime import date
from pydantic import BaseModel, Field


class ExpenseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    amount: float = Field(..., gt=0)
    category: str = Field(..., min_length=1)
    date: str = Field(..., description="ISO date string YYYY-MM-DD")
    note: Optional[str] = None
    tags: list[str] = []


class ExpenseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    amount: Optional[float] = Field(None, gt=0)
    category: Optional[str] = None
    date: Optional[str] = None
    note: Optional[str] = None
    tags: Optional[list[str]] = None


class ExpenseOut(BaseModel):
    id: str
    user_id: str
    title: str
    amount: float
    category: str
    date: str
    note: Optional[str]
    tags: list[str]
    created_at: str
    updated_at: str


class ExpenseFilter(BaseModel):
    category: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    search: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
