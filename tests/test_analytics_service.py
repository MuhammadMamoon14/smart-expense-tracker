"""Unit tests for the analytics service (no HTTP, no disk)."""

import pytest
from app.services.analytics_service import (
    compute_expense_stats,
    monthly_breakdown,
    category_breakdown,
    budget_alerts,
    dashboard_summary,
)


SAMPLE_EXPENSES = [
    {"amount": 100.0, "category": "Food & Dining", "date": "2024-01-10"},
    {"amount": 200.0, "category": "Transport",     "date": "2024-01-15"},
    {"amount": 50.0,  "category": "Food & Dining", "date": "2024-02-05"},
    {"amount": 300.0, "category": "Health",        "date": "2024-02-20"},
    {"amount": 150.0, "category": "Transport",     "date": "2024-03-01"},
]


def test_stats_basic():
    stats = compute_expense_stats(SAMPLE_EXPENSES)
    assert stats["count"] == 5
    assert stats["total"] == 800.0
    assert stats["min"] == 50.0
    assert stats["max"] == 300.0
    assert stats["mean"] == 160.0
    assert stats["median"] == 150.0


def test_stats_empty():
    stats = compute_expense_stats([])
    assert stats["count"] == 0
    assert stats["total"] == 0.0


def test_monthly_breakdown():
    result = monthly_breakdown(SAMPLE_EXPENSES)
    assert result["2024-01"] == 300.0
    assert result["2024-02"] == 350.0
    assert result["2024-03"] == 150.0


def test_category_breakdown():
    result = category_breakdown(SAMPLE_EXPENSES)
    assert result["Food & Dining"] == 150.0
    assert result["Transport"] == 350.0
    assert result["Health"] == 300.0


def test_budget_alerts():
    categories = [
        {"name": "Transport", "budget_limit": 200.0},
        {"name": "Food & Dining", "budget_limit": 500.0},
    ]
    alerts = budget_alerts(SAMPLE_EXPENSES, categories)
    assert len(alerts) == 1
    assert alerts[0]["category"] == "Transport"
    assert alerts[0]["over_by"] == 150.0


def test_dashboard_summary():
    income = [{"amount": 5000.0}]
    savings = [{"target_amount": 1000.0, "current_amount": 400.0}]
    bills = [
        {"amount": 100.0, "is_paid": True},
        {"amount": 200.0, "is_paid": False},
    ]
    result = dashboard_summary(SAMPLE_EXPENSES, income, savings, bills)
    assert result["total_income"] == 5000.0
    assert result["total_expenses"] == 800.0
    assert result["net_balance"] == 4200.0
    assert result["bills"]["unpaid_count"] == 1
    assert result["bills"]["unpaid_amount"] == 200.0
    assert result["top_spending_category"] == "Transport"
