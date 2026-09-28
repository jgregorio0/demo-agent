"""
===============================================================================
PROYECTO DEMO: AGENTE DE ECONOMÍA FAMILIAR Y CONTROL PRESUPUESTARIO
===============================================================================
Este proyecto demuestra la implementación completa de un sistema de agentes
de nivel empresarial utilizando el Google Agent Development Kit (ADK), alineado
con la arquitectura de Gemini Enterprise Agent Platform (GEAP).

Caso de uso: Chatbot de Economía Familiar y Control Presupuestario
Basado en un conjunto de transacciones: (fecha, monto, categoría, descripción)

Soporta:
 1. Estado y memoria multi-nivel a largo plazo (User, App, Session, Transient scopes)
 2. Guardarraíles de seguridad (Callbacks anti-prompt injection y sanitización de PII)
 3. Grounding híbrido con flag 'bypass_multi_tools_limit=True'
 4. Ejecución segura de código Python en Agent Engine Sandbox (Zero Egress)
 5. Arquitectura de Sub-agentes especialista y orquestación
 6. Suite de Evaluación Continua y Optimización Hill Climbing (Quality Flywheel)
 7. Scripting automatizado de despliegue, gobernanza y publicación en Gemini Enterprise
===============================================================================
"""

from . import agent
