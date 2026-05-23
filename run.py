import aiogram

from aiogram import Bot,Dispatcher
import asyncio
from config import TOKEN
from app.handlers import router

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def main():
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt as e:
        print(f"Exit bot {e}")

