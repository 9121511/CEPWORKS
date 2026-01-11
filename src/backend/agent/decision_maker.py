import logging
import json
import math
import aiohttp
from src.backend.config_loader import CONFIG

class TradingAgent:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.api_key = CONFIG.get('openrouter_api_key')
        self.base_url = CONFIG.get('openrouter_base_url')
        self.model = CONFIG.get('llm_model', 'gemini-2.0-flash-exp')

    # CONSTANTS FOR GUI DISPLAY
    AGENT_IDENTITY = "You are the GANN-MATH-ENGINE. You output ONLY statistical facts and geometric logic. No conversational filler."
    
    GANN_RULES = [
        "1. UP_TREND if Price > 50% Level.",
        "2. DOWN_TREND if Price < 50% Level.",
        "3. BREAKOUT if Price > Major High (Rule 1).",
        "4. BREAKDOWN if Price < Major Low (Rule 4).",
        "5. RESISTANCE_TEST if Price near Sq9 Resistance."
    ]

    def _calculate_gann_math(self, price, indicators):
        """
        Calcula la geometría sagrada antes de preguntar a la IA.
        Basado en 'Compact WDGANN.pdf'
        """
        major_high = indicators.get('high_swing', price * 1.1) # Fallback si no hay dato
        major_low = indicators.get('low_swing', price * 0.9)
        
        # [cite_start]1. Regla del 50% (Rule 8 [cite: 50])
        range_price = major_high - major_low
        level_50 = major_low + (range_price * 0.5)
        
        # Niveles de retroceso adicionales (Gann)
        level_25 = major_low + (range_price * 0.25)
        level_75 = major_low + (range_price * 0.75)
        level_33 = major_low + (range_price * 0.333)
        level_66 = major_low + (range_price * 0.666)
        
        # [cite_start]2. Square of Nine (Next Resistance/Support) [cite: 64]
        # Formula simplificada: (Raíz del precio +/- 1)^2 es una rotación de 360 grados
        root_price = math.sqrt(price)
        sq9_resistance = (root_price + 1) ** 2 # 360 grados arriba
        sq9_support = (root_price - 1) ** 2    # 360 grados abajo
        
        # Square of Nine - múltiples rotaciones
        sq9_resistance_720 = (root_price + 2) ** 2  # 720 grados (2 rotaciones)
        sq9_support_720 = (root_price - 2) ** 2    # -720 grados
        
        # 3. Posición Relativa
        trend_status = "BULLISH" if price > level_50 else "BEARISH"
        
        # 4. Distancia a niveles clave
        distance_to_50 = abs(price - level_50) / price * 100 if price > 0 else 0
        distance_to_resistance = abs(price - sq9_resistance) / price * 100 if price > 0 else 0
        distance_to_support = abs(price - sq9_support) / price * 100 if price > 0 else 0
        
        # 5. Gann Angles (simplificado)
        # Ángulo 1x1 (45 grados) - precio = tiempo
        gann_1x1_angle = price  # Base para cálculo
        
        # 6. Ciclos de tiempo (simplificado)
        # Basado en raíz cuadrada del precio
        time_cycle = int(root_price) % 360  # Ciclo de 360 grados
        
        return {
            "level_50_percent": round(level_50, 2),
            "level_25_percent": round(level_25, 2),
            "level_75_percent": round(level_75, 2),
            "level_33_percent": round(level_33, 2),
            "level_66_percent": round(level_66, 2),
            "sq9_next_resistance": round(sq9_resistance, 2),
            "sq9_next_support": round(sq9_support, 2),
            "sq9_resistance_720": round(sq9_resistance_720, 2),
            "sq9_support_720": round(sq9_support_720, 2),
            "trend_50_rule": trend_status,
            "major_high": round(major_high, 2),
            "major_low": round(major_low, 2),
            "range_price": round(range_price, 2),
            "distance_to_50_pct": round(distance_to_50, 2),
            "distance_to_resistance_pct": round(distance_to_resistance, 2),
            "distance_to_support_pct": round(distance_to_support, 2),
            "gann_1x1_angle_base": round(gann_1x1_angle, 2),
            "time_cycle_degrees": time_cycle,
            "root_price": round(root_price, 4)
        }

    async def analyze(self, asset: str, price: float, indicators: dict, current_position: dict = None) -> dict:
        
        # Paso 1: Hacemos la matemática dura aquí (Python es mejor que la IA para esto)
        gann_data = self._calculate_gann_math(price, indicators)
        
        # Prompt Ultra Pro W.D. Gann (Statistical & Direct)
        prompt = f"""
        IDENTITY: {self.AGENT_IDENTITY}
        
        INPUT DATA:
        Asset: {asset} @ {price}
        Range: {gann_data['major_low']} - {gann_data['major_high']}
        
        GEOMETRY (PRE-CALCULATED):
        - Rule 8 (50%): {gann_data['level_50_percent']} (Trend: {gann_data['trend_50_rule']})
        - Sq9 Res (+360deg): {gann_data['sq9_next_resistance']}
        - Sq9 Sup (-360deg): {gann_data['sq9_next_support']}
        
        STRICT RULES:
        1. UP_TREND if Price > {gann_data['level_50_percent']}.
        2. DOWN_TREND if Price < {gann_data['level_50_percent']}.
        3. BREAKOUT if Price > {gann_data['major_high']} (Rule 1).
        4. BREAKDOWN if Price < {gann_data['major_low']} (Rule 4).
        5. RESISTANCE_TEST if Price near {gann_data['sq9_next_resistance']}.

        
        TASK:
        Generate a specific trading signals JSON.
        
        "rationale": "Must be < 15 words. Telegraphic style. E.g., 'BULLISH: Price(91000) > 50%(89000). Target: 92000.'",
        "gann_thoughts": "A short, emoji-rich thought process based on WD Gann rules. E.g., '📐 50% Rule held! 🐂 Targeting Sq9 resistance. Time cycle looks aligned ⏳.'",
        "entry_plan": "Specific trigger condition. E.g., 'Enter LONG on pull-back to 50% (89000) or Breakout > Sq9 (91500).'",
        "exit_plan": "Specific target/invalidation. E.g., 'Exit at 92000 (Sq9+1). Invalid if < 88500.'",
        "gann_analysis": "Bullet points of EXACT match conditions. Max 3 bullets. No prose.",
        
        JSON OUTPUT FORMAT:
        {{
            "action": "buy" | "sell" | "hold" | "close",
            "stop_loss": <float>,
            "take_profit": <float>,
            "confidence": <float_0_to_1>,
            "gann_angle_status": "Above 1x1" | "Below 1x1" | "Unknown",
            "rationale": "STRICT SHORT TEXT",
            "gann_thoughts": "EMOJI RICH GANN THOUGHTS",
            "entry_plan": "Specific entry setup",
            "exit_plan": "Specific exit strategy",
            "gann_analysis": "- Point 1\\n- Point 2"
        }}
        """
        
        retries = 3
        base_delay = 2

        for attempt in range(retries):
            try:
                async with aiohttp.ClientSession() as session:
                    payload = {
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "response_format": { "type": "json_object" }
                    }
                    
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                    
                    if "openrouter" in self.base_url:
                        headers["HTTP-Referer"] = CONFIG.get('openrouter_referer', 'http://localhost:3000')
                        headers["X-Title"] = CONFIG.get('openrouter_app_title', 'GannBot')

                    url = f"{self.base_url}/chat/completions"
                    
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status == 429:
                            if attempt < retries - 1:
                                delay = base_delay * (2 ** attempt)
                                self.logger.warning(f"LLM Error 429 (Rate Limit). Retrying in {delay}s...")
                                import asyncio
                                await asyncio.sleep(delay)
                                continue
                            else:
                                self.logger.error("LLM Error 429: Max retries exceeded")
                                return {**gann_data, "action": "hold", "confidence": 0, "rationale": "API Rate Limit Exceeded", "analyzed_price": price}

                        if resp.status != 200:
                            self.logger.error(f"LLM Error {resp.status}")
                            return {**gann_data, "action": "hold", "confidence": 0, "rationale": f"API Error {resp.status}", "analyzed_price": price}
                            
                        result = await resp.json()
                        content = result['choices'][0]['message']['content']
                        
                        if "```json" in content:
                            content = content.replace("```json", "").replace("```", "")
                        
                        decision = json.loads(content)
                        
                        # 🔥 MEJORA: Fusionamos la decisión de la IA con los datos matemáticos para el Dashboard
                        return {**decision, **gann_data, "analyzed_price": price}

            except Exception as e:
                self.logger.error(f"Gemini Analysis Error (Attempt {attempt+1}/{retries}): {e}")
                if attempt < retries - 1:
                    import asyncio
                    await asyncio.sleep(base_delay)
                    continue
                return {**gann_data, "action": "hold", "confidence": 0, "rationale": f"Connection Error: {str(e)}", "analyzed_price": price}