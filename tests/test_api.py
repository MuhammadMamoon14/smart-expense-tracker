"""
Integration tests using FastAPI TestClient with a temp data directory.
"""

import os
import tempfile
import shutil
import pytest

os.environ["DATA_DIR"] = tempfile.mkdtemp()

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def auth_headers():
    # Register
    client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "full_name": "Test User",
    })
    # Login
    resp = client.post("/api/auth/login", data={"username": "testuser", "password": "testpass123"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def test_register_duplicate():
    client.post("/api/auth/register", json={
        "username": "dup_user", "email": "dup@example.com",
        "password": "pass123", "full_name": "Dup User",
    })
    resp = client.post("/api/auth/register", json={
        "username": "dup_user", "email": "dup@example.com",
        "password": "pass123", "full_name": "Dup User",
    })
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Expenses
# ---------------------------------------------------------------------------

def test_create_and_list_expense(auth_headers):
    resp = client.post("/api/expenses", headers=auth_headers, json={
        "title": "Lunch", "amount": 15.5, "category": "Food & Dining",
        "date": "2024-06-01", "note": "office lunch",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Lunch"
    assert data["amount"] == 15.5

    list_resp = client.get("/api/expenses", headers=auth_headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1


def test_update_expense(auth_headers):
    create = client.post("/api/expenses", headers=auth_headers, json={
        "title": "Coffee", "amount": 5.0, "category": "Food & Dining", "date": "2024-06-02",
    })
    exp_id = create.json()["id"]
    update = client.put(f"/api/expenses/{exp_id}", headers=auth_headers, json={"amount": 6.0})
    assert update.status_code == 200
    assert update.json()["amount"] == 6.0


def test_delete_expense(auth_headers):
    create = client.post("/api/expenses", headers=auth_headers, json={
        "title": "Taxi", "amount": 20.0, "category": "Transport", "date": "2024-06-03",
    })
    exp_id = create.json()["id"]
    delete = client.delete(f"/api/expenses/{exp_id}", headers=auth_headers)
    assert delete.status_code == 204


# ---------------------------------------------------------------------------
# Income
# ---------------------------------------------------------------------------

def test_create_income(auth_headers):
    resp = client.post("/api/income", headers=auth_headers, json={
        "title": "Monthly Salary", "amount": 5000.0,
        "source": "salary", "date": "2024-06-01",
    })
    assert resp.status_code == 201
    assert resp.json()["source"] == "salary"


# ---------------------------------------------------------------------------
# Savings
# ---------------------------------------------------------------------------

def test_savings_goal_and_deposit(auth_headers):
    create = client.post("/api/savings", headers=auth_headers, json={
        "goal_name": "Emergency Fund", "target_amount": 1000.0, "current_amount": 0.0,
    })
    assert create.status_code == 201
    goal_id = create.json()["id"]
    assert create.json()["is_completed"] is False

    dep = client.post(f"/api/savings/{goal_id}/deposit", headers=auth_headers, json={"amount": 1000.0})
    assert dep.status_code == 200
    assert dep.json()["is_completed"] is True


# ---------------------------------------------------------------------------
# Bills
# ---------------------------------------------------------------------------

def test_bill_paid_flow(auth_headers):
    create = client.post("/api/bills", headers=auth_headers, json={
        "title": "Internet Bill", "amount": 50.0,
        "due_date": "2024-06-15", "category": "Utilities",
    })
    assert create.status_code == 201
    bill_id = create.json()["id"]
    assert create.json()["is_paid"] is False

    paid = client.post(f"/api/bills/{bill_id}/mark-paid", headers=auth_headers)
    assert paid.status_code == 200
    assert paid.json()["is_paid"] is True


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

def test_dashboard(auth_headers):
    resp = client.get("/api/analytics/dashboard", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_income" in data
    assert "net_balance" in data


def test_expense_stats(auth_headers):
    resp = client.get("/api/analytics/expenses/stats", headers=auth_headers)
    assert resp.status_code == 200
    assert "mean" in resp.json()


def test_csv_export(auth_headers):
    resp = client.get("/api/expenses/export/csv", headers=auth_headers)
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
