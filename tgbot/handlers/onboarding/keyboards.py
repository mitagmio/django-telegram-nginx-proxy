from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from tgbot.handlers.onboarding.manage_data import SECRET_LEVEL_BUTTON
from tgbot.handlers.onboarding.static_text import github_button_text, secret_level_button_text, start_button_text


def make_keyboard_for_start_command() -> InlineKeyboardMarkup:
    buttons = [[
        InlineKeyboardButton(github_button_text, url="https://github.com/ohld/django-telegram-bot"),
        InlineKeyboardButton(secret_level_button_text, callback_data=f'{SECRET_LEVEL_BUTTON}')
    ]]

    return InlineKeyboardMarkup(buttons)

def make_keyboard_for_start() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text='💃📋 Проекты E. Kostevich', callback_data='Меню'),
            InlineKeyboardButton(text='💰💰 Кошелек', callback_data='Help')
        ],
        [
            InlineKeyboardButton(text='🆘 Помощь', url="https://t.me/KostevichSupport_Bot"),
            InlineKeyboardButton(text='👭👬💃 Рефералка', callback_data='Help')
        ]
    ]

    return InlineKeyboardMarkup(buttons)

def make_keyboard_for_check_username() -> InlineKeyboardMarkup:
    buttons = [[
        InlineKeyboardButton(start_button_text, callback_data='Старт')
    ]]
    return InlineKeyboardMarkup(buttons)

def make_keyboard_for_cmd_menu(adm) -> InlineKeyboardMarkup:
        buttons = []
        btn_help = InlineKeyboardButton(text='🆘 Помощь', url="https://t.me/KostevichSupport_Bot")
        btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Старт')
        btn_vc = InlineKeyboardButton(
            text='👨‍👧‍👦🧍‍♂️ Kostevich VC', callback_data='Help')
        btn_selected = InlineKeyboardButton(
            text='🏵💸 Kostevich Selected', callback_data='Help')
        btn_academy = InlineKeyboardButton(
            text='🧮📝 Kostevich Academy', callback_data='Help')
        buttons.append([btn_vc,btn_selected])
        buttons.append([btn_academy])
        
        if adm:
            btn_admin = InlineKeyboardButton(
                text='📝 Администрирование', callback_data="Администрирование")
            buttons.append([btn_admin])
        buttons.append([btn_help, btn_back])
        return InlineKeyboardMarkup(buttons)

def make_keyboard_for_cmd_help() -> InlineKeyboardMarkup:
    buttons = []
    btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Меню')
    btn_main = InlineKeyboardButton(text='⏮ В начало', callback_data='Старт')
    buttons.append([btn_main, btn_back])
    return InlineKeyboardMarkup(buttons)

def make_keyboard_for_cmd_admin() -> InlineKeyboardMarkup:
    buttons = []
    btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Меню')
    btn_main = InlineKeyboardButton(
        text='⏮ В начало', callback_data='Старт')
    buttons.append([btn_main, btn_back])
    return InlineKeyboardMarkup(buttons)