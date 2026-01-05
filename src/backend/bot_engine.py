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
            
            # Llamada al agente (Gemini 2.0)
            decision = await self.agent.analyze(
                asset=asset,
                price=current_price,
                indicators={}, # Ya no usamos indicadores externos
                current_position=current_pos
            )
            
            # Guardar razonamiento para la GUI
            self.state.last_reasoning[asset] = {
                'action': decision.get('action'),
                'confidence': decision.get('confidence'),
                'rationale': decision.get('rationale'),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Si Gemini decide operar
            if decision['action'] in ['buy', 'sell']:
                proposal = TradeProposal(
                    asset=asset,
                    action=decision['action'],
                    entry_price=current_price,
                    amount=self._calculate_position_size(current_price),
                    confidence=decision.get('confidence', 0.5),
                    rationale=decision.get('rationale', '')
                )
                
                self.state.pending_proposals.append(proposal)
                # Ejecución automática (puedes comentarlo si prefieres manual)
                await self.approve_proposal(proposal.id, proposal)

        except Exception as e:
            self.logger.error(f"Error processing {asset}: {e}")

    def _calculate_position_size(self, price: float) -> float:
        """Tamaño fijo de 10 USD por operación para protección del saldo"""
        usd_size = 10.0 
        return round(usd_size / price, 5)

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