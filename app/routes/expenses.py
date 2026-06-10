"""
expenses.py — Full CRUD for expenses with filtering & CSV export.
"""

import csv
import io
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse

from app.core.file_db import read_json, write_json, generate_id, DB_FILES
from app.core.security import get_current_user
from app.schemas.expense import ExpenseCreate, ExpenseUpdate, ExpenseOut

router = APIRouter(prefix="/api/expenses", tags=["Expenses"])


def _user_expenses(user_id: str) -> list[dict]:
    return [e for e in read_json(DB_FILES["expenses"]) if e["user_id"] == user_id]


@router.post("", response_model=ExpenseOut, status_code=201)
def create_expense(payload: ExpenseCreate, current_user: dict = Depends(get_current_user)):
    now = datetime.now(timezone.utc).isoformat()
    expense = {
        "id": generate_id(),
        "user_id": current_user["id"],
        "title": payload.title,
        "amount": payload.amount,
        "category": payload.category,
        "date": payload.date,
        "note": payload.note,
        "tags": payload.tags,
        "created_at": now,
        "updated_at": now,
    }
    all_expenses = read_json(DB_FILES["expenses"])
    all_expenses.append(expense)
    write_json(DB_FILES["expenses"], all_expenses)
    return expense


@router.get("", response_model=list[ExpenseOut])
def list_expenses(
    category: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    min_amount: Optional[float] = Query(None),
    max_amount: Optional[float] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    expenses = _user_expenses(current_user["id"])

    if category:
        expenses = [e for e in expenses if e["category"].lower() == category.lower()]
    if date_from:
        expenses = [e for e in expenses if e["date"] >= date_from]
    if date_to:
        expenses = [e for e in expenses if e["date"] <= date_to]
    if search:
        s = search.lower()
        expenses = [e for e in expenses if s in e["title"].lower() or s in (e.get("note") or "").lower()]
    if min_amount is not None:
        expenses = [e for e in expenses if e["amount"] >= min_amount]
    if max_amount is not None:
        expenses = [e for e in expenses if e["amount"] <= max_amount]

    return sorted(expenses, key=lambda x: x["date"], reverse=True)


@router.get("/export/csv")
def export_csv(current_user: dict = Depends(get_current_user)):
    expenses = _user_expenses(current_user["id"])
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["id", "title", "amount", "category", "date", "note", "tags", "created_at"],
        extrasaction="ignore",
    )
    writer.writeheader()
    for e in expenses:
        row = dict(e)
        row["tags"] = ", ".join(row.get("tags", []))
        writer.writerow(row)
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=expenses.csv"},
    )


@router.get("/{expense_id}", response_model=ExpenseOut)
def get_expense(expense_id: str, current_user: dict = Depends(get_current_user)):
    expenses = _user_expenses(current_user["id"])
    expense = next((e for e in expenses if e["id"] == expense_id), None)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


@router.put("/{expense_id}", response_model=ExpenseOut)
def update_expense(expense_id: str, payload: ExpenseUpdate, current_user: dict = Depends(get_current_user)):
    all_expenses = read_json(DB_FILES["expenses"])
    idx = next((i for i, e in enumerate(all_expenses) if e["id"] == expense_id and e["user_id"] == current_user["id"]), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Expense not found")

    update_data = payload.model_dump(exclude_none=True)
    all_expenses[idx].update(update_data)
    all_expenses[idx]["updated_at"] = datetime.now(timezone.utc).isoformat()
    write_json(DB_FILES["expenses"], all_expenses)
    return all_expenses[idx]


@router.delete("/{expense_id}", status_code=204)
def delete_expense(expense_id: str, current_user: dict = Depends(get_current_user)):
    all_expenses = read_json(DB_FILES["expenses"])
    new_list = [e for e in all_expenses if not (e["id"] == expense_id and e["user_id"] == current_user["id"])]
    if len(new_list) == len(all_expenses):
        raise HTTPException(status_code=404, detail="Expense not found")
    write_json(DB_FILES["expenses"], new_list)
