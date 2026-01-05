"""
Main GUI Application - Single Page App with internal navigation
REDISEÑO: W.D. GANN ULTRA PRO EDITION (Fixed Layout)
"""

from nicegui import ui
from src.gui.components.header import create_header
from src.gui.services.bot_service import BotService
from src.gui.services.state_manager import StateManager

# Import pages
from src.gui.pages import dashboard, positions, history, market, reasoning, settings, recommendations

# Global services
bot_service = BotService()
state_manager = StateManager()

# Connect services
bot_service.state_manager = state_manager


def create_app():
    """Initialize and configure the NiceGUI application as single page"""

    # Add Material Icons and Gann Fonts
    ui.add_head_html('<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">')
    ui.add_head_html('<link href="https://fonts.cdnfonts.com/css/digital-numbers" rel="stylesheet">')
    
    # --- ESTILOS GANN ULTRA PRO ---
    ui.add_head_html('''
        <style>
            body { 
                background-color: #0f172a; 
                color: #e2e8f0;
                margin: 0;
            }
            * { font-family: 'Inter', sans-serif; }
            .font-mono { font-family: 'Courier New', monospace !important; }

            /* Estilo para las tarjetas de métricas */
            .metric-card {
                background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
                border: 1px solid rgba(251, 191, 36, 0.2);
                border-radius: 8px;
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
            }

            /* Navegación Estilo Terminal */
            .nav-button {
                color: #94a3b8 !important;
                border-left: 3px solid transparent !important;
                transition: all 0.3s ease;
            }
            .nav-button:hover {
                background: rgba(251, 191, 36, 0.05) !important;
                color: #fbbf24 !important;
                border-left: 3px solid #fbbf24 !important;
            }

            .positive { color: #10b981 !important; text-shadow: 0 0 8px rgba(16,185,129,0.3); }
            .negative { color: #ef4444 !important; text-shadow: 0 0 8px rgba(239,68,68,0.3); }

            /* Scrollbar de lujo */
            ::-webkit-scrollbar { width: 6px; }
            ::-webkit-scrollbar-track { background: #0f172a; }
            ::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
            ::-webkit-scrollbar-thumb:hover { background: #fbbf24; }
        </style>
    ''')

    # 1. HEADER (Debe estar en la raíz, fuera de cualquier columna)
    create_header(bot_service, state_manager)

    # 2. CUERPO PRINCIPAL (Sidebar + Contenido)
    # Usamos h-screen y no-wrap para que ocupe todo el alto
    with ui.row().classes('w-full no-wrap h-screen gap-0'):
        
        # --- SIDEBAR ---
        with ui.column().classes('w-72 bg-slate-900 border-r border-slate-800 p-6 gap-2 h-full'):
            ui.label('OPERATIONS').classes('text-xs font-bold text-slate-500 tracking-[0.2em] mb-4')
            
            menu_items = [
                ('Dashboard', 'dashboard', 'DASHBOARD'),
                ('Recommendations', 'smart_toy', 'AI SIGNALS'),
                ('Positions', 'account_balance_wallet', 'POSITIONS'),
                ('History', 'history', 'TRADE LOG'),
                ('Market', 'insights', 'MARKET DATA'),
                ('Reasoning', 'psychology', 'QUANT LOGIC'),
                ('Settings', 'settings', 'SYSTEM CFG'),
            ]

            for page_id, icon, label in menu_items:
                with ui.button(on_click=lambda p=page_id: navigate(p)).classes('nav-button w-full justify-start py-3').props('flat'):
                    ui.icon(icon).classes('mr-4')
                    ui.label(label).classes('font-bold tracking-wider')

            ui.element('div').classes('mt-auto')
            
            # Gann Branding Footer
            with ui.card().classes('bg-slate-800/30 border border-slate-700 p-4 w-full'):
                ui.label('GEOMETRIC ANGLE').classes('text-[10px] text-amber-500/50 font-bold')
                ui.label('45° ACTIVE').classes('text-xs text-amber-500 font-mono')

        # --- CONTENT AREA ---
        global content_container
        # flex-grow asegura que ocupe el resto del espacio
        content_container = ui.column().classes('flex-grow p-8 bg-[#0f172a] overflow-auto items-stretch')

    # Load default page content
    with content_container:
        dashboard.create_dashboard(bot_service, state_manager)


def navigate(page: str):
    """Navigate to different page by clearing and recreating content"""
    global content_container
    content_container.clear()

    with content_container:
        # Título de sección dinámico
        ui.label(f"// SYSTEM / {page.upper()}").classes('text-slate-500 font-mono text-xs mb-6 tracking-widest')
        
        if page == 'Dashboard':
            dashboard.create_dashboard(bot_service, state_manager)
        elif page == 'Recommendations':
            recommendations.create_recommendations(bot_service, state_manager)
        elif page == 'Positions':
            positions.create_positions(bot_service, state_manager)
        elif page == 'History':
            history.create_history(bot_service, state_manager)
        elif page == 'Market':
            market.create_market(bot_service, state_manager)
        elif page == 'Reasoning':
            reasoning.create_reasoning(bot_service, state_manager)
        elif page == 'Settings':
            settings.create_settings(bot_service, state_manager)