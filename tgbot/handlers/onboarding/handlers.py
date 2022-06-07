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
from tgbot.models import User, Cities, Pairs, Periods, Terms, Order, Suggestion, P2p, MerchantsCities, Invoice, Rating
from tgbot.handlers.onboarding.keyboards import make_keyboard_for_start_command
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from tgbot.tasks import broadcast_message
from dtb.settings import BINANCE_API, BINANCE_SECRET

# Начало диалога


def command_start(update: Update, context: CallbackContext):
    u, _ = User.get_user_and_created(update, context)
    state = u.state
    message = get_message_bot(update)
    if state == static_state.S_ACCEPTED_ORDER:
        cmd_accepted_order_show(update, context)
        return
    if state == static_state.S_ACCEPTED_EXCHANGE:
        cmd_accepted_exchange_show(update, context)
        return
    text = "\n"
    # Если пользователь без username мы предлагаем ему заполнить свой профиль.
    if check_username(update, context, text):
        btn_menu = InlineKeyboardButton(text='📋 Меню', callback_data='Меню')
        markup = InlineKeyboardMarkup([
            [btn_menu]
        ])
        # print(bot.get_chat_member(352482305))
        id = context.bot.send_message(message.chat.id, static_text.START_USER.format(
            text, message.chat.id), reply_markup=markup, parse_mode="HTML")  # отправляет приветствие и кнопку
        User.set_message_id(update, context, id.message_id)
    time.sleep(1)
    del_mes(update, context, True)

    # if created:
    #     text = static_text.start_created.format(first_name=u.first_name)
    # else:
    #     text = static_text.start_not_created.format(first_name=u.first_name)

    # update.message.reply_text(text=text, reply_markup=make_keyboard_for_start_command())

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
    call_list = ['Город', 'Пара', 'Период', 'Доставка', 'ТИП_Пары', 'Город_обменника',
                 'Предложить', 'Предложить_курс', 'Выбираю_предложение', 'Клиент_подтвердил_сделку', 'Клиент_отменил_сделку',
                 'Збарать_заявку', 'Ответ_на_отмененный_ордер', 'Ответ_на_выполненный_ордер', 'Отменить_заявку',
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
            text, message.chat.id), reply_markup=markup)  # отправляет приветствие и кнопку
        User.set_message_id(update, context, id.message_id)
        return False
    return True

# Меню


def cmd_menu(update: Update, context: CallbackContext):
    if check_username(update, context):
        message = get_message_bot(update)
        # помечаем состояние пользователя.
        User.set_user_state(update, context, static_state.S_MENU)
        buttons = []
        btn_help = InlineKeyboardButton(text='🆘 Помощь', callback_data='Help')
        btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Старт')
        btn_client = InlineKeyboardButton(
            text='🧍‍♂️ Заказать наличку', callback_data='Меню_Клиент')
        btn_shop = InlineKeyboardButton(
            text='💸 Я Обменник', callback_data='Обменник')
        buttons.append([btn_client, btn_shop])
        u = User.get_user(update, context)
        if u.is_admin:
            btn_admin = InlineKeyboardButton(
                text='📝 Администрирование', callback_data="Администрирование")
            buttons.append([btn_admin])
        buttons.append([btn_help])
        buttons.append([btn_back])
        markup = InlineKeyboardMarkup(buttons)
        id = context.bot.send_message(
            message.chat.id, "Выбери свою роль для проведения сделки:", reply_markup=markup, parse_mode="HTML")
        User.set_message_id(update, context, id.message_id)
    time.sleep(1)
    del_mes(update, context, True)

# Меню клиента ## user_story


def start_client(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    if check_username(update, context):
        if u.orders_client == 'None':
            cmd_client(update, context)
            return
        message = get_message_bot(update)
        # помечаем состояние пользователя.
        User.set_user_state(update, context, static_state.S_MENU)
        buttons = []
        btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Меню')
        btn_client = InlineKeyboardButton(
            text='💸 Новый заказ', callback_data='Клиент')
        btn_shop = InlineKeyboardButton(
            text='📝 Мои заказы', callback_data='Заказы_Клиент')
        buttons.append([btn_client, btn_shop])
        buttons.append([btn_back])
        markup = InlineKeyboardMarkup(buttons)
        id = context.bot.send_message(
            message.chat.id, "Выбери нужный пункт:", reply_markup=markup, parse_mode="HTML")
        User.set_message_id(update, context, id.message_id)
    del_mes(update, context, True)

# новый заказ "Клиент" - Город


def cmd_client(update: Update, context: CallbackContext):
    message = get_message_bot(update)
    User.set_orders_client(update, context, "yes")
    # помечаем состояние пользователя.
    User.set_user_state(update, context, static_state.S_MENU)
    buttons = []
    btn_back = InlineKeyboardButton(
        text='⏪ Назад', callback_data='Меню_Клиент')
    cities = Cities.get_obj()
    if len(cities) >= 1:  # Проверяем есть ли в списке города
        count = 0
        # перебираем весь список если четное количество, то пишем по 2 в ряд.
        for element in cities:
            count += 1
            merchants_id = list(MerchantsCities.objects.filter(
                city_id=element['id']).values_list('merchant_id', flat=True))
            merchants = len(list(User.objects.filter(
                user_id__in=merchants_id, merchant_status='online')))
            # если последний элемент не четный помещаем в одну строку
            if len(cities) == count and len(cities) % 2 != 0:
                city = InlineKeyboardButton(
                    element['ru_name']+'    '+str(merchants), callback_data='Город '+element['ru_name'])
                buttons.append([city])
                break
            if count % 2 != 0:
                city_a = InlineKeyboardButton(
                    element['ru_name']+'    '+str(merchants), callback_data='Город '+element['ru_name'])
            else:
                city_b = InlineKeyboardButton(
                    element['ru_name']+'    '+str(merchants), callback_data='Город '+element['ru_name'])
                buttons.append([city_a, city_b])
    buttons.append([btn_back])
    markup = InlineKeyboardMarkup(buttons)
    id = context.bot.send_message(
        message.chat.id, "<b>Рядом с городом отображается число обменников онлайн, которые получат Вашу заявку и смогут предложить лучшую сделку.\n\nВЫБЕРИ ГОРОД, В КОТОРОМ ХОЧЕШЬ ПРОИЗВЕСТИ ОБМЕН:</b>", reply_markup=markup, parse_mode="HTML")
    User.set_message_id(update, context, id.message_id)
    del_mes(update, context, True)

# Выбран город и выводим меню выбора пары обмена
# Сюда попадаем через колбек с передачей параметра город
# Выбираем направление обмена, тип пары


def cmd_type_pair(update: Update, context: CallbackContext, city: Str = 'None'):
    message = get_message_bot(update)
    if city == 'None':
        cmd_client(update, context)
        return
    del_mes(update, context, True)
    # записываем город в словарь пользователя, потом заберем и очистим поле.
    User.set_city(update, context, city)
    # помечаем состояние пользователя.
    User.set_user_state(update, context, static_state.S_MENU)
    buttons = []
    btn_back = InlineKeyboardButton(
        text='⏪ Назад', callback_data='Меню_Клиент')
    pair_a = InlineKeyboardButton(
        '🇺🇸 USD (наличка)', callback_data='ТИП_Пары '+'USD')
    pair_b = InlineKeyboardButton(
        '🇱🇰 LKR (наличка)', callback_data='ТИП_Пары '+'LKR')
    buttons.append([pair_a, pair_b])
    buttons.append([btn_back])
    markup = InlineKeyboardMarkup(buttons)
    id = context.bot.send_message(
        message.chat.id, "Черновик заказа на обмен\n\nВыбран город <code>{}</code>\n\n<b>ВЫБЕРИ ВАЛЮТУ ДЛЯ ПОЛУЧЕНИЯ:</b>\n\n".format(city), reply_markup=markup, parse_mode="HTML")
    User.set_message_id(update, context, id.message_id)

# Выбран тип пары
# Сюда попадаем через колбек с передачей параметра тип пары
# Выбираем направление обмена


def user_type_pair(update: Update, context: CallbackContext, type_pair: Str = 'None'):
    u, _ = User.get_user_and_created(update, context)
    message = get_message_bot(update)
    if type_pair == 'None':
        cmd_type_pair(update, context, u.city)
        return
    del_mes(update, context, True)
    # записываем город в словарь пользователя, потом заберем и очистим поле.
    User.set_type_pair(update, context, type_pair)
    # помечаем состояние пользователя.
    User.set_user_state(update, context, static_state.S_MENU)
    buttons = []
    btn_back = InlineKeyboardButton(
        text='⏪ Назад', callback_data='Меню_Клиент')
    pairs = Pairs.get_obj()
    if len(pairs) >= 1:  # Проверяем есть ли в списке города
        # перебираем весь список если четное количество, то пишем по 2 в ряд.
        for element in pairs:
            if element['pair'].split('/')[1] == type_pair:
                pair = InlineKeyboardButton(
                    element['ru_pair'], callback_data='Пара '+element['pair'])
                buttons.append([pair])
    buttons.append([btn_back])
    markup = InlineKeyboardMarkup(buttons)
    id = context.bot.send_message(
        message.chat.id, "Черновик заказа на обмен\n\nВыбран город <code>{}</code>\n\n<b>ВЫБЕРИ ПАРУ ДЛЯ ОБМЕНА:</b>\n\n".format(u.city), reply_markup=markup, parse_mode="HTML")
    User.set_message_id(update, context, id.message_id)

# Вписываем другую валюту:


def user_type_pair_custome(update: Update, context: CallbackContext):
    u, _ = User.get_user_and_created(update, context)
    message = get_message_bot(update)
    pair = message.text+'/'+u.pair.split('/')[1]
    if pair == 'None':
        cmd_type_pair(update, context, u.city)
        return
    del_mes(update, context, True)
    # записываем город в словарь пользователя, потом заберем и очистим поле.
    User.set_type_pair(update, context, pair)
    # помечаем состояние пользователя.
    User.set_user_state(update, context, static_state.S_MENU)
    cmd_pair(update, context, pair)


# Выбрана пара и выводим вопрос сколько денег хочет обменять на Рупии в выбранной паре.
# Сюда попадаем через колбек с передачей параметра пара


def cmd_pair(update: Update, context: CallbackContext, pair: Str = 'None'):
    message = get_message_bot(update)
    if pair == 'None':
        return user_type_pair(update, context, u.type_pair)
    del_mes(update, context, True)
    # записываем пару в словарь пользователя, потом заберем и очистим поле.
    User.set_pair(update, context, pair)
    # помечаем состояние пользователя.
    User.set_user_state(update, context, static_state.S_ENTERED_PAIR)
    u, _ = User.get_user_and_created(update, context)
    city = u.city
    buttons = []
    btn_back = InlineKeyboardButton(
        text='⏪ Назад', callback_data='Меню_Клиент')
    buttons.append([btn_back])
    markup = InlineKeyboardMarkup(buttons)
    if pair == 'ANY/LKR' or pair == 'ANY/USD':
        if u.pair in Pairs.get_dict():
            pair = Pairs.get_dict()[u.pair]
        User.set_user_state(update, context, static_state.S_TYPE_PAIR_CUSTOME)
        id = context.bot.send_message(message.chat.id, "Черновик заказа на обмен\n\nВыбран город <code>{}</code>\nВыбрана пара\n<code>{}</code>\n\n<b>ВВЕДИТЕ НАЗВАНИЕ ВАЛЮТЫ:</b>\n\nОбращаем ваше внимание, на данное направление обмена может быть не найден обменник".format(
            city, pair), reply_markup=markup, parse_mode="HTML")
        User.set_message_id(update, context, id.message_id)
    else:
        if u.pair in Pairs.get_dict():
            pair = Pairs.get_dict()[u.pair]
        id = context.bot.send_message(message.chat.id, "Черновик заказа на обмен\n\nВыбран город <code>{}</code>\nВыбрана пара\n<code>{}</code>\n\n<b>ВВЕДИТЕ СУММУ ЦИФРОЙ ДЛЯ ОБМЕНА:</b>\n\n".format(
            city, pair), reply_markup=markup, parse_mode="HTML")
        User.set_message_id(update, context, id.message_id)

# Уточняем период сделки после ввода суммы
# в хендлер попадаем сравнивая состояние пользователя


def cmd_periods(update: Update, context: CallbackContext, summ: float = 0.0):
    u, _ = User.get_user_and_created(update, context)
    message = get_message_bot(update)
    if summ == 0.0:
        summ = message.text
    if isfloat(summ):
        del_mes(update, context, True)
        User.set_user_state(update, context, static_state.S_MENU)
        User.set_summ(update, context, float(summ))
        summ_m = int(float(summ))
        city = u.city
        if u.pair in Pairs.get_dict():
            pair = Pairs.get_dict()[u.pair]
        else:
            pair = u.pair.split('/')[0]+' =>  '+u.pair.split('/')[1]
        buttons = []
        btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Клиент')
        periods = Periods.get_obj()
        for element in periods:
            period = InlineKeyboardButton(
                '⏳ '+element['ru_period'], callback_data='Период '+element['period'])
            buttons.append([period])
        buttons.append([btn_back])
        markup = InlineKeyboardMarkup(buttons)
        id = context.bot.send_message(message.chat.id, "Черновик заказа на обмен\n\nВыбран город <code>{}</code>\nВыбрана пара\n<code>{}</code>\nСумма <code>{}</code> {}\n\n<b>КАК БЫСТРО ВАМ НУЖЕН КЭШ?</b> ⏳".format(
            city, pair, summ_m, pair.split(' =>  ')[0]), reply_markup=markup, parse_mode="HTML")
        User.set_message_id(update, context, id.message_id)
    else:
        pair = u.pair
        cmd_pair(update, context, pair)

# Выбран период и выводим вопрос подтверждения заказа на обмен.


def cmd_transfer(update: Update, context: CallbackContext, period: str = 'None'):
    u, _ = User.get_user_and_created(update, context)
    message = get_message_bot(update)
    if period == 'None':
        return cmd_periods(update, context, u.summ)
    del_mes(update, context, True)
    # записываем период в словарь пользователя, потом заберем и очистим поле.
    User.set_period(update, context, period)
    User.set_user_state(update, context, static_state.S_MENU)
    period = Periods.get_dict()[period]
    city = u.city
    if u.pair in Pairs.get_dict():
        pair = Pairs.get_dict()[u.pair]
    else:
        pair = u.pair.split('/')[0]+' =>  '+u.pair.split('/')[1]
    summ_m = int(u.summ)
    buttons = []
    btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Клиент')
    btn_pickup = InlineKeyboardButton(
        text='Я подъеду к обменнику в г. '+str(city), callback_data='Доставка pickup')
    btn_delivery = InlineKeyboardButton(
        text='Мне нужна доставка по моему адресу', callback_data='Доставка delivery')
    btn_both = InlineKeyboardButton(
        text='Рассмотрю оба варианта', callback_data='Доставка both')
    buttons.append([btn_pickup])
    buttons.append([btn_delivery])
    buttons.append([btn_both])
    buttons.append([btn_back])
    markup = InlineKeyboardMarkup(buttons)
    id = context.bot.send_message(message.chat.id, "Черновик заказа на обмен\n\nВыбран город <code>{}</code>\nВыбрана пара\n<code>{}</code>\nСумма <code>{}</code> {}\nКэш нужен <code>{}</code>\n\n<b>ОСТАВЬТЕ ПОЖЕЛАНИЕ О ДОСТАВКЕ</b>".format(
        city, pair, summ_m, pair.split(' =>  ')[0], period), reply_markup=markup, parse_mode="HTML")
    User.set_message_id(update, context, id.message_id)

# Сюда попадаем через колбек


def cmd_accept_order(update: Update, context: CallbackContext, transfer: str = 'None'):
    u, _ = User.get_user_and_created(update, context)
    message = get_message_bot(update)
    if transfer == 'None':
        return cmd_transfer(update, context, u.period)
    if transfer == 'pickup':
        u.transfer = 'Подъеду к обменнику'
    if transfer == 'delivery':
        u.transfer = 'Нужна доставка по адресу'
    if transfer == 'both':
        u.transfer = 'Рассмотрю оба варианта'
    del_mes(update, context, True)
    # записываем период в словарь пользователя, потом заберем и очистим поле.
    User.set_user_state(update, context, static_state.S_MENU)
    period = Periods.get_dict()[u.period]
    city = u.city
    if u.pair in Pairs.get_dict():
        pair = Pairs.get_dict()[u.pair]
    else:
        pair = u.pair.split('/')[0]+' =>  '+u.pair.split('/')[1]
    summ_m = int(u.summ)
    buttons = []
    btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Клиент')
    btn_yes = InlineKeyboardButton(
        text='✅ Все верно', callback_data='Заявка_подтверждена')
    btn_no = InlineKeyboardButton(
        text='❌ Нет', callback_data='Заявка_отклонена')
    buttons.append([btn_yes, btn_no])
    buttons.append([btn_back])
    markup = InlineKeyboardMarkup(buttons)
    id = context.bot.send_message(message.chat.id, "Черновик заказа на обмен\n\nВыбран город <code>{}</code>\nВыбрана пара\n<code>{}</code>\nСумма <code>{}</code> {}\nКэш нужен <code>{}</code>\nВариант доставки <code>{}</code>\n\n<b>ПОДТВЕРДИТЕ ЗАЯВКУ НА ОБМЕН, ВСЕ ВЕРНО?</b>".format(
        city, pair, summ_m, pair.split(' =>  ')[0], period, u.transfer), reply_markup=markup, parse_mode="HTML")
    u.message_id = id.message_id
    u.save()


def cmd_accepted_order_show(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    message = get_message_bot(update)
    del_mes(update, context, True)
    city = u.city
    if u.pair in Pairs.get_dict():
        pair = Pairs.get_dict()[u.pair]
    else:
        pair = u.pair
    summ = int(u.summ)
    period = Periods.get_dict()[u.period]
    id = context.bot.send_message(message.chat.id, "<b>ВАШ ЗАКАЗ\n\nВыбран город <code>{}</code>\nВыбрана пара\n<code>{}</code>\nСумма {} <code>{}</code>\nКэш нужен <code>{}</code></b>\nВариант доставки <code>{}</code>\n\n<b>Пожалуйста ожидайте один час, за это время обменники сделают свои предложения по вашему заказу.</b>".format(
        city, pair, pair.split('/')[0], summ, period, u.transfer), parse_mode="HTML")
    User.set_message_id(update, context, id.message_id)

# клиент подтвердил заказ на обмен


def cmd_accepted_order(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    message = get_message_bot(update)
    del_mes(update, context, True)
    city = u.city
    if u.pair in Pairs.get_dict():
        pair = Pairs.get_dict()[u.pair]
    else:
        pair = u.pair.split('/')[0]+' =>  '+u.pair.split('/')[1]
    summ = int(u.summ)
    period = Periods.get_dict()[u.period]
    timestamp = int(datetime.datetime.today().timestamp())
    dt = datetime.datetime.fromtimestamp(timestamp + (60*60*5.5))
    minutes_admining = 3
    if int(dt.hour) >= 9 and int(dt.hour) <= 19:
        timestamp_execut = timestamp + (60*minutes_admining)
        text = 'В течении 30 минут мы соберем все предложения от всех обменников, работающих в вашем городе и предоставим вам информацию о их тарифах и предложениях, ожидайте.'
    if int(dt.hour) < 9:
        mod_h = 9 - int(dt.hour)
        timestamp_execut = timestamp + (60*60*mod_h) + (60*minutes_admining)
        text = 'ДОБРЫЙ ВЕЧЕР, МЫ РАБОТАЕМ С 9:00 УТРА ДО 20:00 ВЕЧЕРА.\n\nВАШ ЗАКАЗ БУДЕТ ОБРАБОТАН В 9:00 УТРА И УЖЕ В 9:30 ВЫ ПОЛУЧИТЕ ПРЕДЛОЖЕНИЯ ОТ ОБМЕННИКОВ, ПОЖАЛУЙСТА ОЖИДАЙТЕ...'
    if int(dt.hour) > 19:
        mod_h = 24 - int(dt.hour) + 9
        timestamp_execut = timestamp + (60*60*mod_h) + (60*minutes_admining)
        text = 'ДОБРЫЙ ВЕЧЕР, МЫ РАБОТАЕМ С 9:00 УТРА ДО 20:00 ВЕЧЕРА.\n\nВАШ ЗАКАЗ БУДЕТ ОБРАБОТАН В 9:00 УТРА И УЖЕ В 9:30 ВЫ ПОЛУЧИТЕ ПРЕДЛОЖЕНИЯ ОТ ОБМЕННИКОВ, ПОЖАЛУЙСТА ОЖИДАЙТЕ...'
    date_time_execut = datetime.datetime.fromtimestamp(
        timestamp_execut + (60*60*5.5))
    p2p_last = P2p.objects.latest('timestamp').__dict__
    p2p_last['usdt'] = 1
    pair_dict = Pairs.get_convert_dict()
    if u.pair in pair_dict:
        exchange_rate = p2p_last[pair_dict[u.pair]]
        eq_usdt = round((float(summ) / float(exchange_rate)), 2)
    else:
        exchange_rate = p2p_last['usdt']
        eq_usdt = 0
    order_fee = round((float(summ) / float(exchange_rate))
                      * float(Terms.get_dict()['size_fee']), 2)
    o, created = Order.objects.update_or_create(timestamp_execut=timestamp_execut, client_id=u, defaults={
        'city': u.city,
        'pair': u.pair,
        'summ': u.summ,
        'period': u.period,
        'transfer': u.transfer,
        'date_time_execut': date_time_execut,
        'order_fee': order_fee,
        'status': 'admining'
    })
    if created:
        # admining orders if summ more then 'filter_order_size_adminig'
        # считаем в USDT cумму.

        if eq_usdt >= float(Terms.get_dict()['filter_order_size_adminig']):
            s = Cities.objects.get(ru_name=u.city)
            user_ids = list(s.city_merchant_ids_set.all().values_list(
                'merchant_id', flat=True))  # Список мерчантов представленных в городе
            ids_admins = list(User.objects.filter(user_id__in=user_ids, merchant_status='online', is_admin=True).values_list(
                'user_id', flat=True))  # Проверяем статус мерчантов = 'online'

            percent = 0
            if u.count_client_order > 0:
                percent = round(u.count_client_order_success /
                                u.count_client_order * 100, 2)
            username = str(u)
            un_ = username.split('@')[1]
            username_secure = '@' + un_[0] + \
                un_[1] + '******' + un_[-2] + un_[-1]

            if len(ids_admins) > 0:
                bts = [
                    [{'text': '‼️💵 Сделать предложение и забрать заявку себе',
                        'callback_data': 'Збарать_заявку ' + str(o.id)}],
                    [{'text': '🪁 Пропустить', 'callback_data': 'Удалить'}]
                ]
                # send in async mode via celery
                broadcast_message.delay(
                    user_ids=ids_admins,
                    text="<b>НОВЫЙ ОРДЕР\n{}\nУспешно выполнено \\ всего заявок: <code>{} \\ {}   {}%</code>\nВыбран город <code>{}</code>\nВыбрана пара\n<code>{}</code>\nСумма {} <code>{}</code>\nКэш нужен <code>{}</code>\nВариант доставки <code>{}</code>\n\n Комиссия за сделку <code>{}</code> USDT</b>".format(
                        username_secure, u.count_client_order_success, u.count_client_order, percent, city, pair, pair.split('/')[0], summ, period, u.transfer, order_fee),
                    entities=update.callback_query.message.to_dict().get('entities'),
                    reply_markup=bts
                )
        User.set_user_state(update, context, static_state.S_ACCEPTED_ORDER)
        id = context.bot.send_message(message.chat.id, "<b>АКТИВНЫЙ ОРДЕР\n\nВыбран город: <code>{}</code>\nВыбрана пара:\n<code>{}</code>\nСумма: <code>{}</code> {} \nКэш нужен: <code>{}</code>\nВариант доставки: <code>{}</code>\n\n{}</b>".format(
            city, pair, summ, pair.split(' =>  ')[0], period, u.transfer, text), parse_mode="HTML")
        User.set_message_id(update, context, id.message_id)
        return
    cmd_transfer(update, context, u.period)


def user_canceled_order(update: Update, context: CallbackContext, orderid: str):
    o = Order.objects.get(id=orderid)
    o.status = 'canceled'
    o.save()
    cmd_canceled_order(update, context)

# клиент отменил заказ на обмен


def cmd_canceled_order(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    u.city = 'None'
    u.type_pair = 'None'
    u.pair = 'None'
    u.summ = 0.0
    u.period = 'None'
    u.transfer = 'None'
    u.save()
    start_client(update, context)
    # u = User.get_user(update, context)
    # u.city = 'None'
    # u.type_pair = 'None'
    # u.pair = 'None'
    # u.summ = 0.0
    # u.period = 'None'
    # u.transfer = 'None'
    # u.save()

# заказы клиента


def client_orders(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    message = get_message_bot(update)
    del_mes(update, context, True)
    User.set_user_state(update, context, static_state.S_MENU)
    for i in u.client_id_order_set.filter(status__in=['exchanged_succesfull', 'exchange']).order_by('timestamp_execut').reverse()[:5]:
        try:
            s = Suggestion.objects.get(
                order_id=i.id, merchant_executor_id=i.merchant_executor_id.user_id)
            summ_suggestion = s.summ
        except:
            summ_suggestion = 'информация не сохранена'
        m = i.merchant_executor_id
        if i.pair in Pairs.get_dict():
            pair = Pairs.get_dict()[i.pair]
        else:
            pair = i.pair.split('/')[0]+' =>  '+i.pair.split('/')[1]
        period = Periods.get_dict()[i.period]
        time.sleep(0.2)
        ts = int(i.timestamp_execut) + (60*60*5.5)
        dt = datetime.datetime.fromtimestamp(
            ts).strftime('%Y-%m-%d %H:%M')
        context.bot.send_message(message.chat.id, "<b>{}</b>\n\nВыбран город <code>{}</code>\nВыбрана пара\n<code>{}</code>\n\Сумма {} <code>{}</code>\nКэш нужен <code>{}</code>\nВариант доставки <code>{}</code>\n\nОбменник {} предложил:\nСумма <code>{}</code> {}\n{}".format(
            dt, i.city, pair, pair.split(' =>  ')[0], int(i.summ), period, i.transfer, i.merchant_executor_id, summ_suggestion, pair.split(' =>  ')[1], m.merchant_delivery), parse_mode="HTML")
    buttons = []
    btn_back = InlineKeyboardButton(
        text='⏪ Назад', callback_data='Меню_Клиент')
    buttons.append([btn_back])
    markup = InlineKeyboardMarkup(buttons)
    id = context.bot.send_message(
        message.chat.id, "Отображаем последние 5 выполненных заказов", reply_markup=markup, parse_mode="HTML")
    User.set_message_id(update, context, id.message_id)

# подтвердить и выбрать исполнителя


def cmd_accepted_merchant_executer(update: Update, context: CallbackContext, orderid_merchantid: str):
    orderid_merchantid = orderid_merchantid.split('_')
    orderid = orderid_merchantid[0]
    merchantid = orderid_merchantid[1]
    m = User.objects.get(user_id=merchantid)
    message = get_message_bot(update)
    u = User.get_user(update, context)
    try:
        context.bot.delete_message(
            chat_id=message.chat.id, message_id=u.message_id)
    except:
        pass
    del_mes(update, context, True)
    User.set_user_state(update, context, static_state.S_ACCEPTED_EXCHANGE)
    o = Order.objects.get(id=orderid)
    o.merchant_executor_id = m
    o.status = 'exchange'
    o.save()
    m = User.objects.get(user_id=merchantid)
    if o.pair in Pairs.get_dict():
        pair = Pairs.get_dict()[o.pair]
    else:
        pair = o.pair.split('/')[0]+' =>  '+o.pair.split('/')[1]
    period = Periods.get_dict()[o.period]
    s = Suggestion.objects.get(
        order_id=orderid, merchant_executor_id=merchantid)
    text = "<b>Выбран город <code>{}</code>\nВыбрана пара\n<code>{}</code>\nСумма {} <code>{}</code>\nКэш нужен <code>{}</code>\nВариант доставки <code>{}</code></b>".format(
        o.city, pair, pair.split(' =>  ')[0], int(o.summ), period, o.transfer)
    text_fee = "\n\nКомиссия за сделку <i><b>{} USDT</b></i>".format(
        o.order_fee)
    pay_summ = "{} {}".format(int(s.summ), pair.split(' =>  ')[1])
    id = context.bot.send_message(message.chat.id, "<b>ИНФОРМАЦИЯ ПО ВАШЕЙ СДЕЛКЕ</b>\n\n"+text+"\n\n<b>ВАМ ЗАПЛАТЯТ: "+pay_summ+"\n<code>{}</code>\n\nСВЯЖИТЕСЬ С ОБМЕННИКОМ {}, ДОГОВОРИТЕСЬ О ДЕТАЛЯХ ВАШЕЙ ВСТРЕЧИ</b>".format(m.merchant_delivery, m), reply_markup=InlineKeyboardMarkup(
        [[InlineKeyboardButton(text='✅ Сделка состоялась', callback_data='Клиент_подтвердил_сделку '+orderid)], [InlineKeyboardButton(text='❌ Сделка не состоялась', callback_data='Клиент_отменил_сделку '+orderid)]]), parse_mode="HTML")
    User.set_message_id(update, context, id.message_id)
    time.sleep(0.2)
    client_name = "Клиент {}\n".format(u)
    id_m = context.bot.send_message(merchantid, "КЛИЕНТ ВЫБРАЛ ВАШЕ ПРЕДЛОДЕНИЕ\n\n"+client_name+text+text_fee+"\nВЫ ЗАПЛАТИТЕ КЛИЕНТУ " +
                                    pay_summ, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(text='⏪ Назад', callback_data='Обменник')]]), parse_mode="HTML")
    m.message_id = id_m.message_id
    m.save()


def cmd_accepted_exchange_show(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    message = get_message_bot(update)
    del_mes(update, context, True)
    o = u.client_id_order_set.get(status='exchange')
    m = o.merchant_executor_id
    if o.pair in Pairs.get_dict():
        pair = Pairs.get_dict()[o.pair]
    else:
        pair = o.pair.split('/')[0]+' =>  '+o.pair.split('/')[1]
    period = Periods.get_dict()[o.period]
    text = "<b>Выбран город <code>{}</code>\nВыбрана пара\n<code>{}</code>\nСумма {} <code>{}</code>\nКэш нужен <code>{}</code>\nВариант доставки <code>{}</code></b>".format(
        o.city, pair, pair.split(' =>  ')[0], int(o.summ), period, o.transfer)
    s = Suggestion.objects.get(order_id=o.id, merchant_executor_id=m.user_id)
    pay_summ = "{} {}".format(int(s.summ), pair.split(' =>  ')[1])
    id = context.bot.send_message(message.chat.id, "<b>АКТИВНЫЙ ОРДЕР</b>\n\n"+text+"\nВАМ ЗАПЛАТЯТ "+pay_summ+"\n\n<b>СВЯЖИТЕСЬ С ОБМЕННИКОМ {}, ДОГОВОРИТЕСЬ О ДЕТАЛЯХ ВАШЕЙ ВСТРЕЧИ</b>".format(m), reply_markup=InlineKeyboardMarkup(
        [[InlineKeyboardButton(text='✅ Сделка состоялась', callback_data='Клиент_подтвердил_сделку '+str(o.id))], [InlineKeyboardButton(text='❌ Сделка не состоялась', callback_data='Клиент_отменил_сделку '+str(o.id))]]), parse_mode="HTML")
    User.set_message_id(update, context, id.message_id)


def cmd_finnaly_accepted_order(update: Update, context: CallbackContext, orderid: str):
    del_mes(update, context, True)
    message = get_message_bot(update)
    u = User.get_user(update, context)
    o = Order.objects.get(id=orderid)
    o.status = 'exchanged_succesfull'
    o.save()
    m = o.merchant_executor_id
    cmo = m.count_merchant_order
    m.count_merchant_order = cmo + 1
    cmos = m.count_merchant_order_success
    m.count_merchant_order_success = cmos + 1
    m.save()
    cuo = u.count_client_order
    u.count_client_order = cuo + 1
    cuos = u.count_client_order_success
    u.count_client_order_success = cuos + 1
    id = context.bot.send_message(message.chat.id, "Поздравляем с завершенным обменом!!! Оцените пожалуйста от 1 до 5, где 5 самая высокая оценка:", reply_markup=InlineKeyboardMarkup(
        [[InlineKeyboardButton(text='5', callback_data='Ответ_на_выполненный_ордер '+orderid+'__5'), InlineKeyboardButton(text='4', callback_data='Ответ_на_выполненный_ордер '+orderid+'__4')],
         [InlineKeyboardButton(
             text='3', callback_data='Ответ_на_выполненный_ордер '+orderid+'__3')],
         [InlineKeyboardButton(
             text='2', callback_data='Ответ_на_выполненный_ордер '+orderid+'__2')],
         [InlineKeyboardButton(text='1', callback_data='Ответ_на_выполненный_ордер '+orderid+'__1')]]), parse_mode="HTML")
    u.message_id = id.message_id
    u.state = static_state.S_FINNALY_ACCEPTED_ORDER
    u.save()


def answer_accepted_order(update: Update, context: CallbackContext, orderid: str = 'None'):
    del_mes(update, context, True)
    message = get_message_bot(update)
    u = User.get_user(update, context)
    if orderid != 'None':
        ord = orderid.split('__')[0]
        rank = orderid.split('__')[1]
        text = ''
    else:
        text = ''
        rank = 5
        ord = u.message_id
    o = Order.objects.get(id=ord)
    m = o.merchant_executor_id
    r, created = Rating.objects.update_or_create(who_id=u, whom_id=m, defaults={
        'rank': int(rank),
        'comment': text
    })
    id = context.bot.send_message(message.chat.id, "Спасибо, за Ваш отзыв, порекомендуйте пожалуйста наш бот в ваших группах и пабликах, просто репостните следующий пост вашим друзьям.", reply_markup=InlineKeyboardMarkup(
        [[InlineKeyboardButton(text='⏪ Назад', callback_data='Меню_Клиент')]]), parse_mode="HTML")
    u.message_id = id.message_id
    u.state = static_state.S_MENU
    u.save()
    if int(rank) >= 3:
        context.bot.send_message(
            message.chat.id, "@cash_lanka_bot - самые выгодные цены от лучших обменников на ШриЛанке!\nПолучите предложения сразу от нескольких обменников в одном месте.", parse_mode="HTML")


def cmd_finnaly_rejected_order(update: Update, context: CallbackContext, orderid: str):
    del_mes(update, context, True)
    message = get_message_bot(update)
    u = User.get_user(update, context)
    o = Order.objects.get(id=orderid)
    o.status = 'exchanged_rejected'
    o.save()
    id = context.bot.send_message(message.chat.id, "Сделка не состоялась. Опишите ситуацию, что случилось?", reply_markup=InlineKeyboardMarkup(
        [[InlineKeyboardButton(text='Не удалось связаться с обменником', callback_data='Ответ_на_отмененный_ордер ' +
                               orderid+'__'+'Не удалось связаться с обменником')],
         [InlineKeyboardButton(text='Обменник изменил курс', callback_data='Ответ_на_отмененный_ордер ' +
                               orderid+'__'+'Обменник_изменил_курс')],
         [InlineKeyboardButton(text='Ждать дольше, чем заявленно', callback_data='Ответ_на_отмененный_ордер ' +
                               orderid+'__'+'Ждать_дольше,_чем_заявленно')],
         [InlineKeyboardButton(text='Я передумал(а)', callback_data='Ответ_на_отмененный_ордер ' +
                               orderid+'__'+'Я_передумал(а)')],
         [InlineKeyboardButton(text='Нашел(ла) курс лучше', callback_data='Ответ_на_отмененный_ордер ' +
                               orderid+'__'+'Нашел(ла)_курс_лучше')],
         [InlineKeyboardButton(text='Обменник попросил отменить сделку', callback_data='Ответ_на_отмененный_ордер ' +
                               orderid+'__'+'Обменник_попросил_отменить_сделку')]
         ]), parse_mode="HTML")
    u.message_id = orderid  # пишем ордер, чтоб потом принять причину
    u.state = static_state.S_FINNALY_REJECTED_ORDER
    u.save()


def answer_rejected_order(update: Update, context: CallbackContext, orderid: str = 'None'):
    del_mes(update, context, True)
    message = get_message_bot(update)
    u = User.get_user(update, context)
    if orderid != 'None':
        ord = orderid.split('__')[0]
        text = orderid.split('__')[1].replace('_', ' ')
    else:
        text = ''
        ord = u.message_id
    o = Order.objects.get(id=ord)
    m = o.merchant_executor_id
    if text == '' and text != 'Я передумал(а)' and text != 'Нашел(ла) курс лучше':
        cmo = m.count_merchant_order
        m.count_merchant_order = cmo + 1
        m.save()
    if text == '' or text == 'Я передумал(а)' or text == 'Нашел(ла) курс лучше':
        cuo = u.count_client_order
        u.count_client_order = cuo + 1
    if message.text != None and message.text != '':
        text = message.text
    r, created = Rating.objects.update_or_create(who_id=u, whom_id=m, defaults={
        'rank': 0,
        'comment': text
    })
    id = context.bot.send_message(message.chat.id, "Спасибо, за отзыв!", reply_markup=InlineKeyboardMarkup(
        [[InlineKeyboardButton(text='⏪ Назад', callback_data='Меню_Клиент')]]), parse_mode="HTML")
    u.message_id = id.message_id
    u.state = static_state.S_MENU
    u.save()


#####################################
#####################################
#####################################


# История обменника ## merchant_story
def cmd_merchant(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    message = get_message_bot(update)
    if u.merchant_client != 'None' and u.merchant_client != 'under_consideration':
        cmd_menu_merchant(update, context)
        return
    if u.merchant_client == 'under_consideration':
        merchant_terms_of_use_agreed(update, context)
        return
    User.set_user_state(update, context, static_state.S_MENU)
    buttons = []
    btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Меню')
    btn_yes = InlineKeyboardButton(
        text='✅ Согласен', callback_data='Правила_согласованны')
    btn_no = InlineKeyboardButton(text='❌ Нет', callback_data='Меню')
    buttons.append([btn_yes, btn_no])
    buttons.append([btn_back])
    markup = InlineKeyboardMarkup(buttons)
    id = context.bot.send_message(message.chat.id, "Мы рады приветствовать Вас в нашей программе по предоставлению заявок на обнал на острове Шри-Ланка. Пожалуйста, ознакомьтесь с условиями.\n\n{}\n\n<b>ВЫ СОГЛАСНЫ С УСЛОВИЯМИ?</b>".format(
        Terms.get_dict()['terms_of_use_merchant']), reply_markup=markup, parse_mode="HTML")
    User.set_message_id(update, context, id.message_id)
    del_mes(update, context, True)


# подписываем пользовательское соглашение обменника
def merchant_terms_of_use_agreed(update: Update, context: CallbackContext):
    # Поменять 'True' на 'under_consideration' если хотим сделать верификацию обменников.
    User.set_merchant_client(update, context, 'True')
    message = get_message_bot(update)
    u = User.get_user(update, context)
    if u.merchant_client == 'under_consideration':
        text = 'Вы собираетесь стать обменником.\n\n!!! СВЯЖИТЕСЬ  С  @sri_seacher  ДЛЯ ПРОХОЖДЕНИЯ ПРОВЕРКИ ЛИЧНОСТИ !!!'
        buttons = []
        btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Меню')
        buttons.append([btn_back])
        markup = InlineKeyboardMarkup(buttons)
        id = context.bot.send_message(
            message.chat.id, text, reply_markup=markup, parse_mode="HTML")
        User.set_message_id(update, context, id.message_id)
        del_mes(update, context, True)
        return
    cmd_menu_merchant(update, context)


# получаем курсы из базы.
def merchant_course(update: Update, context: CallbackContext):
    del_mes(update, context, True)
    message = get_message_bot(update)
    User.set_user_state(update, context, static_state.S_MENU)
    p2p_last = P2p.objects.latest('timestamp').__dict__
    text = '<b><i>Курсы валют обновляются раз в час с </i>P2P Binance<i>\nи служат для ориентира пользователей:</i></b>\n\n<code>{}</code> RUB/USDT  (Российский рубль)\nRUB/ <code>{}</code> LKR  (Шри-ланкийская рупия)\nUSDT/ <code>{}</code> LKR  (Шри-ланкийская рупия)\n<code>{}</code> UAH/USDT  (Украинская Гривна)\nUAH/ <code>{}</code> LKR  (Шри-ланкийская рупия)\n<code>{}</code> EUR/USDT    (Евро)\nEUR/ <code>{}</code> LKR  (Шри-ланкийская рупия)\n<code>{}</code> USD/USDT    (Доллар)\nKZT/ <code>{}</code> LKR  (Шри-ланкийская рупия)\n<code>{}</code> KZT/USDT    (Тенге)\n\n'.format(
        p2p_last['rub_tinkoff_usdt'], round(float(p2p_last['usdt_lkr'])/float(p2p_last['rub_tinkoff_usdt']), 2), p2p_last['usdt_lkr'], p2p_last['uah_usdt'], round(float(p2p_last['usdt_lkr'])/float(p2p_last['uah_usdt']), 2), p2p_last['eur_revolut_usdt'], round(float(p2p_last['usdt_lkr'])/float(p2p_last['eur_revolut_usdt']), 2), p2p_last['usd_tinkoff_usdt'], round(float(p2p_last['usdt_lkr'])/float(p2p_last['kzt_usdt']), 2), p2p_last['kzt_usdt'])
    buttons = []
    btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Обменник')
    buttons.append([btn_back])
    markup = InlineKeyboardMarkup(buttons)
    id = context.bot.send_message(
        message.chat.id, text, reply_markup=markup, parse_mode="HTML")
    User.set_message_id(update, context, id.message_id)


# Меню обменника
def cmd_menu_merchant(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    message = get_message_bot(update)
    if u.merchant_client == 'None':
        cmd_merchant(update, context)
        return
    del_mes(update, context, True)
    User.set_user_state(update, context, static_state.S_MENU)
    buttons = []
    btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Меню')
    btn_course = InlineKeyboardButton(
        text='📉📈 Текущий курс валют', callback_data='Курс_валют')
    btn_actual_orders_merchant = InlineKeyboardButton(
        text='📥 Актуальные заявки', callback_data='Актуальные_заявки')
    btn_orders = InlineKeyboardButton(
        text='📨 Мои заказы - к выполнению', callback_data='Заказы_Мерчант')
    btn_orders_suggestion = InlineKeyboardButton(
        text='🧧🧾 Мои предложения - торгуемся', callback_data='Мои_предложения')
    btn_orders_completed = InlineKeyboardButton(
        text='✅🧾 Выполненные заказы', callback_data='Выполненные_заказы')
    merchant_status = u.merchant_status
    if merchant_status == 'None' or merchant_status == 'pause':
        merchant_status_ru = '🛋 Статус: Пауза'
        callback = 'Смена_статуса'
    if merchant_status == 'online':
        merchant_status_ru = '♻️ Статус: Онлайн'
        callback = 'Смена_статуса'
    if merchant_status == 'dolg':
        merchant_status_ru = '‼️ Статус: Долг'
        callback = 'Смена_статуса'
    btn_status = InlineKeyboardButton(
        text=merchant_status_ru, callback_data=callback)
    btn_settings = InlineKeyboardButton(
        text='⚙️ Управление', callback_data='Управление')
    buttons.append([btn_settings, btn_status])
    buttons.append([btn_course])
    buttons.append([btn_actual_orders_merchant])
    buttons.append([btn_orders])
    buttons.append([btn_orders_suggestion])
    buttons.append([btn_orders_completed])
    buttons.append([btn_back])
    markup = InlineKeyboardMarkup(buttons)
    id = context.bot.send_message(message.chat.id, "МЕНЮ ОБМЕННИКА:\n\n <b>♻️ Статус: Онлайн</b> - вы получаете новые заявки на обмен и можете делать свои предложения.\nКлиенты видят вас в списке городов.\n\n<b>🛋 Статус: Пауза</b> - Вы не получаете новых предложений, для пользователей вы не видны в городах.\n Но вы все еще можете взять активную заявку согласно своих городов присутствия.\n\n<b>‼️ Статус: Долг</b> - Вам необходимо погасить задолженность, свяжитесь с @sri_seacher", reply_markup=markup, parse_mode="HTML")
    User.set_message_id(update, context, id.message_id)


# Меняем статус
def merchant_change_status(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    merchant_status = u.merchant_status
    if merchant_status == 'None' or merchant_status == 'pause':
        u.merchant_status = 'online'
    if merchant_status == 'online':
        u.merchant_status = 'pause'
    u.save()
    cmd_menu_merchant(update, context)


# Меню управления обменника.
def merchant_settings(update: Update, context: CallbackContext, text: str = 'None'):
    del_mes(update, context, True)
    message = get_message_bot(update)
    u = User.get_user(update, context)
    if u.state != static_state.S_DELIVERY_COST:
        User.set_user_state(update, context, static_state.S_MENU)
    buttons = []
    btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Обменник')
    btn_yes = InlineKeyboardButton(
        text='💵 Мои долги', callback_data='Мои_долги')
    btn_no = InlineKeyboardButton(
        text='🏘 Мои города', callback_data='Мои_города')
    btn_delivery = InlineKeyboardButton(
        text=u.merchant_delivery, callback_data='Доставка_кеш')
    buttons.append([btn_yes, btn_no])
    buttons.append([btn_delivery])
    buttons.append([btn_back])
    markup = InlineKeyboardMarkup(buttons)
    if text == 'None':
        text = 'Управление обменника\n\n Можно задать один из трех вариантов доставки:\n\n 🛻 Доставка: Самовывозом\n 🛻 Доставка: Доставляю деньги бесплатно\n 🛻 Доставка: Платно, за ХХХ валюты'

    id = context.bot.send_message(
        message.chat.id, text, reply_markup=markup, parse_mode="HTML")
    User.set_message_id(update, context, id.message_id)

# Мои доставка


def merchant_delivery(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    merchant_delivery_ru = u.merchant_delivery
    if merchant_delivery_ru == '🛻 Доставка: Самовывозом':
        u.merchant_delivery = '🛻 Доставка: Доставляю деньги бесплатно'
        u.save()
        merchant_settings(update, context)
    if merchant_delivery_ru == '🛻 Доставка: Доставляю деньги бесплатно' or merchant_delivery_ru == '🛻 Доставка: Доставляю деньги':
        u.merchant_delivery = '🛻 Доставка: Платно, за '
        u.state = static_state.S_DELIVERY_COST
        u.save()
        merchant_settings(
            update, context, '<b>Введите сумму в LKR за доставку денег</b>')
    if '🛻 Доставка: Платно, за' in merchant_delivery_ru:
        u.merchant_delivery = '🛻 Доставка: Самовывозом'
        u.save()
        merchant_settings(update, context)


def merchant_delivery_cost(update: Update, context: CallbackContext):
    u, _ = User.get_user_and_created(update, context)
    message = get_message_bot(update)
    try:
        summ_text = int(message.text)
        text = u.merchant_delivery
        u.merchant_delivery = str(text) + str(summ_text) + ' LKR'
        u.state = static_state.S_MENU
        u.save()
        merchant_settings(update, context)
    except:
        merchant_settings(update, context)

# помечаем город на который нажал пользователь


def change_merchat_city(update: Update, context: CallbackContext, city_merchant: str):
    u = User.get_user(update, context)
    c = Cities.objects.get(ru_name=city_merchant)
    try:
        check_city = MerchantsCities.objects.get(merchant_id=u, city_id=c)
        check_city.delete()
    except:
        MerchantsCities.objects.create(merchant_id=u, city_id=c)
    merchant_cities(update, context)

# Мои города


def merchant_cities(update: Update, context: CallbackContext):
    del_mes(update, context, True)
    u = User.get_user(update, context)
    message = get_message_bot(update)
    User.set_user_state(update, context, static_state.S_MENU)
    merchant_city = [k['city_id'] for k in list(u.merchant_id_cities_set.all().values(
        'city_id'))]  # получаем id всех записей городов присутствия обменника
    merchant_cities = Cities.objects.filter(
        id__in=merchant_city)  # Фильтруем список городов
    cities = Cities.objects.all().order_by('ru_name')
    # Список отмеченных городов присутсвия
    cities_checked = {obj.ru_name: 'checked' for obj in merchant_cities}
    # Все возможные города
    cities_unchecked = {obj.ru_name: 'unchecked' for obj in cities}
    buttons = []
    # обновляем словарь городами присутсвия и получаем готовый словарь отмеченных и не отмеченных городов
    cities_unchecked.update(cities_checked)
    if len(cities_unchecked) >= 1:  # Проверяем есть ли в списке города
        count = 0
        for k in cities_unchecked:  # перебираем весь список
            if cities_unchecked[k] == 'checked':
                box = ' ✅'
            if cities_unchecked[k] == 'unchecked':
                box = ' ⏹'
            count += 1
            # если последний элемент не четный, то помещаем в одну строку
            if len(cities_unchecked) == count and len(cities_unchecked) % 2 != 0:
                city = InlineKeyboardButton(
                    k + box, callback_data='Город_обменника '+k)
                buttons.append([city])
                break
            if count % 2 != 0:  # если четное количество, то пишем по 2 в ряд
                city_a = InlineKeyboardButton(
                    k + box, callback_data='Город_обменника '+k)
            else:
                city_b = InlineKeyboardButton(
                    k + box, callback_data='Город_обменника '+k)
                buttons.append([city_a, city_b])
    btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Обменник')
    buttons.append([btn_back])
    markup = InlineKeyboardMarkup(buttons)
    id = context.bot.send_message(
        message.chat.id, "Отметь города в которых будешь производить объмен:", reply_markup=markup, parse_mode="HTML")
    User.set_message_id(update, context, id.message_id)


# помечаем город на который нажал пользователь
def change_merchat_city(update: Update, context: CallbackContext, city_merchant: str):
    u = User.get_user(update, context)
    c = Cities.objects.get(ru_name=city_merchant)
    try:
        check_city = MerchantsCities.objects.get(merchant_id=u, city_id=c)
        check_city.delete()
    except:
        MerchantsCities.objects.create(merchant_id=u, city_id=c)
    merchant_cities(update, context)


# Актуальные заявки
def actual_orders(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    message = get_message_bot(update)
    del_mes(update, context, True)
    User.set_user_state(update, context, static_state.S_MENU)
    cities_id = list(u.merchant_id_cities_set.all(
    ).values_list('city_id_id', flat=True))
    cities = list(Cities.objects.filter(
        id__in=cities_id).values_list('ru_name', flat=True))
    suggestions = list(
        u.merchant_executor_id_suggestion_set.all().values_list('order_id', flat=True))
    status__in = ['active', 'active_v2', 'mailing']
    if u.is_admin:
        status__in = ['admining', 'active_v2']
    orders = Order.objects.filter(city__in=cities, status__in=status__in, timestamp_execut__gte=time.time(
    )).exclude(id__in=suggestions).order_by('timestamp_execut')[:5]
    text = 'Активных заявок в ваших городах пока нет'
    if u.merchant_status in ['dolg']:
        text = 'У вас не погашен долг, обратитесь в тех. поддержку.\n\nТехническая поддержка: @sri_seacher'
    try:
        if len(orders) >= 1 and u.merchant_status not in ['dolg']:
            for i in orders:
                if i.pair in Pairs.get_dict():
                    pair = Pairs.get_dict()[i.pair]
                else:
                    pair = i.pair.split('/')[0]+' =>  '+i.pair.split('/')[1]
                period = Periods.get_dict()[i.period]
                ts = int(i.timestamp_execut) + (60*60*5.5)
                dt = datetime.datetime.fromtimestamp(
                    ts).strftime('%Y-%m-%d %H:%M:%S')
                buttons = [
                    [InlineKeyboardButton(
                        text='💵 Предложить сумму', callback_data='Предложить ' + str(i.id)),
                     InlineKeyboardButton(
                        text='💵 Предложить курс', callback_data='Предложить_курс ' + str(i.id))]
                ]
                if u.is_admin or (i.status == 'active_v2' and not u.is_admin):
                    btn_admin = InlineKeyboardButton(
                        text='‼️💵 Сделать предложение и забрать заявку себе', callback_data="Збарать_заявку " + str(i.id))
                    buttons.append([btn_admin])
                bts = InlineKeyboardMarkup(buttons)
                context.bot.send_message(message.chat.id, "<b>АКТУАЛЬНЫЙ ОРДЕР\n\nВыбран город <code>{}</code>\nВыбрана пара\n<code>{}</code>\nСумма {} <code>{}</code>\nКэш нужен <code>{}</code>\nВариант доставки <code>{}</code></b>\n\nАтуально до <b>{}</b>\nКомиссия за сделку <i><b>{} USDT</b></i>".format(
                    i.city, pair, pair.split(' =>  ')[0], int(i.summ), period, i.transfer, dt, i.order_fee), reply_markup=bts, parse_mode="HTML")
                time.sleep(0.2)
            text = '<b>СДЕЛАЙТЕ ПРЕДЛОЖЕНИЕ ПО ИНТЕРЕСНОЙ ВАМ ЗАЯВКЕ</b>'
    except:
        pass
    buttons = []
    btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Обменник')
    buttons.append([btn_back])
    markup = InlineKeyboardMarkup(buttons)
    id = context.bot.send_message(
        message.chat.id, text, reply_markup=markup, parse_mode="HTML")
    User.set_message_id(update, context, id.message_id)


# Мои долги
def merchant_debts(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    message = get_message_bot(update)
    del_mes(update, context, True)
    User.set_user_state(update, context, static_state.S_MENU)
    orders = u.merchant_executor_id_order_set.filter(
        status='exchanged_succesfull', status_fee='invoiced', order_fee__gt=0).order_by('timestamp_execut').reverse()
    text = 'Долгов нет'
    if len(orders) >= 1:
        summ_debt = 0
        tt = ''
        list_text = ''
        for i in orders:
            if i.pair in Pairs.get_dict():
                pair = Pairs.get_dict()[i.pair]
            else:
                pair = i.pair.split('/')[0]+' =>  '+i.pair.split('/')[1]
            period = Periods.get_dict()[i.period]
            summ_debt += i.order_fee
            sug_text = ''
            try:
                sug = Suggestion.objects.get(
                    order_id=i.id, merchant_executor_id=i.merchant_executor_id)
                if u == sug.merchant_executor_id:
                    sug_text += str(int(sug.summ))+' ' + \
                        str(pair.split(' =>  ')[1])
                    sug_text += '\n'
            except:
                pass
            list_text = "<b>ВЫПОЛНЕННЫЙ ОРДЕР\nКлиент {}\nВыбран город <code>{}</code>\nВыбрана пара\n<code>{}</code>\nСумма {} <code>{}</code>\nКэш нужен <code>{}</code>\nВариант доставки <code>{}</code></b>\nПредложение:\n{}\n\nКомиссия за сделку <i><b>{} USDT</b></i>\n\n".format(
                i.client_id, i.city, pair, pair.split(' =>  ')[0], int(i.summ), period, i.transfer, sug_text, i.order_fee)
            if len(tt+list_text) > 4096:
                context.bot.send_message(
                    message.chat.id, tt, parse_mode="HTML")
                tt = list_text
            else:
                tt += list_text
            time.sleep(0.2)
        context.bot.send_message(
            message.chat.id, tt, parse_mode="HTML")
        inv = Invoice.objects.get(payer_id_id=u)
        text = 'Ваш статус изменен ‼️ Статус: Долг.\nДля продолжения использования бота вам необходимо отправить сумму {} USDT на кошелек Tron TRC20\n<code>TXBXgpaM5jCXVq45m8UNTuJaA4oJkSUQbY</code>\nПосле оплаты ваш статус будет изменён на ♻️ Статус: Онлайн\n\n <b>ВНИМАНИЕ!!!!\n\n ЕСЛИ ОТПРАВЛЕННАЯ СУММА НЕ БУДЕТ СОВПАДАТЬ, ТО ПЛАТЕЖ НЕ ЗАЧТЕТСЯ АВТОМАТИЧЕСКИ И ВАМ НУЖНО БУДЕТ ПИСАТЬ В ПОДДЕРЖКУ.\n\nТехническая поддержка: @sri_seacher</b>'.format(
            inv.summ_invoice)
    buttons = []
    btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Обменник')
    buttons.append([btn_back])
    markup = InlineKeyboardMarkup(buttons)
    id = context.bot.send_message(
        message.chat.id, text, reply_markup=markup, parse_mode="HTML")
    User.set_message_id(update, context, id.message_id)


# Мои заказы
def merchant_orders(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    message = get_message_bot(update)
    del_mes(update, context, True)
    User.set_user_state(update, context, static_state.S_MENU)
    orders = u.merchant_executor_id_order_set.filter(
        status='exchange', timestamp_execut__lte=time.time()).order_by('timestamp_execut').reverse()[:5]
    text = 'Ордеров нет'
    try:
        if len(orders) >= 1:
            text = 'Вернуться'
            for i in orders:
                if i.pair in Pairs.get_dict():
                    pair = Pairs.get_dict()[i.pair]
                else:
                    pair = i.pair.split('/')[0]+' =>  '+i.pair.split('/')[1]
                period = Periods.get_dict()[i.period]
                time.sleep(0.2)
                context.bot.send_message(message.chat.id, "<b>ОРДЕР В РАБОТЕ\nКлиент {}\nВыбран город <code>{}</code>\nВыбрана пара\n<code>{}</code>\nСумма {} <code>{}</code>\nКэш нужен <code>{}</code>\nВариант доставки <code>{}</code></b>\n\n".format(
                    i.client_id, i.city, pair, pair.split(' =>  ')[0], int(i.summ), period, i.transfer), parse_mode="HTML")
    except:
        pass
    buttons = []
    btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Обменник')
    buttons.append([btn_back])
    markup = InlineKeyboardMarkup(buttons)
    id = context.bot.send_message(
        message.chat.id, text, reply_markup=markup, parse_mode="HTML")
    User.set_message_id(update, context, id.message_id)

# Мои выполненные заказы


def merchant_orders_completed(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    message = get_message_bot(update)
    del_mes(update, context, True)
    User.set_user_state(update, context, static_state.S_MENU)
    orders = u.merchant_executor_id_order_set.filter(
        status='exchanged_succesfull').order_by('timestamp_execut').reverse()[:5]
    text = 'Ордеров нет'
    if len(orders) >= 1:
        text = 'Вернуться'
        for i in orders:
            if i.pair in Pairs.get_dict():
                pair = Pairs.get_dict()[i.pair]
            else:
                pair = i.pair.split('/')[0]+' =>  '+i.pair.split('/')[1]
            period = Periods.get_dict()[i.period]
            time.sleep(0.2)
            context.bot.send_message(message.chat.id, "<b>ВЫПОЛНЕННЫЙ ОРДЕР\nКлиент {}\nВыбран город <code>{}</code>\nВыбрана пара\n<code>{}</code>\nСумма {} <code>{}</code>\nКэш нужен <code>{}</code>\nВариант доставки <code>{}</code></b>\n\n".format(
                i.client_id, i.city, pair, pair.split(' =>  ')[0], int(i.summ), period, i.transfer), parse_mode="HTML")
    buttons = []
    btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Обменник')
    buttons.append([btn_back])
    markup = InlineKeyboardMarkup(buttons)
    id = context.bot.send_message(
        message.chat.id, text, reply_markup=markup, parse_mode="HTML")
    User.set_message_id(update, context, id.message_id)

# Мои предложения


def merchant_suggestions(update: Update, context: CallbackContext):
    u = User.get_user(update, context)
    message = get_message_bot(update)
    del_mes(update, context, True)
    User.set_user_state(update, context, static_state.S_MENU)
    suggestions = list(
        u.merchant_executor_id_suggestion_set.all().values_list('order_id', flat=True))
    orders = Order.objects.filter(id__in=suggestions, status__in=[
                                  'active', 'mailing'])[:5]
    text = 'Ордеров нет'
    try:
        if len(orders) >= 1:
            text = 'Вернуться'
            for i in orders:
                if i.pair in Pairs.get_dict():
                    pair = Pairs.get_dict()[i.pair]
                else:
                    pair = i.pair.split('/')[0]+' =>  '+i.pair.split('/')[1]
                period = Periods.get_dict()[i.period]
                sug_text = ''
                s = Order.objects.get(id=i.id)
                ts = int(i.timestamp_execut) + (60*60*5.5)
                dt = datetime.datetime.fromtimestamp(
                    ts).strftime('%Y-%m-%d %H:%M:%S')
                for sug in s.order_id_suggestion_set.all():
                    sug_text += 'Сумма: ' + str(int(sug.summ))+' ' + \
                        str(pair.split(' =>  ')[1]) + ' Курс: ' + \
                        str(round(float(sug.summ)/float(i.summ), 2))
                    if u == sug.merchant_executor_id:
                        sug_text += ' от Вас ✅'
                    sug_text += '\n'
                bts = InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text='💵 Изменить сумму', callback_data='Предложить ' + str(i.id)),
                     InlineKeyboardButton(
                        text='💵 Изменить курс', callback_data='Предложить_курс ' + str(i.id))]
                ])
                context.bot.send_message(message.chat.id, "<b>ЗАЯВКА В ПРОЦЕССЕ ПОДБОРА ИСПОЛНИТЕЛЯ:\n\nУспешно выполнено \\ всего заявок: <code>{} \\ {}   {}%</code>\nВыбран город <code>{}</code>\nВыбрана пара\n<code>{}</code>\nСумма {} <code>{}</code>\nКэш нужен <code>{}</code>\nВариант доставки <code>{}</code>\n\nАтуально до <b>{}</b>\n\nПредложения от обменников:\n{}</b>".format(
                    i.client_id.count_client_order_success, i.client_id.count_client_order, round(i.client_id.count_client_order_success / i.client_id.count_client_order * 100, 2), i.city, pair, pair.split(' =>  ')[0], int(i.summ), period, i.transfer, dt, sug_text), reply_markup=bts, parse_mode="HTML")
                time.sleep(0.2)
    except:
        pass
    buttons = []
    btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Обменник')
    buttons.append([btn_back])
    markup = InlineKeyboardMarkup(buttons)
    id = context.bot.send_message(
        message.chat.id, text, reply_markup=markup, parse_mode="HTML")
    User.set_message_id(update, context, id.message_id)

# Забрать заявку Доступно Админам и по просроченным заявкам


def execute_order(update: Update, context: CallbackContext, order_id: str = 'None'):
    message = get_message_bot(update)
    User.set_user_state(
        update, context, static_state.S_ENTERED_SUMM_EXECUTING)
    o = Order.objects.get(id=int(order_id))
    if o.status in ['admining', 'active_v2']:
        try:
            city = o.city
            if o.pair in Pairs.get_dict():
                pair = Pairs.get_dict()[o.pair]
            else:
                pair = o.pair.split('/')[0]+' =>  '+o.pair.split('/')[1]
            summ = int(o.summ)
            period = Periods.get_dict()[o.period]
            order_fee = o.order_fee
            User.set_merchant_client(update, context, order_id)
            User.set_message_id(update, context, message.message_id)
            text = "<b>ЗАЯВКА НА ОБМЕН\n\nВыбран город <code>{}</code>\nВыбрана пара\n<code>{}</code>\nСумма {} <code>{}</code>\nКэш нужен <code>{}</code>\nВариант доставки <code>{}</code>\n\n Комиссия за сделку <code>{}</code> USDT\n\n\n ВВЕДИТЕ СУММУ ЦИФРОЙ В {}</b>".format(
                city, pair, pair.split(' => ')[0], summ, period, o.transfer, order_fee, pair.split(' => ')[1])
            buttons = []
            btn_back = InlineKeyboardButton(
                text='Отказаться', callback_data='Отказаться')
            buttons.append([btn_back])
            markup = InlineKeyboardMarkup(buttons)
            context.bot.edit_message_text(chat_id=message.chat.id, text=text,
                                          message_id=message.message_id, reply_markup=markup, parse_mode="HTML")
            return
        except:
            merchant_suggestion_cancel(update, context)
    else:
        merchant_suggestion_cancel(update, context)


# Забираем заявку
def merchant_executing_summ(update: Update, context: CallbackContext, order_id: str = 'None'):
    del_mes(update, context)
    u = User.get_user(update, context)
    message = get_message_bot(update)
    order_id = u.merchant_client
    summ = float(message.text)
    o = Order.objects.get(id=int(order_id))
    if o.status in ['admining', 'active_v2']:
        if isfloat(summ):
            User.set_user_state(update, context, static_state.S_MENU)
            s, created = Suggestion.objects.update_or_create(order_id=o, merchant_executor_id=u, defaults={
                'summ': summ
            })
            success = u.count_merchant_order_success
            count_merchant_order = u.count_merchant_order
            percent = 0
            if count_merchant_order != 0:
                percent = round(u.count_merchant_order_success /
                                u.count_merchant_order * 100, 2)
            username = str(u)
            un_ = username.split('@')[1]
            username_secure = '@' + \
                un_[0] + un_[1] + '******' + un_[-2] + un_[-1]
            # Отправляем сообщение пользователю
            text = '<b>{}\nУспешно выполнено \\ всего заявок: <code>{} \\ {}   {}%</code>\nПредлагаемая сумма {}\n<code>{}</code></b>'.format(
                username_secure, success, count_merchant_order, percent, int(summ), u.merchant_delivery)
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton(text='✅ Выбираю это предложение', callback_data='Выбираю_предложение '+str(
                    o.id)+'_'+str(u.user_id))]
            ])
            context.bot.send_message(
                o.client_id.user_id, text, reply_markup=markup, parse_mode="HTML")
            # Меняем статус заявки
            o.status = 'waiting_client'
            o.save()
        context.bot.delete_message(message.chat.id, u.message_id)
    else:
        merchant_suggestion_cancel(update, context)


# Предложить сумму на обмен
def merchant_suggestion(update: Update, context: CallbackContext, order_id: str = 'None'):
    message = get_message_bot(update)
    User.set_user_state(
        update, context, static_state.S_ENTERED_SUMM_SUGGESTION)
    o = Order.objects.get(id=int(order_id))
    if o.status in ['active', 'mailing', 'admining']:
        try:
            city = o.city
            if o.pair in Pairs.get_dict():
                pair = Pairs.get_dict()[o.pair]
            else:
                pair = o.pair.split('/')[0]+' =>  '+o.pair.split('/')[1]
            summ = int(o.summ)
            period = Periods.get_dict()[o.period]
            order_fee = o.order_fee
            User.set_merchant_client(update, context, order_id)
            User.set_message_id(update, context, message.message_id)
            text = "<b>ЗАЯВКА НА ОБМЕН\n\nВыбран город <code>{}</code>\nВыбрана пара\n<code>{}</code>\nСумма {} <code>{}</code>\nКэш нужен <code>{}</code>\nВариант доставки <code>{}</code>\n\n Комиссия за сделку <code>{}</code> USDT\n\n\n ВВЕДИТЕ СУММУ ЦИФРОЙ В {}</b>".format(
                city, pair, pair.split(' => ')[0], summ, period, o.transfer, order_fee, pair.split(' => ')[1])
            buttons = []
            btn_back = InlineKeyboardButton(
                text='Отказаться', callback_data='Отказаться')
            buttons.append([btn_back])
            markup = InlineKeyboardMarkup(buttons)
            context.bot.edit_message_text(chat_id=message.chat.id, text=text,
                                          message_id=message.message_id, reply_markup=markup, parse_mode="HTML")
        except:
            merchant_suggestion_cancel(update, context)
    else:
        merchant_suggestion_cancel(update, context)

# Предложить_курс сумму на обмен


def merchant_suggestion_course(update: Update, context: CallbackContext, order_id: str = 'None'):
    message = get_message_bot(update)
    User.set_user_state(
        update, context, static_state.S_ENTERED_COURSE_SUGGESTION)
    o = Order.objects.get(id=int(order_id))
    if o.status in ['active', 'mailing', 'admining']:
        try:
            city = o.city
            if o.pair in Pairs.get_dict():
                pair = Pairs.get_dict()[o.pair]
            else:
                pair = o.pair.split('/')[0]+' =>  '+o.pair.split('/')[1]
            summ = int(o.summ)
            period = Periods.get_dict()[o.period]
            order_fee = o.order_fee
            User.set_merchant_client(update, context, order_id)
            User.set_message_id(update, context, message.message_id)
            text = "<b>ЗАЯВКА НА ОБМЕН\n\nВыбран город <code>{}</code>\nВыбрана пара\n<code>{}</code>\nСумма {} <code>{}</code>\nКэш нужен <code>{}</code>\nВариант доставки <code>{}</code>\n\n Комиссия за сделку <code>{}</code> USDT\n\n\n ВВЕДИТЕ КУРС ЦИФРОЙ К {}</b>".format(
                city, pair, pair.split(' => ')[0], summ, period, o.transfer, order_fee, pair.split(' => ')[1])
            buttons = []
            btn_back = InlineKeyboardButton(
                text='Отказаться', callback_data='Отказаться')
            buttons.append([btn_back])
            markup = InlineKeyboardMarkup(buttons)
            context.bot.edit_message_text(chat_id=message.chat.id, text=text,
                                          message_id=message.message_id, reply_markup=markup, parse_mode="HTML")
        except:
            merchant_suggestion_cancel(update, context)
    else:
        merchant_suggestion_cancel(update, context)

# Отказаться от предложения суммы


def merchant_suggestion_cancel(update: Update, context: CallbackContext):
    User.set_user_state(update, context, static_state.S_MENU)
    del_mes(update, context)

# Записываем сумму


def merchant_suggestion_summ(update: Update, context: CallbackContext):
    del_mes(update, context)
    u = User.get_user(update, context)
    message = get_message_bot(update)
    order_id = u.merchant_client
    summ = message.text.replace(",", ".")
    if isfloat(summ):
        o = Order.objects.get(id=int(order_id))
        summ = float(summ.replace(",", "."))
        if u.state == static_state.S_ENTERED_COURSE_SUGGESTION:
            summ = float(summ) * float(o.summ)
        User.set_user_state(update, context, static_state.S_MENU)
        s, created = Suggestion.objects.update_or_create(order_id=o, merchant_executor_id=u, defaults={
            'summ': summ
        })
        o.status = 'mailing'
        o.save()
    try:
        context.bot.delete_message(message.chat.id, u.message_id)
    except:
        try:
            context.bot.delete_message(message.chat.id, u.message_id)
        except:
            try:
                context.bot.delete_message(message.chat.id, u.message_id)
            except:
                pass


###################################
###################################
def cmd_help(update: Update, context: CallbackContext):
    del_mes(update, context, True)
    message = get_message_bot(update)
    buttons = []
    btn_back = InlineKeyboardButton(text='⏪ Назад', callback_data='Меню')
    btn_main = InlineKeyboardButton(text='⏮ В начало', callback_data='Старт')
    buttons.append([btn_main, btn_back])
    markup = InlineKeyboardMarkup(buttons)
    id = context.bot.send_message(
        message.chat.id,
        """<b>ПОМОЩЬ</b>
        
        <a href="https://telegra.ph/FAQ-dlya-obmennikov-04-30">FAQ для обменников</a>
        <a href="https://telegra.ph/Poshagovaya-instrukciya-Kak-menyat-po-samomu-vygodnomu-kursu-na-SHri-Lanke-04-30">Как стать обменником?</a>
        <a href="https://telegra.ph/Usloviya-polzovaniem-botom-dlya-obmennikov-05-06">Условия пользованием ботом (для обменников)</a>
        """,
        reply_markup=markup, parse_mode="HTML", disable_web_page_preview=True)
    User.set_message_id(update, context, id.message_id)


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
        User.set_message_id(update, context, id.message_id)
    else:
        command_start(update, context)


def cmd_pass():
    pass


# словарь функций Меню по состоянию
State_Dict = {
    # Когда выбрано Меню, мы можем только нажимать кнопки. Любой текст удаляется
    static_state.S_MENU: del_mes,
    static_state.S_ENTERED_PAIR: cmd_periods,
    static_state.S_TYPE_PAIR_CUSTOME: user_type_pair_custome,
    # Обменник предлагает сумму для обмена
    static_state.S_ENTERED_SUMM_EXECUTING: merchant_executing_summ,
    static_state.S_ENTERED_SUMM_SUGGESTION: merchant_suggestion_summ,
    static_state.S_ENTERED_COURSE_SUGGESTION: merchant_suggestion_summ,
    static_state.S_FINNALY_REJECTED_ORDER: answer_rejected_order,
    static_state.S_FINNALY_ACCEPTED_ORDER: answer_rejected_order,
    static_state.S_DELIVERY_COST: merchant_delivery_cost,
    # Ожидаем когда пройдет час, чтоб сменился статус, до этого удаляем все сообщения
    static_state.S_ACCEPTED_ORDER: del_mes,
    static_state.S_ACCEPTED_EXCHANGE: del_mes,
}

# словарь функций Меню
Menu_Dict = {
    'Старт': command_start,
    'Меню': cmd_menu,
    'Администрирование': cmd_admin,
    'Меню_Клиент': start_client,
    'Заказы_Клиент': client_orders,
    'Клиент': cmd_client,
    'Город': cmd_type_pair,
    'ТИП_Пары': user_type_pair,
    'Пара': cmd_pair,
    'Период': cmd_transfer,
    'Доставка': cmd_accept_order,
    'Заявка_подтверждена': cmd_accepted_order,
    'Заявка_отклонена': cmd_canceled_order,
    'Отменить_заявку': user_canceled_order,
    'Выбираю_предложение': cmd_accepted_merchant_executer,
    'Обменник': cmd_merchant,
    'Правила_согласованны': merchant_terms_of_use_agreed,
    'Управление': merchant_settings,
    'Смена_статуса': merchant_change_status,
    'Мои_города': merchant_cities,
    'Доставка_кеш': merchant_delivery,
    'Мои_долги': merchant_debts,
    'Город_обменника': change_merchat_city,
    'Выполненные_заказы': merchant_orders_completed,
    'Актуальные_заявки': actual_orders,
    'Заказы_Мерчант': merchant_orders,
    'Удалить': del_mes,
    'Предложить': merchant_suggestion,
    'Предложить_курс': merchant_suggestion_course,
    'Отказаться': merchant_suggestion_cancel,
    'Мои_предложения': merchant_suggestions,
    'Курс_валют': merchant_course,
    'Збарать_заявку': execute_order,
    'pass': cmd_pass,
    'Клиент_подтвердил_сделку': cmd_finnaly_accepted_order,
    'Клиент_отменил_сделку': cmd_finnaly_rejected_order,
    'Help': cmd_help,
    'Ответ_на_отмененный_ордер': answer_rejected_order,
    'Ответ_на_выполненный_ордер': answer_accepted_order,
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
