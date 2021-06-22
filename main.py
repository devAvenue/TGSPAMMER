from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.middlewares.logging import LoggingMiddleware

import asyncio
import config, user
from sqliter import DBConnection

loop = asyncio.get_event_loop()
bot = Bot(token=config.TOKEN, loop=loop, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())
db = DBConnection()

def welcome_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*[types.KeyboardButton(name) for name in ['❓ Доступные каналы', '🔢 Интервал']])
    keyboard.add(*[types.KeyboardButton(name) for name in ['📑 Пост', '➡️ START']])
    return keyboard

@dp.message_handler(commands=['start'])
async def process_start_command(m: types.Message):
    if m.chat.id == config.ADMIN:
        await bot.send_message(m.chat.id, "💾 Рассылка сообщений по групам:\n\n", reply_markup= welcome_keyboard())
    else:
        await bot.send_message(m.chat.id, "❌ Вам запрещенно использовать данного бота.")

class addition(StatesGroup):
    id = State()

class post(StatesGroup):
    text = State()

class time(StatesGroup):
    timeout = State()

@dp.message_handler(state=addition.id)
async def input_report(m: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            channel_id = data['channel_id']
            db.add_additional_text(channel_id,m.text)
            await bot.send_message(m.chat.id, f'☑️ Текст для {channel_id} был успешно обновлен.')
            await state.finish()
    except:
        await bot.send_message(m.chat.id, f'❌ Текст для {channel_id} не был обновлен.')

@dp.message_handler(state=post.text)
async def input_report(m: types.Message, state: FSMContext):
    db.change_text(m.text)
    await bot.send_message(m.chat.id, f'☑️ Текст для поста был обновлен.')
    await state.finish()

@dp.message_handler(state=time.timeout)
async def input_report(m: types.Message, state: FSMContext):
    try:
        if int(m.text) > 1:
            db.setTimeOut(m.text)
            await bot.send_message(m.chat.id, f'☑️ Интервал рассылки был успешно обновлен.')
        else:
            await bot.send_message(m.chat.id, f'❌ Введите число больше 1.')
    except:
        await bot.send_message(m.chat.id, f'❌ Введите число.')
    await state.finish()

@dp.message_handler(content_types='text', state="*")
async def echo_message(m: types.Message):
    keyboard = types.InlineKeyboardMarkup()
    if  m.text == '❓ Доступные каналы':
        chats = await user.get_chats()
        for _ in chats:
            keyboard.add(*[types.InlineKeyboardButton(text=name, callback_data=cb) for name, cb in
                           {f'{_["title"]}': f'EDIT_ID:{_["id"]}'}.items()])
        await bot.send_message(m.chat.id, 'Все доступные каналы:', reply_markup=keyboard)
    elif m.text == '➡️ START':
        db.setSpam(1)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(*[types.KeyboardButton(name) for name in ['🛑 Остановить спам']])
        await bot.send_message(m.chat.id, '😊 Спам был успешно запущен.', reply_markup=keyboard)
        await start_spam("Заказать тг бота - @peacefulb")
    elif m.text == '🛑 Остановить спам':
        db.setSpam(0)
        await bot.send_message(m.chat.id, '😊 Отправляю последние сообщения и закругляюсь', reply_markup=welcome_keyboard())
    elif m.text == '🔢 Интервал':
        settings = db.settings()
        keyboard.add(*[types.InlineKeyboardButton(text=name, callback_data=cb) for name, cb in {'🕘 Изменить интервал':'INTERVAL'}.items()])
        await bot.send_message(m.chat.id, f'🔃 Текущий интервал {settings[5]} минут(а)', reply_markup=keyboard)

    elif m.text == '📑 Пост':
        settings = db.settings()
        try:
            with open(f'{config.DIR}{settings[1]}', 'rb') as photo:
                await bot.send_photo(m.chat.id, photo, caption=settings[2])
        except:
            await bot.send_message(m.chat.id, settings[2])

        keyboard.add(*[types.InlineKeyboardButton(text=name, callback_data=cb) for name, cb in
                       {'🌆 Изменить фото':'EDIT_PHOTO'}.items()])
        keyboard.add(*[types.InlineKeyboardButton(text=name, callback_data=cb) for name, cb in
                       {'📜 Изменить текст': 'EDIT_TEXT'}.items()])
        await bot.send_message(m.chat.id, '🔼 Ваш пост выглядит вот так 🔼', reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data, state="*")
async def poc_callback_but(c:types.CallbackQuery, state: FSMContext):
    m = c.message
    keyboard = types.InlineKeyboardMarkup()
    if 'EDIT_ID:' in c.data:
        channel_id = c.data.split(':')[1]
        try:
            addit_text = db.get_additional_text(channel_id)[0]
        except:
            addit_text = None
        keyboard = types.InlineKeyboardMarkup(row_widht=2)
        keyboard.add(*[types.InlineKeyboardButton(text=name, callback_data=cb) for name, cb in
                       {'❌ Покинуть чат': f'LFC:{channel_id}'}.items()])
        if addit_text != None:
            keyboard.add(*[types.InlineKeyboardButton(text=name, callback_data=cb) for name, cb in
                           {'🗃 Изменить дополнительный текст': f'ADD_ADDITIONAL:{channel_id}'}.items()])
            await bot.send_message(m.chat.id, f'Текущий дополнительный текст для {channel_id}:{addit_text}', reply_markup=keyboard)
        else:
            keyboard.add(*[types.InlineKeyboardButton(text=name, callback_data=cb) for name, cb in
                           {'🗃 Добавить дополнительный текст': f'ADD_ADDITIONAL:{channel_id}'}.items()])
            await bot.send_message(m.chat.id, f'Дополнительного текста для {channel_id} не найдено.', reply_markup=keyboard)
    elif 'ADD_ADDITIONAL:' in c.data:
        channel_id = c.data.split(':')[1]
        async with state.proxy() as data:
            data['channel_id'] = channel_id
        await bot.send_message(m.chat.id, f'💬 Введите дополнительный текст для [{channel_id}]:', reply_markup=keyboard)
        await addition.first()
    elif 'LFC:' in c.data:
        log = await user.leave_from_channel(c.data.split(':')[1])
        if log:
            text = f'☑️ Вы успешно покинули данный канал.'
        else:
            text = '❌ Возникли некие трудности при выходе.'
        await bot.send_message(m.chat.id, text)
    elif 'EDIT_TEXT' == c.data:
        await bot.send_message(m.chat.id, '📄 Введите текст поста:')
        await post.first()
    elif 'EDIT_PHOTO' == c.data:
        await bot.send_message(m.chat.id, '📄 Отправь мне фото для изменения:')
    elif 'INTERVAL' == c.data:
        await bot.send_message(m.chat.id, '📄 Отправь мне интервал рассылки между чатами (в минутах):')
        await time.first()


@dp.message_handler(content_types=["photo"])
async def download_photo(m: types.Message):
    result = await m.photo[-1].download()
    db.change_photo(result.name)
    await bot.send_message(m.chat.id, '🖼 Фото было успешно обновленно.')

async def start_spam(x):
    if db.settings()[4] == 1:
        spam_list = []
        for i in await user.get_chats():
            try:
                addit_text = db.get_additional_text(i['id'])[0]
            except:
                addit_text = ''
            i['text'] = addit_text
            spam_list.append(i)
        settings = db.settings()
        tksNumber = asyncio.create_task(user.spamming(spam_list, settings,db))

if __name__ == '__main__':
  executor.start_polling(dp, skip_updates=True, on_startup=start_spam)