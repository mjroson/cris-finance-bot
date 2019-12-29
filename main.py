"""
This is a echo bot.
It echoes any incoming text messages.
"""

import logging
import os
import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.emoji import emojize
from aiogram.utils import executor
from aiogram.types import InlineQuery, \
    InputTextMessageContent, InlineQueryResultArticle, ParseMode
from src.models import User, Chat, Expense

API_TOKEN = os.environ.get('TELEGRAM_API_TOKEN', '')

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
storage = MemoryStorage()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)

class FormConfirm(StatesGroup):
    answer = State()

# States
class Form(StatesGroup):
    description = State()  # Will be represented in storage as 'Form:description'
    categories = State()  # Will be represented in storage as 'Form:categories'
    price = State()  # Will be represented in storage as 'Form:price'


@dp.message_handler(commands='add')
async def add_expense(message: types.Message):
    await start_poll(message.chat.id)


@dp.message_handler(commands=['lunch'])
async def poll_lunch(message: types.Message):

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("Si", "No")

    await FormConfirm.answer.set()
    await bot.send_message(message.chat.values.get('id'), 'Almorzaste afuera?', reply_markup=markup)

@dp.inline_handler()
async def inline_echo(inline_query: InlineQuery):
    # id affects both preview and content,
    # so it has to be unique for each result
    # (Unique identifier for this result, 1-64 Bytes)
    # you can set your unique id's
    # but for example i'll generate it based on text because I know, that
    # only text will be passed in this example
    text = inline_query.query or 'echo'
    input_content = InputTextMessageContent(text)
    result_id: str = hashlib.md5(text.encode()).hexdigest()
    item = InlineQueryResultArticle(
        id=result_id,
        title=f'Result {text!r}',
        input_message_content=input_content,
    )
    # don't forget to set cache_time=1 for testing (default is 300s or 5m)
    await bot.answer_inline_query(inline_query.id, results=[item], cache_time=1)

@dp.message_handler(state=FormConfirm.answer)
async def process_answer(message: types.Message, state: FSMContext):
    markup = types.ReplyKeyboardRemove()
    yes_choices = ['si', 'sí', 's', 'yes']
    async with state.proxy() as data:
        data['categories'] = 'almuerzo,comida'
    if message.text.lower() in yes_choices:
        await start_poll(message.chat.values.get('id'), 'Que almorzaste?')
    else:
        await message.reply(emojize('Se dejan ver esos ahorros! 💪'), reply_markup=markup)
        await state.finish()

async def start_poll(id, message = 'Describime tu gasto.'):
    """
    Conversation's entry point
    """
    # Set state
    await Form.description.set()

    markup = types.ReplyKeyboardRemove()
    # chat_ids = ['157425944']
    await bot.send_message(id, message, reply_markup=markup)


# You can use state '*' if you need to handle all states
@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    """
    Allow user to cancel any action
    """
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info('Cancelling state %r', current_state)
    # Cancel state and inform user about it
    await state.finish()
    # And remove keyboard (just in case)
    await message.reply('Cancelled.', reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(state=Form.description)
async def process_description(message: types.Message, state: FSMContext):
    """
    Process user description
    """
    async with state.proxy() as data:
        data['description'] = message.text

    await Form.next()

    await message.reply("Ingrese las categorias separadas por coma")

@dp.message_handler(state=Form.categories)
async def process_categories(message: types.Message, state: FSMContext):
    """
    Process user name
    """
    async with state.proxy() as data:
        data['categories'] = message.text

    await Form.next()
    await message.reply("Cuanto? (solo número)")

# Check price. Price gotta be digit
@dp.message_handler(lambda message: not message.text.isdigit(), state=Form.price)
async def process_price_invalid(message: types.Message):
    """
    If price is invalid
    """
    return await message.reply("Me puedes repetir el precio? .\n (solo numeros)")


@dp.message_handler(lambda message: message.text.isdigit(), state=Form.price)
async def process_price(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['price'] = message.text
        user = User.get(User.external_id == message.from_user.values.get('id'))
        Expense.create(**data, user=user)
        # summary of saved expense
        await bot.send_message(
            message.chat.id,
            md.text(
                md.text('Gasto de ', md.bold(data['description']), ' guardado! '),
                md.text('Categorias: ', md.code(data['categories'])),
                md.text('Price: $', data['price']),
                sep='\n',
            ),
            parse_mode=ParseMode.MARKDOWN,
        )

    # Finish conversation
    await state.finish()


@dp.message_handler(commands=['start'])
async def register(message: types.Message):
    data = message.from_user.values
    User.create(
        external_id=data['id'],
        name=message.from_user.full_name,
        username=data.get('username', 'nouser'),
        lang=data.get('language_code', 'es'),
        extra=str(data)
    )
    await message.reply(f'Bienvenid@ {message.from_user.full_name}!')


@dp.message_handler(commands=['help'])
async def haldler_help(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    import pdb; pdb.set_trace()
    await message.reply("Hi!\nI'm EchoBot!\nPowered by aiogram.")


@dp.message_handler()
async def echo(message: types.Message):
    # old style:
    # await bot.send_message(message.chat.id, message.text)

    await message.reply(message.text, reply=False)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
