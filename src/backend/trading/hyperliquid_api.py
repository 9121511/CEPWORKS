"""
Hyperliquid API Client
Handles connection and trading operations with Hyperliquid DEX.
FINAL VERSION: Includes Balance, Open Orders, Fills, and wrapper methods for Trading.
"""

import os
import logging
import asyncio
from typing import Dict, List, Optional, Any
from eth_account import Account
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants

from src.backend.config_loader import CONFIG

class HyperliquidAPI:
    """Interface for Hyperliquid interactions"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 1. Cargar Private Key
        self.private_key = CONFIG.get("hyperliquid_private_key")
        if not self.private_key:
            raise ValueError("Private key not found in configuration")
            
        if self.private_key.startswith("0x"):
            self.private_key = self.private_key[2:]
            
        self.account = Account.from_key(self.private_key)
        
        # 2. Cargar Main Address
        self.main_address = CONFIG.get("hyperliquid_account_address") or os.getenv("HYPERLIQUID_ACCOUNT_ADDRESS")
        
        if self.main_address:
            self.logger.info(f"Using Main Account Address for Balance/Fills: {self.main_address}")
        else:
            self.logger.warning("No Main Account Address set. Using Agent wallet.")

        # 3. Configurar Red
        self.network = CONFIG.get("hyperliquid_network", "mainnet")
        base_url = constants.MAINNET_API_URL if self.network == "mainnet" else constants.TESTNET_API_URL
        
        self.info = Info(base_url, skip_ws=True)
        self.exchange = Exchange(self.account, base_url)
        
        self.logger.info(f"Hyperliquid API initialized on {self.network}")

    async def get_user_state(self) -> Dict[str, Any]:
        """Fetch account balance and positions."""
        try:
            target_address = self.main_address if self.main_address else self.account.address
            state = self.info.user_state(target_address)
            
            margin_summary = state.get("marginSummary", {})
            account_value = float(margin_summary.get("accountValue", 0))
            withdrawable = float(state.get("withdrawable", 0))
            
            if withdrawable == 0 and account_value > 0:
                withdrawable = account_value

            positions = []
            raw_positions = state.get("assetPositions", [])
            
            for p in raw_positions:
                pos = p.get("position", {})
                coin = pos.get("coin")
                size = float(pos.get("szi", 0))
                
                if size != 0:
                    positions.append({
                        "asset": coin,
                        "amount": size,
                        "entry_price": float(pos.get("entryPx", 0)),
                        "pnl": float(pos.get("unrealizedPnl", 0)),
                        "leverage": float(pos.get("leverage", {}).get("value", 0)) if isinstance(pos.get("leverage"), dict) else 0,
                        "liquidation_price": float(pos.get("liquidationPx", 0) or 0)
                    })

            return {
                "balance": withdrawable,
                "total_value": account_value,
                "positions": positions
            }

        except Exception as e:
            self.logger.error(f"Error fetching user state: {e}")
            return {"balance": 0.0, "total_value": 0.0, "positions": []}

    async def get_open_orders(self) -> List[Dict]:
        """Fetch current open orders"""
        try:
            target_address = self.main_address if self.main_address else self.account.address
            raw_orders = self.info.open_orders(target_address)
            
            formatted_orders = []
            for o in raw_orders:
                formatted_orders.append({
                    "id": str(o.get("oid")),
                    "asset": o.get("coin"),
                    "side": "buy" if o.get("side") == "B" else "sell",
                    "amount": float(o.get("sz")),
                    "price": float(o.get("limitPx")),
                    "timestamp": o.get("timestamp")
                })
            return formatted_orders
        except Exception as e:
            self.logger.error(f"Error fetching open orders: {e}")
            return []

    async def get_recent_fills(self, limit: int = 50) -> List[Dict]:
        """Fetch recent trade fills history"""
        try:
            target_address = self.main_address if self.main_address else self.account.address
            raw_fills = self.info.user_fills(target_address)
            
            formatted_fills = []
            for f in raw_fills:
                formatted_fills.append({
                    "id": str(f.get("oid", "")),
                    "asset": f.get("coin", ""),
                    "side": "buy" if f.get("side") == "B" else "sell",
                    "price": float(f.get("px", 0)),
                    "amount": float(f.get("sz", 0)),
                    "fee": float(f.get("fee", 0)),
                    "timestamp": f.get("time", 0),
                    "type": "fill"
                })
            
            formatted_fills.sort(key=lambda x: x["timestamp"], reverse=True)
            return formatted_fills[:limit]
        except Exception as e:
            self.logger.error(f"Error fetching fills: {e}")
            return []

    async def get_current_price(self, asset: str) -> Optional[float]:
        try:
            prices = self.info.all_mids()
            if asset in prices:
                return float(prices[asset])
            return None
        except Exception as e:
            self.logger.error(f"Error fetching price for {asset}: {e}")
            return None

    async def get_funding_rate(self, asset: str) -> Optional[float]:
        return 0.01

    async def get_open_interest(self, asset: str) -> Optional[float]:
        return 0.0

    async def create_order(self, asset: str, is_buy: bool, amount: float, price: float, 
                          order_type: str = "limit", reduce_only: bool = False) -> Dict:
        """Execute an order using the Agent Private Key"""
        try:
            price = float(price)
            # Rounding to 5 significant digits (approx) for safety
            price = round(price, 5) 
            amount = round(amount, 5)
            
            result = self.exchange.order(
                name=asset,
                is_buy=is_buy,
                sz=amount,
                limit_px=price,
                order_type={"limit": {"tif": "Gtc"}},
                reduce_only=reduce_only
            )
            
            status = result.get("status", "error")
            if status == "ok":
                response = result.get("response", {})
                data = response.get("data", {})
                statuses = data.get("statuses", [])
                
                if statuses and "error" in statuses[0]:
                    raise Exception(f"Order error: {statuses[0]}")
                    
                return {
                    "status": "filled" if "filling" in statuses[0] else "open",
                    "order_id": str(statuses[0].get("oid", "")),
                    "price": price,
                    "amount": amount
                }
            else:
                raise Exception(f"Exchange API error: {result}")

        except Exception as e:
            self.logger.error(f"Order failed: {e}")
            raise

    async def cancel_order(self, asset: str, order_id: str) -> bool:
        try:
            result = self.exchange.cancel(asset, int(order_id))
            return result.get("status") == "ok"
        except Exception as e:
            self.logger.error(f"Cancel failed: {e}")
            return False

    async def close_position(self, asset: str) -> bool:
        try:
            state = await self.get_user_state()
            position = next((p for p in state["positions"] if p["asset"] == asset), None)
            if not position: return False
            amount = position["amount"]
            is_buy = amount < 0 
            result = self.exchange.market_open(name=asset, is_buy=is_buy, sz=abs(amount))
            return result.get("status") == "ok"
        except Exception as e:
            self.logger.error(f"Close position failed: {e}")
            return False

    # === NUEVAS FUNCIONES AGREGADAS ===
    # Estos son los "botones" que el motor estaba buscando
    async def place_buy_order(self, asset: str, amount: float, price: float, order_type: str = "limit") -> Dict:
        """Wrapper for create_order (Buy)"""
        return await self.create_order(asset, True, amount, price, order_type)

    async def place_sell_order(self, asset: str, amount: float, price: float, order_type: str = "limit") -> Dict:
        """Wrapper for create_order (Sell)"""
        return await self.create_order(asset, False, amount, price, order_type)