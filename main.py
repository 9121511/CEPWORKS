"""
AI Trading Bot - NiceGUI Desktop Application
Entry point for the application
"""

import signal
import sys
import asyncio
import atexit
from nicegui import ui, app

# Global reference to bot_service for cleanup
bot_service_ref = None

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print("\n[INFO] Shutting down gracefully...")
    cleanup()
    sys.exit(0)

def cleanup():
    """Cleanup function called on exit"""
    global bot_service_ref
    if bot_service_ref and bot_service_ref.is_running():
        print("[INFO] Stopping bot engine...")
        try:
            # Run the async stop in a new event loop if needed
            try:
                loop = asyncio.get_running_loop()
                # If we're here, we're in an async context
                asyncio.create_task(bot_service_ref.stop())
            except RuntimeError:
                # No running loop, create one
                asyncio.run(bot_service_ref.stop())
            print("[INFO] Bot stopped successfully")
        except Exception as e:
            print(f"[WARN] Error stopping bot: {e}")

if __name__ in {"__main__", "__mp_main__"}:
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Register cleanup on exit
    atexit.register(cleanup)

    # Import and setup app on startup
    from src.gui.app import create_app, bot_service

    # Save reference to bot_service for cleanup
    bot_service_ref = bot_service

    # Call create_app to register all pages
    create_app()

    # Auto-start bot on launch
    app.on_startup(lambda: asyncio.create_task(bot_service.start()))

    # Run in BROWSER mode (Native disabled)
    ui.run(
        native=False,             # Browser mode
        window_size=None,         # Not needed for browser
        fullscreen=False,
        title="CASTILLO CAPITAL SYSTEMS",
        favicon="🤖",
        dark=True,                # Dark theme
        reload=False,             # Disable hot reload in production
        show=True,                # Open browser tab immediately
        port=8080,                # Default port
        binding_refresh_interval=0.1  # Faster UI updates
    )
