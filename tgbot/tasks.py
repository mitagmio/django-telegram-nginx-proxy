"""
    Celery tasks. Some of them will be launched periodically from admin panel via django-celery-beat
"""

import time
from datetime import datetime
from typing import Union, List, Optional, Dict

import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from tgbot.models import P2p, Order, Suggestion, Cities, User, Pairs, Periods, Terms, Invoice

from dtb.celery import app
from celery.utils.log import get_task_logger
from tgbot.handlers.broadcast_message.utils import _send_message, _del_message, \
    _from_celery_entities_to_entities, _from_celery_markup_to_markup

logger = get_task_logger(__name__)


@app.task(ignore_result=True)
def broadcast_message(
    user_ids: List[Union[str, int]],
    text: str,
    entities: Optional[List[Dict]] = None,
    reply_markup: Optional[List[List[Dict]]] = None,
    sleep_between: float = 0.4,
    parse_mode=telegram.ParseMode.HTML,
) -> None:
    """ It's used to broadcast message to big amount of users """
    logger.info(f"Going to send message: '{text}' to {len(user_ids)} users")

    entities_ = _from_celery_entities_to_entities(entities)
    reply_markup_ = _from_celery_markup_to_markup(reply_markup)
    for user_id in user_ids:
        try:
            _send_message(
                user_id=user_id,
                text=text,
                entities=entities_,
                parse_mode=parse_mode,
                reply_markup=reply_markup_,
            )
            logger.info(f"Broadcast message was sent to {user_id}")
        except Exception as e:
            logger.error(f"Failed to send message to {user_id}, reason: {e}")
        time.sleep(max(sleep_between, 0.1))

    logger.info("Broadcast finished!")


@app.task(ignore_result=True)
def save_data_from_p2p() -> None:
    """ Получаем курсы с p2p Binance. Первая страница последние 5 записей """
    logger.info("Starting to get p2p courses")

    P2p.from_json(
        p2p_rub_usdt_json=P2p.get_course(
            pay_types='["Tinkoff"]', trade_type='"BUY"', fiat='"RUB"'),
        p2p_usdt_lkr_json=P2p.get_course(
            pay_types='["BANK"]', trade_type='"SELL"', fiat='"LKR"'),
        p2p_uah_usdt_json=P2p.get_course(
            pay_types='["PrivatBank"]', trade_type='"BUY"', fiat='"UAH"'),
        p2p_eur_usdt_json=P2p.get_course(
            pay_types='["Revolut"]', trade_type='"BUY"', fiat='"EUR"'),
        p2p_usd_usdt_json=P2p.get_course(
            pay_types='["Tinkoff"]', trade_type='"BUY"', fiat='"USD"'),
        p2p_kzt_usdt_json=P2p.get_course(
            pay_types='[]', trade_type='"BUY"', fiat='"KZT"')
    )

    logger.info("Get p2p courses are completed!")


@app.task(ignore_result=True)
def invoices() -> None:
    """ Выставляем счета за прошлый день """
    logger.info("Starting send invoices")
    id_merch_debts = User.objects.filter(merchant_status__in=['pause', 'online']).exclude(
        merchant_client__in=['None', 'under_consideration'])
    timestamp = time.time()
    for u in id_merch_debts:
        orders = u.merchant_executor_id_order_set.filter(
            status='exchanged_succesfull', status_fee='not_paid', order_fee__gt=0, timestamp_execut__lt=timestamp).order_by('timestamp_execut')
        if len(orders) >= 1:
            summ_debt = 0
            for i in orders:
                summ_debt += i.order_fee
                time.sleep(0.1)
                i.status_fee = 'invoiced'
                i.save()
            while len(Invoice.objects.filter(summ_invoice=summ_debt)) > 0:
                summ_debt += 0.01
                time.sleep(0.1)
            Invoice.objects.create(summ_invoice=summ_debt, payer_id=u)
            if not u.is_admin:
                u.merchant_status = 'dolg'
                u.save()
            text = 'Ваш статус изменен ‼️ Статус: Долг.\nДля продолжения использования бота вам необходимо отправить сумму {} USDT на кошелек Tron TRC20\n<code>TXBXgpaM5jCXVq45m8UNTuJaA4oJkSUQbY</code>\nПосле оплаты ваш статус будет изменён на ♻️ Статус: Онлайн\n\n <b>ВНИМАНИЕ!!!!\n\n ЕСЛИ ОТПРАВЛЕННАЯ СУММА НЕ БУДЕТ СОВПАДАТЬ, ТО ПЛАТЕЖ НЕ ЗАЧТЕТСЯ АВТОМАТИЧЕСКИ И ВАМ НУЖНО БУДЕТ ПИСАТЬ В ПОДДЕРЖКУ.\n\nТехническая поддержка: @sri_seacher</b>'.format(
                summ_debt)
            _send_message(
                user_id=u.user_id,
                text=text,
                entities=None,
                parse_mode=telegram.ParseMode.HTML,
                reply_markup=None,
            )
            time.sleep(0.1)
    logger.info("Sending invoices was completed!")


@app.task(ignore_result=True)
def payment() -> None:
    """ Подтверждаем оплату по выставленным счетам  """
    logger.info("Starting payment invoices")
    terms = Terms.objects.get(id=1)
    logger.info(
        f"min_timestamp {int(terms.last_time_payment)}")
    try:
        Transactions = Invoice.get_payment(
            int(terms.last_time_payment))['data']
        logger.info(
            f"Transactions {Transactions}")
    except Exception as e:
        Transactions = dict()
        logger.info(
            f"Transactions {len(Transactions)}, reason: {e}")
    if len(Transactions) > 0:
        timeblock = 0
        for t in Transactions:
            if int(t['block_timestamp']) > timeblock:
                timeblock = int(t['block_timestamp'])
            pay_value = float(t['value']) / \
                10**float(t['token_info']['decimals'])

            try:
                inv = Invoice.objects.get(summ_invoice=pay_value)
            except Invoice.DoesNotExist:
                inv = None
            if inv != None:
                u = inv.payer_id
                orders = u.merchant_executor_id_order_set.filter(
                    status='exchanged_succesfull', status_fee='invoiced', order_fee__gt=0).order_by('timestamp_execut')
                if len(orders) >= 1:
                    for i in orders:
                        time.sleep(0.1)
                        i.status_fee = 'payment_successful'
                        i.save()
                if not u.is_admin:
                    u.merchant_status = 'online'
                    u.save()
                text = 'Ваш статус изменен ♻️ Статус: Онлайн.\nПродолжайте использовать бота и получать новые заявки на обмен. Долг на сумму {} USDT погашен.'.format(
                    pay_value)
                _send_message(
                    user_id=u.user_id,
                    text=text,
                    entities=None,
                    parse_mode=telegram.ParseMode.HTML,
                    reply_markup=None,
                )
                time.sleep(0.1)
                inv.delete()
        terms.last_time_payment = timeblock + 1000
        terms.save()
    logger.info("Payment invoices was completed!")


@app.task(ignore_result=True)
def change_order_status_and_mailing_suggestions(
    sleep_between: float = 0.4,
    parse_mode=telegram.ParseMode.HTML
) -> None:
    """ Меняем статус у заказов и рассылаем предложение обменников """
    logger.info("Starting checking orders")

    orders = Order.objects.filter(
        status__in=['active', 'active_v2', 'mailing', 'admining'], timestamp_execut__lte=time.time())
    for o in orders:
        if o.status == 'active_v2':
            # try:
            #     _del_message(
            #         chat_id=o.client_id.user_id,
            #         message_id=o.client_id.message_id,
            #     )
            #     logger.info(
            #         f"Broadcast message was delete to {o.client_id}")
            # except Exception as e:
            #     logger.error(
            #         f"status = 'active_v2' Failed to del message to {o.client_id}, reason: {e}")
            try:
                _send_message(
                    user_id=o.client_id.user_id,
                    text='<b> ЗАКАЗ В ОЖИДАНИИ!!!\n\nНА ВАШ ЗАКАЗ НЕБЫЛО ПРЕДЛОЖЕНИЙ, ПОПРОБУЙ ВЫБРАТЬ ГОРОД ГДЕ БОЛЬШЕ ОБМЕННИКОВ В ДАННЫЙ МОМЕНТ.</b>',
                    entities=None,
                    parse_mode=parse_mode,
                    reply_markup=_from_celery_markup_to_markup([
                        [dict(text='‼️ Отменить заказ и вернуться в меню',
                              callback_data='Отменить_заявку '+str(o.id))]
                    ]),
                )
                logger.info(f"Broadcast message was sent to {o.client_id}")
                timestamp = int(datetime.today().timestamp())
                dt = datetime.fromtimestamp(
                    timestamp + (60*60*5.5))
                hour = 23 - int(dt.hour)
                timestamp_execut = timestamp + (60*60*hour)
                date_time_execut = datetime.fromtimestamp(
                    timestamp_execut + (60*60*5.5))
                date_time_execut
                o.status = 'waiting_end_day'
                o.timestamp_execut = timestamp_execut
                o.date_time_execut = date_time_execut
                o.save()
            except Exception as e:
                logger.error(
                    f"status = 'active_v2' => 'waiting_end_day' Failed to send message to {o.client_id}, reason: {e}")
                o.status = 'canceled'
                o.save()
            # отправляем просрочку в группу
            try:
                if o.status == 'waiting_end_day':
                    u = o.client_id
                    s = Cities.objects.get(ru_name=u.city)
                    user_ids = list(s.city_merchant_ids_set.all().values_list(
                        'merchant_id', flat=True))  # Список мерчантов представленных в городе
                    usernames = list(User.objects.filter(user_id__in=user_ids, merchant_status__in=['online']).values_list(
                        'username', flat=True))  # Проверяем статус мерчантов 'online' 'pause'
                    names_text = ''
                    prom_pre = ' вы работаете по городу '
                    prom_post = ''
                    for name in usernames:
                        names_text += '@' + name + ' (он-лайн), '
                    if len(usernames) > 0:
                        username = str(u)
                        un_ = username.split('@')[1]
                        username_secure = '@' + \
                            un_[0] + un_[1] + '******' + un_[-2] + un_[-1]
                        percent = 0
                        if u.count_client_order > 0:
                            percent = round(u.count_client_order_success /
                                            u.count_client_order * 100, 2)
                        city = o.city
                        if o.pair in Pairs.get_dict():
                            pair = Pairs.get_dict()[o.pair]
                        else:
                            pair = o.pair.split(
                                '/')[0]+' =>  '+o.pair.split('/')[1]
                        summ = int(o.summ)
                        period = Periods.get_dict()[o.period]
                        p2p_last = P2p.objects.latest('timestamp').__dict__
                        p2p_last['usdt'] = 1
                        pair_dict = Pairs.get_convert_dict()
                        if o.pair in pair_dict:
                            exchange_rate = p2p_last[pair_dict[o.pair]]
                        else:
                            exchange_rate = p2p_last['usdt']
                        order_fee = round((float(summ) / float(exchange_rate))
                                          * float(Terms.get_dict()['size_fee']), 2)
                        logger.info(
                            f"Broadcast message must be sent to '-1001717597940'")
                        _send_message(
                            user_id='-1001717597940',
                            text="<b>Внимание! Просроченная заявка!\n( 2 часа, 30 минут без внимания 😱 🤯 😱 )</b>\n{}{}{}{}\n\n Обратите внимание в разделе ''АКТИВНЫЕ ЗАЯВКИ'' висит заявка на обмен:{}\nУспешно выполнено \\ всего заявок: <code>{} \\ {}   {}%</code>\nВыбран город <code>{}</code>\nВыбрана пара\n<code>{}</code>\nСумма {} <code>{}</code>\nКэш нужен <code>{}</code>\nВариант доствки <code>{}</code>\n\n Комиссия за сделку <code>{}</code> USDT\n\n <b>Сейчас</b>: Кто первый сделает ставку, того и покажем клиенту, остальных не покажем!\n\nПравило: Если заявка кажется вам не выгодной - предложите меньший курс, что бы вам было комфортно!".format(
                                names_text, prom_pre, city, prom_post, username_secure, u.count_client_order_success, u.count_client_order, percent, city, pair, pair.split(' =>  ')[0], summ, period, o.transfer, order_fee),
                            entities=None,
                            parse_mode=parse_mode,
                            reply_markup=None,
                        )
                        logger.info(
                            f"Broadcast message was sent to '-1001717597940'")
            except Exception as e:
                logger.error(
                    f"status = 'active' => 'waiting_end_day' Failed to send message to '-1001717597940', reason: {e}")
            time.sleep(max(sleep_between, 0.1))
        if o.status == 'active':
            # try:
            #     _del_message(
            #         chat_id=o.client_id.user_id,
            #         message_id=o.client_id.message_id,
            #     )
            #     logger.info(
            #         f"Broadcast message was delete to {o.client_id} ID {o.client_id.user_id}")
            # except Exception as e:
            #     logger.error(
            #         f"status = 'active' Failed to del message to {o.client_id} ID {o.client_id.user_id}, reason: {e}")
            try:
                print(o.period)
                if o.period == 'Urgently_1h':
                    _text = '<b>ЗАКАЗ В ОЖИДАНИИ!!!\n\nМы оповестили обменники в вашем городе по вашей заявке, но на текущий момент они не озвучили свои предложения по вашей заявке. 🤷‍♂️\n\nУчитывая это, мы скинули дополнительное упоминание о том, что вам надо срочно в наш общий чат с обменниками и мы пришлем вам первое же предложение, полученное от любого из обменников.\n\nЕсли же вы уже нашли предложение где то на стороне, вы можете отменить свою заявку у нас или же дождаться от нашего партнера - обменника.</b>'
                    _rm = _from_celery_markup_to_markup([
                        [dict(text='‼️ Отменить заказ и вернуться в меню',
                              callback_data='Отменить_заявку')]
                    ])
                else:
                    _text = '<b>ЗАКАЗ В ОЖИДАНИИ!!!\n\nМы оповестили обменники в вашем городе по вашей заявке, но на текущий момент они не озвучили свои предложения по вашей заявке. 🤷‍♂️\n\nУчитывая это, мы скинули дополнительное упоминание о том, что вам надо срочно в наш общий чат с обменниками.</b>'
                    _rm = None
                _send_message(
                    user_id=o.client_id.user_id,
                    text=_text,
                    entities=None,
                    parse_mode=parse_mode,
                    reply_markup=_rm,
                )
            except Exception as e:
                if str(e) == 'Chat not found':
                    o.status = 'canceled'
                    o.save()
                logger.error(
                    f"status = 'active' Failed to send message to {o.client_id}, reason: {e}")

            # отправляем просрочку в группу
            try:
                if o.status == 'active':
                    u = o.client_id
                    s = Cities.objects.get(ru_name=u.city)
                    user_ids = list(s.city_merchant_ids_set.all().values_list(
                        'merchant_id', flat=True))  # Список мерчантов представленных в городе
                    usernames = list(User.objects.filter(user_id__in=user_ids, merchant_status__in=['online', 'pause']).values_list(
                        'username', flat=True))  # Проверяем статус мерчантов 'online' 'pause'
                    names_text = ''
                    prom_pre = ' вы работаете по городу '
                    prom_post = ''
                    for name in usernames:
                        names_text += '@' + name + ' (он-лайн), '
                    if len(usernames) == 0:
                        prom_pre = ''
                        names_text = '<code> НЕТ НИ ОДНОГО ОБМЕННИКА В ЭТОМ ГОРОДЕ 😰 </code>'
                        prom_post = ', однако если вы рядом, добавьте в настройках этот город и забирайте заявку в разделе "Активные заявки"'
                    username = str(u)
                    un_ = username.split('@')[1]
                    username_secure = '@' + \
                        un_[0] + un_[1] + '******' + un_[-2] + un_[-1]
                    percent = 0
                    if u.count_client_order > 0:
                        percent = round(u.count_client_order_success /
                                        u.count_client_order * 100, 2)
                    city = o.city
                    if o.pair in Pairs.get_dict():
                        pair = Pairs.get_dict()[o.pair]
                    else:
                        pair = o.pair.split('/')[0] + \
                            ' =>  '+o.pair.split('/')[1]
                    summ = int(o.summ)
                    period = Periods.get_dict()[o.period]
                    p2p_last = P2p.objects.latest('timestamp').__dict__
                    p2p_last['usdt'] = 1
                    pair_dict = Pairs.get_convert_dict()
                    if o.pair in pair_dict:
                        exchange_rate = p2p_last[pair_dict[o.pair]]
                    else:
                        exchange_rate = p2p_last['usdt']
                    order_fee = round((float(summ) / float(exchange_rate))
                                      * float(Terms.get_dict()['size_fee']), 2)
                    logger.info(
                        f"Broadcast message must be sent to '-1001717597940'")

                    text = "<b>Внимание! Просроченная заявка!</b>\n{}{}{}{}\n\n Обратите внимание в разделе ''АКТИВНЫЕ ЗАЯВКИ'' висит заявка на обмен:{}\nУспешно выполнено \\ всего заявок: <code>{} \\ {}   {}%</code>\nВыбран город <code>{}</code>\nВыбрана пара\n<code>{}</code>\nСумма {} <code>{}</code>\nКэш нужен <code>{}</code>\nВариант доствки <code>{}</code>\n\n Комиссия за сделку <code>{}</code> USDT\n\n <b>Сейчас</b>: Кто первый сделает ставку, того и покажем клиенту, остальных не покажем!\n\nПравило: Следите за заявками, которые присылает бот!\nУ всех есть 30 минут на то, что бы сделать свою ставку. Если за 30 минут вы не сделали ставку, то право сделать ставку дается только одному обменнику, который будет первым спустя 30 минут.".format(
                        names_text, prom_pre, city, prom_post, username_secure, u.count_client_order_success, u.count_client_order, percent, city, pair, pair.split(' =>  ')[0], summ, period, o.transfer, order_fee)

                    if len(usernames) == 0:
                        text = "<b>Внимание! Просроченная заявка!</b>\n{}{}{}{}\n\nВыбрана пара\n<code>{}</code>\nСумма {} <code>{}</code>\nКэш нужен <code>{}</code>\nВариант доствки <code>{}</code>".format(
                            names_text, prom_pre, city, prom_post, pair, pair.split(' =>  ')[0], summ, period, o.transfer)
                    _send_message(
                        user_id='-1001717597940',
                        text=text,
                        entities=None,
                        parse_mode=parse_mode,
                        reply_markup=None,
                    )
                    logger.info(
                        f"Broadcast message was sent to '-1001717597940'")
                    # дополнительные 2 часа
                    timestamp = int(datetime.today().timestamp())
                    timestamp_execut = timestamp + (60*60*2)
                    date_time_execut = datetime.fromtimestamp(
                        timestamp_execut + (60*60*5.5))
                    o.status = 'active_v2'
                    o.timestamp_execut = timestamp_execut
                    o.date_time_execut = date_time_execut
                    o.save()
            except Exception as e:
                logger.error(
                    f"status = 'active' => 'active_v2' Failed to send message to '-1001717597940', reason: {e}")
            time.sleep(max(sleep_between, 0.1))
        if o.status == 'mailing':
            suggestion = Suggestion.objects.filter(order_id=o.id)
            for s in suggestion:
                try:
                    success = s.merchant_executor_id.count_merchant_order_success
                    count_merchant_order = s.merchant_executor_id.count_merchant_order
                    merchant_delivery = s.merchant_executor_id.merchant_delivery
                    percent = 0
                    if count_merchant_order != 0:
                        percent = round(s.merchant_executor_id.count_merchant_order_success /
                                        s.merchant_executor_id.count_merchant_order * 100, 2)
                    course = round(float(s.summ)/float(o.summ), 2)
                    username = str(s.merchant_executor_id)
                    un_ = username.split('@')[1]
                    username_secure = '@' + \
                        un_[0] + un_[1] + '******' + un_[-2] + un_[-1]

                    if o.pair in Pairs.get_dict():
                        pair = Pairs.get_dict()[o.pair]
                    else:
                        pair = o.pair.split('/')[0] + \
                            ' =>  '+o.pair.split('/')[1]

                    _send_message(
                        user_id=o.client_id.user_id,
                        text='<b>{}\nУспешно выполнено \\ всего заявок: <code>{} \\ {}   {}%</code>\nПредлагаемая сумма: <code>{}</code> {}\nКурс: <code>{}</code>\n<code>{}</code></b>'.format(
                            username_secure, success, count_merchant_order, percent, int(s.summ), pair.split(' => ')[1], course, merchant_delivery),
                        entities=None,
                        parse_mode=parse_mode,
                        reply_markup=_from_celery_markup_to_markup([
                            [dict(text='✅ Выбираю это предложение', callback_data='Выбираю_предложение '+str(
                                o.id)+'_'+str(s.merchant_executor_id.user_id))]
                        ]),
                    )
                    logger.info(f"Broadcast message was sent to {o.client_id}")
                    o.status = 'waiting_client'
                    o.save()
                except Exception as e:
                    logger.error(
                        f"Failed to send message to {o.client_id}, reason: {e}")
                time.sleep(max(sleep_between, 0.1))
        if o.status == 'admining':
            timestamp = int(datetime.today().timestamp())
            # каждые 30 минут минус 3 минуты администрирования
            timestamp_execut = timestamp + (60*60*0.5) - (60*3)
            date_time_execut = datetime.fromtimestamp(
                timestamp_execut + (60*60*5.5))
            city = o.city
            if o.pair in Pairs.get_dict():
                pair = Pairs.get_dict()[o.pair]
            else:
                pair = o.pair.split('/')[0] + \
                    ' =>  '+o.pair.split('/')[1]
            summ = int(o.summ)
            period = Periods.get_dict()[o.period]
            u = o.client_id
            s = Cities.objects.get(ru_name=u.city)
            user_ids = list(s.city_merchant_ids_set.all().values_list(
                'merchant_id', flat=True))  # Список мерчантов представленных в городе
            ids = list(User.objects.filter(user_id__in=user_ids, merchant_status='online').values_list(
                'user_id', flat=True))  # Проверяем статус мерчантов = 'online'
            
            merchant_names = list(User.objects.filter(user_id__in=user_ids, merchant_status='online').values_list(
                'username', flat=True))  # Проверяем статус мерчантов = 'online'
            
            bts = [
                [{'text': '💵 Предложить сумму',
                    'callback_data': 'Предложить ' + str(o.id)},
                 {'text': '💵 Предложить курс',
                    'callback_data': 'Предложить_курс ' + str(o.id)}
                 ],
                [{'text': '🪁 Пропустить', 'callback_data': 'Удалить'}]
            ]
            percent = 0
            if u.count_client_order > 0:
                percent = round(u.count_client_order_success /
                                u.count_client_order * 100, 2)
            username = str(u)
            un_ = username.split('@')[1]
            username_secure = '@' + un_[0] + \
                un_[1] + '******' + un_[-2] + un_[-1]
            p2p_last = P2p.objects.latest('timestamp').__dict__
            p2p_last['usdt'] = 1
            pair_dict = Pairs.get_convert_dict()
            if o.pair in pair_dict:
                exchange_rate = p2p_last[pair_dict[u.pair]]
            else:
                exchange_rate = p2p_last['usdt']
            order_fee = round((float(summ) / float(exchange_rate))
                              * float(Terms.get_dict()['size_fee']), 2)

            names_text = ''
            for name in merchant_names:
                names_text += '@' + name + ', '

            # отправляем заказ в группу -1001717597940 #Рабочая группа: Биржа обменников биржа ШриЛанка. @cash_market_bot
            broadcast_message.delay(
                user_ids=['-1001717597940'],
                text="<b>ЗАЯВКА от {}$\n\nГород: {}\nПара: {}\nСумма на обмен: {} {}\n\n{} обратите внимание, это ваш город, проверьте раздел ''Активные заявки''</b>".format(
                    int(float(Terms.get_dict()['filter_order_size_adminig'])), city, pair, summ, pair.split(' =>  ')[0], names_text)
            )

            if len(ids) > 0:
                # send in async mode via celery
                broadcast_message.delay(
                    user_ids=ids,
                    text="<b>НОВЫЙ ОРДЕР\n{}\nУспешно выполнено \\ всего заявок: <code>{} \\ {}   {}%</code>\nВыбран город <code>{}</code>\nВыбрана пара\n<code>{}</code>\nСумма {} <code>{}</code>\nКэш нужен <code>{}</code>\nВариант доствки <code>{}</code>\n\n Комиссия за сделку <code>{}</code> USDT</b>".format(
                        username_secure, u.count_client_order_success, u.count_client_order, percent, city, pair, pair.split('/')[0], summ, period, o.transfer, order_fee),
                    reply_markup=bts
                )
            try:
                logger.info(f"Broadcast change status to send messages")
                o.status = 'active'
                o.timestamp_execut = timestamp_execut
                o.date_time_execut = date_time_execut
                o.order_fee = order_fee
                o.save()
            except Exception as e:
                logger.error(
                    f"Failed change status, reason: {e}")
            time.sleep(max(sleep_between, 0.1))
    logger.info("Checking orders completed!")
