"""
Bot Service - GANN ULTRA PRO EDITION
Handles Bot Engine lifecycle, data persistence, and GUI feeds.
FIXED: get_trade_history arguments and added persistent storage.
"""
import asyncio
import logging
import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

from src.backend.bot_engine import TradingBotEngine, BotState
from src.backend.config_loader import CONFIG

class BotService:
    def __init__(self):
        self.bot_engine: Optional[TradingBotEngine] = None
        self.state_manager = None
        self.logger = logging.getLogger(__name__)
        
        # --- ALMACENAMIENTO DE DATOS ---
        self.equity_history: List[Dict] = [] 
        self.recent_events: List[Dict] = []
        self.trade_history: List[Dict] = []
        
        # Cargar historial previo si existe
        self._load_trade_history_from_disk()

    async def start(self):
        """Inicia el motor de trading"""
        if self.bot_engine and self.bot_engine.is_running:
            return

        if not CONFIG.get('openrouter_api_key'):
            raise ValueError("OPENROUTER_API_KEY missing.")
        
        self.bot_engine = TradingBotEngine(
            assets=CONFIG.get('assets'),
            interval=CONFIG.get('interval', '5m'),
            on_state_update=self._on_state_update,
            on_trade_executed=self._on_trade_executed,
            on_error=self._on_error
        )
        
        await self.bot_engine.start()
        self._add_event("🚀 System Initialized - Gann Logic Active", "info")
        self.logger.info("Bot Service Started")

    async def stop(self):
        if self.bot_engine:
            await self.bot_engine.stop()
            self._add_event("🛑 System Halted", "warning")

    def is_running(self) -> bool:
        return self.bot_engine is not None and self.bot_engine.is_running

    def get_state(self) -> BotState:
        if self.bot_engine:
            return self.bot_engine.get_state()
        return BotState()

    def get_assets(self) -> List[str]:
        return CONFIG.get('assets', ['BTC', 'ETH', 'SOL'])

    # ==========================================
    # MÉTODOS DE DATOS PARA LA GUI
    # ==========================================

    def get_equity_history(self) -> List[Dict]:
        return self.equity_history

    def get_recent_events(self, limit: int = 50) -> List[Dict]:
        return list(reversed(self.recent_events[-limit:]))

    # 👇 ESTA ES LA FUNCIÓN CORREGIDA 👇
    def get_trade_history(self, asset: str = None, action: str = None, limit: int = 50) -> List[Dict]:
        """
        Devuelve el historial con filtros opcionales.
        Arregla el error 'unexpected keyword argument asset'.
        """
        filtered = self.trade_history
        
        # Aplicar filtros si existen
        if asset and asset != 'All':
            filtered = [t for t in filtered if t.get('asset') == asset]
        
        if action and action != 'All':
            filtered = [t for t in filtered if t.get('action') == action]
            
        # Devolver los más recientes primero
        return list(reversed(filtered[-limit:]))

    # ==========================================
    # CALLBACKS INTERNOS
    # ==========================================

    def _on_state_update(self, state: BotState):
        if state.total_value > 0:
            self.equity_history.append({
                'time': state.last_update,
                'value': state.total_value
            })
            if len(self.equity_history) > 200:
                self.equity_history.pop(0)
        
        if self.state_manager:
            self.state_manager.update(state)

    def _on_trade_executed(self, trade_info: Dict):
        """Registra el trade en memoria y en disco"""
        msg = f"✅ EXECUTED: {trade_info['action'].upper()} {trade_info['amount']} {trade_info['asset']} @ ${trade_info['price']}"
        self._add_event(msg, "success")
        
        # Agregar timestamp si no viene
        if 'timestamp' not in trade_info:
            trade_info['timestamp'] = datetime.utcnow().isoformat()
            
        self.trade_history.append(trade_info)
        
        # Guardar en disco inmediatamente
        self._save_trade_to_disk(trade_info)

    def _on_error(self, error_msg: str):
        self._add_event(f"⚠️ ERROR: {error_msg}", "error")

    def _add_event(self, message: str, level: str = "info"):
        event = {
            'time': datetime.utcnow().strftime("%H:%M:%S"),
            'message': message,
            'level': level
        }
        self.recent_events.append(event)
        if len(self.recent_events) > 100:
            self.recent_events.pop(0)

    # ==========================================
    # PERSISTENCIA (GUARDAR EN DISCO)
    # ==========================================
    
    def _save_trade_to_disk(self, trade: Dict):
        """Guarda una operación en data/diary.jsonl"""
        try:
            path = Path('data/diary.jsonl')
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'a') as f:
                f.write(json.dumps(trade) + '\n')
        except Exception as e:
            self.logger.error(f"Failed to save trade: {e}")

    def _load_trade_history_from_disk(self):
        """Carga el historial al iniciar"""
        try:
            path = Path('data/diary.jsonl')
            if path.exists():
                with open(path, 'r') as f:
                    for line in f:
                        if line.strip():
                            self.trade_history.append(json.loads(line))
        except Exception as e:
            self.logger.error(f"Failed to load history: {e}")