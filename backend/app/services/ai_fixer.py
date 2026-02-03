"""
AI Fixer Service
Generates code fixes On-Demand for detected issues.
"""
import logging
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from ..config import get_settings

logger = logging.getLogger(__name__)

# Enhanced System Prompt for contextual, actionable guides
SYSTEM_PROMPT = """Tu es un DevOps Senior Expert spécialisé en sécurité web et SEO.
Ta mission : générer des guides de correction ACTIONNABLES et CONTEXTUALISÉS.

Règles STRICTES :
1. Retourne UNIQUEMENT un JSON bien formé avec ces clés exactes :
   - "why": Explication en 2-3 phrases du RISQUE BUSINESS (pas technique)
   - "environment": Auto-détection du serveur probable (Nginx/Apache/Node/Autre)
   - "file_path": Chemin du fichier à modifier (ex: /etc/nginx/nginx.conf)
   - "code": Le snippet de code exact à ajouter
   - "steps": Array de 3-5 étapes numérotées avec actions précises
   - "commands": Array de commandes shell pour appliquer + redémarrer
   - "validation": Checklist de 2-3 tests pour vérifier que ça fonctionne

2. INTERDIT :
   - Markdown (```), explications hors JSON
   - Termes trop techniques (explain comme à un CEO)
   - Généricités ("configurer le serveur") -> sois PRÉCIS

3. Si données insuffisantes : {"error": "CONTEXT_INSUFFISANT"}
"""

async def generate_fix(issue_type: str, context_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a comprehensive, actionable fix guide using LLM.
    
    Args:
        issue_type: The type of issue
        context_data: Context for generating the fix
        
    Returns:
        Dict with structured guide (why, steps, commands, validation)
    """
    settings = get_settings()
    api_key = settings.openrouter_api_key or settings.openai_api_key
    
    if not api_key:
        logger.error("❌ AI Fixer: No API Key found.")
        return {"error": "API_KEY_MISSING"}

    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1"
    )

    user_prompt = _build_user_prompt(issue_type, context_data)
    
    try:
        logger.info(f"✨ AI Fixer: Generating guide for {issue_type}...")
        
        response = await client.chat.completions.create(
            model="google/gemini-2.0-flash-lite-001",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=1000,
            extra_headers={
                 "HTTP-Referer": "http://localhost:3000",
                 "X-Title": "SiteAuditor Fixer"
            }
        )
        
        content = response.choices[0].message.content.strip()
        
        # Parse JSON
        import json
        data = json.loads(content)
        
        logger.info("✅ AI Fixer: Guide generated successfully.")
        return data

    except Exception as e:
        logger.error(f"❌ AI Fixer Error: {str(e)}")
        return {"error": "GENERATION_FAILED", "detail": str(e)}

def _build_user_prompt(issue_type: str, data: Dict[str, Any]) -> str:
    """Constructs the specific prompt for the issue"""
    
    if issue_type == "missing_meta_description":
        title = data.get("title", "Sans titre")
        h1 = data.get("h1", "")
        content_sample = data.get("content_sample", "")
        return (
            f"TASK: Generate a <meta name='description'> tag.\n"
            f"CONTEXT:\n"
            f"- Page Title: {title}\n"
            f"- H1: {h1}\n"
            f"- Content Start: {content_sample[:300]}...\n"
            f"CONSTRAINT: Description must be SEO optimized, between 140-160 chars, and use French."
        )
        
    elif issue_type == "missing_title":
        h1 = data.get("h1", "")
        content_sample = data.get("content_sample", "")
        return (
             f"TASK: Generate a <title> tag.\n"
             f"CONTEXT:\n"
             f"- H1: {h1}\n"
             f"- Content: {content_sample[:200]}\n"
             f"CONSTRAINT: Title must be SEO optimized, max 60 chars, French."
        )

    elif issue_type == "unsafe_cross_origin":
        tag = data.get("tag", "")
        return (
             f"TASK: Secure this anchor tag to prevent Reverse Tabnabbing.\n"
             f"INPUT: {tag}\n"
             f"CONSTRAINT: Add rel='noopener noreferrer' if missing. Preserve other attributes."
        )
        
    elif issue_type == "img_alt_missing":
        img_tag = data.get("tag", "")
        context_text = data.get("surrounding_text", "")
        return (
             f"TASK: Add an alt attribute to this image tag.\n"
             f"INPUT TAG: {img_tag}\n"
             f"CONTEXT TEXT: {context_text}\n"
             f"CONSTRAINT: Describe the image function/content based on context. French."
        )

    elif issue_type == "missing_security_header":
         name = data.get("header_name", "")
         desc = data.get("description", "")
         return (
             f"SECURITY HEADER MISSING: {name}\n"
             f"Description: {desc}\n\n"
             f"Génère un guide JSON structuré pour corriger ce problème.\n"
             f"Fournis :\n"
             f"- 'why': Le risque BUSINESS en langage simple (ex: vol de données clients)\n"
             f"- 'environment': Auto-détecte si Nginx/Apache/Node/Autre basé sur les headers standards\n"
             f"- 'file_path': Chemin exact du fichier config à éditer\n"
             f"- 'code': Le snippet de configuration à ajouter\n"
             f"- 'steps': 3-5 étapes précises (ex: '1. Connectez-vous en SSH', '2. Ouvrez /etc/nginx/...')\n"
             f"- 'commands': Commandes shell pour tester et redémarrer le serveur\n"
             f"- 'validation': 2-3 tests pour vérifier (ex: 'curl -I https://...')\n"
         )
        
    # Generic fallback
    return (
        f"TASK: Fix the following code issue related to '{issue_type}'.\n"
        f"CONTEXT DATA: {str(data)[:500]}"
    )
