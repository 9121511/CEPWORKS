"""
Market Data Page - Live W.D. Gann Scanner
"""

from datetime import datetime
from nicegui import ui
from src.gui.services.bot_service import BotService
from src.gui.services.state_manager import StateManager

def create_market(bot_service: BotService, state_manager: StateManager):
    """Create market data page with W.D. Gann Scanner (Finviz Style)"""

    ui.label('GANN GEOMETRIC SCANNER').classes('text-2xl font-bold mb-4 text-emerald-400 tracking-widest')

    # Container for the scanner
    scanner_container = ui.column().classes('w-full')

    # Define columns for the scanner table
    columns = [
        {'name': 'asset', 'label': 'ASSET', 'field': 'asset', 'sortable': True, 'align': 'left'},
        {'name': 'price', 'label': 'PRICE @ TIME', 'field': 'price', 'sortable': True, 'align': 'right'},
        {'name': 'trend', 'label': 'TREND (50%)', 'field': 'trend', 'sortable': True, 'align': 'center'},
        {'name': 'range_pos', 'label': 'POS %', 'field': 'range_pos', 'sortable': True, 'align': 'right'},
        {'name': 'sq9_res', 'label': 'SQ9 RES (+360°)', 'field': 'sq9_res', 'sortable': True, 'align': 'right'},
        {'name': 'sq9_sup', 'label': 'SQ9 SUP (-360°)', 'field': 'sq9_sup', 'sortable': True, 'align': 'right'},
        {'name': 'action', 'label': 'AI ACTION', 'field': 'action', 'sortable': True, 'align': 'center'},
        {'name': 'rationale', 'label': 'KEY OBSERVATION', 'field': 'rationale', 'align': 'left', 'classes': 'text-xs font-mono'},
    ]

    # Create the table
    # Customizing rows via slots/cell-class logic is limited in standard table, 
    # but we can use HTML formatting in values or cell slots. 
    # For "Matrix" feel, we style the table itself.
    market_table = ui.table(
        columns=columns, 
        rows=[], 
        row_key='asset',
        pagination=10
    ).classes('w-full text-gray-300 bg-slate-900 border border-emerald-500/30 font-mono')
    
    # Custom styling for table headers and slots
    market_table.add_slot('header', r'''
        <q-tr :props="props">
            <q-th v-for="col in props.cols" :key="col.name" :props="props" class="text-emerald-500 font-bold uppercase">
                {{ col.label }}
            </q-th>
        </q-tr>
    ''') 

    # Custom styling for body rows (conditional formatting)
    market_table.add_slot('body', r'''
        <q-tr :props="props">
            <q-td key="asset" :props="props" class="font-bold text-white">
                {{ props.row.asset }}
            </q-td>
            <q-td key="price" :props="props">
                <div class="row items-center justify-end">
                    <span class="text-lg font-bold">{{ props.row.price_str }}</span>
                    <span class="text-xs text-gray-500 ml-2">{{ props.row.time_str }}</span>
                </div>
            </q-td>
            <q-td key="trend" :props="props">
                <div :class="props.row.trend === 'BULLISH' ? 'text-green-400 font-bold' : (props.row.trend === 'BEARISH' ? 'text-red-400 font-bold' : 'text-gray-500')">
                    {{ props.row.trend }}
                </div>
            </q-td>
            <q-td key="range_pos" :props="props" class="text-amber-400">
                {{ props.row.range_pos }}
            </q-td>
            <q-td key="sq9_res" :props="props" class="text-green-300/80">
                {{ props.row.sq9_res }}
            </q-td>
             <q-td key="sq9_sup" :props="props" class="text-red-300/80">
                {{ props.row.sq9_sup }}
            </q-td>
            <q-td key="action" :props="props">
                <div class="px-2 py-1 rounded text-center text-xs font-bold"
                     :class="props.row.action === 'BUY' ? 'bg-green-600 text-white' : (props.row.action === 'SELL' ? 'bg-red-600 text-white' : 'bg-gray-700 text-gray-300')">
                    {{ props.row.action }}
                </div>
            </q-td>
            <q-td key="rationale" :props="props" class="whitespace-normal max-w-xs text-xs text-gray-400">
                {{ props.row.rationale }}
            </q-td>
        </q-tr>
    ''')


    # ===== AUTO-REFRESH LOGIC =====
    async def update_scanner():
        """Update scanner table with data for ALL configured assets"""
        state = state_manager.get_state()
        
        # Get list of assets to scan
        configured_assets = bot_service.get_assets() if bot_service.is_running() else ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE']
        
        # We also want to capture assets that might be in reasoning but not in config (historical)
        if hasattr(state, 'last_reasoning') and isinstance(state.last_reasoning, dict):
            reasoning_assets = list(state.last_reasoning.keys())
            configured_assets = list(set(configured_assets + reasoning_assets))
        
        rows = []
        
        for asset in sorted(configured_assets):
            reasoning = {}
            if hasattr(state, 'last_reasoning') and isinstance(state.last_reasoning, dict):
                reasoning = state.last_reasoning.get(asset, {})
            
            # Base data
            price = 0
            time_str = datetime.now().strftime("%H:%M") # Default to now if no timestamp
                
            if reasoning:
                price = reasoning.get('analyzed_price', 0)
                # Check for timestamp in reasoning or use current
                # (TODO: Add 'analyzed_at' to backend if needed, for now use current if fresh)
            else:
                # Fallback to market_data
                 if state.market_data and isinstance(state.market_data, dict):
                     asset_data = state.market_data.get(asset, {})
                     price = asset_data.get('price', 0)

            # --- Formatting Logic ---
            
            # Trend
            trend = reasoning.get('trend_50_rule', 'WAITING')
            
            # Range Pos
            range_pos_str = '--'
            range_price = reasoning.get('range_price', 0)
            major_low = reasoning.get('major_low', 0)
            major_high = reasoning.get('major_high', 0)
            
            if range_price > 0 and major_high > major_low and price > 0:
                pos_pct = ((price - major_low) / range_price) * 100
                range_pos_str = f"{pos_pct:.1f}%"
            
            # Geometry
            sq9_res = f"${reasoning.get('sq9_next_resistance', 0):,.2f}"
            sq9_sup = f"${reasoning.get('sq9_next_support', 0):,.2f}"
            
            # AI
            action = reasoning.get('action', 'HOLD').upper()
            rationale = reasoning.get('rationale', 'Initializing...')
            
            # Fix empty values
            if price == 0:
                price_str = "$0.00"
                trend = "OFFLINE"
            else:
                price_str = f"${price:,.2f}"

            # Append Row
            rows.append({
                'asset': asset,
                'price': price, # For sorting
                'price_str': price_str,
                'time_str': time_str,
                'trend': trend,
                'range_pos': range_pos_str,
                'sq9_res': sq9_res,
                'sq9_sup': sq9_sup,
                'action': action,
                'rationale': rationale
            })
            
        market_table.rows = rows
        market_table.update()

    # Update immediately and then timer
    # Update immediately via one-shot timer to avoid RuntimeWarning
    ui.timer(0.1, update_scanner, once=True)
    ui.timer(5.0, update_scanner) # 5s refresh for scanner
