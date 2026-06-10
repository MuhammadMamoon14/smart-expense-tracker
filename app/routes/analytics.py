"""
analytics.py — Analytics & dashboard endpoints.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.file_db import read_json, DB_FILES
from app.core.security import get_current_user
from app.services import analytics_service as svc

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


def _expenses(uid: str, date_from: Optional[str] = None, date_to: Optional[str] = None) -> list[dict]:
    all_exp = [e for e in read_json(DB_FILES["expenses"]) if e["user_id"] == uid]
    if date_from:
        all_exp = [e for e in all_exp if e["date"] >= date_from]
    if date_to:
        all_exp = [e for e in all_exp if e["date"] <= date_to]
    return all_exp


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@router.get("/dashboard")
def dashboard(current_user: dict = Depends(get_current_user)):
    uid = current_user["id"]
    expenses = [e for e in read_json(DB_FILES["expenses"]) if e["user_id"] == uid]
    income   = [r for r in read_json(DB_FILES["income"])   if r["user_id"] == uid]
    savings  = [s for s in read_json(DB_FILES["savings"])  if s["user_id"] == uid]
    bills    = [b for b in read_json(DB_FILES["bills"])    if b["user_id"] == uid]
    return svc.dashboard_summary(expenses, income, savings, bills)


# ---------------------------------------------------------------------------
# Expense statistics
# ---------------------------------------------------------------------------

@router.get("/expenses/stats")
def expense_stats(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    expenses = _expenses(current_user["id"], date_from, date_to)
    return svc.compute_expense_stats(expenses)


@router.get("/expenses/monthly")
def expense_monthly(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    expenses = _expenses(current_user["id"], date_from, date_to)
    return svc.monthly_breakdown(expenses)


@router.get("/expenses/by-category")
def expense_by_category(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    expenses = _expenses(current_user["id"], date_from, date_to)
    return svc.category_breakdown(expenses)


# ---------------------------------------------------------------------------
# Budget alerts
# ---------------------------------------------------------------------------

@router.get("/budget-alerts")
def budget_alerts(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    expenses = _expenses(current_user["id"], date_from, date_to)
    categories = read_json(DB_FILES["categories"])
    return svc.budget_alerts(expenses, categories)


# ---------------------------------------------------------------------------
# Monthly summary (combined income + expense)
# ---------------------------------------------------------------------------

@router.get("/summary/monthly")
def monthly_summary(
    year: Optional[int] = Query(None, description="Filter by year, e.g. 2024"),
    current_user: dict = Depends(get_current_user),
):
    uid = current_user["id"]
    expenses = [e for e in read_json(DB_FILES["expenses"]) if e["user_id"] == uid]
    income   = [r for r in read_json(DB_FILES["income"])   if r["user_id"] == uid]

    if year:
        prefix = str(year)
        expenses = [e for e in expenses if e["date"].startswith(prefix)]
        income   = [r for r in income   if r["date"].startswith(prefix)]

    exp_monthly = svc.monthly_breakdown(expenses)
    inc_monthly = svc.monthly_breakdown(income)

    months = sorted(set(list(exp_monthly.keys()) + list(inc_monthly.keys())))
    breakdown = []
    for m in months:
        exp = exp_monthly.get(m, 0.0)
        inc = inc_monthly.get(m, 0.0)
        breakdown.append({
            "month": m,
            "income": inc,
            "expenses": exp,
            "net": round(inc - exp, 2),
        })

    return {"year": year, "monthly": breakdown}
