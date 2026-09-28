"""Punto de entrada para la ejecución y prueba de funcionalidad local de la demo."""

import logging

from family_budget_agent.agent import data_analyst_sub_agent, main_orchestrator_agent
from family_budget_agent.deployment import generate_deployment_manifest
from family_budget_agent.evaluation import QualityFlywheelEvaluator
from family_budget_agent.services import initialize_persistence_and_memory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FamilyBudgetAgentDemo")


def main():
    logger.info("=== INICIALIZANDO DEMO DEL AGENTE DE ECONOMÍA FAMILIAR ===")

    # 1. Configurar infraestructura de sesiones y memoria
    session_service, memory_bank = initialize_persistence_and_memory()

    # 2. Generar manifiesto de despliegue
    generate_deployment_manifest()

    # 3. Ejecutar suite de evaluación de calidad
    evaluator = QualityFlywheelEvaluator()
    eval_results = evaluator.run_baseline_evaluation()

    print("\n---------------------------------------------------------------------")
    print(" RESUMEN DEL SISTEMA DE AGENTES EN PYTHON (GEAP & ADK)")
    print("---------------------------------------------------------------------")
    print(f"1. Orquestador Principal: {main_orchestrator_agent.name} (Modelo: {main_orchestrator_agent.model})")
    print(f"2. Sub-agentes: {[sa.name for sa.name in main_orchestrator_agent.sub_agents]}")
    print(f"3. Herramientas Principales: {[t.__name__ for t in main_orchestrator_agent.tools]}")
    print(f"4. Sandbox de Código Seguro: {data_analyst_sub_agent.code_executor.__class__.__name__}")
    print(f"5. Composite Score Baseline (Quality Flywheel): {eval_results['composite_score']:.4f}")
    print("---------------------------------------------------------------------\n")


if __name__ == "__main__":
    main()
