# Agente de Economía Familiar y Control Presupuestario

Proyecto demo que implementa un sistema de agentes de nivel empresarial con el
**Google Agent Development Kit (ADK)**, alineado con la arquitectura de
**Gemini Enterprise Agent Platform (GEAP)**.

Caso de uso: chatbot de economía familiar que gestiona un conjunto de
transacciones `(fecha, monto, categoría, descripción)` — registra gastos e
ingresos, hace seguimiento del presupuesto mensual, ofrece consejos de ahorro
vía RAG y ejecuta análisis estadísticos en un sandbox seguro.

## Capacidades demostradas

1. **Estado y memoria multi-nivel** — scopes `user:`, `app:`, sesión y `temp:`
   (transitorio), con persistencia en `DatabaseSessionService` y retención a
   largo plazo en `VertexAiMemoryBankService`.
2. **Guardarraíles de seguridad** — callbacks anti-prompt injection,
   enmascaramiento de PII (tarjetas, emails) y control de acceso por rol
   (`parent_admin` vs `family_member`, límite de 500 EUR por transacción).
3. **Grounding híbrido** — `VertexAiSearchTool` combinado con herramientas
   propias mediante `bypass_multi_tools_limit=True`.
4. **Ejecución segura de código** — `AgentEngineSandboxCodeExecutor`
   (Zero Egress) para análisis de datos.
5. **Sub-agentes especializados** — orquestador principal que delega en un
   asesor financiero y un analista de datos.
6. **Evaluación continua** — `QualityFlywheelEvaluator` con composite score
   (`Accuracy - w_cost·Cost - w_latency·Latency`) para optimización
   Hill Climbing.
7. **Despliegue automatizado** — generación de `deploy_and_publish.sh` para
   Cloud Agent Runtime + publicación en Gemini Enterprise.

## Estructura del proyecto

```
demo-agent/
├── main.py                          # Punto de entrada de la demo local
└── family_budget_agent/             # Paquete del agente
    ├── __init__.py                  # Expone el módulo agent (convención ADK)
    ├── agent.py                     # Sub-agentes + orquestador (root_agent)
    ├── models.py                    # Esquemas Pydantic de entrada y perfiles
    ├── callbacks.py                 # Guardarraíles de seguridad y RBAC
    ├── tools.py                     # Herramientas con ToolContext y scopes
    ├── services.py                  # Sesiones persistentes y Memory Bank
    ├── evaluation.py                # Suite Quality Flywheel
    └── deployment.py                # Generación del script de despliegue
```

### Arquitectura de agentes

```
FamilyBudgetOrchestratorAgent  (gemini-2.5-flash)
├── tools: add_family_transaction, get_family_budget_status
├── callbacks: sanitize_and_protect_input, enforce_tool_permissions
├── FamilyFinancialAdvisorAgent  (gemini-2.5-flash)
│   └── tools: VertexAiSearchTool (RAG), get_family_budget_status
└── FamilyDataAnalystAgent  (gemini-2.5-pro)
    └── code_executor: AgentEngineSandboxCodeExecutor
```

## Requisitos

- Python 3.10+
- Dependencias:

```bash
pip install google-adk pydantic
```

Para las funciones de Vertex AI (Search, Memory Bank, Sandbox) se requiere un
proyecto de GCP con las APIs correspondientes habilitadas y credenciales
configuradas (Application Default Credentials).

## Uso

### Demo local

Ejecuta la inicialización completa: servicios de sesión/memoria, generación del
script de despliegue y evaluación baseline:

```bash
python main.py
```

### Ejecutar el agente con ADK

El paquete expone `root_agent`, por lo que es compatible con las herramientas
estándar de ADK:

```bash
adk web        # playground interactivo en el navegador
adk run family_budget_agent
```

## Despliegue

`main.py` genera `deploy_and_publish.sh`, un script que:

1. Configura la gobernanza IAM del agente (roles `agentregistry.viewer`,
   `discoveryengine.viewer`).
2. Despliega en Cloud Agent Runtime con `agents-cli deploy` apuntando al
   entrypoint `family_budget_agent.agent:main_orchestrator_agent`.
3. Publica y registra el agente en Gemini Enterprise con
   `agents-cli publish gemini-enterprise`.

> Los identificadores de GCP (`demo-family-finance-gcp`, data stores, sandbox,
> service account) son valores de demo — ajústalos a tu proyecto antes de un
> despliegue real.
