from functools import wraps
from typing import Dict, Callable

import telegram
from telegram import Update

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