import requests
import logging
from src.backend.config_loader import CONFIG

class TAAPIClient:
    """Client for fetching technical indicators from TAAPI.io"""

    def __init__(self):
        self.api_key = CONFIG.get("taapi_api_key", "")
        self.base_url = "https://api.taapi.io/bulk"
        self.logger = logging.getLogger(__name__)
        
        # Detectar si la clave es falsa o vacía para desactivar el cliente
        self.is_disabled = False
        if not self.api_key or "ignorar" in self.api_key or len(self.api_key) < 10:
            self.is_disabled = True
            self.logger.info("TAAPI Client disabled (No valid API Key detected). Using Price Action only.")

    def fetch_asset_indicators(self, symbol: str, interval: str = "5m"):
        """
        Fetches bulk indicators for a given asset.
        If disabled, returns empty dict immediately to avoid errors.
        """
        if self.is_disabled:
            return {}

        # Standard indicators configuration
        payload = {
            "secret": self.api_key,
            "construct": {
                "exchange": "binance",
                "symbol": f"{symbol}/USDT",
                "interval": interval,
                "indicators": [
                    {"indicator": "ema", "period": 20},
                    {"indicator": "ema", "period": 50},
                    {"indicator": "rsi", "period": 14},
                    {"indicator": "macd"},
                    {"indicator": "atr", "period": 14},
                    {"indicator": "bbands", "period": 20}
                ]
            }
        }

        try:
            response = requests.post(self.base_url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Transform TAAPI bulk format to simpler dict
            result = {}
            for item in data.get("data", []):
                ind_id = item.get("id")
                result[ind_id] = item.get("result", {}).get("value")
                # Handle multipart indicators like MACD/Bbands
                if not result[ind_id]:
                    result[ind_id] = item.get("result")
            
            return {interval: result}

        except Exception as e:
            # Log as debug to keep terminal clean unless debugging
            self.logger.debug(f"TAAPI fetch failed for {symbol}: {e}")
            return {}