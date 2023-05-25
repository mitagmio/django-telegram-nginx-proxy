start_created = "Sup, {first_name}!"
start_not_created = "Welcome back, {first_name}!"
unlock_secret_room = "Congratulations! You've opened a secret room👁‍🗨. There is some information for you:\n" \
           "<b>Users</b>: {user_count}\n" \
           "<b>24h active</b>: {active_24}"
github_button_text = "GitHub"
secret_level_button_text = "Secret level🗝"
start_button_text = "🎉 Старт"

START_USER = """
Привет, @{username}{text}
Этот Бот поможет сориентироваться в сообществе Екатерина Костевич. 

<i>Мы всегда рады новым людям в команде. Если у вас есть идеи, как вы можете помочь развитию сообщества, пишите!</i>

Твой Telegram id: {tgid}"""
NOT_USER_NAME = """Привет!
{text}Мы не обслуживаем пользователей без username.
Пожалуйста открой настройки профиля и заполни свой уникальный username. ☺️

Твой Telegram id: {tgid}"""

NOT_EMAIL_NAME = """Привет!
{text}Введи пожалуйста email.

Почта потребуется для Академии и отправки полезных уведомлений. ☺️

Твой Telegram id: {tgid}"""

NOT_ADDR_TON = """Привет!
{text}Введи пожалуйста адрес кошелька TON:"""

MENU = """
<b>Kostevich Venture</b> - здесь мы инвестируем в перспективные проекты на ранней стадии. 

<b>Kostevich Academy</b> - обучайтесь вместе с нами, совершенствуйте свои навыки в трейдинге.

<b>Kostevich SELECTED</b> - закрытое сообщество с уникальной аналитикой с выводами и мыслями от меня и моей команды, торговые и инвестиционные идеи и рыночные подсказки.

В сообществе предусмотрена программа лояльности: участвуйте в жизни сообщества, проходите обучающие курсы и получайте баллы, которые можно обменять на подписку.
"""

HELP = """
<b>ПОМОЩЬ</b>
        
"""
SOON = """
<b>СКОРО ...</b>
        
"""

ADMIN_MENU_TEXT = """📝 Администрирование:
выбери необходимый пункт для дальнейших действий

<code>{}</code>
"""

WALLET = """
📨 Почта: {email}

💵 Баланс: {balance} USDT

{text}
"""

WALLET_SUMM = """
На какую сумму в USDT ты хочешь пополнить?

введи сумму цифрой, например 10.6 
"""

WALLET_ADR = """
Пополни адрес кошелька TRC20 
<i>(При нажатии на адрес кошелька или на сумму -  текст копируется)</i>

<code>TYXmiSD7KoLmFyWoPauM2MpXfpS3Z1fsCq</code>

на уникальную сумму 

<code>{summ_float}</code>

это позволит зачислить платеж в твой кошелек в боте.

‼️<b>Внимание</b>‼️ Отправляйте точную сумму до центов иначе ваш платеж может быть не распознан.

Зачисление перевода на баланс происходит в течение 15 минут,
если  платёж оформлен правильно и его сумма полностью(все цифры 
после зяпятой) соответствует сумме, выставленной ботом.

После зачисления платежа тебе придет уведомление в бот.

Если с момента отправки прошло более 15 минут или
вы отправили некорректную сумму, пожалуйста,
пришлите свой Телеграм-ник и TxId транзакции в техподдержку:
@KostevichSupport_Bot

"""

MULTI_WALLET = """
Пополни адрес кошелька TRC20 
<i>(При нажатии на адрес кошелька -  текст копируется)</i>

<code>{addr}</code>

‼️<b>Внимание</b>‼️
Адрес генерируется персонально для каждого участника.

Зачисление перевода на баланс происходит в течение 15-25 минут,
это зависит от скорости обработки транзакций.

После зачисления платежа тебе придет уведомление в бот.

Техподдержка:
@KostevichSupport_Bot
"""

ACADEMY = """
<b><u>Академия трейдинга Екатерины Костевич</u></b> - лучший хаб как для начинающих трейдеров, так и для продвинутых гиков. 

⭐️ Вам доступны курсы любой сложности и на любые темы. 
Каждый курс доступен в 3 форматах: 
    1) для самостоятельного ознакомления 
    2) с поддержкой куратора академии который будет проверять усвоение материала
    3) в сопровождением Автора

🎓 <b>Доступные курсы:</b>

{text}
"""

BUY_COURSE = """
Курс успешно оплачен и на почту {email} отправлена иснтрукция.
"""

NOT_BUY = """
У Вас недостаточно средств. Пополните баланс кошелька на {difference}$ USDT для совершения покупки.
Ваш текущий баланс: {balance}$ USDT

Баланс зачисляется в кошелёк бота в течение 15-25 минут.

Вам придет уведомление от бота о пополнении баланса, после этого вы сможете приобрести интересующий вас продукт.
"""

TEXT_SELECTED = """
Спасибо за интерес, проявленный к Kostevich SELECTED.

Если вы ещё не читали подробное описание проекта, вы можете это сделать ниже, перейдя по кнопке “👩🏼‍🏫О SELECTED"

Стоимость подписки:
🔵30 дней - 200 usdt
🔵90 дней - 300 usdt (Скидка 50%, только до 31 мая)

Для приобретения подписки нажмите соответствующую кнопку «купить…». 

Бот предложит вам сначала пополнить баланс. Спустя 15-20 минут usdt поступят вам на счёт - вы получите об этом сообщение от бота.
После этого вам нужно будет вернуться в меню SELECTED и нажать кнопку «купить» ещё один раз.

В ответном сообщении вам придёт пригласительная ссылка, по которой нужно будет перейти.

Для продления необходимо оплатить подписку до окончания, иначе вам потребуется повторно войти в канал по ссылке.

{end_date}
"""

VENTURE = """
Здесь ты можешь инвестировать вместе с нами в технологичные компании на раннем этапе до того, как это станет доступным остальным пользователям.

В этом месяце мы собираем пулы для следующих проектов:

Metamask (в составе Concensys) - самый популярный в мире некостодиальный цифровой кошелек с более, чем 30млн. пользователей

Переходи по кнопке заинтересовавшего тебя проекта за подробностями и присоединяйся к нашему фонду.

"""
# pre-IPO SpaceX - производитель космической техники, основанный Илоном Маском;

# Kraken - крипто-биржа номер 4 в мире, по версии coinmarketcap;

# TRUE - экосистема для создания NFT токенов нового поколения с одной из лучших команд разработки в мире в данном направлении;
METAMASK_INVEST ="""
Здравствуйте.

Мы в чате инвесторов разместили адреса для участия в аллокации, так как бот существенно усложнял процесс. Обратитесь в чат, пожалуйста. 

Извиняемся за неудобства.

Ссылка на чат: https://t.me/+P_Qj-afmC9Y5MTAy
"""
METAMASK_INVEST_1 = """
Здравствуйте.

Этот бот поможет вам инвестировать в MetaMask. 

Описание проекта и условия сделки находятся у вас в чате с участниками waitlist.

❗️ Для того, чтобы войти в аллокацию, следуйте пунктам:
1. Пополните кошелек бота на необходимую сумму
2. Впишите сумму, которую хотите инвестировать в Metamask (от 5000 USDT)
3. Заполните эту <a href="https://forms.gle/c18kZuLuqrkSP8VA8">гугл-форму</a> (клик) 
4. Напишите в личные сообщения @zhukov_zhukov для добавления вас в чат с инвесторами. 


<i>‼️ Если кошелек в Боте пополнен, можно вписать сумму цифрой и она будет инвестирована в 🦊 Метамаск.</i>

{invest}

<code>{text}</code>
"""
BUY_SELECTED = """
Вы успешно приобрели доступ: 
1) в закрытый новостной канал (ссылка активна 24ч, вступайте сразу): {link_channel}
2) в закрытый чат (ссылка активна 24ч, вступайте сразу): {link_chat}

Доступ предоставлен до
{end_date}.
"""

BUY_SELECTED_TOP_UP = """
Доступ продлен до
{end_date}
"""

WALLET_ADMIN = """
Введи ник пользователя: @trolololo
"""

WALLET_ADMIN_USDT = """
Ник пользователя: {username}
Баланс: {balance}
Выставлен счет на сумму: 
<code>{summ_float}</code>

Введи ник и сумму сумму для зачисления: например @trolololo 10.6
"""

WALLET_ADMIN_FINAL = """
Ник пользователя: {username}
Выставленый счет на сумму: 
<code>{summ_float}</code>

Пополнение от администратора, на сумму:
<code>{summ_admin}</code>,
успешно произведено. Пользователь уведомлен.
"""
