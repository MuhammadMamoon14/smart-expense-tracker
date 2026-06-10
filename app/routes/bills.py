"""
bills.py — Bill management with paid/unpaid tracking and due dates.
"""

from datetime import datetime, timezone, date as date_type
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query

from app.core.file_db import read_json, write_json, generate_id, DB_FILES
from app.core.security import get_current_user
from app.schemas.bills import BillCreate, BillUpdate, BillOut

router = APIRouter(prefix="/api/bills", tags=["Bills"])


def _user_bills(user_id: str) -> list[dict]:
    return [b for b in read_json(DB_FILES["bills"]) if b["user_id"] == user_id]


@router.post("", response_model=BillOut, status_code=201)
def create_bill(payload: BillCreate, current_user: dict = Depends(get_current_user)):
    now = datetime.now(timezone.utc).isoformat()
    record = {
        "id": generate_id(),
        "user_id": current_user["id"],
        "title": payload.title,
        "amount": payload.amount,
        "due_date": payload.due_date,
        "category": payload.category,
        "frequency": payload.frequency.value,
        "note": payload.note,
        "is_paid": False,
        "paid_date": None,
        "created_at": now,
        "updated_at": now,
    }
    all_bills = read_json(DB_FILES["bills"])
    all_bills.append(record)
    write_json(DB_FILES["bills"], all_bills)
    return record


@router.get("", response_model=list[BillOut])
def list_bills(
    is_paid: Optional[bool] = Query(None),
    overdue: Optional[bool] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    bills = _user_bills(current_user["id"])
    today = date_type.today().isoformat()

    if is_paid is not None:
        bills = [b for b in bills if b["is_paid"] == is_paid]
    if overdue is True:
        bills = [b for b in bills if not b["is_paid"] and b["due_date"] < today]

    return sorted(bills, key=lambda x: x["due_date"])


@router.get("/overdue", response_model=list[BillOut])
def overdue_bills(current_user: dict = Depends(get_current_user)):
    today = date_type.today().isoformat()
    bills = _user_bills(current_user["id"])
    return [b for b in bills if not b["is_paid"] and b["due_date"] < today]


@router.get("/{bill_id}", response_model=BillOut)
def get_bill(bill_id: str, current_user: dict = Depends(get_current_user)):
    bills = _user_bills(current_user["id"])
    bill = next((b for b in bills if b["id"] == bill_id), None)
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    return bill


@router.put("/{bill_id}", response_model=BillOut)
def update_bill(bill_id: str, payload: BillUpdate, current_user: dict = Depends(get_current_user)):
    all_bills = read_json(DB_FILES["bills"])
    idx = next((i for i, b in enumerate(all_bills) if b["id"] == bill_id and b["user_id"] == current_user["id"]), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Bill not found")

    update_data = payload.model_dump(exclude_none=True)
    if "frequency" in update_data and hasattr(update_data["frequency"], "value"):
        update_data["frequency"] = update_data["frequency"].value
    all_bills[idx].update(update_data)
    all_bills[idx]["updated_at"] = datetime.now(timezone.utc).isoformat()
    write_json(DB_FILES["bills"], all_bills)
    return all_bills[idx]


@router.post("/{bill_id}/mark-paid", response_model=BillOut)
def mark_paid(bill_id: str, current_user: dict = Depends(get_current_user)):
    all_bills = read_json(DB_FILES["bills"])
    idx = next((i for i, b in enumerate(all_bills) if b["id"] == bill_id and b["user_id"] == current_user["id"]), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Bill not found")

    all_bills[idx]["is_paid"] = True
    all_bills[idx]["paid_date"] = date_type.today().isoformat()
    all_bills[idx]["updated_at"] = datetime.now(timezone.utc).isoformat()
    write_json(DB_FILES["bills"], all_bills)
    return all_bills[idx]


@router.post("/{bill_id}/mark-unpaid", response_model=BillOut)
def mark_unpaid(bill_id: str, current_user: dict = Depends(get_current_user)):
    all_bills = read_json(DB_FILES["bills"])
    idx = next((i for i, b in enumerate(all_bills) if b["id"] == bill_id and b["user_id"] == current_user["id"]), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Bill not found")

    all_bills[idx]["is_paid"] = False
    all_bills[idx]["paid_date"] = None
    all_bills[idx]["updated_at"] = datetime.now(timezone.utc).isoformat()
    write_json(DB_FILES["bills"], all_bills)
    return all_bills[idx]


@router.delete("/{bill_id}", status_code=204)
def delete_bill(bill_id: str, current_user: dict = Depends(get_current_user)):
    all_bills = read_json(DB_FILES["bills"])
    new_list = [b for b in all_bills if not (b["id"] == bill_id and b["user_id"] == current_user["id"])]
    if len(new_list) == len(all_bills):
        raise HTTPException(status_code=404, detail="Bill not found")
    write_json(DB_FILES["bills"], new_list)
