"""Modelos Pydantic y perfiles de memoria del agente de economía familiar."""

from pydantic import BaseModel, Field


class TransactionRecordInput(BaseModel):
    """Esquema estricto para la entrada de una transacción financiera familiar."""
    date: str = Field(description="Fecha de la transacción en formato ISO (YYYY-MM-DD).")
    amount: float = Field(gt=0, description="Monto monetario positivo de la transacción.")
    currency: str = Field(default="EUR", description="Código ISO de la moneda (EUR, USD, GBP).")
    category: str = Field(description="Categoría del gasto/ingreso: 'Alimentación', 'Vivienda', 'Transporte', 'Ocio', 'Salud', 'Educación', 'Servicios', 'Ingreso'.")
    description: str = Field(description="Descripción conceptual o detalle de la transacción (ej. 'Compra semanal en supermercado').")
    transaction_type: str = Field(default="gasto", description="Tipo de movimiento: 'gasto' o 'ingreso'.")

class AnalyticsQueryInput(BaseModel):
    """Entrada para la generación de informes y visualizaciones del presupuesto."""
    period: str = Field(default="current_month", description="Período de análisis: 'current_month', 'last_month', 'year_to_date'.")
    group_by: str = Field(default="category", description="Métrica de agrupación: 'category', 'date', 'transaction_type'.")

class FamilyPreferencesProfile(BaseModel):
    """Patrón A: Perfil Estructurado de la Familia para Memory Bank."""
    family_id: str = Field(default="fam_001", description="Identificador de la unidad familiar.")
    monthly_budget_limit: float = Field(default=2500.0, description="Límite máximo de gasto mensual familiar.")
    savings_target_monthly: float = Field(default=500.0, description="Meta de ahorro mensual fijada por los tutores.")
    preferred_currency: str = Field(default="EUR", description="Moneda predeterminada para reportes.")
