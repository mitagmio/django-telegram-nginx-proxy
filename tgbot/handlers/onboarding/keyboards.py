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
        ],
        [
            InlineKeyboardButton(text='🎥 🛑YouTube', url="https://www.youtube.com/c/EkaterinaKostevich")
        ],
        [
            InlineKeyboardButton(text='👫💃 Реферальные ссылки', url="https://telegra.ph/Referalnye-ssylki-dlya-registracii-na-birzhe-04-15")
        ],
        [
            InlineKeyboardButton(text='🆘 Помощь', url="https://t.me/KostevichSupport_Bot"),
            InlineKeyboardButton(text='💰💰 Кошелек', callback_data='Кошелек')
        ]
    ]

    return InlineKeyboardMarkup(buttons)

def make_keyboard_for_check_username() -> InlineKeyboardMarkup:
    buttons = [[
        InlineKeyboardButton(text='💰💰 Кошелек', callback_data='Кошелек')
    ]]
    return InlineKeyboardMarkup(buttons)

def make_keyboard_for_cmd_menu(adm) -> InlineKeyboardMarkup:
        buttons = []
        btn_help = InlineKeyboardButton(text='🆘 Помощь', url="https://t.me/KostevichSupport_Bot")
        btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Старт')
        btn_vc = InlineKeyboardButton(
            text='👨‍👧‍👦🧍‍♂️ Kostevich Venture', url='https://t.me/kostevich_VC')
        btn_selected = InlineKeyboardButton(
            text='🏵💸 Kostevich SELECTED', callback_data='Селектед')#Селектед_soon
        btn_academy = InlineKeyboardButton(
            text='🧮📝 Kostevich Academy', callback_data='Академия')
        buttons.append([btn_vc])
        buttons.append([btn_selected])
        buttons.append([btn_academy])
        
        if adm:
            btn_admin = InlineKeyboardButton(
                text='📝 Администрирование', callback_data="Администрирование")
            buttons.append([btn_admin])
        buttons.append([btn_help, btn_back])
        return InlineKeyboardMarkup(buttons)

def make_keyboard_for_cmd_wallet() -> InlineKeyboardMarkup:
        buttons = []
        btn_help = InlineKeyboardButton(text='🆘 Помощь', url="https://t.me/KostevichSupport_Bot")
        btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Старт')
        btn_top_up_usdt = InlineKeyboardButton(
            text='💸 Пополнить баланс USDT TRC20', callback_data='Пополнить_Кошелек_TRC20')
        btn_change_email = InlineKeyboardButton(
            text='📨 Изменить почту', callback_data='Почта')
        buttons.append([btn_top_up_usdt])
        buttons.append([btn_change_email])
        buttons.append([btn_help, btn_back])
        return InlineKeyboardMarkup(buttons)

def make_keyboard_for_cmd_top_up_wallet_usdt() -> InlineKeyboardMarkup:
        buttons = []
        btn_help = InlineKeyboardButton(text='🆘 Помощь', url="https://t.me/KostevichSupport_Bot")
        btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Старт')
        buttons.append([btn_help, btn_back])
        return InlineKeyboardMarkup(buttons)

def make_keyboard_for_s_top_up_wallet_usdt() -> InlineKeyboardMarkup:
        buttons = []
        btn_help = InlineKeyboardButton(text='‼️ Отменить платеж', callback_data='Удалить_invoice')
        btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Старт')
        buttons.append([btn_help, btn_back])
        return InlineKeyboardMarkup(buttons)

def make_keyboard_for_cmd_academy(btns = []) -> InlineKeyboardMarkup:
    buttons = []
    if len(btns) > 0:
        for b in btns:
               buttons.append([InlineKeyboardButton(text=b['button_name'], callback_data=b['callback_text']+' '+str(b['id']))])
    btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Меню')
    btn_main = InlineKeyboardButton(text='⏮ В начало', callback_data='Старт')

    buttons.append([btn_main, btn_back])
    return InlineKeyboardMarkup(buttons)

def make_keyboard_for_academy_course(btns = []) -> InlineKeyboardMarkup:
    buttons = []
    if len(btns) > 0:
        for b in btns:
               buttons.append([InlineKeyboardButton(text=b['button_buy_name'], callback_data=b['callback_text']+' '+str(b['id']))])
    # btn_detail = InlineKeyboardButton(text='Подробнее о курсе на лендинге', url="https://kostevich.online/level_1")
    btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Академия')
    btn_main = InlineKeyboardButton(text='⏮ В начало', callback_data='Старт')
    # buttons.append([btn_detail])
    buttons.append([btn_main, btn_back])
    return InlineKeyboardMarkup(buttons)

def make_keyboard_for_buy_hamster_to_wolf1() -> InlineKeyboardMarkup:
    buttons = []
    btn_one = InlineKeyboardButton(text='1️⃣ Без сопровождения ', callback_data='Меню')
    btn_two = InlineKeyboardButton(text='2️⃣ С куратором', callback_data='Меню')
    btn_three = InlineKeyboardButton(text='3️⃣ C Екатериной', callback_data='Меню')
    btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Меню')
    btn_main = InlineKeyboardButton(text='⏮ В начало', callback_data='Старт')
    buttons.append([btn_one])
    buttons.append([btn_main, btn_back])
    return InlineKeyboardMarkup(buttons)

def make_keyboard_for_no_money() -> InlineKeyboardMarkup:
    buttons = []
    btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Меню')
    btn_main = InlineKeyboardButton(text='⏮ В начало', callback_data='Старт')
    btn_top_up_usdt = InlineKeyboardButton(
            text='💸 Пополнить баланс USDT TRC20', callback_data='Пополнить_Кошелек_TRC20')
    buttons.append([btn_top_up_usdt])
    buttons.append([btn_main, btn_back])
    return InlineKeyboardMarkup(buttons)

def make_keyboard_for_cmd_venture() -> InlineKeyboardMarkup:
    buttons = []
    buttons.append([InlineKeyboardButton(text='✅ True', callback_data='Меню'), InlineKeyboardButton(text='🐙 Kraken', callback_data='Меню')])
    buttons.append([InlineKeyboardButton(text='🦊 Metamask', callback_data='Меню'), InlineKeyboardButton(text='💰💰 Кошелек', callback_data='Кошелек')])
    buttons.append([InlineKeyboardButton(text='Узнать больше о фонде', url='https://t.me/KostevichSupport_Bot')])
    btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Меню')
    btn_main = InlineKeyboardButton(text='⏮ В начало', callback_data='Старт')
    buttons.append([btn_main, btn_back])
    return InlineKeyboardMarkup(buttons)

def make_keyboard_for_cmd_selected() -> InlineKeyboardMarkup:
    buttons = []
    btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Меню')
    btn_main = InlineKeyboardButton(text='⏮ В начало', callback_data='Старт')
    btn_top_up_usdt = InlineKeyboardButton(
            text='💸 Купить доступ 100$', callback_data='Купить_Селектед')
    btn_about_selected = InlineKeyboardButton(
            text='⁉️ О SELECTED', url='https://telegra.ph/CHto-takoe-Kostevich-SELECTED-i-kakuyu-polzu-mozhno-iz-ehtogo-izvlech-07-26')
    buttons.append([btn_about_selected])
    buttons.append([btn_top_up_usdt])
    buttons.append([btn_main, btn_back])
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