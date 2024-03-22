import asyncio
from datetime import datetime
from aiogram import Router, types, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.models import database
from keyboards.reply import set_alerts_button
from scrape import scrape_prices

user_router = Router()


class SetAlerts(StatesGroup):
    currencies = State()
    threshold = State()
    alert_preference = State()


@user_router.message(CommandStart())
async def start_cmd(message: types.Message):
    if not await database.user_exists(message.from_user.id):
        await database.add_user(message.from_user.id, message.from_user.first_name)
    await message.answer("Started scraping...\nThis may take a few minutes", reply_markup=set_alerts_button())
    while True:
        data = await database.get_user_alerts(message.from_user.id)
        cur_list = await scrape_prices(data["currencies"])
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if cur_list:
            for cur in cur_list:
                if cur['Price'] > data['threshold'] and data['alert_preference'] == 'higher':
                    await message.answer(
                        f"{cur['Name']}({cur['Symbol']}) price is growing.It costs {cur['Price']}$ as of now\n{current_time}")
                    await database.add_alert_history(message.from_user.id,
                                                     f"{cur['Name']}({cur['Symbol']}) price is growing.It costs {cur['Price']}$ as of now")

                elif cur['Price'] < data['threshold'] and data['alert_preference'] == 'lower':
                    await message.answer(
                        f"{cur['Name']}({cur['Symbol']}) price is dropping.It costs {cur['Price']}$ as of now\n{current_time}")
                    await database.add_alert_history(message.from_user.id,
                                                     f"{cur['Name']}({cur['Symbol']}) price is dropping.It costs {cur['Price']}$ as of now")
        else:
            await message.answer("No currencies found for that search.")
        await asyncio.sleep(40)


@user_router.message(StateFilter(None), F.text == 'Get alerts history')
async def get_alerts_history(message: types.Message):
    history = await database.get_alert_history(message.from_user.id)
    for item in history:
        await message.answer(f"{item["alert_text"]}\n{item["alert_datetime"]}")

####################FSM for alerts###################################

@user_router.message(StateFilter(None), F.text == 'Set/Update alerts')
async def set_alerts_start(message: types.Message, state: FSMContext):
    await message.answer("Let's set up your alerts. Please enter the currencies you want to track.")
    await state.set_state(SetAlerts.currencies)  # Set the initial state to ask for currencies


@user_router.message(SetAlerts.currencies, F.text)
async def set_currencies(message: types.Message, state: FSMContext):
    await state.update_data(currencies=message.text)  # Store user's input in FSM context
    await message.answer("Enter the threshold value for the price.")
    await state.set_state(SetAlerts.threshold)


@user_router.message(SetAlerts.threshold, F.text)
async def set_threshold(message: types.Message, state: FSMContext):
    threshold_value = message.text

    threshold_value = float(threshold_value)
    await state.update_data(threshold=threshold_value)  # Store user's input in FSM context
    buttons = [
            [InlineKeyboardButton(text="Higher", callback_data="higher"),
             InlineKeyboardButton(text="Lower", callback_data="lower")]
        ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Do you want to be alerted when the price goes higher or lower than the threshold value?", reply_markup=keyboard)
    await state.set_state(SetAlerts.alert_preference)


@user_router.callback_query(SetAlerts.alert_preference)
async def set_alert_preference_callback(callback_query: types.CallbackQuery, state: FSMContext):
    alert_preference = callback_query.data
    await state.update_data(alert_preference=alert_preference)
    await callback_query.message.answer("Alert preferences saved successfully!")  # You can add more logic here if needed
    data = await state.get_data()
    await database.add_or_update_user_alerts(callback_query.from_user.id, data["currencies"], data["threshold"], data["alert_preference"])
    await state.clear()  # Finish the conversation
    await callback_query.answer("Started tracking")

####################FSM for alerts###################################



