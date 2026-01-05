"""
Trading Agent - Gemini 2.0 Gann Specialist
Decision making logic using LLM via OpenRouter/Google.
"""
import logging
import json
import aiohttp
from src.backend.config_loader import CONFIG

class TradingAgent:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.api_key = CONFIG.get('openrouter_api_key')
        self.base_url = CONFIG.get('openrouter_base_url')
        self.model = CONFIG.get('llm_model', 'gemini-2.0-flash-exp')

    # 👇 ESTA ES LA FUNCIÓN QUE EL MOTOR ESTABA BUSCANDO 👇
    async def analyze(self, asset: str, price: float, indicators: dict, current_position: dict = None) -> dict:
        """
        Analyzes market data and returns a trading decision.
        """
        # Prompt Ultra Pro W.D. Gann
        prompt = f"""
        You are a W.D. Gann trading expert engine. 
        Asset: {asset}
        Current Price: {price}
        Current Position: {current_position if current_position else 'None'}
        
        INSTRUCTIONS:
        1. Apply Gann's "Square of Nine" to find support/resistance levels near {price}.
        2. Check if price is above the 45-degree angle (Bullish) or below (Bearish).
        3. Strategy: HODL winning trades. Accumulate Sats.
        4. If Position exists: HODL unless trend reverses on the 45-degree angle.
        
        OUTPUT FORMAT (JSON ONLY):
        {{
            "action": "buy" | "sell" | "hold",
            "confidence": 0.0 to 1.0,
            "rationale": "Brief Gann analysis (max 15 words)"
        }}
        """
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": { "type": "json_object" }
                }
                
                # Manejo de headers según el proveedor (Google vs OpenRouter)
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                # Si usas OpenRouter, añadimos headers extra
                if "openrouter" in self.base_url:
                    headers["HTTP-Referer"] = CONFIG.get('openrouter_referer', 'http://localhost:3000')
                    headers["X-Title"] = CONFIG.get('openrouter_app_title', 'GannBot')

                url = f"{self.base_url}/chat/completions"
                
                async with session.post(url, headers=headers, json=payload) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        self.logger.error(f"LLM Error {resp.status}: {error_text}")
                        return {"action": "hold", "confidence": 0, "rationale": f"API Error {resp.status}"}
                        
                    result = await resp.json()
                    content = result['choices'][0]['message']['content']
                    
                    # Limpiar markdown si Gemini devuelve ```json ... ```
                    if "```json" in content:
                        content = content.replace("```json", "").replace("```", "")
                    
                    return json.loads(content)

        except Exception as e:
            self.logger.error(f"Gemini Analysis Error: {e}")
            return {"action": "hold", "confidence": 0, "rationale": "Connection Error"}