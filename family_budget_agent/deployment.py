"""Scripts de despliegue, gobernanza y publicación en Gemini Enterprise.

Solo relevante para `AGENT_PROFILE=production`. Genera el script bash que
despliega en Cloud Agent Runtime y publica en Gemini Enterprise usando los
identificadores configurados en `config.py` (variables GCP_*).
"""

import logging

from . import config

logger = logging.getLogger(__name__)


def generate_deployment_manifest():
    """
    Genera el script automatizado (deploy_and_publish.sh) para desplegar el agente
    en Cloud Agent Runtime y registrarlo en Gemini Enterprise Agent Platform.
    """
    bash_script = f"""#!/usr/bin/env bash
set -e

PROJECT_ID="{config.GCP_PROJECT_ID}"
REGION="{config.GCP_LOCATION}"
SERVICE_ACCOUNT="sa-family-agent@{config.GCP_PROJECT_ID}.iam.gserviceaccount.com"

echo "====================================================================="
echo "1. CONFIGURANDO GOBERNANZA E IDENTIDAD IAM DEL AGENTE FAMILIAR"
echo "====================================================================="
gcloud projects add-iam-policy-binding $PROJECT_ID \\
    --member="serviceAccount:$SERVICE_ACCOUNT" \\
    --role="roles/agentregistry.viewer"

gcloud projects add-iam-policy-binding $PROJECT_ID \\
    --member="serviceAccount:$SERVICE_ACCOUNT" \\
    --role="roles/discoveryengine.viewer"

echo "====================================================================="
echo "2. DESPLEGANDO EN GOOGLE CLOUD AGENT RUNTIME"
echo "====================================================================="
DEPLOY_OUTPUT=$(agents-cli deploy \\
    --project=$PROJECT_ID \\
    --region=$REGION \\
    --entrypoint="family_budget_agent.agent:main_orchestrator_agent" \\
    --update-env-vars="ENV=production,LOG_LEVEL=INFO" \\
    --format=json)

RESOURCE_ID=$(echo "$DEPLOY_OUTPUT" | jq -r '.name')
echo "Agente desplegado correctamente. Runtime ID: $RESOURCE_ID"

echo "====================================================================="
echo "3. PUBLICANDO EN LA PLATAFORMA DE GEMINI ENTERPRISE"
echo "====================================================================="
agents-cli publish gemini-enterprise \\
    --registration-type=adk \\
    --gemini-enterprise-app-id="gemini-enterprise-family-app" \\
    --agent-runtime-id="$RESOURCE_ID" \\
    --display-name="Gestor Inteligente de Economía Familiar y Presupuesto" \\
    --description="Asistente financiero familiar. Registra y categoriza gastos e ingresos, realiza seguimiento del presupuesto mensual, ofrece consejos de ahorro y genera análisis estadísticos detallados."

echo "Despliegue y registro completados con éxito."
"""
    if config.PROFILE != "production":
        logger.info(
            "[DEPLOY] Perfil '%s': se omite la generación de 'deploy_and_publish.sh' "
            "(solo aplica a production).",
            config.PROFILE,
        )
        return
    with open("deploy_and_publish.sh", "w", encoding="utf-8") as f:
        f.write(bash_script)
    logger.info("[DEPLOY] Script 'deploy_and_publish.sh' generado exitosamente.")
