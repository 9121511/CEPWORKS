"""
Centralized environment variable loading for the trading agent configuration.
GANN ONLY EDITION - All TAAPI dependencies removed.
"""

import json
import os
from dotenv import load_dotenv
from typing import Optional, List, Dict, Union, Any

# Cargar variables de entorno desde el archivo .env
load_dotenv()


def _get_env(name: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """Fetch an environment variable with optional default and required validation."""
    value = os.getenv(name, default)
    if required and (value is None or value == ""):
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _get_bool(name: str, default: bool = False) -> bool:
    """Parse boolean environment variables."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _get_json(name: str, default: Optional[dict] = None) -> Optional[dict]:
    """Parse JSON objects from environment variables."""
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise RuntimeError(f"Environment variable {name} must be a JSON object")
        return parsed
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON for {name}: {raw}") from exc


def _get_list(name: str, default: Optional[List[str]] = None) -> Optional[List[str]]:
    """Robust list parser that handles commas, spaces, and JSON arrays."""
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    
    raw = raw.strip()
    
    # 1. Try JSON list format ["BTC", "ETH"]
    if raw.startswith("[") and raw.endswith("]"):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(item).strip().strip('"\'') for item in parsed if str(item).strip()]
        except json.JSONDecodeError:
            pass 
            
    # 2. Try Comma Separation (BTC,ETH,SOL)
    if "," in raw:
        return [item.strip() for item in raw.split(",") if item.strip()]
        
    # 3. Try Space Separation (BTC ETH SOL)
    return raw.split()


# --- DICCIONARIO DE CONFIGURACIÓN GLOBAL ---
CONFIG = {
    # HYPERLIQUID CONFIGURATION
    "hyperliquid_private_key": _get_env("HYPERLIQUID_PRIVATE_KEY"),
    "hyperliquid_account_address": _get_env("HYPERLIQUID_ACCOUNT_ADDRESS") or _get_env("HL_ACCOUNT_ADDRESS"),
    "hyperliquid_network": _get_env("HYPERLIQUID_NETWORK", "mainnet"),
    "hyperliquid_base_url": _get_env("HYPERLIQUID_BASE_URL"),
    
    # AI / LLM (Gemini 2.0 via OpenRouter/Google Base URL)
    "openrouter_api_key": _get_env("OPENROUTER_API_KEY"),
    "openrouter_base_url": _get_env("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
    "openrouter_app_title": _get_env("OPENROUTER_APP_TITLE", "trading-agent-gann"),
    "llm_model": _get_env("LLM_MODEL", "gemini-2.0-flash-exp"),
    
    # Reasoning tokens
    "reasoning_enabled": _get_bool("REASONING_ENABLED", False),
    "reasoning_effort": _get_env("REASONING_EFFORT", "high"),
    
    # Runtime controls
    "assets": _get_list("ASSETS") or ["BTC", "ETH", "SOL"],
    "interval": _get_env("INTERVAL", "5m"),
    "trading_mode": _get_env("TRADING_MODE", "auto"),
    
    # API server settings
    "api_host": _get_env("API_HOST", "0.0.0.0"),
    "api_port": _get_env("APP_PORT") or _get_env("API_PORT") or "3000",
}