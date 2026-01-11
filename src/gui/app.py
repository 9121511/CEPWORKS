"""
Main GUI Application - Single Page App with internal navigation
REDISEÑO: WIDESCREEN HYBRID LAYOUT (FIXED)
Forces full width/height flex containers to prevent stacking.
CRITICAL FIX: Moved content container OUT of sidebar.
"""

from nicegui import ui
from src.gui.services.bot_service import BotService
from src.gui.services.state_manager import StateManager

# Import pages
from src.gui.pages import dashboard, positions, history, market, reasoning, settings, recommendations

# Global services
# Global services
bot_service = BotService()
# bot_service.start()  <-- REMOVED: Caused 'coroutine never awaited' warning
state_manager = StateManager()

# Connect services
bot_service.state_manager = state_manager


def create_app():
    """Initialize and configure the NiceGUI application pages"""
    
    @ui.page('/')
    def index_page():
        """Main page builder"""
        ui.add_head_html('<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">')
        
        # --- STYLES: 100% Viewport Height/Width Forced ---
        ui.add_head_html('''
            <style>
                :root {
                    --bg-primary: #050505;
                    --text-primary: #e5e5e5;
                    --accent: #00ff41;
                    --border: #1a1a1a;
                }
                body, html { 
                    margin: 0; 
                    padding: 0;
                    width: 100vw;
                    height: 100vh;
                    background-color: var(--bg-primary); 
                    color: var(--text-primary);
                    font-family: -apple-system, "SF Pro Text", monospace;
                    overflow: hidden; /* No Body Scroll */
                }
                
                /* THE MAIN CONTAINER: ROW, NO WRAP */
                .app-container {
                    display: flex;
                    flex-direction: row;
                    width: 100vw;
                    height: 100vh;
                    overflow: hidden;
                }

                /* SIDEBAR: FIXED WIDTH */
                .sidebar-container {
                    flex: 0 0 280px; /* Force fixed width, don't shrink/grow */
                    width: 280px;
                    height: 100%;
                    background: #000000;
                    border-right: 1px solid var(--border);
                    display: flex;
                    flex-direction: column;
                    padding: 24px;
                    z-index: 10;
                }

                /* CONTENT: FLEX GROW, SCROLLABLE Y */
                .content-container {
                    flex: 1; /* Grow to fill remaining space */
                    height: 100%;
                    background: #050505;
                    overflow-y: auto; /* Scroll content inside */
                    padding: 40px;
                    position: relative;
                    display: flex;
                    flex-direction: column; 
                }

                /* UTILS */
                .matrix-text { color: var(--accent); font-family: monospace; }
                .nav-btn {
                    width: 100%;
                    text-align: left;
                    padding: 12px;
                    margin-bottom: 8px; /* More spacing */
                    border-radius: 8px;
                    color: #888;
                    transition: all 0.2s;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    font-size: 0.85rem;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                }
                .nav-btn:hover { background: rgba(0,255,65,0.1); color: var(--accent); }
                
                /* Scrollbar clean */
                 ::-webkit-scrollbar { width: 8px; height: 8px; }
                 ::-webkit-scrollbar-track { background: transparent; }
                 ::-webkit-scrollbar-thumb { background: #333; border-radius: 4px; }
                 ::-webkit-scrollbar-thumb:hover { background: #555; }
            </style>
        ''')

        # --- LAYOUT STRUCTURE ---
        # 1. Root Element (Flex Row, Full Viewport)
        with ui.element('div').classes('app-container'):
            
            # 2. Sidebar (Fixed Left)
            with ui.element('div').classes('sidebar-container'):
                # Logo
                with ui.row().classes('items-center gap-3 mb-10'):
                    ui.icon('hub', size='32px').classes('matrix-text')
                    with ui.column().classes('gap-0'):
                        ui.label('ALPHA ARENA').classes('text-white font-bold tracking-widest text-base')
                        ui.label('SYSTEM V2.0').classes('matrix-text text-[10px]')

                # Navigation
                menu_items = [
                    ('MISSION CONTROL', 'dashboard', 'dashboard'),
                    ('TRADE LOG', 'history', 'history'),
                    ('MARKET FEED', 'candlestick_chart', 'candlestick_chart'),
                    ('NEURAL LOGIC', 'psychology', 'psychology'),
                    ('SYSTEM CONFIG', 'settings', 'settings'),
                ]
                
                # Define nav function wrapper to use later
                nav_handlers = {}

                for label, page_key, icon in menu_items:
                    # Capture page_key in default arg
                    def make_handler(pk=page_key):
                        return lambda: nav(pk)
                    
                    with ui.button(on_click=make_handler()).classes('nav-btn shadow-none bg-transparent'):
                        ui.icon(icon).classes('text-xl')
                        ui.label(label)

                ui.element('div').classes('mt-auto')
                
                # Status
                with ui.row().classes('items-center gap-2 border border-[#1a1a1a] p-3 rounded bg-[#0a0a0a] w-full'):
                    ui.element('div').classes('w-2 h-2 rounded-full bg-[#00ff41] animate-pulse')
                    ui.label('ONLINE').classes('matrix-text text-[10px]')


            # 3. Main Content Area (Sibling to Sidebar)
            main_area = ui.element('div').classes('content-container')
            
            # Nav Logic
            def nav(page):
                main_area.clear()
                with main_area:
                    if page == 'dashboard': dashboard.create_dashboard(bot_service, state_manager)
                    elif page == 'history': history.create_history(bot_service, state_manager)
                    elif page == 'candlestick_chart': market.create_market(bot_service, state_manager)
                    elif page == 'psychology': reasoning.create_reasoning(bot_service, state_manager)
                    elif page == 'settings': settings.create_settings(bot_service, state_manager)

            # Initial Load
            with main_area:
                dashboard.create_dashboard(bot_service, state_manager)

            # Auto-start bot (Safe Async)
            async def auto_start():
                if not bot_service.is_running():
                    await bot_service.start()
            
            # Use a timer with 0.1s delay to run it inside the event loop
            ui.timer(0.1, auto_start, once=True)

    ui.run(title='Alpha Arena', port=8080, dark=True)