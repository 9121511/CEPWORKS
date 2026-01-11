"""
Dashboard Page - Hybrid Apple/Matrix Style
Full Screen Layout
"""

from nicegui import ui
from src.gui.services.bot_service import BotService
from src.gui.services.state_manager import StateManager

def create_dashboard(bot_service: BotService, state_manager: StateManager):
    """Create dashboard page with high-density grid and hybrid styling"""
    
    state = state_manager.get_state()

    # Container needs to be full height of parent
    with ui.column().classes('w-full h-full gap-6'):  # Main column fills content area

        # --- HEADER & CONTROLS ---
        with ui.row().classes('w-full items-center justify-between'):
            with ui.column().classes('gap-0'):
                ui.label('MISSION CONTROL').classes('text-2xl font-bold text-white font-mono tracking-tight')
                ui.label(f'SYSTEM MONITORING // {len(state.last_reasoning)} ASSETS TRACKED').classes('text-[10px] text-[#00ff41] font-mono tracking-widest opacity-80')
            
            # Bot Toggle
            async def toggle_bot():
                if bot_service.is_running():
                    await bot_service.stop()
                else:
                    await bot_service.start()
                update_dashboard()

            btn_color = 'bg-[#1a0000] text-[#ff0000] border-[#ff0000]' if state.is_running else 'bg-[#001a00] text-[#00ff41] border-[#00ff41]'
            btn_text = 'TERMINATE PROTOCOL' if state.is_running else 'INITIATE SEQUENCE'
            
            ui.button(btn_text, on_click=toggle_bot, icon='power_settings_new').classes(f'border {btn_color} px-6 py-2 font-mono text-xs font-bold rounded hover:opacity-80')

        # --- METRICS ROW ---
        with ui.grid(columns=4).classes('w-full gap-4'):
            def stat_card(label, value, sub, icon, accent_class):
                with ui.card().classes('bg-[#0a0a0a] border border-[#1a1a1a] p-4 flex flex-row items-center gap-4 rounded-lg hover:border-[#333] transition-colors shadow-none'):
                    ui.icon(icon).classes(f'text-3xl {accent_class} opacity-80')
                    with ui.column().classes('gap-0'):
                        ui.label(label).classes('text-[10px] text-gray-500 font-mono uppercase tracking-widest')
                        ui.label(value).classes('text-xl font-bold text-white font-mono')
                        ui.label(sub).classes(f'text-[10px] {accent_class} font-mono')

            pnl = state.total_value - state.start_balance
            pnl_color = 'text-[#00ff41]' if pnl >= 0 else 'text-[#ff0000]'
            
            stat_card('NET EQUITY', f'${state.total_value:,.2f}', f'{pnl:+.2f} USD', 'account_balance', pnl_color)
            stat_card('EXPOSURE', str(len(state.positions)), 'OPEN POSITIONS', 'layers', 'text-[#00ff41]')
            stat_card('PERFORMANCE', f'{state.win_rate:.1f}%', f'{state.trades_count} EXEC', 'analytics', 'text-yellow-400')
            stat_card('RISK FACTOR', f'{state.sharpe_ratio:.2f}', 'SHARPE RATIO', 'security', 'text-blue-400')

        # --- INTELLIGENCE PARAMETERS ---
        from src.backend.agent.decision_maker import TradingAgent
        with ui.expansion('INTELLIGENCE PARAMETERS // GANN-MATH-ENGINE', icon='psychology').classes('w-full border border-[#1a1a1a] bg-[#050505] text-[#00ff41] font-mono text-xs'):
            with ui.row().classes('w-full p-4 gap-6'):
                with ui.column().classes('flex-1 gap-2'):
                    ui.label('PRIMARY DIRECTITVE (PROMPT IDENTITY):').classes('font-bold text-white opacity-80')
                    ui.label(TradingAgent.AGENT_IDENTITY).classes('text-gray-400 italic border-l-2 border-[#00ff41] pl-2')
                
                with ui.column().classes('flex-1 gap-2'):
                    ui.label('WD GANN STRICT RULES:').classes('font-bold text-white opacity-80')
                    for rule in TradingAgent.GANN_RULES:
                        ui.label(rule).classes('text-[#00ff41]')

        # --- DATA GRID (FLEX GROW) ---
        # This container expands to fill the rest of the 27" screen
        with ui.column().classes('w-full flex-grow bg-[#0a0a0a] border border-[#1a1a1a] rounded-lg overflow-hidden relative flex flex-col'):
            
            # Grid Header
            with ui.row().classes('w-full p-2 pl-4 border-b border-[#1a1a1a] items-center justify-between bg-[#050505] shrink-0'):
                 with ui.row().classes('items-center gap-2'):
                     ui.icon('table_chart', size='16px').classes('text-[#00ff41]')
                     ui.label('MARKET_INTELLIGENCE_MATRIX').classes('text-xs font-mono font-bold text-[#00ff41]')
                 
                 ui.input(placeholder='SEARCH...').props('dense borderless dark').classes('font-mono text-xs bg-[#1a1a1a] px-2 rounded text-white')

            # AgGrid - Height 100% of parent flex container
            grid = ui.aggrid({
                'columnDefs': [
                    {'headerName': 'ASSET', 'field': 'asset', 'pinned': 'left', 'width': 80, 'cellClass': 'font-bold'},
                    {'headerName': 'PRICE', 'field': 'price', 'width': 90},
                    {'headerName': 'SIGNAL', 'field': 'signal', 'width': 80, 'cellStyle': {'fontWeight': 'bold'}},
                    {'headerName': 'CONF', 'field': 'confidence', 'width': 70},
                    {'headerName': 'ENTRY PLAN', 'field': 'entry', 'width': 150, 'tooltipField': 'entry'},
                    {'headerName': 'EXIT PLAN', 'field': 'exit', 'width': 150, 'tooltipField': 'exit'},
                    {'headerName': 'GANN ANALYSIS (THOUGHTS)', 'field': 'gann', 'flex': 1, 'minWidth': 200, 'tooltipField': 'gann'},
                    {'headerName': '50% LEVEL', 'field': 'level_50', 'width': 90},
                    {'headerName': 'SQ9 RES', 'field': 'sq9_res', 'width': 90},
                    {'headerName': 'SQ9 SUP', 'field': 'sq9_sup', 'width': 90},
                    {'headerName': 'TREND', 'field': 'trend', 'width': 90},
                ],
                'defaultColDef': {
                    'sortable': True,
                    'filter': True,
                    'resizable': True,
                    'cellClass': 'font-mono text-xs flex items-center',
                    'headerClass': 'font-mono text-xs font-bold text-[#00ff41] bg-[#000]'
                },
                'rowHeight': 40,
                'headerHeight': 35,
                'theme': 'ag-theme-balham-dark',
                'enableCellTextSelection': True
            }).classes('w-full h-full border-none')  # h-full is critical here

    # --- REFRESH ---
    async def update_dashboard():
        try:
            state = state_manager.get_state()
            last_reasoning = getattr(state, 'last_reasoning', {})
            
            rows = []
            if last_reasoning:
                for asset, data in last_reasoning.items():
                    if not isinstance(data, dict): continue
                    
                    rows.append({
                        'asset': asset,
                        'price': f"${data.get('analyzed_price', 0):,.2f}",
                        'signal': data.get('action', 'HOLD').upper(),
                        'confidence': f"{data.get('confidence', 0)*100:.0f}%",
                        'entry': data.get('entry_plan', '-'),
                        'exit': data.get('exit_plan', '-'),
                        'gann': data.get('gann_thoughts', '-'),
                        'level_50': f"${data.get('level_50_percent', 0):,.2f}",
                        'sq9_res': f"${data.get('sq9_next_resistance', 0):,.2f}",
                        'sq9_sup': f"${data.get('sq9_next_support', 0):,.2f}",
                        'trend': data.get('trend_50_rule', '-')
                    })
            
            if rows:
                grid.options['rowData'] = rows
                grid.update()
        except: pass

    ui.timer(2.0, update_dashboard)
