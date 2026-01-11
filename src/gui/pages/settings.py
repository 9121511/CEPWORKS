"""
Settings Page - Hybrid Apple/Matrix Style
"""

import asyncio
import json
import os
from pathlib import Path
from nicegui import ui
from src.gui.services.bot_service import BotService
from src.gui.services.state_manager import StateManager
from src.backend.config_loader import CONFIG

def create_settings(bot_service: BotService, state_manager: StateManager):
    """Create settings page with Hybrid UI"""

    # --- HEADER ---
    with ui.row().classes('w-full items-center justify-between mb-8'):
        with ui.column().classes('gap-1'):
            ui.label('SYSTEM CONFIGURATION').classes('text-2xl font-bold tracking-tight text-white font-mono')
            ui.label('CORE PARAMETERS & CREDENTIALS').classes('text-xs text-[#00ff41] font-mono tracking-widest opacity-80')

    # Config Logic
    config_file = Path('data/config.json')

    def load_config():
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except: pass
        return {
            'strategy': {
                'assets': CONFIG.get('assets') or 'BTC ETH',
                'interval': CONFIG.get('interval') or '5m',
                'llm_model': CONFIG.get('llm_model') or 'gemini-2.0-flash',
                'reasoning_enabled': CONFIG.get('reasoning_enabled', False),
                'reasoning_effort': CONFIG.get('reasoning_effort') or 'high'
            },
            'api_keys': {
                'taapi_api_key': CONFIG.get('taapi_api_key') or '',
                'hyperliquid_private_key': CONFIG.get('hyperliquid_private_key') or '',
                'hyperliquid_network': CONFIG.get('hyperliquid_network') or 'mainnet',
                'openrouter_api_key': CONFIG.get('openrouter_api_key') or ''
            },
            'notifications': {
                'desktop_enabled': True,
                'telegram_enabled': False
            }
        }

    def save_config(config_data):
        try:
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            return True
        except: return False

    config_data = load_config()
    def safe_get(section, key, default):
        return config_data.get(section, {}).get(key, default)

    # --- UI HELPERS ---
    def config_section(title):
        ui.label(title).classes('text-sm font-bold text-[#00ff41] mt-6 mb-2 font-mono uppercase tracking-wider')
        return ui.card().classes('w-full p-6 bg-[#0a0a0a] border border-[#1a1a1a] rounded-lg shadow-none')

    # --- TABS ---
    with ui.tabs().classes('w-full mb-6 border-b border-[#1a1a1a]') as tabs:
        t_gen = ui.tab('STRATEGY').classes('text-[#00ff41] font-mono tracking-wide')
        t_api = ui.tab('API KEYS').classes('text-[#00ff41] font-mono tracking-wide')
        t_not = ui.tab('ALERTS').classes('text-[#00ff41] font-mono tracking-wide')

    with ui.tab_panels(tabs, value=t_gen).classes('w-full bg-transparent'):
        
        # TAB 1: STRATEGY
        with ui.tab_panel(t_gen).classes('p-0 gap-6'):
            
            with config_section('MARKET UNIVERSE'):
                with ui.grid(columns=2).classes('w-full gap-6'):
                    common_assets = ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'XMR', 'ZEC', 'LTC', 'ADA', 'DOT']
                    c_assets = safe_get('strategy', 'assets', 'BTC ETH')
                    c_assets_list = c_assets if isinstance(c_assets, list) else [a.strip() for a in str(c_assets).replace(',', ' ').split() if a.strip()]

                    assets_input = ui.select(
                        options=common_assets,
                        value=c_assets_list,
                        multiple=True,
                        with_input=True,
                        new_value_mode='add-unique',
                        label='Selected Assets'
                    ).classes('w-full font-mono').props('use-chips outlined dense dark color="green-4"')

                    interval_select = ui.select(
                        options=['1m', '5m', '15m', '1h', '4h'],
                        value=safe_get('strategy', 'interval', '5m'),
                        label='Timeframe'
                    ).classes('w-full font-mono').props('outlined dense dark color="green-4"')

            with config_section('NEURAL ENGINE'):
                llm_model = ui.select(
                    options=['gemini-2.0-flash', 'x-ai/grok-4', 'openai/gpt-4'],
                    value=safe_get('strategy', 'llm_model', 'gemini-2.0-flash'),
                    label='Model'
                ).classes('w-full mb-4 font-mono').props('outlined dense dark color="green-4"')

                with ui.row().classes('items-center justify-between w-full p-3 border border-[#1a1a1a] rounded bg-[#050505]'):
                    ui.label('ENABLE DEEP REASONING').classes('text-xs font-mono text-white')
                    reason_switch = ui.switch(value=safe_get('strategy', 'reasoning_enabled', False)).props('color="green-13"')

            # Save Logic
            async def save_strat():
                if 'strategy' not in config_data: config_data['strategy'] = {}
                config_data['strategy']['assets'] = assets_input.value
                config_data['strategy']['interval'] = interval_select.value
                config_data['strategy']['llm_model'] = llm_model.value
                config_data['strategy']['reasoning_enabled'] = reason_switch.value
                
                if save_config(config_data):
                    await bot_service.update_config({
                        'assets': assets_input.value,
                        'interval': interval_select.value,
                        'model': llm_model.value
                    })
                    ui.notify('STRATEGY UPDATED', type='positive')

            ui.button('APPLY CONFIGURATION', on_click=save_strat).classes('bg-[#003300] text-[#00ff41] border border-[#00ff41] font-mono w-full py-2 hover:bg-[#004400]')


        # TAB 2: API
        with ui.tab_panel(t_api).classes('p-0'):
             with config_section('SECURE CREDENTIALS'):
                 k_taapi = ui.input(label='TAAPI.IO KEY', password=True, value=safe_get('api_keys', 'taapi_api_key', '')).classes('w-full mb-2 font-mono').props('outlined dense dark color="green-4"')
                 k_open = ui.input(label='OPENROUTER KEY', password=True, value=safe_get('api_keys', 'openrouter_api_key', '')).classes('w-full mb-2 font-mono').props('outlined dense dark color="green-4"')
                 k_hl = ui.input(label='HYPERLIQUID PRIVATE KEY', password=True, value=safe_get('api_keys', 'hyperliquid_private_key', '')).classes('w-full mb-4 font-mono').props('outlined dense dark color="green-4"')

                 async def save_api():
                     if 'api_keys' not in config_data: config_data['api_keys'] = {}
                     config_data['api_keys']['taapi_api_key'] = k_taapi.value
                     config_data['api_keys']['openrouter_api_key'] = k_open.value
                     config_data['api_keys']['hyperliquid_private_key'] = k_hl.value
                     
                     if save_config(config_data):
                         if k_taapi.value: os.environ['TAAPI_API_KEY'] = k_taapi.value
                         if k_open.value: os.environ['OPENROUTER_API_KEY'] = k_open.value
                         if k_hl.value: os.environ['HYPERLIQUID_PRIVATE_KEY'] = k_hl.value
                         ui.notify('KEYS SECURED', type='positive')

                 async def test_conn():
                     ui.notify('PINGING SERVERS...', type='info')
                     await bot_service.test_api_connections()
                     ui.notify('HANDSHAKE COMPLETE', type='positive')

                 with ui.row().classes('w-full gap-2 mt-4'):
                     ui.button('TEST UPLINK', on_click=test_conn).classes('flex-1 border border-[#333] text-gray-400 font-mono hover:text-white')
                     ui.button('SAVE KEYS', on_click=save_api).classes('flex-1 bg-[#003300] text-[#00ff41] border border-[#00ff41] font-mono hover:bg-[#004400]')
