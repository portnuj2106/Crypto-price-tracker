from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def set_alert_buttons():
    buttons = [
            [InlineKeyboardButton(text="Higher", callback_data="higher"),
             InlineKeyboardButton(text="Lower", callback_data="lower")]
        ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard