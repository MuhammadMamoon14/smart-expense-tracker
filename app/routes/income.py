"""
income.py — Income CRUD + monthly summary.
"""

from datetime import datetime, timezone
from typing import Optional
from collections import defaultdict

from fastapi import APIRouter, HTTPException, Depends, Query

from app.core.file_db import read_json, write_json, generate_id, DB_FILES
from app.core.security import get_current_user
from app.schemas.income import IncomeCreate, IncomeUpdate, IncomeOut

router = APIRouter(prefix="/api/income", tags=["Income"])


def _user_income(user_id: str) -> list[dict]:
    return [i for i in read_json(DB_FILES["income"]) if i["user_id"] == user_id]


@router.post("", response_model=IncomeOut, status_code=201)
def create_income(payload: IncomeCreate, current_user: dict = Depends(get_current_user)):
    now = datetime.now(timezone.utc).isoformat()
    record = {
        "id": generate_id(),
        "user_id": current_user["id"],
        "title": payload.title,
        "amount": payload.amount,
        "source": payload.source.value,
        "date": payload.date,
        "note": payload.note,
        "recurring": payload.recurring,
        "created_at": now,
        "updated_at": now,
    }
    all_income = read_json(DB_FILES["income"])
    all_income.append(record)
    write_json(DB_FILES["income"], all_income)
    return record


@router.get("", response_model=list[IncomeOut])
def list_income(
    source: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    records = _user_income(current_user["id"])
    if source:
        records = [r for r in records if r["source"] == source]
    if date_from:
        records = [r for r in records if r["date"] >= date_from]
    if date_to:
        records = [r for r in records if r["date"] <= date_to]
    return sorted(records, key=lambda x: x["date"], reverse=True)


@router.get("/summary/monthly")
def monthly_summary(current_user: dict = Depends(get_current_user)):
    records = _user_income(current_user["id"])
    monthly: dict[str, float] = defaultdict(float)
    source_totals: dict[str, float] = defaultdict(float)

    for r in records:
        month = r["date"][:7]  # YYYY-MM
        monthly[month] += r["amount"]
        source_totals[r["source"]] += r["amount"]

    total = sum(monthly.values())
    return {
        "total_income": round(total, 2),
        "monthly_breakdown": {k: round(v, 2) for k, v in sorted(monthly.items())},
        "by_source": {k: round(v, 2) for k, v in source_totals.items()},
        "entry_count": len(records),
    }


@router.get("/{income_id}", response_model=IncomeOut)
def get_income(income_id: str, current_user: dict = Depends(get_current_user)):
    records = _user_income(current_user["id"])
    record = next((r for r in records if r["id"] == income_id), None)
    if not record:
        raise HTTPException(status_code=404, detail="Income record not found")
    return record


@router.put("/{income_id}", response_model=IncomeOut)
def update_income(income_id: str, payload: IncomeUpdate, current_user: dict = Depends(get_current_user)):
    all_income = read_json(DB_FILES["income"])
    idx = next((i for i, r in enumerate(all_income) if r["id"] == income_id and r["user_id"] == current_user["id"]), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Income record not found")

    update_data = payload.model_dump(exclude_none=True)
    if "source" in update_data and hasattr(update_data["source"], "value"):
        update_data["source"] = update_data["source"].value
    all_income[idx].update(update_data)
    all_income[idx]["updated_at"] = datetime.now(timezone.utc).isoformat()
    write_json(DB_FILES["income"], all_income)
    return all_income[idx]


@router.delete("/{income_id}", status_code=204)
def delete_income(income_id: str, current_user: dict = Depends(get_current_user)):
    all_income = read_json(DB_FILES["income"])
    new_list = [r for r in all_income if not (r["id"] == income_id and r["user_id"] == current_user["id"])]
    if len(new_list) == len(all_income):
        raise HTTPException(status_code=404, detail="Income record not found")
    write_json(DB_FILES["income"], new_list)
