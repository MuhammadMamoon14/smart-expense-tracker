"""
categories.py — Category management (global, shared by all users).
"""

from fastapi import APIRouter, HTTPException, Depends

from app.core.file_db import read_json, write_json, generate_id, DB_FILES
from app.core.security import get_current_user
from app.schemas.categories import CategoryCreate, CategoryUpdate, CategoryOut

router = APIRouter(prefix="/api/categories", tags=["Categories"])


@router.get("", response_model=list[CategoryOut])
def list_categories(current_user: dict = Depends(get_current_user)):
    return read_json(DB_FILES["categories"])


@router.post("", response_model=CategoryOut, status_code=201)
def create_category(payload: CategoryCreate, current_user: dict = Depends(get_current_user)):
    cats = read_json(DB_FILES["categories"])
    if any(c["name"].lower() == payload.name.lower() for c in cats):
        raise HTTPException(status_code=400, detail="Category already exists")
    new_cat = {
        "id": generate_id(),
        "name": payload.name,
        "icon": payload.icon or "📌",
        "budget_limit": payload.budget_limit,
    }
    cats.append(new_cat)
    write_json(DB_FILES["categories"], cats)
    return new_cat


@router.put("/{category_id}", response_model=CategoryOut)
def update_category(category_id: str, payload: CategoryUpdate, current_user: dict = Depends(get_current_user)):
    cats = read_json(DB_FILES["categories"])
    idx = next((i for i, c in enumerate(cats) if c["id"] == category_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Category not found")
    update_data = payload.model_dump(exclude_none=True)
    cats[idx].update(update_data)
    write_json(DB_FILES["categories"], cats)
    return cats[idx]


@router.delete("/{category_id}", status_code=204)
def delete_category(category_id: str, current_user: dict = Depends(get_current_user)):
    cats = read_json(DB_FILES["categories"])
    new_list = [c for c in cats if c["id"] != category_id]
    if len(new_list) == len(cats):
        raise HTTPException(status_code=404, detail="Category not found")
    write_json(DB_FILES["categories"], new_list)
