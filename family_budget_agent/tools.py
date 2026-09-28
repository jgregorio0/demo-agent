"""Herramientas con ToolContext y manejo de scopes (user:, app:, temp:, sesión)."""

import logging
from datetime import datetime
from typing import Any, Dict

from google.adk.tools import ToolContext

from .models import TransactionRecordInput

logger = logging.getLogger(__name__)


def add_family_transaction(input_data: TransactionRecordInput, context: ToolContext) -> Dict[str, Any]:
    """
    Registra una nueva transacción en el libro contable de la sesión y evalúa el impacto presupuestario.
    Utiliza los scopes 'user:', 'app:', 'temp:' y el estado global de la sesión.
    """
    user_id = context.state.get("user:id", "family_member_1")
    family_budget_limit = context.state.get("user:monthly_budget_limit", 2500.0)

    # Lectura y mutación del estado de la sesión
    current_transactions = context.state.get("transactions_log", [])

    new_entry = {
        "transaction_id": f"TXN-{len(current_transactions) + 1:04d}",
        "timestamp": datetime.now().isoformat(),
        "date": input_data.date,
        "amount": input_data.amount,
        "currency": input_data.currency,
        "category": input_data.category,
        "description": input_data.description,
        "type": input_data.transaction_type,
        "recorded_by": user_id
    }

    current_transactions.append(new_entry)
    context.state["transactions_log"] = current_transactions

    # Cálculo de métricas acumuladas
    total_spent = sum(t["amount"] for t in current_transactions if t.get("type") == "gasto")
    remaining_budget = family_budget_limit - total_spent

    # Scope Transitorio (se descarta al concluir el turno)
    context.state["temp:last_action_status"] = "TRANSACTION_RECORDED_SUCCESSFULLY"

    return {
        "status": "SUCCESS",
        "transaction_id": new_entry["transaction_id"],
        "entry": new_entry,
        "total_spent_this_month": total_spent,
        "remaining_budget": remaining_budget,
        "budget_alert": remaining_budget < 0
    }

def get_family_budget_status(context: ToolContext) -> Dict[str, Any]:
    """Recupera el resumen presupuestario actual, desglose por categorías y metas de ahorro."""
    budget_limit = context.state.get("user:monthly_budget_limit", 2500.0)
    savings_goal = context.state.get("user:savings_target_monthly", 500.0)
    transactions = context.state.get("transactions_log", [])

    total_expenses = sum(t["amount"] for t in transactions if t.get("type", "gasto") == "gasto")
    total_income = sum(t["amount"] for t in transactions if t.get("type") == "ingreso")

    # Desglose por categoría
    categories: Dict[str, float] = {}
    for t in transactions:
        if t.get("type", "gasto") == "gasto":
            cat = t.get("category", "Otros")
            categories[cat] = categories.get(cat, 0.0) + t.get("amount", 0.0)

    return {
        "monthly_budget_limit": budget_limit,
        "monthly_savings_goal": savings_goal,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_savings": total_income - total_expenses,
        "remaining_budget": budget_limit - total_expenses,
        "category_breakdown": categories,
        "transaction_count": len(transactions)
    }
