import asyncio
import threading
import uvicorn

def run_web():
    uvicorn.run("web.app:app", host="0.0.0.0", port=8000, reload=False)

def main():
    # Start web server in a background thread
    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()
    print("Web dashboard running at http://localhost:8000")

    # Start Telegram bot (blocks main thread)
    from bot.main import create_app
    from bot.scheduler import start_scheduler

    app = create_app()

    async def post_init(application):
        start_scheduler(application.bot)

    app.post_init = post_init
    print("Telegram bot starting...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
