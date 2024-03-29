from typing import Union, Optional, Dict, List

import telegram
from telegram import MessageEntity, InlineKeyboardButton, InlineKeyboardMarkup

from dtb.settings import TELEGRAM_TOKEN
from tgbot.models import User
import time

def _from_celery_markup_to_markup(celery_markup: Optional[List[List[Dict]]]) -> Optional[InlineKeyboardMarkup]:
    markup = None
    if celery_markup:
        print(celery_markup)
        markup = []
        for row_of_buttons in celery_markup:
            print(row_of_buttons)
            row = []
            for button in row_of_buttons:
                print(button)
                print(button['text'])
                print(button.get('callback_data'))
                row.append(
                    InlineKeyboardButton(
                        text=button['text'],
                        callback_data=button.get('callback_data'),
                        url=button.get('url'),
                    )
                )
            markup.append(row)
        markup = InlineKeyboardMarkup(markup)
    return markup


def _from_celery_entities_to_entities(celery_entities: Optional[List[Dict]] = None) -> Optional[List[MessageEntity]]:
    entities = None
    if celery_entities:
        entities = [
            MessageEntity(
                type=entity['type'],
                offset=entity['offset'],
                length=entity['length'],
                url=entity.get('url'),
                language=entity.get('language'),
            )
            for entity in celery_entities
        ]
    return entities


def _send_message(
    user_id: Union[str, int],
    text: str,
    parse_mode: Optional[str] = telegram.ParseMode.HTML,
    reply_markup: Optional[List[List[Dict]]] = None,
    reply_to_message_id: Optional[int] = None,
    disable_web_page_preview: Optional[bool] = None,
    entities: Optional[List[MessageEntity]] = None,
    tg_token: str = TELEGRAM_TOKEN,
) -> bool:
    bot = telegram.Bot(tg_token)
    try:
        m = bot.send_message(
            chat_id=user_id,
            text=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
            reply_to_message_id=reply_to_message_id,
            disable_web_page_preview=disable_web_page_preview,
            entities=entities,
        )
    except telegram.error.Unauthorized:
        print(f"Can't send message to {user_id}. Reason: Bot was stopped.")
        User.objects.filter(user_id=user_id).update(is_blocked_bot=True)
        success = False
    else:
        success = True
        User.objects.filter(user_id=user_id).update(is_blocked_bot=False)
    return success


def _del_message(
    chat_id: Union[str, int],
    message_id: Optional[int],
    tg_token: str = TELEGRAM_TOKEN,
) -> bool:
    bot = telegram.Bot(tg_token)
    try:
        m = bot.delete_message(
            chat_id=chat_id, message_id=message_id)
    except telegram.error.Unauthorized:
        print(f"Can't delete message to {chat_id} and message {message_id}.")
        success = False
    finally:
        success = True
    return success

def _get_admins(
    chat_id: Union[str, int],
    tg_token: str = TELEGRAM_TOKEN,
) -> List[Union[str, int]]:
    bot = telegram.Bot(tg_token)
    try:
        admins = bot.get_chat_administrators(chat_id=chat_id)
    except telegram.error.Unauthorized:
        print(f"Can't get admins from {chat_id}")
        success = []
    finally:
        success = []
        for a in admins:
            success.append(a.user.id)
    return success

def _get_invite_selected(
    chat_id: Union[str, int],
    channel_id: Union[str, int],
    tg_token: str = TELEGRAM_TOKEN,
) -> tuple:
    bot = telegram.Bot(tg_token)
    try:
        timestamp = time.time()
        link_chat = bot.create_chat_invite_link(chat_id=chat_id, expire_date=timestamp + 60 * 60 * 24 * 3, member_limit=1).invite_link
        link_channel = bot.create_chat_invite_link(chat_id=channel_id, expire_date=timestamp + 60 * 60 * 24 * 3, member_limit=1).invite_link
    except telegram.error.Unauthorized:
        print(f"Can't get admins from {chat_id}")
        link_chat = ''
        link_channel = ''
    return link_chat, link_channel

def _kick_member(
    chat_id: Union[str, int],
    user_id: Union[str, int],
    admin_ids: List[Union[str, int]],
    tg_token: str = TELEGRAM_TOKEN,
) -> bool:
    bot = telegram.Bot(tg_token)
    try:
        admin = False
        for a in admin_ids:
            if a == user_id:
                admin = True
        if admin == False:
            check_in_user = bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            # print(f"check from {chat_id} member {user_id}.\n {check_in_user}")
            if hasattr(check_in_user, 'status') and (check_in_user.status == 'member'):# 'left' 'member' 'kicked'
                time.sleep(0.1)
                print(f"kicked from {chat_id} member {user_id}.\n {check_in_user}")
                m = bot.unban_chat_member(chat_id=chat_id, user_id=user_id)
    except telegram.error.Unauthorized:
        print(f"Can't kicked from {chat_id} member {user_id}.")
        success = False
    finally:
        success = True
    return success
