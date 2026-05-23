import asyncio
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from config import TOKEN
from app.handlers import router

async def handle(request):
    return web.Response(text="Bot is live")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Render автоматически передает порт в переменную окружения PORT
    port = int(os.getenv("PORT", 10000)) 
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Web server started on port {port}")


bot = Bot(token=TOKEN)
dp = Dispatcher()

async def main():
    dp.include_router(router)
    
    # Запускаем веб-сервер параллельно с ботом
    await start_web_server()
    
    # Запускаем поллинг
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit bot")
