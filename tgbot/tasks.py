"""
    Celery tasks. Some of them will be launched periodically from admin panel via django-celery-beat
"""

import time
from datetime import datetime
from typing import Union, List, Optional, Dict

import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from tgbot.models import P2p, User, Terms, Invoice

from dtb.celery import app
from celery.utils.log import get_task_logger
from dtb.settings import TELEGRAM_LOGS_CHAT_ID
from tgbot.handlers.broadcast_message.utils import _send_message, _del_message, _kick_member,  \
    _from_celery_entities_to_entities, _from_celery_markup_to_markup, _get_admins

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
        tr_text = f"Transactions {Transactions}"
        logger.info(tr_text)
    except Exception as e:
        Transactions = dict()
        tr_text = f"Transactions {len(Transactions)}, reason: {e}"
        logger.info(tr_text)
    if len(Transactions) > 0:
        timeblock = 0
        for t in Transactions:
            if int(t['block_timestamp']) > timeblock:
                timeblock = int(t['block_timestamp'])
            if t['token_info']['symbol']=='USDT':
                pay_value = float(t['value']) / \
                    10**float(t['token_info']['decimals'])

                try:
                    inv = Invoice.objects.get(summ_invoice=pay_value)
                    bal_after = inv.payer_id.balance
                    log_text = f"Invoice payment success {pay_value}, User {inv.payer_id}, id {inv.payer_id.user_id}, bal_before {inv.payer_id.balance}"
                    logger.info(log_text)
                except Invoice.DoesNotExist:
                    inv = None
                    log_text = f"Invoice {pay_value}, Invoice.DoesNotExist. \n Transaction {t}"
                    logger.info(log_text)
                if inv != None:
                    u = inv.payer_id
                    u.balance += pay_value
                    u.save()
                    bal_after = u.balance
                    text = '💵 Ваш платеж на сумму <code>{}</code> USDT зачислен.\n\nТекущий баланс составляет <code>{}</code> USDT'.format(
                        pay_value, u.balance)
                    _send_message(
                        user_id=u.user_id,
                        text=text,
                        entities=None,
                        parse_mode=telegram.ParseMode.HTML,
                        reply_markup=None,
                    )
                    time.sleep(0.1)
                    inv.delete()
                _send_message(
                    user_id=TELEGRAM_LOGS_CHAT_ID,
                    text=log_text+f", bal_after {bal_after} ",
                    entities=None,
                    parse_mode=telegram.ParseMode.HTML,
                    reply_markup=None,
                )
        terms.last_time_payment = timeblock + 1000
        terms.save()
    logger.info("Payment invoices was completed!")


@app.task(ignore_result=True)
def kick_selected() -> None:
    """ Выгоняем пользователей из selected """
    logger.info("Starting kicking Selected users")
    timestamp = int(datetime.today().timestamp())
    logger.info(
        f"timestamp {int(timestamp)}")
    try:
        Users = User.objects.filter(execute_selected_time__lt=timestamp).filter(execute_selected_time__gt=0)
        channel_id = -1001695923729
        admin_ids = _get_admins(chat_id=channel_id)
        # logger.info(
        #     f"Users {Users}")
    except Exception as e:
        Users = dict()
        admin_ids = []
        logger.info(
            f"Users {len(Users)}, reason: {e}")
    if len(Users) > 0:
        for u in Users:
            # _kick_member(
            #     user_id=u.user_id,
            #     chat_id=-1001796561677
            # )
            # time.sleep(0.1)
            _kick_member(
                user_id=u.user_id,
                admin_ids=admin_ids,
                chat_id=channel_id
            )
            u.execute_selected_time = 0
            u.save()
    logger.info("Selected kicked users was completed!")

@app.task(ignore_result=True)
def kick_selected_all() -> None:
    """ Выгоняем пользователей из selected """
    logger.info("Starting kicking all Selected users")
    timestamp = int(datetime.today().timestamp())
    logger.info(
        f"timestamp {int(timestamp)}")
    try:
        Users = User.objects.filter(execute_selected_time__lt=timestamp)
        channel_id = -1001695923729
        admin_ids = _get_admins(chat_id=channel_id)
        # logger.info(
        #     f"Users {Users}")
    except Exception as e:
        Users = dict()
        admin_ids = []
        logger.info(
            f"Users {len(Users)}, reason: {e}")
    if len(Users) > 0:
        for u in Users:
            # _kick_member(
            #     user_id=u.user_id,
            #     chat_id=-1001796561677
            # )
            # time.sleep(0.1)
            _kick_member(
                user_id=u.user_id,
                admin_ids=admin_ids,
                chat_id=channel_id
            )
            u.execute_selected_time = 0
            u.save()
    logger.info("Selected kicked all users was completed!")