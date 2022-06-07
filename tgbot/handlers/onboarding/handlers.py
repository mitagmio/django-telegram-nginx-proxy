from ast import Pass, Str
from ctypes import Union
import datetime
from email.policy import default
import time
from turtle import update

from django.utils import timezone
from telegram import Bot, ParseMode, Update
from telegram.ext import CallbackContext

from tgbot.handlers.onboarding import static_text, static_state
from tgbot.handlers.utils.info import extract_user_data_from_update
from tgbot.models import User, P2p
from tgbot.handlers.onboarding.keyboards import make_keyboard_for_start_command
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from tgbot.tasks import broadcast_message
from dtb.settings import BINANCE_API, BINANCE_SECRET

# Принимаем любой текст и проверяем состояние пользователя


def message_handler_func(update: Update, context: CallbackContext):
    state = User.get_user_state(update, context)
    if update.message.chat.id != -1001717597940:
        if state in State_Dict:
            func_menu = State_Dict[state]
            func_menu(update, context)
        elif update.message.text in Menu_Dict:  # button_message проверяем текст на соответствие любой кнопке
            func_menu = Menu_Dict[update.message.text]
            func_menu(update, context)
        else:
            del_mes(update, context)


def callback_inline(update: Update, context: CallbackContext):
    # Если сообщение из чата с ботом
    # print('callback_inline', update)
    call_list = ['Город',
                 ]
    call = update.callback_query
    if call.message:
        call_func = call.data.split(' ')
        if len(call_func) > 1:
            if call_func[0] in call_list:
                func_menu = Menu_Dict[call_func[0]]
                func_menu(update, context, call_func[1])
        else:
            func_menu = Menu_Dict[call.data]
            func_menu(update, context)
    # Если сообщение из инлайн-режима
    # elif call.inline_message_id:
    #	func_menu = Menu_Dict[call.data]
    #	func_menu(call, context)

# Удаляем записи для отображения только одной


# функция удаляющая предыдущие сообщения бота (делает эффект обновления меню при нажатии кнопки) и человека по States.S_MENU(всегда, если его статус=1)
def del_mes(update: Update, context: CallbackContext, bot_msg: bool = False):
    message = get_message_bot(update)
    try:
        context.bot.delete_message(message.chat.id, message.message_id)
    except:
        pass
    if bot_msg:
        # time.sleep(0.1)
        try:
            context.bot.delete_message(
                message.chat.id, int(message.message_id)-1)
        except:
            pass
        # time.sleep(0.1)
        try:
            context.bot.delete_message(
                message.chat.id, int(message.message_id)-2)
        except:
            pass
        # time.sleep(0.1)
        try:
            context.bot.delete_message(
                message.chat.id, int(message.message_id)-3)
        except:
            pass
        # time.sleep(0.1)
        try:
            context.bot.delete_message(
                message.chat.id, int(message.message_id)-4)
        except:
            pass
        # time.sleep(0.1)
        try:
            context.bot.delete_message(
                message.chat.id, int(message.message_id)-5)
        except:
            pass
        # time.sleep(0.1)
        try:
            context.bot.delete_message(
                message.chat.id, int(message.message_id)-6)
        except:
            pass

# Распаковываем message


def get_message_bot(update):
    if hasattr(update, 'message') and update.message != None:
        message = update.message
    if hasattr(update, 'callback_query') and update.callback_query != None:
        message = update.callback_query.message
    return message

# Проверяем является ли float


def isfloat(num):
    try:
        float(num)
        return True
    except ValueError:
        return False

# Проверка на username


def check_username(update: Update, context: CallbackContext, text='\n'):
    message = get_message_bot(update)
    if not hasattr(message.chat, 'username') or message.chat.username == '' or message.chat.username == None:
        btn_menu = InlineKeyboardButton(text='🎉 Старт', callback_data='Старт')
        markup = InlineKeyboardMarkup([
            [btn_menu]
        ])
        id = context.bot.send_message(message.chat.id, static_text.NOT_USER_NAME.format(
            text=text, tgid=message.chat.id), reply_markup=markup)  # отправляет приветствие и кнопку
        User.set_message_id(update, context, id.message_id)
        return False
    return True


# Начало диалога


def command_start(update: Update, context: CallbackContext):
    u, _ = User.get_user_and_created(update, context)
    message = get_message_bot(update)
    # if u.state == static_state.S_ACCEPTED_ORDER:
    #     cmd_accepted_order_show(update, context)
    #     return
    # if u.state == static_state.S_ACCEPTED_EXCHANGE:
    #     cmd_accepted_exchange_show(update, context)
    #     return
    text = "\n"
    # Если пользователь без username мы предлагаем ему заполнить свой профиль.
    if check_username(update, context, text):
        btn_menu = InlineKeyboardButton(text='📋 Меню', callback_data='Меню')
        markup = InlineKeyboardMarkup([
            [btn_menu]
        ])
        # print(bot.get_chat_member(352482305))
        id = context.bot.send_message(message.chat.id, static_text.START_USER.format(
            username=u.username,text=text, tgid=message.chat.id), reply_markup=markup, parse_mode="HTML")  # отправляет приветствие и кнопку
        u.message_id = id.message_id
        u.save()
    del_mes(update, context, True)

    # if created:
    #     text = static_text.start_created.format(first_name=u.first_name)
    # else:
    #     text = static_text.start_not_created.format(first_name=u.first_name)

    # update.message.reply_text(text=text, reply_markup=make_keyboard_for_start_command())


# Меню


def cmd_menu(update: Update, context: CallbackContext):
    if check_username(update, context):
        u = User.get_user(update, context)
        message = get_message_bot(update)
        # помечаем состояние пользователя.
        u.state = static_state.S_MENU
        buttons = []
        btn_help = InlineKeyboardButton(text='🆘 Помощь', callback_data='Help')
        btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Старт')
        btn_vc = InlineKeyboardButton(
            text='👨‍👧‍👦🧍‍♂️ Kostevich VC', callback_data='Help')
        btn_selected = InlineKeyboardButton(
            text='🏵💸 Kostevich Selected', callback_data='Help')
        btn_academy = InlineKeyboardButton(
            text='🧮📝 Kostevich Academy', callback_data='Help')
        buttons.append([btn_vc,btn_selected])
        buttons.append([btn_academy])
        
        if u.is_admin:
            btn_admin = InlineKeyboardButton(
                text='📝 Администрирование', callback_data="Администрирование")
            buttons.append([btn_admin])
        buttons.append([btn_help, btn_back])
        markup = InlineKeyboardMarkup(buttons)
        id = context.bot.send_message(
            message.chat.id, static_text.MENU, reply_markup=markup, parse_mode="HTML")
        u.message_id = id.message_id
        u.save()
    del_mes(update, context, True)


###################################
###################################
def cmd_help(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    message = get_message_bot(update)
    buttons = []
    btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Меню')
    btn_main = InlineKeyboardButton(text='⏮ В начало', callback_data='Старт')
    buttons.append([btn_main, btn_back])
    markup = InlineKeyboardMarkup(buttons)
    id = context.bot.send_message(
        message.chat.id,
        """<b>ПОМОЩЬ</b>
        
        """,
        reply_markup=markup, parse_mode="HTML", disable_web_page_preview=True)
    u.message_id = id.message_id
    u.save()
    del_mes(update, context, True)


def cmd_admin(update: Update, context: CallbackContext):
    del_mes(update, context, True)
    u = User.get_user(update, context)
    if u.is_admin:
        message = get_message_bot(update)
        buttons = []
        btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Меню')
        btn_main = InlineKeyboardButton(
            text='⏮ В начало', callback_data='Старт')
        buttons.append([btn_main, btn_back])
        markup = InlineKeyboardMarkup(buttons)
        id = context.bot.send_message(message.chat.id, "📝 Администрирование:\nвыбери необходимый пункт для дальнейших действий\n\n<code>{}</code>".format(
            P2p.pay_trade_history()), reply_markup=markup, parse_mode="HTML")
        u.message_id = id.message_id
        u.save()
    else:
        command_start(update, context)


def cmd_pass():
    pass


# словарь функций Меню по состоянию
State_Dict = {
    # Когда выбрано Меню, мы можем только нажимать кнопки. Любой текст удаляется
    static_state.S_MENU: del_mes,
}

# словарь функций Меню
Menu_Dict = {
    'Старт': command_start,
    'Меню': cmd_menu,
    'Администрирование': cmd_admin,
    'pass': cmd_pass,
    'Help': cmd_help,
}


def secret_level(update: Update, context: CallbackContext) -> None:
    # callback_data: SECRET_LEVEL_BUTTON variable from manage_data.py
    """ Pressed 'secret_level_button_text' after /start command"""
    user_id = extract_user_data_from_update(update)['user_id']
    text = static_text.unlock_secret_room.format(
        user_count=User.objects.count(),
        active_24=User.objects.filter(
            updated_at__gte=timezone.now() - datetime.timedelta(hours=24)).count()
    )

    context.bot.edit_message_text(
        text=text,
        chat_id=user_id,
        message_id=update.callback_query.message.message_id,
        parse_mode=ParseMode.HTML
    )
