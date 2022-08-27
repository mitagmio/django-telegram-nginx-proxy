import datetime
import time

from django.utils import timezone
from telegram import Bot, ParseMode, Update
from telegram.ext import CallbackContext
from traitlets import Float

from tgbot.handlers.onboarding import static_text, static_state
from tgbot.handlers.utils.info import extract_user_data_from_update, generate_qr
from tgbot.models import User, P2p, Invoice, Tarif, Сourse
from tgbot.handlers.onboarding.keyboards import *
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from tgbot.tasks import broadcast_message
from dtb.settings import BINANCE_API, BINANCE_SECRET

# Принимаем любой текст и проверяем состояние пользователя


def message_handler_func(update: Update, context: CallbackContext):
    print(update)
    if (hasattr(update, 'message') and update.message != None and update.message.chat.id != -1001796561677) or (hasattr(update, 'channel_post') and update.channel_post != None and update.channel_post.chat.id != -1001695923729):
        u = User.get_user(update, context)
        if u.state in State_Dict:
            func_menu = State_Dict[u.state]
            func_menu(update, context)
        elif update.message.text in Menu_Dict:  # button_message проверяем текст на соответствие любой кнопке
            func_menu = Menu_Dict[update.message.text]
            func_menu(update, context)
        else:
            del_mes(update, context)


def callback_inline(update: Update, context: CallbackContext):
    # Если сообщение из чата с ботом
    # print('callback_inline', update)
    call_list = ['Курс','Тариф'
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
        u = User.get_user(update, context)
        u.state = static_state.S_USERNAME
        id = context.bot.send_message(message.chat.id, static_text.NOT_USER_NAME.format(
            text=text, tgid=message.chat.id), reply_markup=make_keyboard_for_check_username())  # отправляет приветствие и кнопку
        u.message_id = id.message_id
        u.save()
        return False
    return True

# Проверка на email
def chenge_email(update: Update, context: CallbackContext, text='\n'):
    message = get_message_bot(update)
    u, _ = User.get_user_and_created(update, context)
    u.state = static_state.S_EMAIL
    id = context.bot.send_message(message.chat.id, static_text.NOT_EMAIL_NAME.format(
        text=text, tgid=message.chat.id), reply_markup=make_keyboard_for_check_username())  # отправляет приветствие и кнопку
    u.message_id = id.message_id
    u.save()
    del_mes(update, context, True)

def check_email(update: Update, context: CallbackContext, text='\n'):
    message = get_message_bot(update)
    u, _ = User.get_user_and_created(update, context)
    if u.email == '' or u.email == None:
        u = User.get_user(update, context)
        u.state = static_state.S_EMAIL
        id = context.bot.send_message(message.chat.id, static_text.NOT_EMAIL_NAME.format(
            text=text, tgid=message.chat.id), reply_markup=make_keyboard_for_check_username())  # отправляет приветствие и кнопку
        u.message_id = id.message_id
        u.save()
        return False
    return True

def s_email(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    message = get_message_bot(update)
    email = message.text
    try:
        u.email = email
        u.state = static_state.S_MENU
        u.save()
    except:
        del_mes(update, context, True)
        return check_email(update, context)
    cmd_wallet(update, context)
# Начало диалога


def command_start(update: Update, context: CallbackContext):
    u, _ = User.get_user_and_created(update, context)
    message = get_message_bot(update)
    if context is not None and context.args is not None and len(context.args) > 0:
        payload = context.args[0]
        if payload == 'metamask':
            if u.marker is not None and u.marker != '' and len(u.marker) > 1 and 'metamask' not in u.marker:
                u.marker += ', metamask'
            if u.marker is None or u.marker == '':
                u.marker = 'metamask'
            u.save()
            cmd_top_up_metamask(update, context)
            del_mes(update, context, True)
            return
    # if u.state == static_state.S_ACCEPTED_ORDER:
    #     cmd_accepted_order_show(update, context)
    #     return
    if u.state == static_state.S_USERNAME or u.state == static_state.S_EMAIL:
        cmd_wallet(update, context)
        del_mes(update, context, True)
        return
    text = '\n'
    u.state = static_state.S_MENU
    id = context.bot.send_message(message.chat.id, static_text.START_USER.format(
        username=u.username,text=text, tgid=message.chat.id), reply_markup=make_keyboard_for_start(), parse_mode="HTML")  # отправляет приветствие и кнопку
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
    u = User.get_user(update, context)
    message = get_message_bot(update)
    # помечаем состояние пользователя.
    u.state = static_state.S_MENU
    metamask = False
    if u.marker is not None and 'metamask' in u.marker:
        metamask = True
    id = context.bot.send_message(
        message.chat.id, static_text.MENU, reply_markup=make_keyboard_for_cmd_menu(u.is_admin, metamask), parse_mode="HTML")
    u.message_id = id.message_id
    u.save()
    del_mes(update, context, True)


# Кошелек

def cmd_wallet(update: Update, context: CallbackContext):
    u = User.set_user_addr(update, context)
    message = get_message_bot(update)
    # помечаем состояние пользователя.
        # Если пользователь без username мы предлагаем ему заполнить свой профиль.
    # print(bot.get_chat_member(352482305))
    if check_username(update, context):
        if check_email(update, context):
            u.state = static_state.S_MENU
            text = ''
            if u.metamask_balance > 0:
                 text = f'Инвестировано в 🦊 Метамаск {u.metamask_balance} USDT'
            id = context.bot.send_message(
                message.chat.id, static_text.WALLET.format(balance=u.balance, email=u.email, text=text), reply_markup=make_keyboard_for_cmd_wallet(), parse_mode="HTML")
            u.message_id = id.message_id
            u.save()
    del_mes(update, context, True)

# Кнопка пополнения мультикошельков USDT TRC20 

def cmd_top_up_multi_wallet_usdt(update: Update, context: CallbackContext):
    u = User.set_user_addr(update, context)
    message = get_message_bot(update)
    if check_username(update, context):
        if check_email(update, context):
            u = User.get_user(update, context)
            if u.addr != '0':
                id = context.bot.send_photo(
                    chat_id=message.chat.id, photo=generate_qr(u.addr).getvalue(), caption=static_text.MULTI_WALLET.format(addr=u.addr), reply_markup=make_keyboard_for_cmd_top_up_wallet_usdt(), parse_mode="HTML")
                u.message_id = id.message_id
                u.save()
                return
            return cmd_wallet(update, context)
    del_mes(update, context, True)


# Кнопка пополнения USDT TRC20 

def cmd_top_up_wallet_usdt(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    message = get_message_bot(update)
    if check_username(update, context):
        if check_email(update, context):
            # помечаем состояние пользователя.
            u.state = static_state.S_TOP_UP_WALLET_USDT
            invoice = Invoice.objects.filter(payer_id=u)
            if len(invoice) > 0:
                return s_top_up_wallet_usdt(update, context, invoice[0].summ_invoice)
            id = context.bot.send_message(
                message.chat.id, static_text.WALLET_SUMM, reply_markup=make_keyboard_for_cmd_top_up_wallet_usdt(), parse_mode="HTML")
            u.message_id = id.message_id
            u.save()
    del_mes(update, context, True)

# Показываем счет на оплату

def s_top_up_wallet_usdt(update: Update, context: CallbackContext, summ: float = 0.0):
    u = User.get_user(update, context)
    message = get_message_bot(update)
    if summ == 0.0:
        summ = message.text
        if isfloat(summ) and float(summ) > 0:
            summ = float(summ)
            while len(Invoice.objects.filter(summ_invoice=summ)) > 0:
                    summ = ((summ * 100) + 1)/100
                    time.sleep(0.1)
            Invoice.objects.create(summ_invoice=summ, payer_id=u)
            # помечаем состояние пользователя.
            u.state = static_state.S_MENU
        else:
            return cmd_top_up_wallet_usdt(update, context)
    id = context.bot.send_photo(
            chat_id=message.chat.id, photo=generate_qr('TYXmiSD7KoLmFyWoPauM2MpXfpS3Z1fsCq').getvalue(), caption=static_text.WALLET_ADR.format(summ_float=summ), reply_markup=make_keyboard_for_s_top_up_wallet_usdt(), parse_mode="HTML")
    u.message_id = id.message_id
    u.save()
    del_mes(update, context, True)

# Удаляем выставленный счет
def cmd_del_invoice_trc20(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    invoice = Invoice.objects.get(payer_id=u)
    invoice.delete() 
    cmd_wallet(update, context)



##### Академия
def cmd_academy(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    message = get_message_bot(update)
    try:
        Сourses = Сourse.objects.all().order_by('id')
        text = ''
        for c in Сourses:
            text += "➡️ <u><b>{title}</b></u> - {teaser}\n\n".format(title=c.title, teaser=c.teaser)
        reply_markup = make_keyboard_for_cmd_academy(Сourses.values())
    except:
        reply_markup = make_keyboard_for_cmd_help()
        text = "Курсов пока нет 😇"
    id = context.bot.send_message(
        message.chat.id, static_text.ACADEMY.format(text=text),
        reply_markup=reply_markup, parse_mode="HTML", disable_web_page_preview=True)
    u.message_id = id.message_id
    u.save()
    del_mes(update, context, True)

def cmd_academy_course(update: Update, context: CallbackContext, course_id: int):
    u = User.get_user(update, context)
    message = get_message_bot(update)
    # try:
    cource = Сourse.objects.get(id=course_id)
    tarifs = Сourse.objects.get(id=course_id).сourse_tarifs_set.all().order_by('id')
    text = '🪙 <b>ТАРИФЫ:</b>\n\n'
    for t in tarifs:
        text += t.__dict__['description']+'\n\n'
    reply_markup = make_keyboard_for_academy_course(tarifs.values())
    # except:
    #     reply_markup = make_keyboard_for_academy_course()
    #     text = "Тарифов пока нет 😇"
    id = context.bot.send_message(
        message.chat.id,  cource.description +'\n\n' + text,
        reply_markup=reply_markup, parse_mode="HTML")
    u.message_id = id.message_id
    u.save()
    del_mes(update, context, True)

def buy_tarif(update: Update, context: CallbackContext, tarif_id: int):
    u = User.get_user(update, context)
    message = get_message_bot(update)

    if check_email(update, context):
        t = Tarif.objects.get(id=tarif_id)
        if u.balance >= t.coast:
            text = static_text.BUY_COURSE.format(email=u.email)
            params = '{"user":{"email":"'+u.email+'"},"system":{"refresh_if_exists":1},"deal":{"offer_code":"'+str(t.offer_code)+'","deal_status":"new","deal_cost":"'+str(t.coast)+'","deal_is_paid":"1","payment_status":"accepted","payment_type":"CASH","deal_currency":"USD"}}'
            print(Tarif.buy_tarif(params))
            reply_markup = make_keyboard_for_cmd_help()
            u.balance -= t.coast
            u.save()
        else:
            text = static_text.NOT_BUY.format(difference=t.coast-u.balance, balance=u.balance)
            reply_markup = make_keyboard_for_no_money()
        id = context.bot.send_message(
                message.chat.id, text,
                reply_markup=reply_markup, parse_mode="HTML")
        u.message_id = id.message_id
        u.save()
    del_mes(update, context, True)

# Venture
def cmd_venture(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    message = get_message_bot(update)

    id = context.bot.send_message(
        message.chat.id, static_text.VENTURE,
        reply_markup=make_keyboard_for_cmd_venture(), parse_mode="HTML", disable_web_page_preview=True)
    u.message_id = id.message_id
    u.save()
    del_mes(update, context, True)

# Metamask
def cmd_top_up_metamask(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    message = get_message_bot(update)
    invest = ''
    text = ''
    reply_markup = make_keyboard_for_cmd_help()
    if u.metamask_balance > 0:
        invest = f'Инвестировано {u.metamask_balance} USDT'

    if u.state == static_state.S_TOP_UP_WALLET_METAMASK:
        summ = message.text
        if isfloat(summ) and float(summ) >= 1000 and u.balance >= float(summ):
            summ = float(summ)
            u.balance -= summ
            u.metamask_balance += summ
            u.save()
            invest = f'Инвестировано {u.metamask_balance} USDT'
            text = f'Успешно инвестировано'
        else:
            price = 5000
            text = static_text.NOT_BUY.format(difference=price-u.balance, balance=u.balance)
    # u.state = static_state.S_TOP_UP_WALLET_METAMASK
    id = context.bot.send_photo(chat_id=message.chat.id, photo=open('dtb/media/photo_2022-07-12_14-00-52.jpg', 'rb'), caption=static_text.METAMASK_INVEST.format(invest=invest, text=text), reply_markup=reply_markup, parse_mode="HTML")
    u.message_id = id.message_id
    u.save()
    del_mes(update, context, True)

# selected
def cmd_selected(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    message = get_message_bot(update)
    reply_markup = make_keyboard_for_cmd_selected()
    timestamp = int(datetime.datetime.today().timestamp())
    if u.execute_selected_time > timestamp:
        execute_selected_time = u.execute_selected_time
        time_string_format = '‼️ Доступ заканчивается: ' + str(datetime.datetime.fromtimestamp(execute_selected_time).strftime('%Y-%m-%d %H:%M'))
    else:
        time_string_format = ''
    id = context.bot.send_message(
                message.chat.id, static_text.TEXT_SELECTED.format(end_date=time_string_format),
                reply_markup=reply_markup, parse_mode="HTML")
    u.message_id = id.message_id
    u.save()
    del_mes(update, context, True)

def not_remind (update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    u.remind = False
    u.save()
    command_start(update, context)

def buy_selected(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    message = get_message_bot(update)

    if check_email(update, context):
        timestamp = int(datetime.datetime.today().timestamp())
        price = 100
        if u.bonus_programm == 'first_month':
            price = 100
        if u.balance >= price:
            reply_markup = make_keyboard_for_cmd_help()
            u.balance -= price
            if timestamp < 1661990400:
                u.first_month = True
                u.bonus_programm = 'first_month'
            if timestamp < u.execute_selected_time:
                u.execute_selected_time += 60 * 60 * 24 * 30
                execute_selected_time = u.execute_selected_time
                time_string_format = datetime.datetime.fromtimestamp(execute_selected_time).strftime('%Y-%m-%d %H:%M')
                text = static_text.BUY_SELECTED_TOP_UP.format(end_date='‼️ Доступ заканчивается: ' + str(time_string_format))
            else:
                execute_selected_time = timestamp + 60 * 60 * 24 * 30
                time_string_format = datetime.datetime.fromtimestamp(execute_selected_time).strftime('%Y-%m-%d %H:%M')
                u.execute_selected_time = execute_selected_time
                # link_chat = context.bot.create_chat_invite_link(chat_id=-1001796561677, expire_date=execute_selected_time, member_limit=1).invite_link
                link_channel = context.bot.create_chat_invite_link(chat_id=-1001695923729, expire_date=timestamp + 60 * 60 * 24, member_limit=1).invite_link
                # print('link_chat',link_chat)
                print('link_channel',link_channel)
                text = static_text.BUY_SELECTED.format(end_date=time_string_format, link_channel=link_channel) # link_chat=link_chat,
            u.execute_bonus_time = 0
            u.remind = True
            u.save()
        else:
            text = static_text.NOT_BUY.format(difference=price-u.balance, balance=u.balance)
            reply_markup = make_keyboard_for_no_money()
        id = context.bot.send_message(
                message.chat.id, text,
                reply_markup=reply_markup, parse_mode="HTML")
        u.message_id = id.message_id
        u.save()
    del_mes(update, context, True)

###################################
###################################
def cmd_help(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    message = get_message_bot(update)

    id = context.bot.send_message(
        message.chat.id, static_text.HELP,
        reply_markup=make_keyboard_for_cmd_help(), parse_mode="HTML", disable_web_page_preview=True)
    u.message_id = id.message_id
    u.save()
    del_mes(update, context, True)

def cmd_soon(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    message = get_message_bot(update)

    id = context.bot.send_message(
        message.chat.id, static_text.SOON,
        reply_markup=make_keyboard_for_cmd_help(), parse_mode="HTML", disable_web_page_preview=True)
    u.message_id = id.message_id
    u.save()
    del_mes(update, context, True)

def cmd_admin(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    if u.is_admin:
        message = get_message_bot(update)
        id = context.bot.send_message(message.chat.id, static_text.ADMIN_MENU_TEXT, reply_markup=make_keyboard_for_cmd_admin(u), parse_mode="HTML")
        #static_text.ADMIN_MENU_TEXT.format(P2p.pay_trade_history())
        u.state = static_state.S_MENU_ADMIN
        u.message_id = id.message_id
        u.save()
        del_mes(update, context, True)
    else:
        command_start(update, context)

def cmd_top_up_user_admin(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    if u.is_admin and u.user_id == 352482305:
        message = get_message_bot(update)
        # помечаем состояние пользователя.
        u.state = static_state.S_TOP_UP_WALLET_ADMIN
        id = context.bot.send_message(
            message.chat.id, static_text.WALLET_ADMIN, reply_markup=make_keyboard_for_cmd_admin(u), parse_mode="HTML")
        u.message_id = id.message_id
        u.save()
        del_mes(update, context, True)
    else:
        command_start(update, context)

def s_top_up_user_admin(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    if u.is_admin and u.user_id == 352482305:
        message = get_message_bot(update)
        username = User.get_user_by_username_or_user_id(message.text)
        invoice = Invoice.objects.filter(payer_id=username)
        if len(invoice) > 0:
            invoice = invoice[0].summ_invoice
        else:
            invoice = 0 
        id = context.bot.send_message(
            message.chat.id, static_text.WALLET_ADMIN_USDT.format(username=username.username, summ_float=invoice, balance=username.balance), reply_markup=make_keyboard_for_cmd_admin(u), parse_mode="HTML")
        u.state = static_state.S_TOP_UP_WALLET_USDT_ADMIN
        u.message_id = id.message_id
        u.save()
        del_mes(update, context, True)
    else:
        command_start(update, context)


def top_up_user_wallet_admin(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    if u.is_admin and u.user_id == 352482305:
        message = get_message_bot(update)
        username = User.get_user_by_username_or_user_id(message.text.split(' ')[0])
        summ = float(message.text.split(' ')[1])
        # помечаем состояние пользователя.
        u.state = static_state.S_MENU_ADMIN
        try:
            invoice = Invoice.objects.get(payer_id=username)
            inv = invoice.summ_invoice
            invoice.delete()
        except:
            inv = 0
            pass
        username.balance += summ
        username.save()
        text = '💵 Ваш платеж на сумму <code>{}</code> USDT зачислен.\n\nТекущий баланс составляет <code>{}</code> USDT'.format(
            summ, username.balance)
        context.bot.send_message(
            chat_id =username.user_id,
            text=text,
            entities=None,
            parse_mode="HTML",
            reply_markup=None,
        )
        id = context.bot.send_message(
            message.chat.id, static_text.WALLET_ADMIN_FINAL.format(username=username.username, summ_float=inv, summ_admin=summ), reply_markup=make_keyboard_for_cmd_admin(u), parse_mode="HTML")
        u.message_id = id.message_id
        u.save()
        del_mes(update, context, True)
    else:
        command_start(update, context)

def cmd_pass():
    pass


# словарь функций Меню по состоянию
State_Dict = {
    # Когда выбрано Меню, мы можем только нажимать кнопки. Любой текст удаляется
    static_state.S_MENU: del_mes,
    static_state.S_TOP_UP_WALLET_USDT: s_top_up_wallet_usdt,
    static_state.S_EMAIL: s_email,
    # админка
    static_state.S_TOP_UP_WALLET_ADMIN: s_top_up_user_admin,
    static_state.S_TOP_UP_WALLET_USDT_ADMIN: top_up_user_wallet_admin,
    static_state.S_TOP_UP_WALLET_METAMASK: cmd_top_up_metamask,
}

# словарь функций Меню
Menu_Dict = {
    'Старт': command_start,
    'Меню': cmd_menu,
    'Кошелек': cmd_wallet,
    'Почта': chenge_email,
    'Пополнить_Кошелек': cmd_top_up_multi_wallet_usdt,
    'Пополнить_Кошелек_TRC20':cmd_top_up_wallet_usdt,
    'Удалить_invoice':cmd_del_invoice_trc20,
    'Академия': cmd_academy,
    'Курс': cmd_academy_course,
    'Тариф': buy_tarif,
    'Венчур': cmd_venture,
    'МетаМаск_Invest':cmd_top_up_metamask,
    'Селектед': cmd_selected,
    'Селектед_soon':cmd_soon,
    'Купить_Селектед': buy_selected,
    'Не_напоминать': not_remind,
    'Администрирование': cmd_admin,
    'Пополнить_пользователю': cmd_top_up_user_admin,
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
