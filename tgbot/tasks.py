"""
    Celery tasks. Some of them will be launched periodically from admin panel via django-celery-beat
"""

import time
from datetime import datetime, timedelta
from typing import Union, List, Optional, Dict

import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from tgbot.models import P2p, User, Terms, Invoice, Settings

from dtb.celery import app
from celery.utils.log import get_task_logger
from dtb.settings import TELEGRAM_LOGS_CHAT_ID, TRON_TRC20
from tgbot.handlers.broadcast_message.utils import _send_message, _del_message, _kick_member,  \
    _from_celery_entities_to_entities, _from_celery_markup_to_markup, _get_admins, _get_invite_selected

from tronpy import Tron
from tronpy.keys import PrivateKey
from tronpy.providers import HTTPProvider

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

# @app.task(ignore_result=True)
# def payment_manual() -> None:
#     """ Подтверждаем оплату по ручному счетам  """
#     logger.info("Starting payment manual")
#     settings = Settings.objects.get(id=1)
#     timeblock = 0
#     Users = User.objects.filter(addr='TDM5MWGD7BpdxePzhe75aNc44n7jvomYWj')
#     logger.info(
#         f"min_timestamp {int(1662035164000)}")
#     try:
#         client = Tron(provider=HTTPProvider(api_key=[settings.key1, settings.key2, settings.key3]), network='mainnet')
#         contract = client.get_contract('TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t') #usdt
#     except Exception as e:
#         print('Error Client or Contract', e)
#         pass
#     for u in Users:
#         try:
#             print(u.username, u.addr)
#             Transactions = Invoice.get_payment(
#                 int(1662035164000),
#                 str(u.addr)
#                 )['data']
#             logger.info(
#                 f"Transactions {Transactions}")
#         except Exception as e:
#             Transactions = dict()
#             logger.info(
#                 f"Transactions {len(Transactions)}, reason: {e}")
#         if len(Transactions) > 0:

#             for t in Transactions:
#                 if t['transaction_id'] == "fa88f3ad9add4a62e5f91438acdb2671bc675966e9f9672a8bd50d330fd9c692":
#                     if int(t['block_timestamp']) > timeblock:
#                         timeblock = int(t['block_timestamp'])
#                     pay_value = float(0.0)
#                     if t['to'] == str(u.addr) and t['token_info']['symbol']=='USDT':
#                         pay_value = float(t['value']) / \
#                             10**float(t['token_info']['decimals'])
#                     if pay_value > 0 :
#                         bal_before = u.balance
#                         u.balance += pay_value
#                         text = '💵 Ваш платеж на сумму <code>{}</code> USDT зачислен.\n\nТекущий баланс составляет <code>{}</code> USDT'.format(
#                             pay_value, u.balance)
#                         _send_message(
#                             user_id=u.user_id,
#                             text=text,
#                             entities=None,
#                             parse_mode=telegram.ParseMode.HTML,
#                             reply_markup=None,
#                         )
#                         time.sleep(0.5)
#                         bal_after = u.balance
#                         log_text = f"Invoice payment success {pay_value},Adr {u.addr}, User {u}, id {u.user_id}, bal_before {bal_before}"
#                         _send_message(
#                             user_id=TELEGRAM_LOGS_CHAT_ID,
#                             text=log_text+f", bal_after {bal_after} ",
#                             entities=None,
#                             parse_mode=telegram.ParseMode.HTML,
#                             reply_markup=None,
#                         )
#                     u.hot_balance_usdt += pay_value # contract.functions.balanceOf(str(u.addr))/10**float(contract.functions.decimals())
#                     if u.hot_balance_usdt >= 100:
#                         try:
#                             u.hot_balance_trx = float(client.get_account_balance(str(u.addr)))
#                             time.sleep(1.5)
#                             if u.hot_balance_trx > 0 and u.hot_balance_trx < 20:
#                                 fee = float(20 - u.hot_balance_trx)
#                         except Exception as e:
#                             print('Error Get balance TRX', e)
#                             fee = float(20)
            
#                         if u.hot_balance_trx == 0:
#                             fee = float(20)

#                         if u.hot_balance_trx >= 20:
#                             fee = 0
#                         try:
#                             if fee > 0:    
#                                 giver = User.objects.get(user_id=352482305)
#                                 priv_key = PrivateKey(bytes.fromhex(giver.private_key))
#                                 txn = (
#                                     client.trx.transfer(giver.addr, u.addr, int(fee*1000000))
#                                     .build()
#                                     .sign(priv_key)
#                                 )
#                                 txn.broadcast().wait(timeout=60, interval=1.8)
#                                 u.hot_balance_trx += fee
#                         except Exception as e:
#                             print('Error Send TRX from giver wallet', e)
#             u.save()
#     logger.info("Payment manual was completed!")

@app.task(ignore_result=True)
def payment_multi() -> None:
    """ Подтверждаем оплату по выставленным счетам  """
    logger.info("Starting payment invoices")
    settings = Settings.objects.get(id=1)
    timeblock = 0
    Users = User.objects.exclude(addr='0')
    logger.info(
        f"min_timestamp {int(settings.last_time_payment)}")
    try:
        client = Tron(provider=HTTPProvider(api_key=[settings.key1, settings.key2, settings.key3]), network='mainnet')
        contract = client.get_contract('TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t') #usdt
    except Exception as e:
        print('Error Client or Contract', e)
        pass
    for u in Users:
        try:
            # print(u.username, u.addr)
            Transactions = Invoice.get_payment(
                int(settings.last_time_payment),
                str(u.addr)
                )['data']
            # logger.info(f"Transactions {Transactions}")
        except Exception as e:
            Transactions = dict()
            logger.info(
                f"Transactions {len(Transactions)}, reason: {e}, pause 1.5 seconds and try again")
            time.sleep(1.5)
            try:
                # print(u.username, u.addr)
                Transactions = Invoice.get_payment(
                    int(settings.last_time_payment),
                    str(u.addr)
                    )['data']
                # logger.info(f"Transactions {Transactions}")
            except Exception as e:
                Transactions = dict()
                logger.info(
                    f"Transactions {len(Transactions)}, reason: {e}, pause 3 seconds and try again")
                time.sleep(3)
                try:
                    # print(u.username, u.addr)
                    Transactions = Invoice.get_payment(
                        int(settings.last_time_payment),
                        str(u.addr)
                        )['data']
                    # logger.info(f"Transactions {Transactions}")
                except Exception as e:
                    Transactions = dict()
                    logger.info(
                        f"Transactions {len(Transactions)}, reason: {e}")

        if len(Transactions) > 0:
            print(u.username, u.addr)
            logger.info(
                    f"Transactions {Transactions}")
            for t in Transactions:
                if int(t['block_timestamp']) > timeblock:
                    timeblock = int(t['block_timestamp'])
                pay_value = float(0.0)
                if t['to'] == str(u.addr) and t['token_info']['symbol']=='USDT':
                    pay_value = float(t['value']) / \
                        10**float(t['token_info']['decimals'])

                # try:
                #     inv = Invoice.objects.get(summ_invoice=pay_value)
                # except Invoice.DoesNotExist:
                #     inv = None
                # if inv != None:
                    # u = inv.payer_id
                if pay_value > 0 :
                    bal_before = u.balance
                    u.balance += pay_value
                    text = '💵 Ваш платеж на сумму <code>{}</code> USDT зачислен.\n\nТекущий баланс составляет <code>{}</code> USDT'.format(
                        pay_value, u.balance)
                    _send_message(
                        user_id=u.user_id,
                        text=text,
                        entities=None,
                        parse_mode=telegram.ParseMode.HTML,
                        reply_markup=None,
                    )
                    time.sleep(0.5)
                    bal_after = u.balance
                    log_text = f"Invoice payment success {pay_value},Adr {u.addr}, User {u}, id {u.user_id}, bal_before {bal_before}"
                    _send_message(
                        user_id=TELEGRAM_LOGS_CHAT_ID,
                        text=log_text+f", bal_after {bal_after} ",
                        entities=None,
                        parse_mode=telegram.ParseMode.HTML,
                        reply_markup=None,
                    )
                    # inv.delete()
                u.hot_balance_usdt += pay_value # contract.functions.balanceOf(str(u.addr))/10**float(contract.functions.decimals())
                if u.hot_balance_usdt >= 100:
                    try:
                        u.hot_balance_trx = float(client.get_account_balance(str(u.addr)))
                        time.sleep(1.5)
                        if u.hot_balance_trx > 0 and u.hot_balance_trx < 20:
                            fee = float(20 - u.hot_balance_trx)
                    except Exception as e:
                        print(f'Error Get balance TRX u.username: {u.username}, addr: {u.addr}', e)
                        fee = float(20)
        
                    if u.hot_balance_trx == 0:
                        fee = float(20)

                    if u.hot_balance_trx >= 20:
                        fee = 0
                    try:
                        if fee > 0:    
                            giver = User.objects.get(user_id=352482305)
                            priv_key = PrivateKey(bytes.fromhex(giver.private_key))
                            txn = (
                                client.trx.transfer(giver.addr, u.addr, int(fee*1000000))
                                .build()
                                .sign(priv_key)
                            )
                            txn.broadcast().wait(timeout=60, interval=1.8)
                            u.hot_balance_trx += fee
                    except Exception as e:
                        print('Error Send TRX from giver wallet', e)

                    # try:        
                    #     if fee == 0:
                    #         priv_key = PrivateKey(bytes.fromhex(u.private_key))
                    #         txn = (
                    #             contract.functions.transfer('THKqtdfNBxqkSwzLTV9JMANgW9p1uZBDN4', int(pay_value*1000000))
                    #             .with_owner(u.addr) # address of the private key
                    #             .fee_limit(20_000_000)
                    #             .build()
                    #             .sign(priv_key)
                    #         )
                    #         txn.broadcast().wait(timeout=60, interval=1.8)
                    # except Exception as e:
                    #     print('Error Send to treasure wallet', e)
            u.save()
    if timeblock > settings.last_time_payment:
        settings.last_time_payment = timeblock + 1000
        settings.save()
    logger.info("Payment invoices was completed!")


@app.task(ignore_result=True)
def send_to_treasure() -> None:
    """ Отправляем в хранилище  """
    logger.info("Starting send to treasure")
    Users = User.objects.filter(hot_balance_trx__gt=0, hot_balance_usdt__gt=0)
    try:
        len_u = len(Users)
    except:
        len_u = 0
    if len_u > 0:
        settings = Settings.objects.get(id=1)
        try:
            client = Tron(provider=HTTPProvider(api_key=[settings.key1, settings.key2, settings.key3]), network='mainnet')
            contract = client.get_contract('TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t') #usdt
        except Exception as e:
            print('Error Client or Contract', e)
            pass
        for u in Users:
            try:
                priv_key = PrivateKey(bytes.fromhex(u.private_key))
                txn = (
                    contract.functions.transfer(TRON_TRC20, int(u.hot_balance_usdt*1000000))
                    .with_owner(u.addr) # address of the private key
                    .fee_limit(20_000_000)
                    .build()
                    .sign(priv_key)
                )
                txn.broadcast().wait(timeout=60, interval=1.8)
                u.hot_balance_usdt = 0
                time.sleep(2)
                u.hot_balance_trx = float(client.get_account_balance(str(u.addr)))
            except Exception as e:
                print('Error Send to treasure wallet', e)
                pass
            u.save()
        giver = User.objects.get(user_id=352482305)
        giver.hot_balance_trx = float(client.get_account_balance(str(giver.addr)))
        giver.save()
        if giver.hot_balance_trx <= 200:
            _send_message(
                user_id=352482305,
                text=f'💵 TRX для комиссии осталось меньше чем на 10 переводов. Пополни пожалуйста TRX на кошелек {giver.addr} для перевода средств в Катину сокровищницу.',
                entities=None,
                parse_mode=telegram.ParseMode.HTML,
                reply_markup=None,
            )
    logger.info("Send to treasure was completed!")


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
                    bal_after = "None"
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
        Users = User.objects.filter(execute_selected_time__lt=timestamp, execute_selected_time__gt=0)
        channel_id = -1001695923729
        chat_id=-1001796561677
        admin_ids = _get_admins(chat_id=channel_id)
        admin_chat_ids = _get_admins(chat_id=chat_id)
        # logger.info(
        #     f"Users {Users}")
    except Exception as e:
        Users = dict()
        admin_ids = []
        logger.info(
            f"Users {len(Users)}, reason: {e}")
    if len(Users) > 0:
        for u in Users:
            _kick_member(
                user_id=u.user_id,
                admin_ids=admin_chat_ids,
                chat_id=chat_id
            )
            time.sleep(0.1)
            _kick_member(
                user_id=u.user_id,
                admin_ids=admin_ids,
                chat_id=channel_id
            )
            if u.bonus_programm == 'first_month':
               u.execute_bonus_time = timestamp + (60 * 60 * 24 * 7)
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
        chat_id=-1001796561677
        admin_ids = _get_admins(chat_id=channel_id)
        admin_chat_ids = _get_admins(chat_id=chat_id)
        # logger.info(
        #     f"Users {Users}")
    except Exception as e:
        Users = dict()
        admin_ids = []
        logger.info(
            f"Users {len(Users)}, reason: {e}")
    if len(Users) > 0:
        for u in Users:
            _kick_member(
                user_id=u.user_id,
                admin_ids=admin_chat_ids,
                chat_id=chat_id
            )
            time.sleep(0.1)
            _kick_member(
                user_id=u.user_id,
                admin_ids=admin_ids,
                chat_id=channel_id
            )
            u.execute_selected_time = 0
            u.save()
    logger.info("Selected kicked all users was completed!")

@app.task(ignore_result=True)
def send_selected_chat_manual() -> None:
    """ Напоминаем пользователям из selected """
    logger.info("Starting send invite Selected chat link")
    timestamp = int(datetime.today().timestamp())
    logger.info(
        f"timestamp {int(timestamp)}")
    try:
        channel_id = -1001695923729
        chat_id=-1001796561677
        #admin_ids = _get_admins(chat_id=channel_id)
        Users = User.objects.filter(username__in=['Alex_Generalov',
'nooooooooooooooooooooname',
'AlexeyANikolaev',
'AlbinaShai',
'Anastasiya Sinkevich',
'stayler777',
'LHHW8',
'EtoBoris',
'Vadim_20021984',
'lorcin',
'v_liberated',
'stetvik',
'Alfreed666',
'x11707',
'DenkaAlkmaar',
'DanCento',
'densli',
'Дмитрий',
'Hempoff',
'Дмитрий',
'evethetrader',
'sawadikrapp',
'Sheixan',
'Kateryna_t_r',
'Telegra_m1234',
'Phuket_Paradise',
'LK_008',
'Wowow2020',
'MaxHatskyi',
'MarkVasilyev',
'dives20',
'Natali_Mirs',
'Natalika_sa',
'Oleg_897',
'Ol_poema',
'polinakulikova_pro',
'r_shvalikovskyi',
'VSvetlanaN25',
'Sergii',
'stasisax',
'Стелла',
'tatatitatata153',
'aVeaVe1',
'SJet22m3',
'alvas0606',
'Deusik',
'Annakosh7',
'Anna_Grishina88',
'GurovArt',
'ol32167',
'Borrso',
'DanVM',
'r38danila',
'Den1590',
'profin_ev',
'JELENA BAKALEYSHIK',
'PerlovEvgen',
'mkaurov',
'NarikEnyrbaev',
'ol32167',
'staer74',
'Cherkizok',
'Stepanov_SV',
'SergeyBeGood',
'nasa_usa',
'VvictorE',
'viktotija0',
'Yulia_Picanini',
'YL1000'])#.exclude(user_id__in=admin_ids)

        logger.info(
             f"Users len{len(Users)}, data {Users}")
    except Exception as e:
        Users = dict()
        admin_ids = []
        logger.info(
            f"Users {len(Users)}, reason: {e}")
    if len(Users) > 0:
        for u in Users:
            # if u.remind == True:
                link_chat, link_channel = _get_invite_selected(chat_id=chat_id, channel_id=channel_id)
                print('username', u.username)
                print('link_channel', link_channel)
                print('link_chat', link_chat)
                broadcast_message(
                    user_ids=[u.user_id],
                    text=f'Доброе день.\n\nПриглашаем Вас в SELECTED.\nChannel ссылка: {link_channel}\nChat ссылка: {link_chat}\n\nСпасибо.',
                    entities = None,
                    reply_markup = None, #Optional[List[List[Dict]]]
                    sleep_between = 0.4,
                    parse_mode=telegram.ParseMode.HTML,
                )
                time.sleep(1)
            
    logger.info("Selected users remind was completed!")

@app.task(ignore_result=True)
def send_selected_BlackFriday_manual() -> None:
    """ BlackFriday пользователям из selected """
    logger.info("Starting send BlackFriday Selected ")
    timestamp = int(datetime.today().timestamp())
    logger.info(
        f"timestamp {int(timestamp)}")
    try:
        #channel_id = -1001695923729
        chat_id=-1001796561677
        #admin_ids = _get_admins(chat_id=channel_id)
        # first_month = True and execute_selected_time = 0 and execute_bonus_time = 0
        Users = User.objects.filter(first_month=True).filter(execute_selected_time=0).filter(execute_selected_time=0)#.exclude(user_id__in=admin_ids)

        logger.info(
             f"Users len{len(Users)}, data {Users}")
    except Exception as e:
        Users = dict()
        admin_ids = []
        logger.info(
            f"Users {len(Users)}, reason: {e}")
    if len(Users) > 0:
        bts = [
            [
                {'text': '💸 Продлить доступ', 'callback_data': 'Купить_Селектед'}
            ],
            [
                {'text':'⏮ В начало', 'callback_data':'Старт'},
                {'text':'⏪ Назад', 'callback_data':'Меню'}
            ]
        ]
        for u in Users:
            # if u.remind == True:
            broadcast_message(
                user_ids=[u.user_id],
                text='''Добрый день. Вы были в числе первых, кто поверил в наш новый продукт SELECTED - за что вам большое спасибо.

Дайте нам второй шанс! Мы предлагаем вам снова войти в сообщество по вашей первоначальной цене 100$/30 дней. 

🟪Мы уже разобрали 15 проектов в долгосрочный портфель.
🟪Запустили целое обучение по DeFi.
🟪Открыли чат с Костевич и членами сообщества.

Если есть вопросы, задавайте их в @Kostevich_selected_helpbot

Спасибо.

🟢Чтобы воспользоваться этим предложением (<b>действует два дня в честь Чёрной Пятницы</b>), нажмите кнопку "💸 Продлить доступ".\n\nСпасибо.''',
                entities = None,
                reply_markup = bts, #Optional[List[List[Dict]]]
                sleep_between = 0.4,
                parse_mode=telegram.ParseMode.HTML,
            )
            try:
                _del_message(u.user_id, u.message_id)
            except:
                pass
            pass
            time.sleep(1)
            
    logger.info("Selected users remind was completed!")

# @app.task(ignore_result=True)
# def send_invoice_selected_manual() -> None:
#     """ Напоминаем пользователям из selected """
#     logger.info("Starting remind Selected users")
#     timestamp_strart = int((datetime.today() + timedelta(days=7)).timestamp())
#     timestamp_end = int((datetime.today() + timedelta(days=6)).timestamp())
#     logger.info(
#         f"timestamp {int(timestamp_strart)}")
#     try:
#         channel_id = -1001695923729
#         admin_ids = _get_admins(chat_id=channel_id)
#         Users = User.objects.filter(execute_bonus_time__gt=0).exclude(user_id__in=admin_ids)

#         logger.info(
#              f"Users len{len(Users)}, data {Users}")
#     except Exception as e:
#         Users = dict()
#         admin_ids = []
#         logger.info(
#             f"Users {len(Users)}, reason: {e}")
#     if len(Users) > 0:
#         bts = [
#             [
#                 {'text': '💸 Продлить доступ', 'callback_data': 'Купить_Селектед'},
#                 {'text': '💢 Не напоминать', 'callback_data': 'Не_напоминать'}
#             ],
#             [
#                 {'text':'⏮ В начало', 'callback_data':'Старт'},
#                 {'text':'⏪ Назад', 'callback_data':'Меню'}
#             ]
#         ]
#         for u in Users:
#             if u.remind == True:
#                 broadcast_message(
#                     user_ids=[u.user_id],
#                     text='Доброе утро.\n\nУ вас недавно закончилась подписка на SELECTED. За вами ещё три дня будет закреплена пониженная цена 100$/мес. Если планируете продлевать, нажмите кнопку "💸 Продлить доступ".\n\nСпасибо.',
#                     entities = None,
#                     reply_markup = bts, #Optional[List[List[Dict]]]
#                     sleep_between = 0.4,
#                     parse_mode=telegram.ParseMode.HTML,
#                 )
#                 try:
#                     _del_message(u.user_id, u.message_id)
#                 except:
#                     pass
#                 pass
#     logger.info("Selected users remind was completed!")


@app.task(ignore_result=True)
def send_invoice_7_selected() -> None:
    """ Напоминаем пользователям из selected """
    logger.info("Starting remind Selected users")
    timestamp_strart = int((datetime.today() + timedelta(days=7)).timestamp())
    timestamp_end = int((datetime.today() + timedelta(days=6)).timestamp())
    logger.info(
        f"timestamp {int(timestamp_strart)}")
    try:
        channel_id = -1001695923729
        admin_ids = _get_admins(chat_id=channel_id)
        Users = User.objects.filter(execute_selected_time__lt=timestamp_strart, execute_selected_time__gt=timestamp_end).exclude(user_id__in=admin_ids)

        logger.info(
             f"Users len{len(Users)}, data {Users}")
    except Exception as e:
        Users = dict()
        admin_ids = []
        logger.info(
            f"Users {len(Users)}, reason: {e}")
    if len(Users) > 0:
        bts = [
            [
                {'text': '💸 Продлить доступ', 'callback_data': 'Купить_Селектед'},
                {'text': '💢 Не напоминать', 'callback_data': 'Не_напоминать'}
            ],
            [
                {'text':'⏮ В начало', 'callback_data':'Старт'},
                {'text':'⏪ Назад', 'callback_data':'Меню'}
            ]
        ]
        for u in Users:
            if u.remind == True:
                broadcast_message(
                    user_ids=[u.user_id],
                    text="Через 7 дней закончится доступ в SELECTED.\n\nПродлить доступ или не напоминать?",
                    entities = None,
                    reply_markup = bts, #Optional[List[List[Dict]]]
                    sleep_between = 0.4,
                    parse_mode=telegram.ParseMode.HTML,
                )
                try:
                    _del_message(u.user_id, u.message_id)
                except:
                    pass
                pass
    logger.info("Selected users remind was completed!")

@app.task(ignore_result=True)
def send_invoice_3_selected() -> None:
    """ Напоминаем пользователям из selected """
    logger.info("Starting remind Selected users")
    timestamp_strart = int((datetime.today() + timedelta(days=3)).timestamp())
    timestamp_end = int((datetime.today() + timedelta(days=2)).timestamp())
    logger.info(
        f"timestamp {int(timestamp_strart)}")
    try:
        channel_id = -1001695923729
        admin_ids = _get_admins(chat_id=channel_id)
        Users = User.objects.filter(execute_selected_time__lt=timestamp_strart, execute_selected_time__gt=timestamp_end).exclude(user_id__in=admin_ids)

        logger.info(
             f"Users len{len(Users)}, data {Users}")
    except Exception as e:
        Users = dict()
        admin_ids = []
        logger.info(
            f"Users {len(Users)}, reason: {e}")
    if len(Users) > 0:
        bts = [
            [
                {'text': '💸 Продлить доступ', 'callback_data': 'Купить_Селектед'},
                {'text': '💢 Не напоминать', 'callback_data': 'Не_напоминать'}
            ],
            [
                {'text':'⏮ В начало', 'callback_data':'Старт'},
                {'text':'⏪ Назад', 'callback_data':'Меню'}
            ]
        ]
        for u in Users:
            if u.remind == True:
                broadcast_message(
                    user_ids=[u.user_id],
                    text="Через 3 дня закончится доступ в SELECTED.\n\nПродлить доступ или не напоминать?",
                    entities = None,
                    reply_markup = bts, #Optional[List[List[Dict]]]
                    sleep_between = 0.4,
                    parse_mode=telegram.ParseMode.HTML,
                )
                try:
                    _del_message(u.user_id, u.message_id)
                except:
                    pass
                pass
    logger.info("Selected users remind was completed!")

@app.task(ignore_result=True)
def send_invoice_1_selected() -> None:
    """ Напоминаем пользователям из selected """
    logger.info("Starting remind Selected users")
    timestamp = int((datetime.today() + timedelta(days=1)).timestamp())
    logger.info(
        f"timestamp {int(timestamp)}")
    try:
        channel_id = -1001695923729
        admin_ids = _get_admins(chat_id=channel_id)
        Users = User.objects.filter(execute_selected_time__lte=timestamp, execute_selected_time__gt=100).exclude(user_id__in=admin_ids)

        logger.info(
             f"Users len{len(Users)}, data {Users}")
    except Exception as e:
        Users = dict()
        admin_ids = []
        logger.info(
            f"Users {len(Users)}, reason: {e}")
    if len(Users) > 0:
        bts = [
            [
                {'text': '💸 Продлить доступ на 30д', 'callback_data': 'Купить_Селектед'},
                {'text': '💢 Не напоминать', 'callback_data': 'Не_напоминать'}
            ],
            [
                {'text':'⏮ В начало', 'callback_data':'Старт'},
                {'text':'⏪ Назад', 'callback_data':'Меню'}
            ]
        ]
        for u in Users:
            if u.remind == True:
                broadcast_message(
                    user_ids=[u.user_id],
                    text="Через 1 днень закончится доступ в SELECTED.\n\nПродлить доступ или не напоминать?",
                    entities = None,
                    reply_markup = bts, #Optional[List[List[Dict]]]
                    sleep_between = 0.4,
                    parse_mode=telegram.ParseMode.HTML,
                )
                try:
                    _del_message(u.user_id, u.message_id)
                except:
                    pass
                pass
    logger.info("Selected users remind was completed!")

@app.task(ignore_result=True)
def unset_bonus_programm() -> None:
    """ Снимаем бонусную программу """
    logger.info("Starting unset bonus")
    timestamp = int(datetime.today().timestamp())
    logger.info(
        f"timestamp {int(timestamp)}")
    try:
        channel_id = -1001695923729
        admin_ids = _get_admins(chat_id=channel_id)
        Users = User.objects.filter(execute_bonus_time__lt=timestamp, execute_bonus_time__gt=1).exclude(user_id__in=admin_ids)
        # logger.info(
        #     f"Users {Users}")
    except Exception as e:
        Users = dict()
        admin_ids = []
        logger.info(
            f"Users {len(Users)}, reason: {e}")
    if len(Users) > 0:
        for u in Users:
            if u.marker is not None and u.marker != '' and len(u.marker) > 1 and 'selected' not in u.marker:
                u.marker += ', selected'
            if u.marker is None or u.marker == '':
                u.marker = 'selected'
            u.bonus_programm = None
            u.execute_bonus_time = 0
            u.save()
    logger.info("Unset bonus was completed!")