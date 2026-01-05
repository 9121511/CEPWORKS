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
        'bg-slate-900 border-b-2 border-amber-600/50 shadow-[0_0_15px_rgba(217,119,6,0.2)]'
    ):
        # --- LEFT: BRANDING & STATUS ---
        with ui.row().classes('items-center gap-4'):
            # Logo / Title with Gann Theme
            with ui.column().classes('gap-0'):
                ui.label('NOF1.AI').classes(
                    'text-2xl font-black tracking-widest text-transparent bg-clip-text bg-gradient-to-r from-amber-300 to-amber-600'
                )
                ui.label('ALPHA ARENA | GANN SYSTEM').classes(
                    'text-[10px] tracking-[0.2em] text-cyan-500 font-mono'
                )
            
            # Vertical Separator
            ui.element('div').classes('h-10 w-px bg-slate-700 mx-2')

            # Status Indicator (Glowing Dot)
            with ui.row().classes('items-center gap-2 bg-slate-800/50 px-3 py-1 rounded-full border border-slate-700'):
                status_dot = ui.element('div').classes(
                    'w-3 h-3 rounded-full bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]'
                )
                status_label = ui.label('DISCONNECTED').classes('text-xs font-bold text-slate-400')

        # --- CENTER: KEY METRICS (Balance & PnL) ---
        # Designed like a ticker tape / cockpit
        with ui.row().classes('items-center gap-8'):
            
            # Balance Display
            with ui.column().classes('items-center gap-0'):
                ui.label('TOTAL EQUITY').classes('text-[10px] font-mono text-slate-400 tracking-wider')
                balance_label = ui.label('$0.00').classes(
                    'text-xl font-mono font-bold text-white tracking-tight'
                )

            # PnL Display (The most important number)
            with ui.column().classes('items-center gap-0'):
                ui.label('SESSION RETURN').classes('text-[10px] font-mono text-slate-400 tracking-wider')
                pnl_label = ui.label('0.00%').classes(
                    'text-xl font-mono font-bold text-cyan-400 tracking-tight'
                )

            # Available Liquidity
            with ui.column().classes('items-center gap-0'):
                ui.label('LIQUIDITY (USDC)').classes('text-[10px] font-mono text-slate-400 tracking-wider')
                liquidity_label = ui.label('$0.00').classes(
                    'text-lg font-mono text-amber-400'
                )

        # --- RIGHT: SYSTEM TIME & CONTROLS ---
        with ui.row().classes('items-center gap-4'):
            # System Time (Crucial for Gann Analysis)
            with ui.column().classes('items-end gap-0 mr-4'):
                time_label = ui.label('00:00:00 UTC').classes('text-lg font-mono font-bold text-slate-200')
                date_label = ui.label('YYYY-MM-DD').classes('text-xs font-mono text-slate-500')

            # Start/Stop Button (Styled as a Master Switch)
            btn_toggle = ui.button('INITIALIZE', on_click=lambda: toggle_bot()).props('unelevated').classes(
                'font-bold tracking-wide px-6 py-2 '
                'bg-emerald-600 hover:bg-emerald-500 text-white '
                'border border-emerald-400 shadow-[0_0_10px_rgba(16,185,129,0.4)]'
            )

    # --- LOGIC & UPDATES ---

    async def toggle_bot():
        if bot_service.is_running():
            await bot_service.stop()
            btn_toggle.text = 'INITIALIZE'
            btn_toggle.classes(remove='bg-red-600 hover:bg-red-500 border-red-400 shadow-[0_0_10px_rgba(239,68,68,0.4)]')
            btn_toggle.classes(add='bg-emerald-600 hover:bg-emerald-500 border-emerald-400 shadow-[0_0_10px_rgba(16,185,129,0.4)]')
            ui.notify('SYSTEM HALTED', type='warning', position='top')
        else:
            await bot_service.start()
            btn_toggle.text = 'TERMINATE'
            btn_toggle.classes(remove='bg-emerald-600 hover:bg-emerald-500 border-emerald-400 shadow-[0_0_10px_rgba(16,185,129,0.4)]')
            btn_toggle.classes(add='bg-red-600 hover:bg-red-500 border-red-400 shadow-[0_0_10px_rgba(239,68,68,0.4)]')
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
            pnl_label.classes(remove='text-red-400 text-cyan-400', add='text-emerald-400')
        elif pnl_val < 0:
            pnl_label.classes(remove='text-emerald-400 text-cyan-400', add='text-red-400')
        else:
            pnl_label.classes(remove='text-emerald-400 text-red-400', add='text-cyan-400')

        # 3. Update Time
        now = datetime.utcnow()
        time_label.set_text(now.strftime('%H:%M:%S UTC'))
        date_label.set_text(now.strftime('%Y-%m-%d'))

        # 4. Update Status Indicator
        if bot_service.is_running():
            status_dot.classes(remove='bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]')
            status_dot.classes(add='bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]')
            status_label.text = 'SYSTEM ACTIVE'
            status_label.classes(remove='text-slate-400', add='text-emerald-400')
            btn_toggle.text = 'TERMINATE'
             # Ensure button style matches state if refreshed
            btn_toggle.classes(remove='bg-emerald-600 hover:bg-emerald-500 border-emerald-400 shadow-[0_0_10px_rgba(16,185,129,0.4)]')
            btn_toggle.classes(add='bg-red-600 hover:bg-red-500 border-red-400 shadow-[0_0_10px_rgba(239,68,68,0.4)]')
        else:
            status_dot.classes(remove='bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]')
            status_dot.classes(add='bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]')
            status_label.text = 'STANDBY'
            status_label.classes(remove='text-emerald-400', add='text-slate-400')
            btn_toggle.text = 'INITIALIZE'
            # Ensure button style matches state if refreshed
            btn_toggle.classes(remove='bg-red-600 hover:bg-red-500 border-red-400 shadow-[0_0_10px_rgba(239,68,68,0.4)]')
            btn_toggle.classes(add='bg-emerald-600 hover:bg-emerald-500 border-emerald-400 shadow-[0_0_10px_rgba(16,185,129,0.4)]')

    # Start the update timer (every 1 second for clock)
    ui.timer(1.0, update_header)