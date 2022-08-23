from functools import wraps
from typing import Dict, Callable

import telegram
from telegram import Update

import base58
import ecdsa
import random
from Crypto.Hash import keccak

from io import BytesIO
import qrcode
from PIL import Image

def generate_qr(text: str, logo: str = 'dtb/media/tether-usdt-trc20.png'):
    # taking image which user wants 
    # in the QR code center
    Logo_link = logo
    logo = Image.open(Logo_link)
 
    # taking base width

    basewidth = 100
    
    # adjust image size

    wpercent = (basewidth/float(logo.size[0]))

    hsize = int((float(logo.size[1])*float(wpercent)))

    logo = logo.resize((basewidth, hsize), Image.ANTIALIAS)

    QRcode = qrcode.QRCode(

        error_correction=qrcode.constants.ERROR_CORRECT_H
    )
    
    # taking url or text

    text_to_qr = text
    
    # adding URL or text to QRcode
    QRcode.add_data(text_to_qr)
    
    # generating QR code
    QRcode.make()
    
    # taking color name from user

    QRcolor = 'Black'
    
    # adding color to QR code

    QRimg = QRcode.make_image(

        fill_color=QRcolor, back_color="white").convert('RGB')
    
    # set size of QR code

    pos = ((QRimg.size[0] - logo.size[0]) // 2,

        (QRimg.size[1] - logo.size[1]) // 2)
    QRimg.paste(logo, pos)
    
    # save the QR code generated

    #QRimg.save('gfg_QR.png')

    # return bytes image
    data = BytesIO()
    QRimg.save(data, "PNG")
    return data

def keccak256(data):
    hasher = keccak.new(digest_bits=256)
    hasher.update(data)
    return hasher.digest()


def get_signing_key(raw_priv):
    return ecdsa.SigningKey.from_string(raw_priv, curve=ecdsa.SECP256k1)


def verifying_key_to_addr(key):
    pub_key = key.to_string()
    primitive_addr = b'\x41' + keccak256(pub_key)[-20:]
    # 0 (zero), O (capital o), I (capital i) and l (lower case L)
    addr = base58.b58encode_check(primitive_addr)
    return addr


def gen_addr_priv():
    raw = bytes(random.sample(range(0, 256), 32))
    # raw = bytes.fromhex('a0a7acc6256c3..........b9d7ec23e0e01598d152')
    key = get_signing_key(raw)
    addr = verifying_key_to_addr(key.get_verifying_key()).decode()
    addr_hex = base58.b58decode_check(addr.encode()).hex()
    public_key = key.get_verifying_key().to_string().hex()
    private_key = raw.hex()

    return addr, addr_hex, public_key, private_key
    

def send_typing_action(func: Callable):
    """Sends typing action while processing func command."""
    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=telegram.ChatAction.TYPING)
        return func(update, context,  *args, **kwargs)

    return command_func


def extract_user_data_from_update(update: Update) -> Dict:
    """ python-telegram-bot's Update instance --> User info """
    if update.message is not None:
        user = update.message.from_user.to_dict()
    elif update.inline_query is not None:
        user = update.inline_query.from_user.to_dict()
    elif update.chosen_inline_result is not None:
        user = update.chosen_inline_result.from_user.to_dict()
    elif update.callback_query is not None and update.callback_query.from_user is not None:
        user = update.callback_query.from_user.to_dict()
    elif update.callback_query is not None and update.callback_query.message is not None:
        user = update.callback_query.message.chat.to_dict()
    else:
        raise Exception(f"Can't extract user data from update: {update}")

    return dict(
        user_id=user["id"],
        is_blocked_bot=False,
        **{
            k: user[k]
            for k in ["username", "first_name", "last_name", "language_code"]
            if k in user and user[k] is not None
        },
    )