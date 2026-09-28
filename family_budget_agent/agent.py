"""Sub-agentes especializados y agente orquestador principal."""

from google.adk.agents import LlmAgent
from google.adk.tools import VertexAiSearchTool
from google.adk.code_executors import AgentEngineSandboxCodeExecutor

from .callbacks import enforce_tool_permissions, sanitize_and_protect_input
from .tools import add_family_transaction, get_family_budget_status

# 1. Herramienta RAG sobre Guías de Economía Familiar y Ahorro
family_education_search_tool = VertexAiSearchTool(
    project="demo-family-finance-gcp",
    location="global",
    data_store_id="family-finance-guides-ds"
)

# 2. Sub-agente especialista en Educación Financiera y Normas del Hogar
# Se habilita 'bypass_multi_tools_limit=True' para combinar RAG con herramientas del cliente.
advisor_sub_agent = LlmAgent(
    name="FamilyFinancialAdvisorAgent",
    model="gemini-2.5-flash",
    instruction="""Eres un educador y asesor financiero familiar experto.
Tu objetivo es ofrecer consejos prácticos sobre optimización de gastos, estrategias de ahorro,
fondos de emergencia y educación financiera para niños y adultos.
Consulta la base de conocimientos antes de responder y verifica el estado actual del presupuesto.""",
    tools=[family_education_search_tool, get_family_budget_status],
    bypass_multi_tools_limit=True
)

# 3. Sub-agente Analista de Datos en Sandbox de Ejecución Segura
sandbox_executor = AgentEngineSandboxCodeExecutor(
    sandbox_resource_name="projects/demo-family-finance-gcp/locations/us-central1/sandboxes/family-finance-sandbox"
)

data_analyst_sub_agent = LlmAgent(
    name="FamilyDataAnalystAgent",
    model="gemini-2.5-pro",
    instruction="""Genera y ejecuta código Python en el sandbox seguro para analizar la lista de transacciones.
Calcula porcentajes de variación mensual, proyecciones de ahorro al final del año y genera gráficos estadísticos
desagregados por categoría o miembros de la familia.""",
    code_executor=sandbox_executor
)

# 4. Agente Orquestador principal (FamilyBudgetOrchestratorAgent)
main_orchestrator_agent = LlmAgent(
    name="FamilyBudgetOrchestratorAgent",
    model="gemini-2.5-flash",
    instruction="""Eres el Asistente Orquestador Principal de la Economía Familiar.
Usuario activo: {user:id} | Rol: {user:role} | Presupuesto Mensual: {user:monthly_budget_limit} EUR

Responsabilidades:
1. Si el usuario desea registrar un gasto o ingreso (fecha, monto, categoría, descripción), usa 'add_family_transaction'.
2. Si el usuario consulta sobre el estado actual del presupuesto, saldos o límites, invoca 'get_family_budget_status'.
3. Si solicita recomendaciones de ahorro o consejos de finanzas, delega en 'FamilyFinancialAdvisorAgent'.
4. Si requiere análisis de tendencias complejas, estadísticas o gráficos, delega en 'FamilyDataAnalystAgent'.
5. Mantén un tono empático, claro, constructivo y estructurado.""",
    tools=[add_family_transaction, get_family_budget_status],
    sub_agents=[advisor_sub_agent, data_analyst_sub_agent],
    before_model_callback=sanitize_and_protect_input,
    before_tool_callback=enforce_tool_permissions,
    output_key="last_family_orchestration_summary"
)

# Alias estándar que ADK utiliza para descubrir el agente raíz (adk web / adk run / deploy)
root_agent = main_orchestrator_agent
