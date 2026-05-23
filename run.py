import asyncio
import os
import sys

# ========== КРИТИЧЕСКИЙ FIX для Render.com ==========
# Должен быть ПЕРВЫМ!
import aiohttp
import aiodns

# Патчим проблемный метод aiodns
_original_getaddrinfo = aiodns.DNSChannel.getaddrinfo

def _patched_getaddrinfo(self, host, port, cb, family=0, type=0, proto=0, flags=0):
    # Конвертируем вызов в правильный формат
    try:
        return _original_getaddrinfo(self, host, port, cb, family, type, proto, flags)
    except TypeError:
        # Если не работает, используем стандартный резолвер
        import socket
        try:
            addrs = socket.getaddrinfo(host, port, family, type, proto, flags)
            cb(addrs)
        except Exception as e:
            cb([], error=str(e))

aiodns.DNSChannel.getaddrinfo = _patched_getaddrinfo

# Принудительно используем ThreadedResolver
aiohttp.resolver.DefaultResolver = aiohttp.resolver.ThreadedResolver
aiohttp.connector.DefaultResolver = aiohttp.resolver.ThreadedResolver

# ==================================================

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
    
    port = int(os.getenv("PORT", 10000)) 
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Web server started on port {port}")

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def main():
    dp.include_router(router)
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit bot")
