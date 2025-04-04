import nest_asyncio
import asyncio
import logging
import random
import re
from datetime import datetime, timezone, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from urllib.parse import urlparse
from telegram import CopyTextButton
import sqlite3
import pytz

nest_asyncio.apply()

API_TOKEN = '7705193251:AAFrnXeNBgiFo3ZQsGNvEOa2lNzQPKo3XHM'
ADMIN_CHAT_ID = -1002651165474
USER_CHAT_ID = 5283100992
LOG_CHAT_ID = -1002411396364
ALLOWED_USERS = [5283100992, 6340673182, 5344318601, 1552417677, 1385118926, 6139706645, 5222780613]
GROUP_ID = -1002268486160
LOG_CHAT_ID = -4665694960

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(API_TOKEN)
app = Application.builder().token(API_TOKEN).build()

# Храним уже подтверждённые репорты
confirmed_reports = set()

# Возможные ответы на "РаФа"
rafa_responses = [
    "<b>Blue_Nexus иногда стает ебланом</b>", 
    "<b>Blue_Nexus держат в рабстве</b>",  
    "<b>Blue_Nexus абажает чат гпт</b>",
    "<b>Кирич любит аниме-тянок... но в жизни девушек он не любит</b>", 
    "<b>Изначально Кирич создавал канал про свою жизнь</b>", 
    "<b>Кирич невнимательный</b>",
    "<b>IDC - очень занятый человек... не спрашивайте чем, зачем и почему</b>", 
    "<b>IDC любит скамить детей на петов в адопт ми</b>", 
    "<b>IDC... я не придумал что он делает</b>",
    "<b>Freezee - успех успешный</b>", 
    "<b>Freezee - антипацифист☮</b>", 
    "<b>Freezee похуист по жизни</b>",
    "<b>Vipsii - долбаеб</b>", 
    "<b>Vipsii слишком глупый</b>", 
    "<b>Третий факт про себя Vipsii забыл</b>", 
    "<b>Exponnentik - повелитель чая</b>", 
    "<b>Exponnentik держит чери в заложниках</b>", 
    "<b>Exponnentik главный пупс кирича(кирич этого не знает)</b>",
    "<b>РаФа - сокращенно Рандом Факт про Андминов</b>"
]
  
# Возможные ответы для "РаФу"
rafu_responses = [
    "<b>Интересный факт! SsVladiSlaveSs не знает этот факт</b>", 
    "<b>На самом деле @khvtg не только отличный игрок, хороший администратор, щедрый согильдиец и крутой дизайнер – он еще и невероятно скромная личность</b>", 
    "<b>#Хаюш#Бой.#твикат#Not Хочет умереть от своей души</b>",
    "<b>Бомбабот на самом деле не бот🙈</b>",
    "<b>О пушочке: 11 лет, гей, ищет жену</b>",
    "<b>Ниндзя - майнкрафтер</b>",
    "<b>Тихий_Сон пытается найти мираж остров и на нем шестеренку для в4 рас в блокс фрукт</b>",
    "<b>Vloger про себя: я студент и очень тащус по аниме тянкам но в риле девушек боюсь</b>",
    "<b>StrazhTellOffichal Очень любит Юни, что он даже создал свой культ по своей любимой кошке Uni Cat</b>",
    "<b>Mapc - невероятный Python-айтишник с большим стажом валяния на кровати... накормите его пожалуйста</b>",
    "<b>Интересный факт: вся вселенная — это подвал, владелец которого — danyagreench.</b>",
    "<b>Интересный факт, SsVladiSlaveSs это SsVladiSlaveSs</b>",
    "<b>Александр любит котиков</b>",
    "<b>Просто чел - гей</b>",
    "<b>Кот ананас стал ананасом когда на его голову свалился ананас</b>",
    "<b>🐍ɥɥƎ очень боится собак</b>",
    "<b>У Люцика сегодня экзамен</b>",
    "<b>РаФу - сокращенно РАндом Факт про Участников</b>"
]

# Регулярное выражение для проверки формата причины репорта (например, "П1.3", "п1.3")
REPORT_REASON_REGEX = re.compile(r"^п\d+\.\d+$", re.IGNORECASE)

DB_PATH = "database.db"  # Файл бази даних SQLite

def create_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Створення таблиці з усіма необхідними стовпцями
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message_id INTEGER,
            report_text TEXT,
            report_time TEXT,
            reporter_name TEXT,
            reported_name TEXT,
            message_link TEXT
        )
    ''')
    
    conn.commit()
    cursor.close()
    conn.close()

create_db()

async def show_reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id  # Отримуємо ID користувача

    if user_id not in ALLOWED_USERS:  # Перевіряємо, чи є користувач у списку дозволених
        await update.message.reply_text("У вас нету доступа к этой команде.")
        return

    reports = get_reports()

    if reports:
        report_message = ""
        for r in reports:
            if len(r) >= 8:  # Перевіряємо, що є достатньо елементів
                report_message += f"Репорт {r[0]}:\nПричина: {r[3]}\nВремя: {r[4]}\nТот кто кинул репорт: {r[5]}\nТот на кого кинули репорт: {r[6]}\nСсылка: {r[7]}\n\n"
            else:
                report_message += f"Репорт {r[0]} имеет недостаточно даных.\n\n"
    else:
        report_message = "Нету репортов."

    # Відправка повідомлення без попереднього перегляду веб-сторінок
    await update.message.reply_text(report_message, disable_web_page_preview=True)

def get_reports():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reports")  # Извлекаем все столбцы
    reports = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return reports

# Функция отправки логов в группу
async def log_action(text: str):
    try:
        await bot.send_message(LOG_CHAT_ID, text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Ошибка при отправке лога: {e}")

# Функция старта
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Напиши /report в ответ на сообщение, чтобы отправить репорт.")

# Функция для сохранения репорта в SQLite
moscow_tz = pytz.timezone('Europe/Moscow')

def save_report(user_id, message_id, reason, reporter_name, reported_name, message_link):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Отримуємо поточний час у МСК
    report_time = datetime.now(moscow_tz).strftime('%Y-%m-%d %H:%M:%S')
    
    # Вставляємо новий репорт з усіма даними
    cur.execute('''
        INSERT INTO reports (user_id, message_id, report_text, report_time, reporter_name, reported_name, message_link) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, message_id, reason, report_time, reporter_name, reported_name, message_link))
    
    conn.commit()
    cur.close()
    conn.close()

# Функция репорта
async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text(
            "⚠️ <b>Репорт можно отправить только <i>ответом на сообщение</i>!</b>\n\n"
            "Пример репорта: <code>/report П1.3</code>",
            parse_mode=ParseMode.HTML
        )
        return

    if not context.args:
        await update.message.reply_text(
            "⚠️ <b>Не указана причина репорта!</b>\n\n"
            "Пример репорта: <code>/report П1.3</code>",
            parse_mode=ParseMode.HTML
        )
        return

    reason = context.args[0]
    if not REPORT_REASON_REGEX.match(reason):
        await update.message.reply_text(
            "⚠️ <b>Неверный формат причины!</b>\n\n"
            "Пример правильного формата: <code>/report П1.3</code>",
            parse_mode=ParseMode.HTML
        )
        return

    message_id = update.message.reply_to_message.message_id
    user_id = update.message.from_user.id
    report_key = f"{user_id}_{message_id}"
    reporter_name = update.message.from_user.full_name
    reported_name = update.message.reply_to_message.from_user.full_name
    message_link = f"https://t.me/{update.message.chat.username}/{message_id}"
    report_time = update.message.date
    reported_text = update.message.reply_to_message.text
    report_date = update.message.date

    if report_key in confirmed_reports:
        await update.message.reply_text("⚠️ Этот репорт уже был подтверждён!")
        return

    keyboard = [[
        InlineKeyboardButton("✅ Да", callback_data=f"confirm_{user_id}_{message_id}"),
        InlineKeyboardButton("❌ Нет", callback_data=f"cancel_{user_id}_{message_id}")
    ]] 

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"Вы уверены, что хотите отправить репорт с причиной <b>{reason}</b>?",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )
    
    # Сохранение репорта в базу
    await log_action(f"📌 Репорт отправил {update.message.from_user.full_name} ({user_id}) с причиной {reason}")
    save_report(user_id, message_id, reason, update.message.from_user.full_name, update.message.reply_to_message.from_user.full_name, f"https://t.me/{update.message.chat.username}/{message_id}")# Функция обработки репорта

async def handle_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    data = query.data.split("_")
    if len(data) < 3:
        await query.message.edit_text("❌ Ошибка: неправильный формат данных!")
        return

    action = data[0]
    try:
        user_id = int(data[1])
        message_id = int(data[2])
    except ValueError:
        await query.message.edit_text("❌ Ошибка: неверные данные для обработки репорта!")
        return

    if query.from_user.id != user_id:
        await query.answer(text="❌ Нельзя жмякать чужие репорты!", show_alert=True)
        return

    report_key = f"{user_id}_{message_id}"
    if report_key in confirmed_reports:
        await query.answer(text="⚠️ Этот репорт уже был обработан!", show_alert=True)
        return

    if action == "confirm":
        reported_message = query.message.reply_to_message
        reported_user = reported_message.from_user

        if query.message.chat.username:
            message_link = f"https://t.me/{query.message.chat.username}/{reported_message.message_id}"
            link_text = f"<a href='{message_link}'>Перейти к сообщению</a>"
        else:
            link_text = "Сообщение отправлено в приватном чате, ссылка недоступна."

        message_text = reported_message.text if reported_message.text else "(медиа-файл)"
        reported_user_mention = f"<b>{reported_user.full_name}</b> (@{reported_user.username})"

        report_text = (
            f"<blockquote>⚠️ <b>Новый репорт!</b>\n\n"
            f"👤 <b>Пользователь:</b> {reported_user_mention}\n"
            f"💬 <b>Сообщение:</b>\n<blockquote>{message_text}</blockquote>\n</blockquote>"
            f"🔗 <b>Ссылка:</b> {link_text}"
        )

        await query.message.edit_text("⏳Отправка...")

        # Получаем администраторов
        admins = await bot.get_chat_administrators(ADMIN_CHAT_ID)
        admin_mentions = [f"@{admin.user.username}" for admin in admins if admin.user.username]

        await bot.send_message(
            ADMIN_CHAT_ID, report_text,
            parse_mode=ParseMode.HTML,
            protect_content=True,
            disable_web_page_preview=True
        )

        if admin_mentions:
            half = len(admin_mentions) // 2
            await asyncio.sleep(4)
            await bot.send_message(ADMIN_CHAT_ID, "Первая часть админов: " + " ".join(admin_mentions[:half]))
            await asyncio.sleep(4)
            await bot.send_message(ADMIN_CHAT_ID, "Вторая часть админов: " + " ".join(admin_mentions[half:]))

        confirmed_reports.add(report_key)
        await query.message.edit_text("✅Репорт успешно отправлен!")
        await log_action(f"✅ Репорт подтверждён пользователем {query.from_user.full_name} ({query.from_user.id})")
    elif action == "cancel":
        await query.message.edit_text("❌ Репорт отменен.")
        await log_action(f"❌ Репорт отменён пользователем {query.from_user.full_name} ({query.from_user.id})")

# Функция обработки пинга администраторов
async def handle_ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split("_")
    
    if len(data) < 3:
        await query.message.edit_text("❌ Ошибка: неправильный формат данных!")
        return

    action = data[0]  # Действие: ping

    if len(data) == 3:
        ping_answer = data[2]
        
        if ping_answer == "yes":
            await query.message.edit_text("⏳ Отправка репорта...")

            # Получаем администраторов
            admins = await bot.get_chat_administrators(ADMIN_CHAT_ID)
            admin_mentions = [f"@{admin.user.username}" for admin in admins if admin.user.username]

            # Отправляем репорт и пинг
            await bot.send_message(ADMIN_CHAT_ID, "Репорт от пользователя", parse_mode=ParseMode.HTML)

            if admin_mentions:
                half = len(admin_mentions) // 2
                await asyncio.sleep(4)
                await bot.send_message(ADMIN_CHAT_ID, "Первая часть админов: " + " ".join(admin_mentions[:half]))
                await asyncio.sleep(4)
                await bot.send_message(ADMIN_CHAT_ID, "Вторая часть админов: " + " ".join(admin_mentions[half:]))

            await query.message.edit_text("✅ Репорт и пинг отправлены!")
        elif ping_answer == "no":
            await query.message.edit_text("❌ Репорт отправлен без пинга.")
        else:
            await query.message.edit_text("❌ Ошибка: неверный ответ на вопрос о пинге.")
    else:
        await query.message.edit_text("❌ Ошибка: неправильный формат данных для пинга.")

# Функция одержания ID чату
async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    # Юзаем InlineKeyboardButton для кнопки копирования ID
    button = InlineKeyboardButton(text="Скопировать", copy_text=CopyTextButton(text=chat_id))
    keyboard = [[button]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"🆔 ID этого чата: `{chat_id}`", parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

# Оброботка кнопки Copy ID
async def handle_copy_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.data.split('_')[1]
    await query.answer()  # Отвечаем на запрос

# Кидаем сообщение, что ID скопировано
    await query.edit_message_text(f"✅ ID чата: `{chat_id}` скопировано!")

# Функция оброботки 
async def handle_message(update: Update, context):
    message = update.message.text.lower()
    
# Функция обработки сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text.strip()

    if message.lower() == "Неко".lower():
        admins = await bot.get_chat_administrators(ADMIN_CHAT_ID)
        if admins:
            random_admin = random.choice(admins)
            random_username = random_admin.user.username if random_admin.user.username else "unknown_user"
            sent_message = await update.message.reply_text("вычисления кошко-девочки по айпи💻")
            await asyncio.sleep(5)
            await sent_message.edit_text(f"Кошко-девочка вычислена! Она находится у @{random_username}")
        else:
            await update.message.reply_text("❌ Не удалось получить администраторов для вычислений!")

    elif message.lower() == "Пинг".lower():
        await update.message.reply_text("А нахуя он тебе?")

    elif message.lower() == "РаФа".lower():
        response = random.choice(rafa_responses)
        await update.message.reply_text(f"<b>{response}</b>", parse_mode=ParseMode.HTML)
    
    elif message.lower() == "РаФу".lower():
        response = random.choice(rafu_responses)
        await update.message.reply_text(response, parse_mode=ParseMode.HTML)

    elif message.lower() == "привет".lower():  # Добавляем проверку на "привет" без учета регистра
        current_time = datetime.now(timezone.utc) + timedelta(hours=3)
        hour = current_time.hour

        if 5 <= hour < 7:
            response = "А ты спать не хочешь?"
        elif 7 <= hour < 13:
            response = "Доброго утра!"
        elif 13 <= hour < 17:
            response = "Хорошего дня!"
        elif 17 <= hour < 22:
            response = "Доброго вечера!"
        else:
            response = "А ну ка спать!"

        await update.message.reply_text(response)

# Функция для отправки сообщений через бота
async def send_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверка доступа
    if update.message.from_user.id not in ALLOWED_USERS:
        await update.message.reply_text("❌ У вас нет доступа к этой команде.")
        return

    # Проверка на параметры
    if len(context.args) < 2:
        await update.message.reply_text("❌ Использование: /send [chat_id] [текст сообщения]")
        return

    chat_id = context.args[0]
    text = ' '.join(context.args[1:])

    try:
        sent_message = await bot.send_message(chat_id=chat_id, text=text)
        message_link = f"https://t.me/c/{str(chat_id).replace('-100', '')}/{sent_message.message_id}"
        log_text = (f"📩 Сообщение отправлено через бота\n"
                    f"👤 Отправитель: {update.message.from_user.full_name} ({update.message.from_user.id})\n"
                    f"📍 В чат: {chat_id}\n"
                    f"💬 Текст: {text}\n"
                    f"🔗 <a href='{message_link}'>Ссылка на сообщение</a>")
        await log_action(log_text)
        await update.message.reply_text(f"✅ Сообщение отправлено {chat_id}")
    except Exception as e:
        await update.message.reply_text(f"❌ Случилась ошибка: {e}")

# Збереження повідомлень у словнику {chat_id: {message_id: текст}}
message_storage = {}

async def save_message(update: Update, context: CallbackContext):
    """Зберігає повідомлення у словнику"""
    if update.message:
        chat_id = update.message.chat_id
        message_id = update.message.message_id
        text = update.message.text or "[MEDIA]"
        user = update.message.from_user.full_name

        if chat_id not in message_storage:
            message_storage[chat_id] = {}

        message_storage[chat_id][message_id] = (user, text)

async def check_deleted_messages(context: CallbackContext):
    """Перевіряє, які повідомлення ще існують"""
    for chat_id, messages in message_storage.items():
        to_delete = []
        for message_id in messages:
            try:
                await context.bot.forward_message(chat_id=chat_id, from_chat_id=chat_id, message_id=message_id)
            except Exception:
                # Якщо forward_message не вдається – значить, повідомлення видалене
                user, text = messages[message_id]
                log_msg = f"🚫 Видалено повідомлення!\n👤 {user}\n💬 {text}"
                print(log_msg)  # Лог для тесту
                to_delete.append(message_id)

        # Видаляємо записані повідомлення, які більше не існують
        for msg_id in to_delete:
            del message_storage[chat_id][msg_id]

async def start_checking(app: Application):
    """Запускає перевірку видалених повідомлень кожні 10 секунд"""
    while True:
        await check_deleted_messages(app)
        await asyncio.sleep(10)  # Перевірка кожні 10 секунд


app.add_handler(MessageHandler(filters.Chat(GROUP_ID) & ~filters.Command(), save_message))

# Добавляем команду /send
app.add_handler(CommandHandler("send", send_message))

# Добавляем команду /id
app.add_handler(CommandHandler("id", get_chat_id))

app.add_handler(CommandHandler("show_reports", show_reports))

# Основной цикл программы
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("report", report_command))
app.add_handler(CallbackQueryHandler(handle_report, pattern="^(confirm|cancel)_"))
app.add_handler(CallbackQueryHandler(handle_ping, pattern="^(ping)_"))
app.add_handler(MessageHandler(filters.TEXT, handle_message))
app.add_handler(CallbackQueryHandler(handle_copy_id, pattern="^copy_"))

async def main():
    print("🚀 Бот запущений!")

    # Запуск polling і фонової перевірки одночасно
    await asyncio.gather(app.run_polling(), start_checking(app))

if __name__ == "__main__":
    asyncio.run(main())
