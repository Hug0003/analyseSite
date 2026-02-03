
"""
AI Advisor Service
Uses OpenAI API to generate executive summaries from technical audit data.
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from pydantic import BaseModel

# Configure logging
logger = logging.getLogger(__name__)

class AiSummaryResponse(BaseModel):
    summary: str
    top_priorities: list[str]
    estimated_time: str

from ..config import get_settings

async def generate_executive_summary(scan_results: Dict[str, Any]) -> AiSummaryResponse:
    """
    Generates a high-level executive summary using OpenAI GPT-4o or GPT-3.5-Turbo.
    Filters the input data to minimize token usage and ensuring privacy.
    """
    settings = get_settings()
    # Try OpenRouter Key first, then OpenAI Key
    api_key = settings.openrouter_api_key or settings.openai_api_key
    
    # DEBUG LOGS
    logger.info(f"🤖 AI Advisor: Starting analysis. Data size: {len(str(scan_results))} chars")
    
    if not api_key:
        logger.error("❌ AI Advisor: No API Key found in settings (OPENROUTER_API_KEY or OPENAI_API_KEY missing).")
        return _get_fallback_summary()
    
    logger.info(f"🔑 AI Advisor: Using API Key starting with: {api_key[:10]}...")
    logger.info(f"🌐 AI Advisor: Target Base URL: https://openrouter.ai/api/v1")

    try:
        # 1. Filter and Prepare Data
        minimized_data = _minimize_scan_data(scan_results)
        logger.info("📉 AI Advisor: Data minimized for prompt.")
        
        # 2. Prepare Prompt & Client
        client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        
        system_prompt = (
            "Tu es un Expert CTO et Auditeur Web de renommée mondiale. Analyse ces résultats d'audit technique. "
            "Ton but est de rassurer ou d'alerter un CEO qui ne connaît rien à la technique. "
            "Génère une réponse au format JSON strict avec ces 3 clés : "
            "1. 'summary': Un paragraphe de 3 phrases résumant l'état général (Ton professionnel, direct). "
            "2. 'top_priorities': Une liste des 3 actions les plus urgentes à mener (en langage business, ex: 'Sécuriser les paiements' au lieu de 'Fix SSL'). "
            "3. 'estimated_time': Une estimation approximative du temps de travail pour un développeur (ex: '2 jours')."
        )

        logger.info("⏳ AI Advisor: Sending request to OpenRouter...")
        
        # 3. Call OpenRouter API
        # Using a widely available model alias or the specific one
        model_name = "google/gemini-2.0-flash-lite-001"
        
        response = await client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(minimized_data, ensure_ascii=False)}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=600,
            extra_headers={
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "SiteAuditor Local"
            }
        )
        
        logger.info("✅ AI Advisor: Response received from OpenRouter.")

        # 4. Parse Response
        content = response.choices[0].message.content
        logger.debug(f"📝 AI Raw Content: {content[:100]}...") # Log first 100 chars
        
        if not content:
            raise ValueError("Empty response from API")
            
        data = json.loads(content)
        return AiSummaryResponse(
            summary=data.get("summary", "Analyse indisponible."),
            top_priorities=data.get("top_priorities", []),
            estimated_time=data.get("estimated_time", "Non estimé")
        )

    except Exception as e:
        logger.error(f"❌ AI Advisor Error: {str(e)}", exc_info=True)
        # Return fallback but keeping the error in logs
        return _get_fallback_summary()

def _minimize_scan_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts only the essential failing metrics to send to the LLM.
    Reduces token usage significantly.
    """
    minimized = {
        "global_score": data.get("global_score"),
        "url": data.get("url"),
        "failing_audits": [],
        "tech_stack_count": data.get("tech_stack", {}).get("outdated_count", 0),
        "security_score": data.get("security", {}).get("score"),
        "seo_performance": data.get("seo", {}).get("scores", {}).get("performance")
    }

    # Extract failing SEO audits
    if "seo" in data and "audits" in data["seo"]:
        for audit in data["seo"]["audits"]:
            if not audit.get("passed", True) or audit.get("score") != 1:
                minimized["failing_audits"].append(f"SEO: {audit.get('title')}")

    # Extract missing Security Headers
    if "security" in data and "headers" in data["security"]:
        for h in data["security"]["headers"]:
            if not h.get("present", True) and h.get("severity") != "info":
                 minimized["failing_audits"].append(f"Security: Header manquante {h.get('name')}")
                 
    # Extract exposed files
    if "security" in data and "exposed_files" in data["security"]:
        for f in data["security"]["exposed_files"]:
             if f.get("accessible", False):
                 minimized["failing_audits"].append(f"Security: Fichier exposé {f.get('path')}")

    # Extract Green IT grade
    if "green_it" in data:
        minimized["green_it_grade"] = data["green_it"].get("grade")
        
    # Extract GDPR status
    if "gdpr" in data:
        minimized["gdpr_compliant"] = data["gdpr"].get("compliant")

    return minimized

def _get_fallback_summary() -> AiSummaryResponse:
    return AiSummaryResponse(
        summary="L'analyse IA est indisponible pour le moment, veuillez consulter les détails techniques ci-dessous.",
        top_priorities=["Mettre à jour la sécurité", "Optimiser le SEO", "Vérifier la conformité RGPD"],
        estimated_time="Indéterminé"
    )
