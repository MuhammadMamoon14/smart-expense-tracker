"""
savings.py — Savings goals CRUD + deposit endpoint.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends

from app.core.file_db import read_json, write_json, generate_id, DB_FILES
from app.core.security import get_current_user
from app.schemas.savings import SavingsCreate, SavingsUpdate, SavingsDeposit, SavingsOut

router = APIRouter(prefix="/api/savings", tags=["Savings"])


def _build_out(record: dict) -> dict:
    remaining = max(0.0, record["target_amount"] - record["current_amount"])
    progress_pct = (
        round((record["current_amount"] / record["target_amount"]) * 100, 2)
        if record["target_amount"] > 0 else 0.0
    )
    return {
        **record,
        "remaining": round(remaining, 2),
        "progress_pct": min(progress_pct, 100.0),
        "is_completed": record["current_amount"] >= record["target_amount"],
    }


def _user_savings(user_id: str) -> list[dict]:
    return [s for s in read_json(DB_FILES["savings"]) if s["user_id"] == user_id]


@router.post("", response_model=SavingsOut, status_code=201)
def create_goal(payload: SavingsCreate, current_user: dict = Depends(get_current_user)):
    now = datetime.now(timezone.utc).isoformat()
    record = {
        "id": generate_id(),
        "user_id": current_user["id"],
        "goal_name": payload.goal_name,
        "target_amount": payload.target_amount,
        "current_amount": payload.current_amount,
        "target_date": payload.target_date,
        "note": payload.note,
        "created_at": now,
        "updated_at": now,
    }
    all_savings = read_json(DB_FILES["savings"])
    all_savings.append(record)
    write_json(DB_FILES["savings"], all_savings)
    return _build_out(record)


@router.get("", response_model=list[SavingsOut])
def list_goals(current_user: dict = Depends(get_current_user)):
    return [_build_out(s) for s in _user_savings(current_user["id"])]


@router.get("/{goal_id}", response_model=SavingsOut)
def get_goal(goal_id: str, current_user: dict = Depends(get_current_user)):
    goals = _user_savings(current_user["id"])
    goal = next((g for g in goals if g["id"] == goal_id), None)
    if not goal:
        raise HTTPException(status_code=404, detail="Savings goal not found")
    return _build_out(goal)


@router.put("/{goal_id}", response_model=SavingsOut)
def update_goal(goal_id: str, payload: SavingsUpdate, current_user: dict = Depends(get_current_user)):
    all_savings = read_json(DB_FILES["savings"])
    idx = next((i for i, g in enumerate(all_savings) if g["id"] == goal_id and g["user_id"] == current_user["id"]), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Savings goal not found")

    update_data = payload.model_dump(exclude_none=True)
    all_savings[idx].update(update_data)
    all_savings[idx]["updated_at"] = datetime.now(timezone.utc).isoformat()
    write_json(DB_FILES["savings"], all_savings)
    return _build_out(all_savings[idx])


@router.post("/{goal_id}/deposit", response_model=SavingsOut)
def deposit(goal_id: str, payload: SavingsDeposit, current_user: dict = Depends(get_current_user)):
    all_savings = read_json(DB_FILES["savings"])
    idx = next((i for i, g in enumerate(all_savings) if g["id"] == goal_id and g["user_id"] == current_user["id"]), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Savings goal not found")

    all_savings[idx]["current_amount"] = round(all_savings[idx]["current_amount"] + payload.amount, 2)
    all_savings[idx]["updated_at"] = datetime.now(timezone.utc).isoformat()
    write_json(DB_FILES["savings"], all_savings)
    return _build_out(all_savings[idx])


@router.delete("/{goal_id}", status_code=204)
def delete_goal(goal_id: str, current_user: dict = Depends(get_current_user)):
    all_savings = read_json(DB_FILES["savings"])
    new_list = [g for g in all_savings if not (g["id"] == goal_id and g["user_id"] == current_user["id"])]
    if len(new_list) == len(all_savings):
        raise HTTPException(status_code=404, detail="Savings goal not found")
    write_json(DB_FILES["savings"], new_list)
