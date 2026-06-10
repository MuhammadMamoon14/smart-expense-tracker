"""
analytics_service.py — Statistics engine using only Python built-ins.
"""

import statistics
from collections import defaultdict
from typing import Any


def compute_expense_stats(expenses: list[dict]) -> dict[str, Any]:
    """Core statistical analysis using the statistics module."""
    if not expenses:
        return {
            "count": 0,
            "total": 0.0,
            "mean": 0.0,
            "median": 0.0,
            "mode": 0.0,
            "min": 0.0,
            "max": 0.0,
            "std_dev": 0.0,
        }

    amounts = [e["amount"] for e in expenses]
    total = sum(amounts)
    mean = statistics.mean(amounts)
    median = statistics.median(amounts)
    std_dev = statistics.stdev(amounts) if len(amounts) > 1 else 0.0

    try:
        mode = statistics.mode(amounts)
    except statistics.StatisticsError:
        # No unique mode — return the most frequent rounded value
        from collections import Counter
        rounded = [round(a, 0) for a in amounts]
        mode = Counter(rounded).most_common(1)[0][0]

    return {
        "count": len(amounts),
        "total": round(total, 2),
        "mean": round(mean, 2),
        "median": round(median, 2),
        "mode": round(mode, 2),
        "min": round(min(amounts), 2),
        "max": round(max(amounts), 2),
        "std_dev": round(std_dev, 2),
    }


def monthly_breakdown(expenses: list[dict]) -> dict[str, float]:
    """Group total spending by YYYY-MM."""
    monthly: dict[str, float] = defaultdict(float)
    for e in expenses:
        month = e["date"][:7]
        monthly[month] += e["amount"]
    return {k: round(v, 2) for k, v in sorted(monthly.items())}


def category_breakdown(expenses: list[dict]) -> dict[str, float]:
    """Total spending per category."""
    totals: dict[str, float] = defaultdict(float)
    for e in expenses:
        totals[e["category"]] += e["amount"]
    return {k: round(v, 2) for k, v in sorted(totals.items(), key=lambda x: x[1], reverse=True)}


def top_category(expenses: list[dict]) -> str | None:
    cats = category_breakdown(expenses)
    return max(cats, key=lambda k: cats[k]) if cats else None


def budget_alerts(expenses: list[dict], categories: list[dict]) -> list[dict]:
    """Return categories where spending exceeds the configured budget_limit."""
    cat_map = {c["name"]: c.get("budget_limit") for c in categories}
    cat_totals = category_breakdown(expenses)
    alerts = []
    for cat, total in cat_totals.items():
        limit = cat_map.get(cat)
        if limit and total > limit:
            alerts.append({
                "category": cat,
                "spent": total,
                "budget_limit": limit,
                "over_by": round(total - limit, 2),
                "severity": "high" if total > limit * 1.5 else "medium",
            })
    return alerts


def dashboard_summary(
    expenses: list[dict],
    income: list[dict],
    savings: list[dict],
    bills: list[dict],
) -> dict[str, Any]:
    """Single-call summary for the dashboard endpoint."""
    total_income = round(sum(r["amount"] for r in income), 2)
    total_expenses = round(sum(e["amount"] for e in expenses), 2)
    net_balance = round(total_income - total_expenses, 2)

    total_savings_target = round(sum(s["target_amount"] for s in savings), 2)
    total_savings_current = round(sum(s["current_amount"] for s in savings), 2)

    unpaid_bills = [b for b in bills if not b["is_paid"]]
    total_unpaid_bills = round(sum(b["amount"] for b in unpaid_bills), 2)

    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_balance": net_balance,
        "savings": {
            "goals_count": len(savings),
            "total_target": total_savings_target,
            "total_saved": total_savings_current,
            "total_remaining": round(total_savings_target - total_savings_current, 2),
        },
        "bills": {
            "total_bills": len(bills),
            "unpaid_count": len(unpaid_bills),
            "unpaid_amount": total_unpaid_bills,
        },
        "top_spending_category": top_category(expenses),
        "expense_count": len(expenses),
        "income_count": len(income),
    }
