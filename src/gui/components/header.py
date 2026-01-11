"""
Header Component - W.D. Gann Ultra Pro Style
Displays real-time status, equity, and PnL with a professional financial terminal look.
"""

from nicegui import ui
from datetime import datetime
from src.gui.services.state_manager import StateManager
from src.gui.services.bot_service import BotService

def create_header(bot_service: BotService, state_manager: StateManager):
    """Creates the top navigation and status bar with Gann Aesthetics"""

    with ui.header().classes(
        'w-full h-20 flex items-center justify-between px-6 '
        'bg-black border-b border-green-900 shadow-[0_0_15px_rgba(0,255,0,0.1)]'
    ):
        # --- LEFT: BRANDING & STATUS ---
        with ui.row().classes('items-center gap-4'):
            # Logo / Title with Matrix Theme
            with ui.column().classes('gap-0'):
                ui.label('CASTILLO').classes(
                    'text-2xl font-black tracking-widest text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-green-700'
                )
                ui.label('CAPITAL SYSTEMS | GANN').classes(
                    'text-[10px] tracking-[0.2em] text-green-500 font-mono'
                )
            
            # Vertical Separator
            ui.element('div').classes('h-10 w-px bg-green-900 mx-2')

            # Status Indicator (Glowing Dot)
            with ui.row().classes('items-center gap-2 bg-black px-3 py-1 rounded-full border border-green-900'):
                status_dot = ui.element('div').classes(
                    'w-3 h-3 rounded-full bg-red-600 shadow-[0_0_8px_rgba(255,0,0,0.6)]'
                )
                status_label = ui.label('DISCONNECTED').classes('text-xs font-bold text-green-800')

        # --- CENTER: KEY METRICS (Balance & PnL) ---
        # Designed like a ticker tape / cockpit
        with ui.row().classes('items-center gap-8'):
            
            # Balance Display
            with ui.column().classes('items-center gap-0'):
                ui.label('TOTAL EQUITY').classes('text-[10px] font-mono text-green-800 tracking-wider')
                balance_label = ui.label('$0.00').classes(
                    'text-xl font-mono font-bold text-green-400 tracking-tight'
                )

            # PnL Display (The most important number)
            with ui.column().classes('items-center gap-0'):
                ui.label('SESSION RETURN').classes('text-[10px] font-mono text-green-800 tracking-wider')
                pnl_label = ui.label('0.00%').classes(
                    'text-xl font-mono font-bold text-green-400 tracking-tight'
                )

            # Available Liquidity
            with ui.column().classes('items-center gap-0'):
                ui.label('LIQUIDITY (USDC)').classes('text-[10px] font-mono text-green-800 tracking-wider')
                liquidity_label = ui.label('$0.00').classes(
                    'text-lg font-mono text-green-600'
                )

        # --- RIGHT: SYSTEM TIME & CONTROLS ---
        with ui.row().classes('items-center gap-4'):
            # System Time (Crucial for Gann Analysis)
            with ui.column().classes('items-end gap-0 mr-4'):
                time_label = ui.label('00:00:00 UTC').classes('text-lg font-mono font-bold text-green-300')
                date_label = ui.label('YYYY-MM-DD').classes('text-xs font-mono text-green-800')

            # Start/Stop Button (Styled as a Master Switch)
            btn_toggle = ui.button('INITIALIZE', on_click=lambda: toggle_bot()).props('unelevated').classes(
                'font-bold tracking-wide px-6 py-2 '
                'bg-green-900 hover:bg-green-800 text-green-100 '
                'border border-green-600 shadow-[0_0_10px_rgba(0,255,0,0.2)]'
            )

    # --- LOGIC & UPDATES ---

    async def toggle_bot():
        if bot_service.is_running():
            await bot_service.stop()
            btn_toggle.text = 'INITIALIZE'
            btn_toggle.classes(remove='bg-red-900 hover:bg-red-800 border-red-600 shadow-[0_0_10px_rgba(255,0,0,0.4)]')
            btn_toggle.classes(add='bg-green-900 hover:bg-green-800 border-green-600 shadow-[0_0_10px_rgba(0,255,0,0.2)]')
            ui.notify('SYSTEM HALTED', type='warning', position='top')
        else:
            await bot_service.start()
            btn_toggle.text = 'TERMINATE'
            btn_toggle.classes(remove='bg-green-900 hover:bg-green-800 border-green-600 shadow-[0_0_10px_rgba(0,255,0,0.2)]')
            btn_toggle.classes(add='bg-red-900 hover:bg-red-800 border-red-600 shadow-[0_0_10px_rgba(255,0,0,0.4)]')
            ui.notify('SYSTEM ENGAGED: GANN PROTOCOLS ACTIVE', type='positive', position='top')
        update_header()

    def update_header():
        """Updates the UI elements with latest state data"""
        state = state_manager.get_state()
        
        # 1. Update Balance & Liquidity
        # Total Value (Equity)
        balance_label.set_text(f"${state.total_value:,.2f}")
        # Available (Balance)
        liquidity_label.set_text(f"${state.balance:,.2f}")

        # 2. Update PnL Color and Value
        # Ahora usamos el campo que ya existe en BotState
        pnl_val = getattr(state, 'total_return_pct', 0.0)
        pnl_label.set_text(f"{pnl_val:+.2f}%")
        
        if pnl_val > 0:
            pnl_label.classes(remove='text-red-500 text-green-400', add='text-green-400')
        elif pnl_val < 0:
            pnl_label.classes(remove='text-green-400 text-green-400', add='text-red-500')
        else:
            pnl_label.classes(remove='text-green-400 text-red-500', add='text-green-400')

        # 3. Update Time
        now = datetime.utcnow()
        time_label.set_text(now.strftime('%H:%M:%S UTC'))
        date_label.set_text(now.strftime('%Y-%m-%d'))

        # 4. Update Status Indicator
        if bot_service.is_running():
            status_dot.classes(remove='bg-red-600 shadow-[0_0_8px_rgba(255,0,0,0.6)]')
            status_dot.classes(add='bg-green-500 shadow-[0_0_8px_rgba(0,255,0,0.6)]')
            status_label.text = 'SYSTEM ACTIVE'
            status_label.classes(remove='text-green-800', add='text-green-400')
            btn_toggle.text = 'TERMINATE'
             # Ensure button style matches state if refreshed
            btn_toggle.classes(remove='bg-green-900 hover:bg-green-800 border-green-600 shadow-[0_0_10px_rgba(0,255,0,0.2)]')
            btn_toggle.classes(add='bg-red-900 hover:bg-red-800 border-red-600 shadow-[0_0_10px_rgba(255,0,0,0.4)]')
        else:
            status_dot.classes(remove='bg-green-500 shadow-[0_0_8px_rgba(0,255,0,0.6)]')
            status_dot.classes(add='bg-red-600 shadow-[0_0_8px_rgba(255,0,0,0.6)]')
            status_label.text = 'STANDBY'
            status_label.classes(remove='text-green-400', add='text-green-800')
            btn_toggle.text = 'INITIALIZE'
            # Ensure button style matches state if refreshed
            btn_toggle.classes(remove='bg-red-900 hover:bg-red-800 border-red-600 shadow-[0_0_10px_rgba(255,0,0,0.4)]')
            btn_toggle.classes(add='bg-green-900 hover:bg-green-800 border-green-600 shadow-[0_0_10px_rgba(0,255,0,0.2)]')

    # Start the update timer (every 1 second for clock)
    ui.timer(1.0, update_header)