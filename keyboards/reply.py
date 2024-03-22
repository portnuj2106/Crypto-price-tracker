from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def set_alerts_button():
    kb = [
        [KeyboardButton(text="Set/Update alerts")],
        [KeyboardButton(text="Get alerts history")]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    return keyboard