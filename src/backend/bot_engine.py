"""
Trading Bot Engine - GANN ONLY EDITION
Core logic for the trading bot.
REMOVED: All TAAPI dependencies.
FIXED: Missing attributes (error, sharpe_ratio, etc.) to prevent GUI crashes.
"""

import asyncio
import logging
import json
import traceback
from datetime import datetime
from typing import List, Dict, Callable, Optional, Union
from dataclasses import dataclass, field

from src.backend.trading.hyperliquid_api import HyperliquidAPI
from src.backend.agent.decision_maker import TradingAgent

# ==========================================
# DEFINICIONES DE CLASES (BotState & Proposal)
# ==========================================

@dataclass
class TradeProposal:
    asset: str
    action: str  # 'buy' or 'sell'
    entry_price: float
    amount: float
    confidence: float
    rationale: str
    id: str = field(default_factory=lambda: datetime.now().strftime("%Y%m%d%H%M%S"))
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.utcnow)
    risk_reward_ratio: float = 0.0
    tp_price: float = 0.0
    sl_price: float = 0.0
    gann_thoughts: str = "" # Emoji-rich reasoning

@dataclass
class BotState:
    is_running: bool = False
    balance: float = 0.0
    total_value: float = 0.0
    start_balance: float = 0.0
    
    # --- MÉTRICAS FINANCIERAS (Requeridas por Dashboard) ---
    total_return_pct: float = 0.0
    sharpe_ratio: float = 0.0
    win_rate: float = 0.0
    max_drawdown: float = 0.0
    trades_count: int = 0
    
    # --- DATOS OPERATIVOS ---
    positions: List[Dict] = field(default_factory=list)
    open_orders: List[Dict] = field(default_factory=list)
    market_data: Dict = field(default_factory=dict)
    
    # --- DATOS DE IA ---
    active_proposals: List[TradeProposal] = field(default_factory=list)
    pending_proposals: List[TradeProposal] = field(default_factory=list)
    last_reasoning: Dict = field(default_factory=dict)
    
    last_update: str = ""
    
    # --- MANEJO DE ERRORES ---
    errors: List[str] = field(default_factory=list)
    error: str = "" # Alias para evitar AttributeError en la GUI

# ==========================================
# MOTOR PRINCIPAL
# ==========================================

class TradingBotEngine:
    def __init__(self, assets: List[str], interval: str, 
                 on_state_update: Optional[Callable] = None,
                 on_trade_executed: Optional[Callable] = None,
                 on_error: Optional[Callable] = None):
        
        self.logger = logging.getLogger(__name__)
        self.assets = assets
        self.interval = interval
        self.is_running = False
        self.state = BotState()
        
        # Callbacks
        self.on_state_update = on_state_update
        self.on_trade_executed = on_trade_executed
        self.on_error = on_error

        # COMPONENTES (Solo Hyperliquid y Gemini)
        self.hyperliquid = HyperliquidAPI()
        self.agent = TradingAgent()
        
        self._loop_task = None
        self._stop_event = asyncio.Event()

    def get_assets(self) -> List[str]:
        """Retorna la lista de activos configurados"""
        return self.assets

    async def start(self):
        """Inicia el bot"""
        if self.is_running: return
        
        self.logger.info(f"Gann Bot Engaged - Assets: {self.assets}")
        self.is_running = True
        self._stop_event.clear()
        
        # Sincronización inicial
        await self._update_account_state()
        
        # ENFORCE LEVERAGE (Max 7x per user request)
        # We cap at 7x here regardless of settings for safety, or use config
        from src.backend.config_loader import CONFIG
        max_leverage = min(CONFIG.get('risk_management', {}).get('max_leverage', 3), 7)
        
        for asset in self.assets:
            try:
                # Default to isolated margin (is_cross=False)
                await self.hyperliquid.update_leverage(asset, int(max_leverage), is_cross=False)
            except Exception as e:
                self.logger.error(f"Failed to set leverage for {asset}: {e}")

        if self.state.total_value > 0 and self.state.start_balance == 0:
             self.state.start_balance = self.state.total_value
        
        self._loop_task = asyncio.create_task(self._main_loop())

    async def stop(self):
        """Detiene el bot"""
        self.is_running = False
        self._stop_event.set()
        if self._loop_task:
            await self._loop_task
        self.logger.info("Bot stopped successfully")

    def get_state(self) -> BotState:
        return self.state

    async def _main_loop(self):
        """Bucle principal de ejecución cada 60 segundos"""
        while self.is_running:
            try:
                # 1. Actualizar balance y órdenes
                await self._update_account_state()
                await self._update_orders_and_fills()

                # 2. Analizar cada activo con Gemini
                for asset in self.assets:
                    if not self.is_running: break
                    await self._process_asset(asset)
                    # THROTTLING: Wait 2s between assets to avoid LLM Rate Limits
                    await asyncio.sleep(2)

                # 3. Actualizar Interfaz
                if self.on_state_update:
                    self.on_state_update(self.state)

                await asyncio.sleep(60)

            except Exception as e:
                err_msg = f"Loop Error: {str(e)}"
                self.logger.error(err_msg)
                self.state.error = err_msg
                if self.on_error:
                    self.on_error(err_msg)
                await asyncio.sleep(10)

    async def _update_account_state(self):
        """Sincroniza con la API de Hyperliquid"""
        try:
            state_data = await self.hyperliquid.get_user_state()
            self.state.balance = state_data.get('balance', 0)
            self.state.total_value = state_data.get('total_value', 0)
            self.state.positions = state_data.get('positions', [])
            self.state.last_update = datetime.utcnow().isoformat()

            # Cálculo de retorno de sesión
            if self.state.start_balance > 0:
                pnl = self.state.total_value - self.state.start_balance
                self.state.total_return_pct = (pnl / self.state.start_balance) * 100
            else:
                self.state.total_return_pct = 0.0
        except Exception as e:
            self.logger.error(f"Account state sync failed: {e}")

    async def _update_orders_and_fills(self):
        """Sincroniza órdenes abiertas"""
        try:
            self.state.open_orders = await self.hyperliquid.get_open_orders()
        except Exception as e:
            self.logger.error(f"Order Sync Error: {e}")

    async def _process_asset(self, asset: str):
        """Análisis puro Gann vía Gemini"""
        try:
            current_price = await self.hyperliquid.get_current_price(asset)
            if not current_price: return

            if asset not in self.state.market_data:
                self.state.market_data[asset] = {}
            self.state.market_data[asset]['price'] = current_price

            # Contexto operativo para Gemini
            current_pos = next((p for p in self.state.positions if p['asset'] == asset), None)
            
            # --- FETCH OHLC IN MULTIPLE TIMEFRAMES ---
            # User requested: Daily, Weekly, Monthly, Intraday (4m -> using 5m as proxy)
            # Hyperliquid intervals: 1m, 5m, 15m, 30m, 1h, 2h, 4h, 8h, 12h, 1d
            
            # Fetch concurrently to save time
            candles_1d, candles_1h, candles_5m = await asyncio.gather(
                asyncio.to_thread(self.hyperliquid.get_ohlc, asset, '1d'),
                asyncio.to_thread(self.hyperliquid.get_ohlc, asset, '1h'),
                asyncio.to_thread(self.hyperliquid.get_ohlc, asset, '5m')
            )
            
            indicators = {}
            
            # 1. DAILY / WEEKLY / MONTHLY CONTEXT (Derived from 1d)
            if candles_1d:
                # Basic Swing High/Low (last 30 days ~ Monthly)
                recent_30d = candles_1d[-30:] if len(candles_1d) > 30 else candles_1d
                highs_30d = [c['high'] for c in recent_30d]
                lows_30d = [c['low'] for c in recent_30d]
                
                indicators['high_swing'] = max(highs_30d) if highs_30d else current_price * 1.1
                indicators['low_swing'] = min(lows_30d) if lows_30d else current_price * 0.9
                
                # Monthly / Weekly estimation
                indicators['monthly_open'] = recent_30d[0]['open'] if recent_30d else 0
                indicators['weekly_open'] = candles_1d[-7]['open'] if len(candles_1d) >= 7 else candles_1d[0]['open']
                
                indicators['prev_close'] = candles_1d[-2]['close'] if len(candles_1d) >= 2 else current_price
                indicators['day_open'] = candles_1d[-1]['open'] if candles_1d else current_price
                indicators['day_high'] = candles_1d[-1]['high'] if candles_1d else current_price
                indicators['day_low'] = candles_1d[-1]['low'] if candles_1d else current_price
            
            # 2. INTRADAY CONTEXT (5m - User asked for 4m, using 5m as standard proxy)
            if candles_5m:
                recent_5m = candles_5m[-12:] # Last hour
                indicators['last_5m_opens'] = [c['open'] for c in recent_5m]
                indicators['last_5m_closes'] = [c['close'] for c in recent_5m]
                indicators['intraday_trend'] = 'BULLISH' if recent_5m[-1]['close'] > recent_5m[0]['open'] else 'BEARISH'
            
            # 3. HOURLY CONTEXT
            if candles_1h:
                indicators['ma_20_1h'] = sum(c['close'] for c in candles_1h[-20:]) / 20 if len(candles_1h) >= 20 else current_price
            
            # Llamada al agente (Gemini 2.0)
            decision = await self.agent.analyze(
                asset=asset,
                price=current_price,
                indicators=indicators,
                current_position=current_pos
            )
            
            # Guardar razonamiento completo con todos los datos de Gann para la GUI
            self.state.last_reasoning[asset] = {
                'action': decision.get('action'),
                'confidence': decision.get('confidence'),
                'rationale': decision.get('rationale'),
                'gann_thoughts': decision.get('gann_thoughts', ''), # Capture emoji reasoning
                'entry_plan': decision.get('entry_plan', 'No entry plan provided'),
                'exit_plan': decision.get('exit_plan', 'No exit plan provided'),
                'gann_analysis': decision.get('gann_analysis', ''),
                'timestamp': datetime.utcnow().isoformat(),
                # Incluir todos los datos de Gann calculados
                'analyzed_price': decision.get('analyzed_price', current_price),
                'level_50_percent': decision.get('level_50_percent'),
                'level_25_percent': decision.get('level_25_percent'),
                'level_75_percent': decision.get('level_75_percent'),
                'level_33_percent': decision.get('level_33_percent'),
                'level_66_percent': decision.get('level_66_percent'),
                'sq9_next_resistance': decision.get('sq9_next_resistance'),
                'sq9_next_support': decision.get('sq9_next_support'),
                'sq9_resistance_720': decision.get('sq9_resistance_720'),
                'sq9_support_720': decision.get('sq9_support_720'),
                'trend_50_rule': decision.get('trend_50_rule'),
                'major_high': decision.get('major_high'),
                'major_low': decision.get('major_low'),
                'range_price': decision.get('range_price'),
                'distance_to_50_pct': decision.get('distance_to_50_pct'),
                'distance_to_resistance_pct': decision.get('distance_to_resistance_pct'),
                'distance_to_support_pct': decision.get('distance_to_support_pct'),
                'gann_1x1_angle_base': decision.get('gann_1x1_angle_base'),
                'time_cycle_degrees': decision.get('time_cycle_degrees'),
                'root_price': decision.get('root_price'),
                'gann_angle_status': decision.get('gann_angle_status'),
                'stop_loss': decision.get('stop_loss'),
                'take_profit': decision.get('take_profit')
            }

            # Update position metadata if exists
            if current_pos:
                current_pos['take_profit'] = decision.get('take_profit')
                current_pos['stop_loss'] = decision.get('stop_loss')
            
            # Si Gemini decide operar
            if decision['action'] in ['buy', 'sell', 'close', 'reverse']:
                proposal = TradeProposal(
                    asset=asset,
                    action=decision['action'],
                    entry_price=current_price,
                    amount=self._calculate_position_size(current_price),
                    confidence=decision.get('confidence', 0.5),
                    rationale=decision.get('rationale', ''),
                    gann_thoughts=decision.get('gann_thoughts', '')
                )
                
                # Para close/reverse, la cantidad puede ser irrelevante aqui, se calcula en ejecucion
                if decision['action'] in ['close', 'reverse']:
                    proposal.amount = 0 # Placeholder
                    
                self.state.pending_proposals.append(proposal)
                # Ejecución automática (puedes comentarlo si prefieres manual)
                await self.approve_proposal(proposal.id, proposal)

        except Exception as e:
            self.logger.error(f"Error processing {asset}: {e}")

    def _calculate_position_size(self, price: float) -> float:
        """
        Calcula el tamaño de la posición con gestión de riesgo 'Tranquila'.
        Allocación: 5% del Equity Total (o el mínimo de $12 USD).
        """
        try:
            # 1. Obtener Equity Total
            total_equity = self.state.total_value
            if total_equity <= 0:
                # Fallback si no se ha sincronizado aun
                total_equity = 20.0 # Asumir algo bajo para seguridad
            
            # --- CIRCUIT BREAKER: LOW BALANCE ---
            # Si el balance es peligrosamente bajo (< $2), ni siquiera intentar
            if self.state.balance < 2.0:
                 if self.state.balance > 0.1: # Log only if not practically zero to avoid crazy spam if empty
                     self.logger.warning(f"CIRCUIT BREAKER: Balance too low (${self.state.balance:.2f}) to trade safely.")
                 return 0.0

            # 2. Calcular Target Size (5% del equity)
            
            # 2. Calcular Target Size (5% del equity)
            target_usd_size = total_equity * 0.05
            
            # 3. Aplicar Limites
            # Mínimo absoluto para Hyperliquid es $10, usamos $12 por seguridad + fees
            min_usd_size = 12.0
            
            # Si el 5% es menor que $12, forzamos $12 (riesgo un poco mayor para cuentas pequeñas)
            if target_usd_size < min_usd_size:
                target_usd_size = min_usd_size
                
            # Verificar si tenemos suficiente 'withdrawable'
            # Nota: Esto es una estimación, lo ideal es que la API rechace si no hay margen
            # Pero ajustamos aquí para "intentar" que pase.
            if target_usd_size > self.state.balance * 0.95:
                 # Si no hay balance libre suficiente, usar lo que haya (menos un buffer del 5%)
                 target_usd_size = self.state.balance * 0.95
                 
            # Si aun así es menor que el mínimo, retornamos 0 para no saturar la API con errores
            if target_usd_size < 10.0:
                self.logger.warning(f"Insufficient funds for min order. Balance: {self.state.balance}")
                return 0.0

            # 4. Calcular cantidad en activo
            amount = target_usd_size / price
            return round(amount, 5)

        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return 0.0

    async def approve_proposal(self, proposal_id: str, proposal_obj: Optional[TradeProposal] = None):
        """Ejecuta la orden en Hyperliquid"""
        proposal = proposal_obj or next((p for p in self.state.pending_proposals if p.id == proposal_id), None)
        if not proposal: return

        self.logger.info(f"Executing trade: {proposal.action} {proposal.asset}")
        
        try:
            if proposal.action == 'buy':
                await self.hyperliquid.place_buy_order(proposal.asset, proposal.amount, proposal.entry_price)
            elif proposal.action == 'sell':
                await self.hyperliquid.place_sell_order(proposal.asset, proposal.amount, proposal.entry_price)
            elif proposal.action == 'close':
                await self.hyperliquid.close_position(proposal.asset)
            elif proposal.action == 'reverse':
                # 1. Close existing
                await self.hyperliquid.close_position(proposal.asset)
                # 2. Wait a bit
                await asyncio.sleep(2)
                # 3. Open opposite (need to know which side, usually reverse means flip)
                # To keep it simple, reverse might just close for now, OR we need the agent to specify direction
                # Standard reverse: if long -> short, if short -> long.
                # Find current pos
                current_pos = next((p for p in self.state.positions if p['asset'] == proposal.asset), None)
                if current_pos:
                    is_long = current_pos['amount'] > 0
                    new_action = 'sell' if is_long else 'buy'
                    new_amount = self._calculate_position_size(proposal.entry_price)
                    if new_action == 'buy':
                        await self.hyperliquid.place_buy_order(proposal.asset, new_amount, proposal.entry_price)
                    else:
                        await self.hyperliquid.place_sell_order(proposal.asset, new_amount, proposal.entry_price)
            
            self.state.trades_count += 1
            # Limpiar de pendientes
            self.state.pending_proposals = [p for p in self.state.pending_proposals if p.id != proposal_id]
            
            if self.on_trade_executed:
                self.on_trade_executed({
                    'asset': proposal.asset,
                    'action': proposal.action,
                    'amount': proposal.amount,
                    'price': proposal.entry_price
                })
        except Exception as e:
            self.logger.error(f"Trade Fail: {e}")
            self.state.error = f"Trade Failed: {str(e)}"

    async def reject_proposal(self, proposal_id: str, reason: str):
        self.state.pending_proposals = [p for p in self.state.pending_proposals if p.id != proposal_id]
        
    async def close_position(self, asset: str) -> bool:
        return await self.hyperliquid.close_position(asset)

    def get_pending_proposals(self) -> List[TradeProposal]:
        return self.state.pending_proposals