from __future__ import annotations

from typing import List, Union, Optional, Tuple, Dict
import hmac
import time
import hashlib
import requests
from requests.structures import CaseInsensitiveDict
from urllib.parse import urlencode
from datetime import datetime

from django.db import models
from django.db.models import QuerySet, Manager
from telegram import Update
from telegram.ext import CallbackContext

from dtb.settings import BINANCE_API, BINANCE_SECRET, DEBUG
from tgbot.handlers.utils.info import extract_user_data_from_update
from utils.models import CreateUpdateTracker, nb, CreateTracker, GetOrNoneManager


class AdminUserManager(Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_admin=True)


class P2p(CreateTracker):
    timestamp = models.PositiveBigIntegerField(primary_key=True)
    date_time = models.DateTimeField(null=False, auto_now=False)
    usdt_lkr = models.FloatField(default=0)
    uah_usdt = models.FloatField(default=0)
    eur_revolut_usdt = models.FloatField(default=0)
    rub_tinkoff_usdt = models.FloatField(default=0)
    usd_tinkoff_usdt = models.FloatField(default=0)
    kzt_usdt = models.FloatField(default=0)

    @classmethod
    def from_json(cls, p2p_rub_usdt_json: Dict, p2p_usdt_lkr_json: Dict, p2p_uah_usdt_json: Dict, p2p_eur_usdt_json: Dict, p2p_usd_usdt_json: Dict, p2p_kzt_usdt_json: Dict):
        rub_usdt = p2p_rub_usdt_json.get("data")
        usdt_lkr = p2p_usdt_lkr_json.get("data")
        uah_usdt = p2p_uah_usdt_json.get("data")
        eur_usdt = p2p_eur_usdt_json.get("data")
        usd_usdt = p2p_usd_usdt_json.get("data")
        kzt_usdt = p2p_kzt_usdt_json.get("data")
        # if "data" not in p2p_rub_usdt_json or rub_usdt == None:
        #     return

        # if "data" not in p2p_usdt_lkr_json or usdt_lkr == None:
        #     return

        # if "data" not in p2p_uah_usdt_json or uah_usdt == None:
        #     return

        # if "data" not in p2p_eur_usdt_json or eur_usdt == None:
        #     return

        # if "data" not in p2p_usd_usdt_json or usd_usdt == None:
        #     return

        summ = 0
        for element in rub_usdt:
            summ += float(element['adv']['price'])
        rub_usdt_price = round(summ / len(rub_usdt), 2)

        summ = 0
        for element in usdt_lkr:
            summ += float(element['adv']['price'])
        usdt_lkr_price = round(summ / len(usdt_lkr), 2)

        summ = 0
        for element in uah_usdt:
            summ += float(element['adv']['price'])
        uah_usdt_price = round(summ / len(uah_usdt), 2)

        summ = 0
        for element in eur_usdt:
            summ += float(element['adv']['price'])
        eur_usdt_price = round(summ / len(eur_usdt), 2)

        summ = 0
        for element in usd_usdt:
            summ += float(element['adv']['price'])
        usd_usdt_price = round(summ / len(usd_usdt), 2)

        summ = 0
        for element in kzt_usdt:
            summ += float(element['adv']['price'])
        kzt_usdt_price = round(summ / len(kzt_usdt), 2)

        timestamp = int(datetime.today().timestamp()) + (60*60*5.5)
        dt_obj = datetime.fromtimestamp(timestamp)

        p2p_obj = {
            "date_time": dt_obj,
            "usdt_lkr": usdt_lkr_price,
            "uah_usdt": uah_usdt_price,
            "eur_revolut_usdt": eur_usdt_price,
            "rub_tinkoff_usdt": rub_usdt_price,
            "usd_tinkoff_usdt": usd_usdt_price,
            "kzt_usdt": kzt_usdt_price,
        }

        p2p, _ = cls.objects.update_or_create(
            timestamp=timestamp, defaults=p2p_obj)
        print(p2p, _)
        return

    @staticmethod
    def get_course(pay_types: str, trade_type: str, fiat: str) -> Dict:
        url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
        headers = CaseInsensitiveDict()
        headers["Content-type"] = "application/json"
        data = f'{{"page":2,"rows":5,"payTypes":{pay_types},"publisherType":null,"asset":"USDT","tradeType":{trade_type},"fiat":{fiat},"merchantCheck":false}}'
        r = requests.post(url, headers=headers, data=data)
        print(f"status code = {r.status_code}")
        return r.json()

    @staticmethod
    # https://github.com/binance/binance-signature-examples/blob/f5d4a6869c24d8bf08f58daacee3fb2bb5299587/python/spot/spot.py#L40
    def pay_trade_history() -> Dict:
        base_url = "https://api.binance.com"
        url_path = "/sapi/v1/pay/transactions"
        timestamp = int(time.time() * 1000)
        query_string = urlencode({}, True)
        if query_string:
            query_string = "{}&timestamp={}".format(query_string, timestamp)
        else:
            query_string = "timestamp={}".format(timestamp)
        signature = hmac.new(
            BINANCE_SECRET.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        url = (
            base_url + url_path + "?" + query_string + "&signature=" + signature
        )
        params = {"url": url, "params": {}}
        session = requests.Session()
        session.headers.update(
            {"Content-Type": "application/json;charset=utf-8",
                "X-MBX-APIKEY": BINANCE_API}
        )
        print(url)
        r = session.get(**params)
        print(f"status code = {r.status_code}")
        return r.json()


class Cities(models.Model):
    name = models.CharField(max_length=32, **nb)
    ru_name = models.CharField(max_length=32, **nb)

    @classmethod
    def get_dict(cls) -> Dict:
        cities = list(cls.objects.all().values('id', 'ru_name'))
        dict_cities = {}
        for el in cities:
            dict_cities[el['ru_name']] = el['id']
        return dict_cities

    @classmethod
    def get_obj(cls) -> List:
        cities = cls.objects.all().values('id', 'name', 'ru_name').order_by('ru_name')
        return list(cities)


class Pairs(models.Model):
    pair = models.CharField(max_length=100, **nb)
    ru_pair = models.CharField(max_length=100, **nb)
    convert = models.CharField(max_length=32, **nb)

    @classmethod
    def get_dict(cls) -> Dict:
        pairs = list(cls.objects.all().values('id', 'pair', 'ru_pair'))
        dict_pairs = {}
        for el in pairs:
            dict_pairs[el['pair']] = el['ru_pair']
        return dict_pairs

    @classmethod
    def get_convert_dict(cls) -> Dict:
        pairs = list(cls.objects.all().values('id', 'pair', 'convert'))
        dict_pairs = {}
        for el in pairs:
            dict_pairs[el['pair']] = el['convert']
        return dict_pairs

    @classmethod
    def get_obj(cls) -> List:
        pairs = cls.objects.all().values('id', 'pair', 'ru_pair').order_by('id')
        return list(pairs)


class Periods(models.Model):
    period = models.CharField(max_length=100, **nb)
    ru_period = models.CharField(max_length=100, **nb)

    @classmethod
    def get_dict(cls) -> Dict:
        periods = list(cls.objects.all().values('id', 'period', 'ru_period'))
        dict_periods = {}
        for el in periods:
            dict_periods[el['period']] = el['ru_period']
        return dict_periods

    @classmethod
    def get_obj(cls) -> List:
        periods = cls.objects.all().values('id', 'period', 'ru_period')
        return list(periods)


class Terms(models.Model):
    terms_of_use_user = models.TextField(blank=True, null=True)
    terms_of_use_merchant = models.TextField(blank=True, null=True)
    size_fee = models.FloatField(default=0)
    filter_order_size_adminig = models.FloatField(default=300)
    last_time_payment = models.PositiveBigIntegerField(default=1651688047000)

    @classmethod
    def get_dict(cls) -> Dict:
        terms = list(cls.objects.all().values(
            'terms_of_use_user', 'terms_of_use_merchant', 'size_fee', 'filter_order_size_adminig', 'last_time_payment'))
        dict_terms = {}
        for el in terms:
            dict_terms['terms_of_use_user'] = el['terms_of_use_user']
            dict_terms['terms_of_use_merchant'] = el['terms_of_use_merchant']
            dict_terms['size_fee'] = el['size_fee']
            dict_terms['filter_order_size_adminig'] = el['filter_order_size_adminig']
            dict_terms['last_time_payment'] = el['last_time_payment']
        return dict_terms

    @classmethod
    def get_obj(cls) -> List:
        periods = cls.objects.all().values('terms_of_use_user', 'terms_of_use_merchant')
        return list(periods)


class User(CreateUpdateTracker):
    user_id = models.PositiveBigIntegerField(primary_key=True)  # telegram_id
    username = models.CharField(max_length=32, **nb)
    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256, **nb)
    language_code = models.CharField(
        max_length=8, help_text="Telegram client's lang", **nb)
    deep_link = models.CharField(max_length=64, **nb)
    state = models.CharField(max_length=32, default='0')
    orders_client = models.CharField(max_length=32, default='None')
    merchant_client = models.CharField(max_length=32, default='None')
    merchant_status = models.CharField(max_length=32, default='pause')
    city = models.CharField(max_length=32, **nb)
    type_pair = models.CharField(max_length=32, **nb)
    pair = models.CharField(max_length=32, **nb)
    summ = models.FloatField(default=0)
    period = models.CharField(max_length=32, **nb)
    transfer = models.CharField(max_length=256, **nb)
    merchant_delivery = models.CharField(
        max_length=256, default='🛻 Доставка: Самовывозом')
    message_id = models.PositiveBigIntegerField(default=0)
    count_client_order = models.PositiveBigIntegerField(default=0)
    count_client_order_success = models.PositiveBigIntegerField(default=0)
    count_merchant_order = models.PositiveBigIntegerField(default=0)
    count_merchant_order_success = models.PositiveBigIntegerField(default=0)
    ref_id = models.PositiveBigIntegerField(default=0)

    is_blocked_bot = models.BooleanField(default=False)

    is_admin = models.BooleanField(default=False)

    objects = GetOrNoneManager()  # user = User.objects.get_or_none(user_id=<some_id>)
    admins = AdminUserManager()  # User.admins.all()

    def __str__(self):
        return f'@{self.username}' if self.username is not None else f'{self.user_id}'

    @classmethod
    def get_user_and_created(cls, update: Update, context: CallbackContext) -> Tuple[User, bool]:
        """ python-telegram-bot's Update, Context --> User instance """
        data = extract_user_data_from_update(update)
        u, created = cls.objects.update_or_create(
            user_id=data["user_id"], defaults=data)

        if created:
            # Save deep_link to User model
            if context is not None and context.args is not None and len(context.args) > 0:
                payload = context.args[0]
                # you can't invite yourself
                if str(payload).strip() != str(data["user_id"]).strip():
                    u.deep_link = payload
                    u.save()

        return u, created

    @classmethod
    def get_user_state(cls, update: Update, context: CallbackContext) -> str:
        u, _ = cls.get_user_and_created(update, context)
        return u.state

    @classmethod
    def set_user_state(cls, update: Update, context: CallbackContext, state) -> str:
        u, _ = cls.get_user_and_created(update, context)
        u.state = state
        u.save()
        return

    @classmethod
    def set_period(cls, update: Update, context: CallbackContext, period) -> str:
        u, _ = cls.get_user_and_created(update, context)
        u.period = period
        u.save()
        return

    @classmethod
    def set_city(cls, update: Update, context: CallbackContext, city) -> str:
        u, _ = cls.get_user_and_created(update, context)
        u.city = city
        u.save()
        return

    @classmethod
    def set_type_pair(cls, update: Update, context: CallbackContext, type_pair) -> str:
        u, _ = cls.get_user_and_created(update, context)
        u.type_pair = type_pair
        u.save()
        return

    @classmethod
    def set_pair(cls, update: Update, context: CallbackContext, pair) -> str:
        u, _ = cls.get_user_and_created(update, context)
        u.pair = pair
        u.save()
        return

    @classmethod
    def set_summ(cls, update: Update, context: CallbackContext, summ) -> str:
        u, _ = cls.get_user_and_created(update, context)
        u.summ = summ
        u.save()
        return

    @classmethod
    def set_orders_client(cls, update: Update, context: CallbackContext, orders_client) -> str:
        u, _ = cls.get_user_and_created(update, context)
        u.orders_client = orders_client
        u.save()
        return

    @classmethod
    def set_merchant_client(cls, update: Update, context: CallbackContext, merchant_client) -> str:
        u, _ = cls.get_user_and_created(update, context)
        u.merchant_client = merchant_client
        u.save()
        return

    @classmethod
    def set_message_id(cls, update: Update, context: CallbackContext, message_id) -> str:
        u, _ = cls.get_user_and_created(update, context)
        u.message_id = message_id
        u.save()
        return

    @classmethod
    def get_user(cls, update: Update, context: CallbackContext) -> User:
        u, _ = cls.get_user_and_created(update, context)
        return u

    @classmethod
    def get_user_by_username_or_user_id(cls, username_or_user_id: Union[str, int]) -> Optional[User]:
        """ Search user in DB, return User or None if not found """
        username = str(username_or_user_id).replace("@", "").strip().lower()
        if username.isdigit():  # user_id
            return cls.objects.filter(user_id=int(username)).first()
        return cls.objects.filter(username__iexact=username).first()

    @property
    def invited_users(self) -> QuerySet[User]:
        return User.objects.filter(deep_link=str(self.user_id), created_at__gt=self.created_at)

    @property
    def tg_str(self) -> str:
        if self.username:
            return f'@{self.username}'
        return f"{self.first_name} {self.last_name}" if self.last_name else f"{self.first_name}"


class Invoice (models.Model):
    summ_invoice = models.FloatField(primary_key=True)
    payer_id = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='payer_id_invoice_set')

    @staticmethod
    def get_payment(min_timestamp: int) -> Dict:
        url = "https://api.trongrid.io/v1/accounts/TXBXgpaM5jCXVq45m8UNTuJaA4oJkSUQbY/transactions/trc20?limit=20&contract_address=TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t&only_confirmed=true&min_timestamp={}".format(
            min_timestamp)
        headers = CaseInsensitiveDict()
        headers["Content-type"] = "application/json"
        r = requests.get(url, headers=headers)
        print(f"status code = {r.status_code}")
        return r.json()


class Order(CreateUpdateTracker):
    client_id = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='client_id_order_set')
    city = models.CharField(max_length=32, **nb)
    pair = models.CharField(max_length=32, **nb)
    summ = models.FloatField(default=0)
    period = models.CharField(max_length=32, **nb)
    transfer = models.CharField(max_length=256, **nb)
    timestamp_execut = models.PositiveBigIntegerField()
    date_time_execut = models.DateTimeField(null=False, auto_now=False)
    merchant_executor_id = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='merchant_executor_id_order_set', **nb)
    order_fee = models.FloatField(default=0)
    status = models.CharField(max_length=32, **nb)
    status_fee = models.CharField(max_length=32, default='not_paid')

    @classmethod
    def get_obj(cls) -> List:
        pairs = cls.objects.all()
        return list(pairs)


class Suggestion(CreateUpdateTracker):
    order_id = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='order_id_suggestion_set')
    merchant_executor_id = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='merchant_executor_id_suggestion_set', **nb)
    summ = models.FloatField(default=0)


class Rating(CreateUpdateTracker):
    who_id = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='who_id_rating_set')
    whom_id = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='whom_id_rating_set')
    rank = models.IntegerField(blank=False, null=True)
    comment = models.TextField(**nb)


class MerchantsCities(models.Model):
    merchant_id = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='merchant_id_cities_set', **nb)
    city_id = models.ForeignKey(
        Cities, on_delete=models.CASCADE, related_name='city_merchant_ids_set', **nb)

    @classmethod
    def get_obj(cls) -> List:
        cities = cls.objects.all().values('id', 'merchant_id', 'city_id')
        return list(cities)


class Location(CreateTracker):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    latitude = models.FloatField()
    longitude = models.FloatField()

    objects = GetOrNoneManager()

    def __str__(self):
        return f"user: {self.user}, created at {self.created_at.strftime('(%H:%M, %d %B %Y)')}"

    def save(self, *args, **kwargs):
        super(Location, self).save(*args, **kwargs)
        # Parse location with arcgis
        from arcgis.tasks import save_data_from_arcgis
        if DEBUG:
            save_data_from_arcgis(latitude=self.latitude,
                                  longitude=self.longitude, location_id=self.pk)
        else:
            save_data_from_arcgis.delay(
                latitude=self.latitude, longitude=self.longitude, location_id=self.pk)
