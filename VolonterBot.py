import telebot
from telebot import types
import sqlite3
import atexit
import time
from datetime import datetime, timedelta
import os
from PIL import Image, ImageDraw, ImageFont
import random
import string
import sys
import threading
from datetime import datetime

import pandas as pd

from io import BytesIO
import openpyxl



TOKEN = '7277176904:AAHHm2P0vDtgtB9EZn7kmgvFH5rjJchjITU'  # Замените на ваш токен
bot = telebot.TeleBot(TOKEN)

# Подключение к базе данных
conn = sqlite3.connect('/app/data/volunter_bot.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS blocked_users (
        user_id INTEGER PRIMARY KEY,
        block_time DATETIME
    )
''')

conn.commit()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS task_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        report_text TEXT,
        media_file_id TEXT,
        status TEXT DEFAULT 'на рассмотрении',  -- статус отчета: на рассмотрении, одобрен, отклонен
        FOREIGN KEY (task_id) REFERENCES tasks(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
''')
conn.commit()
# Создание таблицы для заданий
cursor.execute('''
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    points INTEGER DEFAULT 0,
    end_time DATETIME,
    max_participants INTEGER DEFAULT 0
)
''')
conn.commit()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS task_applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        full_name TEXT NOT NULL,
        group_name TEXT NOT NULL,
        faculty TEXT NOT NULL,
        FOREIGN KEY (task_id) REFERENCES tasks(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
''')
try:
    cursor.execute('ALTER TABLE tasks ADD COLUMN start_time DATETIME')
    conn.commit()
    print("Столбец 'start_time' успешно добавлен.")
except sqlite3.Error as e:
    print(f"Ошибка при добавлении столбца: {e}")
conn.commit()
# Создание таблицы для заданий
cursor.execute('''
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    points INTEGER DEFAULT 0,
    end_time DATETIME,
    max_participants INTEGER DEFAULT 0
)
''')
conn.commit()


cursor.execute('''
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    link TEXT,
    points INTEGER DEFAULT 0,
    description TEXT,
    end_time DATETIME 
)
''')
try:
    cursor.execute('ALTER TABLE events ADD COLUMN participants TEXT;')
    print("Столбец participants успешно добавлен.")
except sqlite3.Error as e:
    print(f"Ошибка при добавлении столбца: {e}")

# Попытка добавить новый столбец max_participants в таблицу events
try:
    cursor.execute('ALTER TABLE events ADD COLUMN max_participants INTEGER DEFAULT 0;')
    print("Столбец max_participants успешно добавлен.")
except sqlite3.Error as e:
    print(f"Ошибка при добавлении столбца: {e}")


cursor.execute('''
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    group_name TEXT NOT NULL,
    faculty TEXT NOT NULL,
    event_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    needs_release INTEGER DEFAULT 0,  -- 1 - да, 0 - нет
    needs_volunteer_hours INTEGER DEFAULT 0,  -- 1 - да, 0 - нет
    FOREIGN KEY (event_id) REFERENCES events(id),
    FOREIGN KEY (user_id) REFERENCES users(id));

''')
try:
    cursor.execute('ALTER TABLE applications ADD COLUMN status TEXT DEFAULT "подтверждена";')
    print("Столбец status успешно добавлен.")
except sqlite3.Error as e:
    print(f"Ошибка при добавлении столбца: {e}")
try:
    cursor.execute('ALTER TABLE applications ADD COLUMN age INTEGER;')
    print("Столбец age успешно добавлен.")
except sqlite3.Error as e:
    print(f"Ошибка при добавлении столбца: {e}")
    

cursor.execute('''
CREATE TABLE IF NOT EXISTS subscribers (
    user_id INTEGER PRIMARY KEY,
    is_subscribed INTEGER DEFAULT 1  -- 1 - подписан, 0 - отписан
)
''')

# Проверка существования столбца и добавление его, если он отсутствует
try:
    cursor.execute('ALTER TABLE subscribers ADD COLUMN is_subscribed INTEGER DEFAULT 1;')
    print("Столбец is_subscribed успешно добавлен.")
except sqlite3.Error as e:
    print(f"Ошибка при добавлении столбца: {e}")

cursor.execute('''
CREATE TABLE IF NOT EXISTS user_points (
    user_id INTEGER PRIMARY KEY,
    points INTEGER DEFAULT 0
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS user_states (
    user_id INTEGER PRIMARY KEY,
    has_passed_captcha INTEGER DEFAULT 0
)
''')
try:
    cursor.execute('ALTER TABLE user_states ADD COLUMN has_received_welcome_message INTEGER DEFAULT 0')
    conn.commit()
    print("Столбец has_received_welcome_message успешно добавлен.")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("Столбец has_received_welcome_message уже существует.")
    else:
        print(f"Ошибка при добавлении столбца: {e}")

# Новая таблица для сохраненных анкет
cursor.execute('''
CREATE TABLE IF NOT EXISTS saved_applications (
    user_id INTEGER PRIMARY KEY,
    full_name TEXT NOT NULL,
    group_name TEXT NOT NULL,
    faculty TEXT NOT NULL
)
''')
try:
    cursor.execute('ALTER TABLE saved_applications ADD COLUMN age INTEGER;')
    print("Столбец age успешно добавлен в таблицу saved_applications.")
except sqlite3.Error as e:
    if "duplicate column name" in str(e):
        print("Столбец age уже существует в таблице saved_applications.")
    else:
        print(f"Ошибка при добавлении столбца age: {e}")

conn.commit()
# Проверка существования столбца start_time в таблице events
def add_start_time_column():
    try:
        # Попытка добавить новый столбец start_time
        cursor.execute('ALTER TABLE events ADD COLUMN start_time DATETIME;')
        print("Столбец start_time успешно добавлен.")
    except sqlite3.Error as e:
        # Проверяем, если ошибка связана с тем, что столбец уже существует
        if "duplicate column name" in str(e):
            print("Столбец start_time уже существует.")
        else:
            print(f"Ошибка при добавлении столбца: {e}")

# Вызов функции для добавления столбца
add_start_time_column()
conn.commit()

# ID администраторов
ADMIN_IDS = [5656088749,893172924,1375841281]  # Замените на ID ваших администраторов

# Глобальные переменные и списки
user_ids = []
last_message_time = {}
repeat_count = {}
user_captchas = {}
user_requests = {}



# Функция генерации капчи
def generate_captcha(text):
    try:
        width, height = 200, 100
        image = Image.new('RGB', (width, height), color=(random.randint(150, 255), random.randint(150, 255), random.randint(150, 255)))
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()
        text_color = (random.randint(0, 100), random.randint(0, 100), random.randint(0, 100))
        text_x = random.randint(20, width - 50)
        text_y = random.randint(10, height - 30)
        draw.text((text_x, text_y), text, fill=text_color, font=font)
        
        # Добавление шума
        for _ in range(5):
            draw.line([(random.randint(0, width), random.randint(0, height)),
                       (random.randint(0, width), random.randint(0, height))],
                      fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), width=2)
        
        return image
    
    except Exception as e:
        print(f"Ошибка при генерации капчи: {e}")
        return None
def check_captcha(message, correct_text):
    try:
        user_id = message.from_user.id
        
        if message.text.strip().upper() == correct_text:
            bot.send_message(message.chat.id, "Проверка пройдена!")
            
            # Проверяем, получил ли пользователь приветственное сообщение
            cursor.execute('SELECT has_received_welcome_message FROM user_states WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            
            # Если запись не существует, создаем ее
            if not result:
                cursor.execute('INSERT INTO user_states (user_id, has_passed_captcha, has_received_welcome_message) VALUES (?, ?, ?)', 
                              (user_id, 1, 0))
                conn.commit()
                result = (0,)  # Устанавливаем флаг в 0 для нового пользователя
            
            # Если флаг равен 0, отправляем приветственное сообщение
            if result[0] == 0:
                # Отправляем приветственное сообщение
                welcome_message = (
                    "А теперь давай познакомимся! Я - «карманный помощник» для волонтера ВГЛТУ. "
                    "С помощью меня ты можешь узнать о актуальных мероприятиях и записаться на участие в них, "
                    "а так же поучаствовать в розыгрыше призов и посоревноваться с другими ребятами в выполнении заданий!"
                )
                bot.send_message(message.chat.id, welcome_message)
                
                # Обновляем флаг в базе данных
                cursor.execute('UPDATE user_states SET has_received_welcome_message = 1 WHERE user_id = ?', (user_id,))
                conn.commit()
            
            # Обновляем состояние прохождения капчи
            cursor.execute('INSERT OR REPLACE INTO user_states (user_id, has_passed_captcha) VALUES (?, ?)', (user_id, 1))
            conn.commit()
            
            del user_captchas[user_id]
            show_main_menu(message)
        else:
            bot.send_message(message.chat.id, "Неправильный текст капчи. Попробуйте снова.")
            
            if user_id not in repeat_count:
                repeat_count[user_id] = 0
            
            repeat_count[user_id] += 1
            
            if repeat_count[user_id] < 10:
                start(message)
            else:
                bot.send_message(message.chat.id, "Вы исчерпали все попытки ввода капчи. Попробуйте позже или обратитесь к администратору.")
                
                # Блокировка пользователя на 30 минут
                cursor.execute('INSERT OR REPLACE INTO blocked_users (user_id, block_time) VALUES (?, ?)', (user_id, datetime.now() + timedelta(minutes=30)))
                conn.commit()
    
    except Exception as e:
        print(f"Ошибка при проверке капчи: {e}")

def send_reminders():
    while True:
        try:
            current_time = datetime.now()
            reminder_time = current_time + timedelta(hours=1)
            
            cursor.execute('''
                SELECT name, start_time, link FROM events 
                WHERE start_time BETWEEN ? AND ?
            ''', (current_time, reminder_time))
            
            upcoming_events = cursor.fetchall()
            
            for event in upcoming_events:
                event_name, start_time_str, link = event
                start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M')
                
                # Получаем всех подписчиков
                cursor.execute('SELECT user_id FROM subscribers')
                subscribers = cursor.fetchall()
                
                for subscriber in subscribers:
                    try:
                        bot.send_message(subscriber[0], f"Напоминание: мероприятие '{event_name}' начнется в {start_time.strftime('%Y-%m-%d %H:%M')}. Ссылка: {link}")
                    except Exception as e:
                        print(f"Ошибка при отправке напоминания: {e}")
            
            conn.commit()
        
        except sqlite3.Error as e:
            print(f"Ошибка при работе с базой данных: {e}")
        
        except Exception as e:
            print(f"Общая ошибка: {e}")
        
        time.sleep(3600)  # Проверяем каждый час

# Запускаем поток для отправки напоминаний
threading.Thread(target=send_reminders, daemon=True).start()
from datetime import datetime


@bot.message_handler(commands=['start'])
def start(message):
    try:
        user_id = message.from_user.id
        
        # Проверка блокировки пользователя
        cursor.execute('SELECT block_time FROM blocked_users WHERE user_id = ?', (user_id,))
        block_result = cursor.fetchone()
        
        if block_result and block_result[0]:
            # Удаляем микросекунды из строки
            block_time_str = block_result[0].split('.')[0]
            
            # Преобразуем строку в datetime
            block_time = datetime.strptime(block_time_str, '%Y-%m-%d %H:%M:%S')
            
            if block_time > datetime.now():
                bot.send_message(message.chat.id, "Вы временно заблокированы. Попробуйте позже.")
                return
        
        # Если пользователь уже прошёл капчу, показываем меню
        cursor.execute('SELECT has_passed_captcha FROM user_states WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        if result and result[0] == 1:
            current_hour = datetime.now().hour
            if 6 <= current_hour < 12:
                greeting = "Доброе утро! ☀️"
            elif 12 <= current_hour < 18:
                greeting = "Добрый день! 😊"
            elif 18 <= current_hour < 22:
                greeting = "Добрый вечер! 🌙"
            else:
                greeting = "Доброй ночи! 🌌"
            
            bot.send_message(message.chat.id, f"{greeting} Рад снова тебя видеть!")
            show_main_menu(message)
        else:
            # Генерация и отправка капчи
            captcha_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            captcha_image = generate_captcha(captcha_text)
            user_captchas[user_id] = captcha_text
            
            with BytesIO() as captcha_file:
                captcha_image.save(captcha_file, format='PNG')
                captcha_file.seek(0)
                bot.send_photo(message.chat.id, captcha_file)
                bot.send_message(message.chat.id, "Привет! Для начала введи текст с картинки, чтобы мы точно знали что ты человек! 🤖")                                      
                bot.register_next_step_handler(message, lambda msg: check_captcha(msg, captcha_text))
    
    except Exception as e:
        print(f"Ошибка при отправке капчи: {e}")





@bot.message_handler(commands=['menu'])
@bot.message_handler(func=lambda message: message.text.lower() == "меню!")
def show_menu(message):
    try:
        user_id = message.from_user.id
        
        # Проверка блокировки пользователя
        cursor.execute('SELECT block_time FROM blocked_users WHERE user_id = ?', (user_id,))
        block_result = cursor.fetchone()
        
        if block_result and block_result[0]:
            # Удаляем микросекунды из строки
            block_time_str = block_result[0].split('.')[0]
            
            # Преобразуем строку в datetime
            block_time = datetime.strptime(block_time_str, '%Y-%m-%d %H:%M:%S')
            
            if block_time > datetime.now():
                bot.send_message(message.chat.id, "Вы временно заблокированы. Попробуйте позже.")
                return
        
        # Проверка прохождения капчи
        cursor.execute('SELECT has_passed_captcha FROM user_states WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        if result and result[0] == 1:
            show_main_menu(message)
        else:
            bot.send_message(message.chat.id, "Сначала пройдите проверку капчи. Используйте команду /start для начала.")
    
    except Exception as e:
        print(f"Ошибка при отображении меню: {e}")



def check_captcha_passed(message):
    try:
        user_id = message.from_user.id
        cursor.execute('SELECT has_passed_captcha FROM user_states WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        if result and result[0] == 1:
            return True
        else:
            bot.send_message(message.chat.id, "Сначала пройдите проверку капчи.")
            return False
    
    except Exception as e:
        print(f"Ошибка при проверке капчи: {e}")
        return False



# Главное меню
def show_main_menu(message):
    try:
        user_id = message.from_user.id
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        
        # Основные категории меню
        buttons = [
            types.KeyboardButton("📅 Мероприятия"),
            types.KeyboardButton("📋 Задания"),
            types.KeyboardButton("👤 Профиль"),
            types.KeyboardButton("❓ Задать вопрос")  # Новая кнопка
        ]
        
        # Добавляем кнопку администрирования, если пользователь — администратор
        if message.from_user.id in ADMIN_IDS:
            buttons.append(types.KeyboardButton("⚙️ Администрирование"))
        
        # Добавляем кнопки в меню
        for button in buttons:
            markup.add(button)
        
        bot.send_message(message.chat.id, "Выберите категорию:", reply_markup=markup)
    except Exception as e:
        print(f"Ошибка при отображении главного меню: {e}")

# Обработка выбора категории
@bot.message_handler(func=lambda message: message.text in ["📅 Мероприятия", "📋 Задания", "👤 Профиль", "⚙️ Администрирование", "❓ Задать вопрос"])
def handle_category_selection(message):
    try:
        if message.text == "📅 Мероприятия":
            show_events_menu(message)
        elif message.text == "📋 Задания":
            show_tasks_menu(message)
        elif message.text == "👤 Профиль":
            show_profile_menu(message)
        elif message.text == "⚙️ Администрирование":
            show_admin_menu(message)
        elif message.text == "❓ Задать вопрос":
            ask_question(message)  # Обработка кнопки "Задать вопрос"
    except Exception as e:
        print(f"Ошибка при обработке выбора категории: {e}")

# Подменю для мероприятий
def show_events_menu(message):
    try:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        
        buttons = [
            types.KeyboardButton("🟢 Список мероприятий"),
            types.KeyboardButton("🟢 Записаться на мероприятие"),
            types.KeyboardButton("🚫 Отказаться от участия"),
            types.KeyboardButton("📝 Отправить отчет"),
            types.KeyboardButton("🔙 Назад")
        ]
        
        for button in buttons:
            markup.add(button)
        
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
    except Exception as e:
        print(f"Ошибка при отображении меню мероприятий: {e}")

# Подменю для заданий
def show_tasks_menu(message):
    try:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        
        buttons = [
            types.KeyboardButton("📋 Список заданий"),
            types.KeyboardButton("📝 Отправить отчет по заданию"),
            types.KeyboardButton("🔙 Назад")
        ]
        
        for button in buttons:
            markup.add(button)
        
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
    except Exception as e:
        print(f"Ошибка при отображении меню заданий: {e}")

    
 
# Подменю для профиля
def show_profile_menu(message):
    try:
        user_id = message.from_user.id
        cursor.execute('SELECT full_name FROM saved_applications WHERE user_id=?', (user_id,))
        full_name = cursor.fetchone()
        
        if full_name:
            bot.send_message(message.chat.id, f"Привет, {full_name[0]}! Вот твой профиль:")
        else:
            bot.send_message(message.chat.id, "Привет! Вот твой профиль:")
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = [
            types.KeyboardButton("✏️ Редактировать данные"),
            types.KeyboardButton("🔢 Мои баллы"),
            types.KeyboardButton("🏆 Рейтинг"),
            types.KeyboardButton("🔗 Запросить ссылку на волонтерские часы"),
            types.KeyboardButton("🔙 Назад")
        ]
        
        for button in buttons:
            markup.add(button)
        
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
    except Exception as e:
        print(f"Ошибка при отображении меню профиля: {e}")

# Подменю для администрирования
def show_admin_menu(message):
    try:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        
        buttons = [
            types.KeyboardButton("🟢 Добавить задание"),
            types.KeyboardButton("🟢 Удалить задание"),
            types.KeyboardButton("🟢 Добавить мероприятие"),
            types.KeyboardButton("🟢 Удалить мероприятие"),
            types.KeyboardButton("🟢 Список участников"),
            types.KeyboardButton("🟢 Экспорт данных о мероприятии"),
            types.KeyboardButton("🟢 Отправить баллы"),
            types.KeyboardButton("🟢 Рассмотреть отчеты"),
            types.KeyboardButton("📊 Полный отчет по боту"),
            types.KeyboardButton("🟢 Отправить ссылку на получение часов"),  # Новая кнопка
            types.KeyboardButton("🔙 Назад")
        ]
        
        for button in buttons:
            markup.add(button)
        
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
    except Exception as e:
        print(f"Ошибка при отображении меню администрирования: {e}")

# Обработка кнопки "🔙 Назад"
@bot.message_handler(func=lambda message: message.text == "🔙 Назад")
def handle_back_button(message):
    show_main_menu(message)
def send_question_to_admins(message):
    try:
        # Проверяем, что сообщение является текстовым
        if message.content_type != 'text':
            bot.send_message(message.chat.id, "Извините, я принимаю только текстовые сообщения. Пожалуйста, напишите ваш вопрос текстом.")
            return
        
        question = message.text.strip()
        if not question:
            bot.send_message(message.chat.id, "Вопрос не может быть пустым. Попробуйте снова.")
            return
        
        # Отправляем вопрос всем администраторам
        for admin_id in ADMIN_IDS:
            bot.send_message(admin_id, f"Новый вопрос от пользователя @{message.from_user.username or message.from_user.first_name}:\n\n{question}")
        
        # Уведомляем пользователя
        bot.send_message(message.chat.id, "Ваш вопрос отправлен администраторам. Спасибо!")
    except Exception as e:
        print(f"Ошибка при отправке вопроса: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при отправке вопроса. Попробуйте позже.")
def ask_question(message):
    try:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("❌ Выйти в главное меню"))  # Добавляем кнопку выхода
        bot.send_message(message.chat.id, "Напишите ваш вопрос или нажмите '❌ Выйти в главное меню':", reply_markup=markup)
        bot.register_next_step_handler(message, handle_question_input)
    except Exception as e:
        print(f"Ошибка при запросе вопроса: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Попробуйте позже.")

def handle_question_input(message):
    try:
        if message.text.strip() == "❌ Выйти в главное меню":
            cancel_action(message)  # Возвращаем пользователя в главное меню
            return
        else:
            send_question_to_admins(message)  # Отправляем вопрос администраторам
    except Exception as e:
        print(f"Ошибка при обработке вопроса: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Попробуйте позже.")

def send_question_to_admins(message):
    try:
        # Проверяем, что сообщение является текстовым
        if message.content_type != 'text':
            bot.send_message(message.chat.id, "Извините, я принимаю только текстовые сообщения. Пожалуйста, напишите ваш вопрос текстом.")
            return
        
        question = message.text.strip()
        if not question:
            bot.send_message(message.chat.id, "Вопрос не может быть пустым. Попробуйте снова.")
            return
        
        # Отправляем вопрос всем администраторам
        for admin_id in ADMIN_IDS:
            bot.send_message(admin_id, f"Новый вопрос от пользователя @{message.from_user.username or message.from_user.first_name}:\n\n{question}")
        
        # Уведомляем пользователя
        bot.send_message(message.chat.id, "Ваш вопрос отправлен администраторам. Спасибо!")
    except Exception as e:
        print(f"Ошибка при отправке вопроса: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при отправке вопроса. Попробуйте позже.")

def cancel_action(message):
    bot.send_message(message.chat.id, "Вы вернулись в главное меню.")
    show_main_menu(message)  # Возвращаем пользователя в главное меню

# Отправка вопроса администраторам
# Отправка вопроса администраторам
@bot.message_handler(func=lambda message: message.text == "📊 Полный отчет по боту")
def generate_full_report(message):
    try:
        if message.from_user.id in ADMIN_IDS:
            # Сбор данных из всех таблиц
            # Таблица tasks
            cursor.execute('SELECT * FROM tasks')
            tasks = cursor.fetchall()
            tasks_columns = [description[0] for description in cursor.description]  # Получаем названия столбцов
            tasks_df = pd.DataFrame(tasks, columns=tasks_columns)

            # Таблица events
            cursor.execute('SELECT * FROM events')
            events = cursor.fetchall()
            events_columns = [description[0] for description in cursor.description]
            events_df = pd.DataFrame(events, columns=events_columns)

            # Таблица applications
            cursor.execute('SELECT * FROM applications')
            applications = cursor.fetchall()
            applications_columns = [description[0] for description in cursor.description]
            applications_df = pd.DataFrame(applications, columns=applications_columns)

            # Таблица task_applications
            cursor.execute('SELECT * FROM task_applications')
            task_applications = cursor.fetchall()
            task_applications_columns = [description[0] for description in cursor.description]
            task_applications_df = pd.DataFrame(task_applications, columns=task_applications_columns)

            # Таблица task_reports
            cursor.execute('SELECT * FROM task_reports')
            task_reports = cursor.fetchall()
            task_reports_columns = [description[0] for description in cursor.description]
            task_reports_df = pd.DataFrame(task_reports, columns=task_reports_columns)

            # Таблица user_points
            cursor.execute('SELECT * FROM user_points')
            user_points = cursor.fetchall()
            user_points_columns = [description[0] for description in cursor.description]
            user_points_df = pd.DataFrame(user_points, columns=user_points_columns)

            # Таблица subscribers
            cursor.execute('SELECT * FROM subscribers')
            subscribers = cursor.fetchall()
            subscribers_columns = [description[0] for description in cursor.description]
            subscribers_df = pd.DataFrame(subscribers, columns=subscribers_columns)

            # Таблица saved_applications
            cursor.execute('SELECT * FROM saved_applications')
            saved_applications = cursor.fetchall()
            saved_applications_columns = [description[0] for description in cursor.description]
            saved_applications_df = pd.DataFrame(saved_applications, columns=saved_applications_columns)

            # Таблица blocked_users
            cursor.execute('SELECT * FROM blocked_users')
            blocked_users = cursor.fetchall()
            blocked_users_columns = [description[0] for description in cursor.description]
            blocked_users_df = pd.DataFrame(blocked_users, columns=blocked_users_columns)

            # Таблица user_states
            cursor.execute('SELECT * FROM user_states')
            user_states = cursor.fetchall()
            user_states_columns = [description[0] for description in cursor.description]
            user_states_df = pd.DataFrame(user_states, columns=user_states_columns)

            # Создание Excel-файла
            with pd.ExcelWriter('full_report.xlsx') as writer:
                tasks_df.to_excel(writer, sheet_name='Задания', index=False)
                events_df.to_excel(writer, sheet_name='Мероприятия', index=False)
                applications_df.to_excel(writer, sheet_name='Заявки', index=False)
                task_applications_df.to_excel(writer, sheet_name='Заявки на задания', index=False)
                task_reports_df.to_excel(writer, sheet_name='Отчеты по заданиям', index=False)
                user_points_df.to_excel(writer, sheet_name='Баллы пользователей', index=False)
                subscribers_df.to_excel(writer, sheet_name='Подписчики', index=False)
                saved_applications_df.to_excel(writer, sheet_name='Сохраненные заявки', index=False)
                blocked_users_df.to_excel(writer, sheet_name='Заблокированные пользователи', index=False)
                user_states_df.to_excel(writer, sheet_name='Состояния пользователей', index=False)

            # Отправка файла администратору
            with open('full_report.xlsx', 'rb') as file:
                bot.send_document(message.chat.id, file, caption="Полный отчет по деятельности бота")

            # Удаление временного файла
            os.remove('full_report.xlsx')

        else:
            bot.send_message(message.chat.id, "Эта функция доступна только администраторам.")
    except Exception as e:
        print(f"Ошибка при создании отчета: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при создании отчета.")

    
@bot.message_handler(func=lambda message: message.text == "📝 Отправить отчет по заданию")
def prompt_send_task_report(message):
    try:
        # Получаем список заданий, на которые пользователь записан
        cursor.execute('SELECT task_id FROM task_applications WHERE user_id = ?', (message.from_user.id,))
        user_tasks = cursor.fetchall()

        if user_tasks:
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
            for task in user_tasks:
                cursor.execute('SELECT name FROM tasks WHERE id = ?', (task[0],))
                task_result = cursor.fetchone()
                
                # Проверяем, что task_result не равен None
                if task_result:
                    task_name = task_result[0]
                    markup.add(task_name)
                else:
                    # Если задание не найдено, пропускаем его
                    continue
            
            markup.add(types.KeyboardButton("❌ Выйти в главное меню"))
            bot.send_message(message.chat.id, "Выберите задание для отправки отчета:", reply_markup=markup)
            bot.register_next_step_handler(message, handle_task_report_selection)
        else:
            bot.send_message(message.chat.id, "Вы не записаны ни на одно задание.")
    
    except sqlite3.Error as e:
        print(f"Ошибка при получении списка заданий: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при получении данных.")
    
    except Exception as e:
        print(f"Общая ошибка при отправке отчета: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")
def handle_task_report_selection(message):
    try:
        if message.text.strip() == "❌ Выйти в главное меню":
            cancel_action(message)
            return

        selected_task = message.text.strip()
        cursor.execute('SELECT id FROM tasks WHERE name = ?', (selected_task,))
        task_id_result = cursor.fetchone()

        if task_id_result:
            task_id = task_id_result[0]
            bot.send_message(message.chat.id, "Введите текст отчета или отправьте фото/видео:")
            bot.register_next_step_handler(message, lambda msg: save_task_report(msg, task_id))
        else:
            bot.send_message(message.chat.id, "Выбранное задание не найдено.")
    
    except sqlite3.Error as e:
        print(f"Ошибка при обработке выбора задания: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при обработке данных.")
    
    except Exception as e:
        print(f"Общая ошибка при обработке выбора задания: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")
def save_task_report(message, task_id):
    try:
        if message.text and message.text.strip() == "❌ Выйти в главное меню":
            cancel_action(message)
            return

        report_text = message.text if message.text else ""
        media_file_id = None

        if message.content_type in ['photo', 'video']:
            media_file_id = message.photo[-1].file_id if message.content_type == 'photo' else message.video.file_id

        user_id = message.from_user.id

        # Получаем полную информацию о пользователе из таблицы saved_applications
        cursor.execute('SELECT full_name, group_name, faculty FROM saved_applications WHERE user_id=?', (user_id,))
        user_data = cursor.fetchone()

        if user_data:
            full_name, group_name, faculty = user_data
        else:
            full_name, group_name, faculty = "Неизвестно", "Неизвестно", "Неизвестно"

        # Сохраняем отчет в базу данных
        cursor.execute(
            'INSERT INTO task_reports (task_id, user_id, report_text, media_file_id) VALUES (?, ?, ?, ?)',
            (task_id, user_id, report_text, media_file_id)
        )
        conn.commit()

        # Получаем название задания
        cursor.execute('SELECT name FROM tasks WHERE id = ?', (task_id,))
        task_name_result = cursor.fetchone()
        task_name = task_name_result[0] if task_name_result else "Неизвестное задание"

        # Формируем сообщение для администратора
        admin_message = (
            f"Новый отчет по заданию '{task_name}':\n"
            f"Пользователь: @{message.from_user.username or message.from_user.first_name}\n"
            f"ФИО: {full_name}\n"
            f"Группа: {group_name}\n"
            f"Факультет: {faculty}\n"
            f"Текст отчета: {report_text}\n"
            f"Медиафайл: {'Присутствует' if media_file_id else 'Отсутствует'}"
        )

        # Отправляем уведомление администратору
        for admin in ADMIN_IDS:
            bot.send_message(admin, admin_message)
            if media_file_id:
                if message.content_type == 'photo':
                    bot.send_photo(admin, media_file_id, caption="Медиафайл из отчета")
                elif message.content_type == 'video':
                    bot.send_video(admin, media_file_id, caption="Медиафайл из отчета")

        bot.send_message(message.chat.id, "Ваш отчет успешно отправлен на рассмотрение!")
    
    except sqlite3.Error as e:
        print(f"Ошибка при сохранении отчета: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при сохранении данных.")
    
    except Exception as e:
        print(f"Общая ошибка при сохранении отчета: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")
@bot.message_handler(func=lambda message: message.text == "🟢 Рассмотреть отчеты")
def review_reports(message):
    try:
        if message.from_user.id in ADMIN_IDS:
            # Получаем отчеты, которые находятся на рассмотрении
            cursor.execute('SELECT id, task_id, user_id, report_text, media_file_id FROM task_reports WHERE status = "на рассмотрении"')
            reports = cursor.fetchall()

            if reports:
                markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
                for report in reports:
                    report_id, task_id, user_id, report_text, media_file_id = report
                    
                    # Получаем название задания по task_id
                    cursor.execute('SELECT name FROM tasks WHERE id = ?', (task_id,))
                    task_result = cursor.fetchone()
                    
                    # Получаем информацию о пользователе из таблицы saved_applications
                    cursor.execute('SELECT full_name FROM saved_applications WHERE user_id = ?', (user_id,))
                    user_result = cursor.fetchone()
                    full_name = user_result[0] if user_result else "Неизвестный пользователь"

                    # Проверяем, что task_result не равен None
                    if task_result:
                        task_name = task_result[0]
                        # Добавляем report_id в текст сообщения
                        markup.add(f"Отчет по заданию: {task_name} (От: {full_name}) (ID: {report_id})")
                    else:
                        # Если задание не найдено, пропускаем этот отчет
                        print(f"Задание с ID {task_id} не найдено в таблице tasks.")
                        continue
                
                markup.add(types.KeyboardButton("❌ Выйти в главное меню"))
                bot.send_message(message.chat.id, "Выберите отчет для рассмотрения:", reply_markup=markup)
                bot.register_next_step_handler(message, handle_report_review)
            else:
                bot.send_message(message.chat.id, "Нет отчетов на рассмотрении.")
        else:
            bot.send_message(message.chat.id, "Эта функция доступна только администраторам.")
    
    except sqlite3.Error as e:
        print(f"Ошибка при получении отчетов: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при получении данных.")
    
    except Exception as e:
        print(f"Общая ошибка при рассмотрении отчетов: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")

def handle_report_review(message):
    try:
        if message.text.strip() == "❌ Выйти в главное меню":
            cancel_action(message)
            return

        # Извлекаем ID отчета из текста сообщения
        report_id = int(message.text.split("(ID: ")[1].replace(")", ""))
        
        # Получаем данные отчета
        cursor.execute('SELECT task_id, user_id, report_text, media_file_id FROM task_reports WHERE id = ?', (report_id,))
        report_data = cursor.fetchone()

        if report_data:
            task_id, user_id, report_text, media_file_id = report_data

            # Получаем название задания
            cursor.execute('SELECT name FROM tasks WHERE id = ?', (task_id,))
            task_name_result = cursor.fetchone()
            task_name = task_name_result[0] if task_name_result else "Неизвестное задание"

            # Получаем полную информацию о пользователе
            cursor.execute('SELECT full_name, group_name, faculty FROM saved_applications WHERE user_id=?', (user_id,))
            user_data = cursor.fetchone()

            if user_data:
                full_name, group_name, faculty = user_data
            else:
                full_name, group_name, faculty = "Неизвестно", "Неизвестно", "Неизвестно"

            # Формируем сообщение для администратора
            report_message = (
                f"Отчет по заданию '{task_name}':\n"
                f"Пользователь: @{message.from_user.username or message.from_user.first_name}\n"
                f"ФИО: {full_name}\n"
                f"Группа: {group_name}\n"
                f"Факультет: {faculty}\n"
                f"Текст отчета: {report_text}\n"
                f"Медиафайл: {'Присутствует' if media_file_id else 'Отсутствует'}"
            )

            # Отправляем сообщение администратору
            bot.send_message(message.chat.id, report_message)

            # Если есть медиафайл, отправляем его
            if media_file_id:
                if message.content_type == 'photo':
                    bot.send_photo(message.chat.id, media_file_id, caption="Медиафайл из отчета")
                elif message.content_type == 'video':
                    bot.send_video(message.chat.id, media_file_id, caption="Медиафайл из отчета")

            # Предлагаем администратору одобрить или отклонить отчет
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
            markup.add("Одобрить", "Отклонить")
            markup.add(types.KeyboardButton("❌ Выйти в главное меню"))
            bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
            bot.register_next_step_handler(message, lambda msg: approve_or_reject_report(msg, report_id, user_id, task_id))
        else:
            bot.send_message(message.chat.id, "Отчет не найден.")
    
    except Exception as e:
        print(f"Ошибка при рассмотрении отчета: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")
def approve_or_reject_report(message, report_id, user_id, task_id):
    try:
        if message.text.strip() == "❌ Выйти в главное меню":
            cancel_action(message)
            return

        if message.text.strip() == "Одобрить":
            # Получаем количество баллов за задание
            cursor.execute('SELECT points FROM tasks WHERE id = ?', (task_id,))
            task_points = cursor.fetchone()[0]

            # Обновляем статус отчета
            cursor.execute('UPDATE task_reports SET status = "одобрен" WHERE id = ?', (report_id,))
            
            # Начисляем баллы пользователю
            cursor.execute('''
                INSERT INTO user_points (user_id, points)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET points = points + ?
            ''', (user_id, task_points, task_points))
            conn.commit()

            # Уведомляем пользователя
            bot.send_message(user_id, f"Ваш отчет по заданию одобрен! Вам начислено {task_points} баллов.")
            bot.send_message(message.chat.id, "Отчет одобрен, баллы начислены.")
        
        elif message.text.strip() == "Отклонить":
            cursor.execute('UPDATE task_reports SET status = "отклонен" WHERE id = ?', (report_id,))
            conn.commit()

            bot.send_message(user_id, "Ваш отчет по заданию отклонен администратором.")
            bot.send_message(message.chat.id, "Отчет отклонен.")
    
    except Exception as e:
        print(f"Ошибка при обработке отчета: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")
        
 
@bot.message_handler(func=lambda message: message.text == "📋 Список заданий")
def show_tasks(message):
    try:
        cursor.execute('SELECT name FROM tasks')
        tasks = cursor.fetchall()

        if tasks:
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
            for task in tasks:
                markup.add(task[0])
            markup.add(types.KeyboardButton("❌ Выйти в главное меню"))
            bot.send_message(message.chat.id, "Выберите задание:", reply_markup=markup)
            bot.register_next_step_handler(message, handle_task_selection)
        else:
            bot.send_message(message.chat.id, "Нет доступных заданий.")
    
    except sqlite3.Error as e:
        print(f"Ошибка при получении списка заданий: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при получении данных.")
    
    except Exception as e:
        print(f"Общая ошибка при показе списка заданий: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")
def handle_task_selection(message):
    try:
        if message.text.strip() == "❌ Выйти в главное меню":
            cancel_action(message)
            return

        selected_task = message.text.strip()
        cursor.execute('SELECT id, description FROM tasks WHERE name = ?', (selected_task,))
        task_info = cursor.fetchone()

        if task_info:
            task_id, description = task_info
            bot.send_message(message.chat.id, f"Описание задания '{selected_task}':\n{description}")
            
            # Предлагаем записаться на задание
            bot.send_message(
                message.chat.id,
                "Хотите записаться на это задание?",
                reply_markup=create_yes_no_keyboard()
            )
            bot.register_next_step_handler(message, lambda msg: handle_task_application(msg, task_id))
        else:
            bot.send_message(message.chat.id, "Выбранное задание не найдено.")
    
    except sqlite3.Error as e:
        print(f"Ошибка при обработке выбора задания: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при обработке данных.")
     
    except Exception as e:
        print(f"Общая ошибка при обработке выбора задания: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")
def handle_task_application(message, task_id):
    try:
        if message.text.strip() == "❌ Выйти в главное меню":
            cancel_action(message)
            return

        if message.text.strip().lower() == "да":
            user_id = message.from_user.id

            # Проверяем, не записан ли пользователь уже на это задание
            cursor.execute('SELECT id FROM task_applications WHERE task_id = ? AND user_id = ?', (task_id, user_id))
            existing_application = cursor.fetchone()

            if existing_application:
                bot.send_message(message.chat.id, "Вы уже записаны на это задание.")
                return

            # Проверяем, есть ли сохраненные данные пользователя
            cursor.execute('SELECT full_name, group_name, faculty FROM saved_applications WHERE user_id = ?', (user_id,))
            saved_data = cursor.fetchone()

            if saved_data:
                full_name, group_name, faculty = saved_data

                # Записываем пользователя на задание
                cursor.execute(
                    'INSERT INTO task_applications (task_id, user_id, full_name, group_name, faculty) VALUES (?, ?, ?, ?, ?)',
                    (task_id, user_id, full_name, group_name, faculty)
                )
                conn.commit()

                # Получаем название задания
                cursor.execute('SELECT name FROM tasks WHERE id = ?', (task_id,))
                task_name = cursor.fetchone()[0]

                # Отправляем уведомление администратору
                for admin in ADMIN_IDS:
                    bot.send_message(
                        admin,
                        f"Новая запись на задание:\n"
                        f"Пользователь: @{message.from_user.username or message.from_user.first_name}\n"
                        f"ФИО: {full_name}\n"
                        f"Группа: {group_name}\n"
                        f"Факультет: {faculty}\n"
                        f"Задание: {task_name}"
                    )

                bot.send_message(message.chat.id, f"Вы успешно записаны на задание '{task_name}'!")
            else:
                # Если данных нет, запрашиваем их у пользователя
                bot.send_message(message.chat.id, "Введите ваше ФИО:")
                bot.register_next_step_handler(message, lambda msg: ask_for_group_for_task(msg, task_id))
        else:
            bot.send_message(message.chat.id, "Запись на задание отменена.")
    
    except sqlite3.Error as e:
        print(f"Ошибка при записи на задание: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при записи на задание.")
    
    except Exception as e:
        print(f"Общая ошибка при записи на задание: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")

def ask_for_group_for_task(message, task_id):
    try:
        if message.text.strip() == "❌ Выйти в главное меню":
            cancel_action(message)
            return

        full_name = message.text.strip()
        
        # Валидация ФИО (например, проверка на длину)
        if len(full_name) > 80:
            bot.send_message(message.chat.id, "ФИО слишком длинное. Пожалуйста, сократите.")
            return
        
        bot.send_message(message.chat.id, "Введите вашу группу:")
        bot.register_next_step_handler(message, lambda msg: ask_for_faculty_for_task(msg, task_id, full_name))
    
    except Exception as e:
        print(f"Ошибка при получении группы: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")
def ask_for_faculty_for_task(message, task_id, full_name):
    try:
        if message.text.strip() == "❌ Выйти в главное меню":
            cancel_action(message)
            return

        group_name = message.text.strip()
        
        # Валидация группы (например, проверка на длину)
        if len(group_name) > 50:
            bot.send_message(message.chat.id, "Группа слишком длинная. Пожалуйста, сократите.")
            return
        
        # Отправляем клавиатуру с факультетами
        bot.send_message(
            message.chat.id,
            "Выберите ваш факультет:",
            reply_markup=create_faculty_keyboard()  # Используем клавиатуру с факультетами
        )
        bot.register_next_step_handler(message, lambda msg: save_task_application(msg, task_id, full_name, group_name))
    
    except Exception as e:
        print(f"Ошибка при получении факультета: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")

def save_task_application(message, task_id, full_name, group_name):
    try:
        if message.text.strip() == "❌ Выйти в главное меню":
            cancel_action(message)
            return

        faculty = message.text.strip()
        
        # Валидация факультета (например, проверка на длину)
        if len(faculty) > 80:
            bot.send_message(message.chat.id, "Факультет слишком длинный. Пожалуйста, сократите.")
            return

        user_id = message.from_user.id

        # Записываем пользователя на задание
        cursor.execute(
            'INSERT INTO task_applications (task_id, user_id, full_name, group_name, faculty) VALUES (?, ?, ?, ?, ?)',
            (task_id, user_id, full_name, group_name, faculty)
        )
        conn.commit()

        # Сохраняем данные пользователя в таблицу saved_applications
        cursor.execute(
            'INSERT OR REPLACE INTO saved_applications (user_id, full_name, group_name, faculty) VALUES (?, ?, ?, ?)',
            (user_id, full_name, group_name, faculty)
        )
        conn.commit()

        # Получаем название задания
        cursor.execute('SELECT name FROM tasks WHERE id = ?', (task_id,))
        task_name = cursor.fetchone()[0]

        # Отправляем уведомление администратору
        for admin in ADMIN_IDS:
            bot.send_message(
                admin,
                f"Новая запись на задание:\n"
                f"Пользователь: @{message.from_user.username or message.from_user.first_name}\n"
                f"ФИО: {full_name}\n"
                f"Группа: {group_name}\n"
                f"Факультет: {faculty}\n"
                f"Задание: {task_name}"
            )

        bot.send_message(message.chat.id, f"Вы успешно записаны на задание '{task_name}'!")
    
    except sqlite3.Error as e:
        print(f"Ошибка при сохранении заявки на задание: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при сохранении данных.")
    
    except Exception as e:
        print(f"Общая ошибка при сохранении заявки на задание: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")
# Глобальный словарь для хранения данных задания
task_data = {}

@bot.message_handler(func=lambda message: message.text == "🟢 Добавить задание")
def prompt_add_task(message):
    if message.from_user.id in ADMIN_IDS:
        # Инициализируем словарь для хранения данных задания
        global task_data
        task_data = {}  # Очищаем предыдущие данные
        
        # Запрашиваем название задания
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("❌ Выйти в главное меню"))
        bot.send_message(message.chat.id, "Введите название задания:", reply_markup=markup)
        bot.register_next_step_handler(message, save_task_name)
    else:
        bot.send_message(message.chat.id, "Эта функция доступна только администраторам.")

def save_task_name(message):
    if message.text == "❌ Выйти в главное меню":
        return cancel_action(message)
    
    try:
        global task_data
        task_name = message.text.strip()
        
        if len(task_name) > 100:
            bot.send_message(message.chat.id, "Название задания слишком длинное. Пожалуйста, сократите.")
            bot.register_next_step_handler(message, save_task_name)
            return
        
        task_data['name'] = task_name  # Сохраняем название задания
        
        # Запрашиваем описание задания
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("❌ Выйти в главное меню"))
        bot.send_message(message.chat.id, "Введите описание задания (или оставьте пустым):", reply_markup=markup)
        bot.register_next_step_handler(message, save_task_description)
    
    except Exception as e:
        print(f"Ошибка при сохранении названия задания: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")

def save_task_description(message):
    if message.text == "❌ Выйти в главное меню":
        return cancel_action(message)
    
    try:
        global task_data
        description = message.text.strip()
        
        if len(description) > 500:
            bot.send_message(message.chat.id, "Описание задания слишком длинное. Пожалуйста, сократите.")
            bot.register_next_step_handler(message, save_task_description)
            return
        
        task_data['description'] = description or None  # Сохраняем описание задания
        
        # Запрашиваем количество баллов
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("❌ Выйти в главное меню"))
        bot.send_message(message.chat.id, "Введите количество баллов за выполнение задания:", reply_markup=markup)
        bot.register_next_step_handler(message, save_task_points)
    
    except Exception as e:
        print(f"Ошибка при сохранении описания задания: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")

def save_task_points(message):
    if message.text == "❌ Выйти в главное меню":
        return cancel_action(message)
    
    try:
        global task_data
        points = message.text.strip()
        
        if not points.isdigit() or int(points) <= 0:
            bot.send_message(message.chat.id, "Пожалуйста, введите корректное количество баллов (целое число больше нуля).")
            bot.register_next_step_handler(message, save_task_points)
            return
        
        task_data['points'] = int(points)  # Сохраняем количество баллов
        
        # Запрашиваем максимальное количество участников
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("❌ Выйти в главное меню"))
        bot.send_message(message.chat.id, "Введите максимальное количество участников (или 0 для неограниченного):", reply_markup=markup)
        bot.register_next_step_handler(message, save_task_max_participants)
    
    except Exception as e:
        print(f"Ошибка при сохранении баллов задания: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")

def save_task_max_participants(message):
    if message.text == "❌ Выйти в главное меню":
        return cancel_action(message)
    
    try:
        global task_data
        max_participants = message.text.strip()
        
        if not max_participants.isdigit() or int(max_participants) < 0:
            bot.send_message(message.chat.id, "Пожалуйста, введите корректное количество участников (целое число больше или равно нулю).")
            bot.register_next_step_handler(message, save_task_max_participants)
            return
        
        task_data['max_participants'] = int(max_participants)  # Сохраняем максимальное количество участников
        
        # Запрашиваем время начала задания
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("❌ Выйти в главное меню"))
        bot.send_message(message.chat.id, "Введите время начала задания (формат: ГГГГ-ММ-ДД ЧЧ:ММ):", reply_markup=markup)
        bot.register_next_step_handler(message, save_task_start_time)
    
    except Exception as e:
        print(f"Ошибка при сохранении максимального количества участников: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")

MAX_RETRIES = 3

def save_task_start_time(message, retries=0):
    if message.text == "❌ Выйти в главное меню":
        return cancel_action(message)
    
    try:
        global task_data
        start_time_input = message.text.strip()

        # Проверка на пустой ввод
        if not start_time_input:
            bot.send_message(message.chat.id, "Вы не ввели время. Пожалуйста, введите время в формате 'ГГГГ-ММ-ДД ЧЧ:ММ'.")
            bot.register_next_step_handler(message, save_task_start_time, retries=retries)
            return

        # Проверка длины и структуры ввода
        if len(start_time_input) != 16 or start_time_input[4] != '-' or start_time_input[7] != '-' or start_time_input[10] != ' ' or start_time_input[13] != ':':
            bot.send_message(message.chat.id, "Неверный формат времени. Пожалуйста, введите время в формате 'ГГГГ-ММ-ДД ЧЧ:ММ'.")
            if retries < MAX_RETRIES:
                bot.register_next_step_handler(message, save_task_start_time, retries=retries + 1)
            else:
                bot.send_message(message.chat.id, "Превышено количество попыток. Возвращаюсь в главное меню.")
                show_main_menu(message)
            return

        # Попытка преобразовать введенный текст в datetime
        try:
            start_time = datetime.strptime(start_time_input, '%Y-%m-%d %H:%M')
        except ValueError:
            bot.send_message(message.chat.id, "Неверный формат времени. Пожалуйста, введите время в формате 'ГГГГ-ММ-ДД ЧЧ:ММ'.")
            if retries < MAX_RETRIES:
                bot.register_next_step_handler(message, save_task_start_time, retries=retries + 1)
            else:
                bot.send_message(message.chat.id, "Превышено количество попыток. Возвращаюсь в главное меню.")
                show_main_menu(message)
            return

        # Сохраняем время начала задания
        task_data['start_time'] = start_time
        bot.send_message(message.chat.id, "Время начала успешно сохранено.")

        # Переходим к следующему шагу (например, запрос времени окончания)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("❌ Выйти в главное меню"))
        bot.send_message(message.chat.id, "Введите время окончания задания (формат: ГГГГ-ММ-ДД ЧЧ:ММ) или напишите 'нет':", reply_markup=markup)
        bot.register_next_step_handler(message, save_task_end_time)

    except Exception as e:
        print(f"Ошибка при сохранении времени начала: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте снова.")
        show_main_menu(message)

def save_task_end_time(message, retries=0):
    if message.text == "❌ Выйти в главное меню":
        return cancel_action(message)
    
    try:
        global task_data
        end_time_input = message.text.strip()

        # Если пользователь ввел "нет"
        if end_time_input.lower() == 'нет':
            task_data['end_time'] = None
            bot.send_message(message.chat.id, "Время окончания не указано.")
            save_task_to_db(message)
            return

        # Проверка длины и структуры ввода
        if len(end_time_input) != 16 or end_time_input[4] != '-' or end_time_input[7] != '-' or end_time_input[10] != ' ' or end_time_input[13] != ':':
            bot.send_message(message.chat.id, "Неверный формат времени. Пожалуйста, введите время в формате 'ГГГГ-ММ-ДД ЧЧ:ММ' или напишите 'нет'.")
            if retries < MAX_RETRIES:
                bot.register_next_step_handler(message, save_task_end_time, retries=retries + 1)
            else:
                bot.send_message(message.chat.id, "Превышено количество попыток. Возвращаюсь в главное меню.")
                show_main_menu(message)
            return

        # Попытка преобразовать введенный текст в datetime
        try:
            end_time = datetime.strptime(end_time_input, '%Y-%m-%d %H:%M')
        except ValueError:
            bot.send_message(message.chat.id, "Неверный формат времени. Пожалуйста, введите время в формате 'ГГГГ-ММ-ДД ЧЧ:ММ' или напишите 'нет'.")
            if retries < MAX_RETRIES:
                bot.register_next_step_handler(message, save_task_end_time, retries=retries + 1)
            else:
                bot.send_message(message.chat.id, "Превышено количество попыток. Возвращаюсь в главное меню.")
                show_main_menu(message)
            return

        # Сохраняем время окончания задания
        task_data['end_time'] = end_time
        bot.send_message(message.chat.id, "Время окончания успешно сохранено.")
        save_task_to_db(message)

    except Exception as e:
        print(f"Ошибка при сохранении времени окончания: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте снова.")
        show_main_menu(message)

def save_task_to_db(message):
    try:
        global task_data

        # Проверяем обязательные поля
        required_fields = ['name', 'points', 'start_time']
        missing_fields = [field for field in required_fields if field not in task_data]

        if missing_fields:
            bot.send_message(message.chat.id, f"Пожалуйста, заполните следующие обязательные поля: {', '.join(missing_fields)}.")
            prompt_add_task(message)  # Возвращаем пользователя в меню ввода данных
            return

        # Сохраняем задание в базу данных
        cursor.execute('''
            INSERT INTO tasks (name, description, points, max_participants, start_time, end_time)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            task_data['name'],
            task_data.get('description'),
            task_data['points'],
            task_data.get('max_participants', 0),
            task_data['start_time'].strftime('%Y-%m-%d %H:%M'),
            task_data.get('end_time').strftime('%Y-%m-%d %H:%M') if task_data.get('end_time') else None
        ))
        conn.commit()

        bot.send_message(message.chat.id, f"Задание '{task_data['name']}' успешно добавлено!")
        task_data.clear()  # Очищаем данные задания
        show_main_menu(message)  # Возвращаем пользователя в главное меню
    
    except sqlite3.Error as e:
        print(f"Ошибка при сохранении задания: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при сохранении данных.")
        show_main_menu(message)
    
    except Exception as e:
        print(f"Общая ошибка при сохранении задания: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")
        show_main_menu(message)
def remove_expired_tasks():
    conn = sqlite3.connect('/app/data/volunter_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    while True:
        try:
            current_time = datetime.now()
            cursor.execute('SELECT id FROM tasks WHERE end_time IS NOT NULL AND end_time < ?', (current_time,))
            expired_tasks = cursor.fetchall()
            for task in expired_tasks:
                task_id = task[0]
                cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
                print(f"Задание с ID {task_id} было удалено.")
            conn.commit()
        except sqlite3.Error as e:
            print(f"Ошибка при удалении истекших заданий: {e}")
        except Exception as e:
            print(f"Общая ошибка при удалении заданий: {e}")
        time.sleep(60)  # Проверяем каждую минуту
    conn.close()()
threading.Thread(target=remove_expired_tasks, daemon=True).start()  
@bot.message_handler(func=lambda message: message.text == "🟢 Удалить задание")
def prompt_delete_task(message):
    """
    Функция для отображения списка заданий и запроса выбора задания для удаления.
    """
    if message.from_user.id in ADMIN_IDS:
        # Получаем список всех заданий
        cursor.execute('SELECT name FROM tasks')
        tasks = cursor.fetchall()
        
        if tasks:
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
            for task in tasks:
                markup.add(task[0])  # Добавляем название задания в клавиатуру
            markup.add(types.KeyboardButton("❌ Выйти в главное меню"))  # Кнопка отмены
            bot.send_message(message.chat.id, "Выберите задание для удаления:", reply_markup=markup)
            bot.register_next_step_handler(message, handle_task_deletion)
        else:
            bot.send_message(message.chat.id, "Нет заданий для удаления.")
    else:
        bot.send_message(message.chat.id, "Эта функция доступна только администраторам.")


def handle_task_deletion(message):
    """
    Функция для обработки выбора задания и запроса подтверждения удаления.
    """
    try:
        if message.text.strip() == "❌ Выйти в главное меню":
            cancel_action(message)
            return
        
        selected_task = message.text.strip()
        
        # Проверяем, существует ли задание с таким названием
        cursor.execute('SELECT id FROM tasks WHERE name = ?', (selected_task,))
        task_id_result = cursor.fetchone()
        
        if task_id_result:
            task_id = task_id_result[0]
            
            # Запрашиваем подтверждение удаления
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
            markup.add(types.KeyboardButton("Да"), types.KeyboardButton("Нет"))
            bot.send_message(message.chat.id, f"Вы уверены, что хотите удалить задание '{selected_task}'? (Да/Нет)", reply_markup=markup)
            
            # Передаем task_id и selected_task в следующую функцию
            bot.register_next_step_handler(message, lambda msg: confirm_task_deletion(msg, task_id, selected_task))
        else:
            bot.send_message(message.chat.id, "Выбранное задание не найдено.")
    except sqlite3.Error as e:
        print(f"Ошибка при удалении задания: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при удалении задания.")
    except Exception as e:
        print(f"Общая ошибка при удалении задания: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")


def confirm_task_deletion(message, task_id, task_name):
    """
    Функция для подтверждения удаления задания и выполнения каскадного удаления.
    """
    try:
        if message.text.strip().lower() == "да":
            # Удаляем связанные данные из таблиц task_applications и task_reports
            cursor.execute('DELETE FROM task_applications WHERE task_id = ?', (task_id,))
            cursor.execute('DELETE FROM task_reports WHERE task_id = ?', (task_id,))
            
            # Удаляем само задание из таблицы tasks
            cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
            conn.commit()
            
            # Уведомляем администратора об успешном удалении
            bot.send_message(message.chat.id, f"Задание '{task_name}' и все связанные данные успешно удалены.")
        else:
            bot.send_message(message.chat.id, "Удаление отменено.")
        
        # Возвращаем администратора в главное меню
        show_main_menu(message)
    except sqlite3.Error as e:
        print(f"Ошибка при удалении задания: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при удалении задания.")
    except Exception as e:
        print(f"Общая ошибка при удалении задания: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")
# ========== МЕНЮ РЕДАКТИРОВАНИЯ ==========
@bot.message_handler(func=lambda message: message.text == "✏️ Редактировать данные")
def show_edit_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("✏️ Изменить ФИО"))
    markup.add(types.KeyboardButton("✏️ Изменить группу"))
    markup.add(types.KeyboardButton("✏️ Изменить факультет"))
    markup.add(types.KeyboardButton("✏️ Изменить возраст"))
    markup.add(types.KeyboardButton("🔙 Назад"))
    bot.send_message(message.chat.id, "✏️ Выберите поле для редактирования:", reply_markup=markup)

# ========== РЕДАКТИРОВАНИЕ ФИО ==========
@bot.message_handler(func=lambda message: message.text == "✏️ Изменить ФИО")
def edit_full_name(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🔙 Назад"))
    msg = bot.send_message(message.chat.id, "✍️ Введите новое ФИО:", reply_markup=markup)
    bot.register_next_step_handler(msg, process_full_name)

def process_full_name(message):
    if message.text == "🔙 Назад":
        return show_edit_menu(message)
    
    try:
        cursor.execute('UPDATE saved_applications SET full_name=? WHERE user_id=?', 
                      (message.text, message.from_user.id))
        conn.commit()
        bot.send_message(message.chat.id, "✅ ФИО успешно обновлено!")
    except Exception as e:
        bot.send_message(message.chat.id, "❌ Ошибка при сохранении!")
    
    show_edit_menu(message)

# ========== РЕДАКТИРОВАНИЕ ГРУППЫ ==========
@bot.message_handler(func=lambda message: message.text == "✏️ Изменить группу")
def edit_group(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🔙 Назад"))
    msg = bot.send_message(message.chat.id, "🏫 Введите новую группу:", reply_markup=markup)
    bot.register_next_step_handler(msg, process_group)

def process_group(message):
    if message.text == "🔙 Назад":
        return show_edit_menu(message)
    
    try:
        cursor.execute('UPDATE saved_applications SET group_name=? WHERE user_id=?', 
                      (message.text, message.from_user.id))
        conn.commit()
        bot.send_message(message.chat.id, "✅ Группа успешно обновлена!")
    except Exception as e:
        bot.send_message(message.chat.id, "❌ Ошибка при сохранении!")
    
    show_edit_menu(message)

# ========== РЕДАКТИРОВАНИЕ ФАКУЛЬТЕТА ==========
@bot.message_handler(func=lambda message: message.text == "✏️ Изменить факультет")
def edit_faculty(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    faculties = [
        "Лесной",
        "Лесопромышленный",
        "Экономический",
        "Факультет компьютерных наук и технологий (ФКНиТ)",
        "Машиностроительный",
        "Автомобильный"
    ]
    markup.add(*[types.KeyboardButton(f) for f in faculties])
    markup.add(types.KeyboardButton("🔙 Назад"))
    msg = bot.send_message(message.chat.id, "🏛 Выберите факультет:", reply_markup=markup)
    bot.register_next_step_handler(msg, process_faculty)

def process_faculty(message):
    if message.text == "🔙 Назад":
        return show_edit_menu(message)
    
    valid_faculties = [
        "Лесной",
        "Лесопромышленный",
        "Экономический",
        "Факультет компьютерных наук и технологий (ФКНиТ)",
        "Машиностроительный",
        "Автомобильный"
    ]
    
    if message.text not in valid_faculties:
        bot.send_message(message.chat.id, "⚠️ Выберите факультет из списка!")
        return edit_faculty(message)
    
    try:
        cursor.execute('UPDATE saved_applications SET faculty=? WHERE user_id=?', 
                      (message.text, message.from_user.id))
        conn.commit()
        bot.send_message(message.chat.id, f"✅ Факультет обновлен: {message.text}")
    except Exception as e:
        bot.send_message(message.chat.id, "❌ Ошибка при сохранении!")
    
    show_edit_menu(message)

# ========== РЕДАКТИРОВАНИЕ ВОЗРАСТА ==========
@bot.message_handler(func=lambda message: message.text == "✏️ Изменить возраст")
def edit_age(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🔙 Назад"))
    msg = bot.send_message(message.chat.id, "🎂 Введите ваш возраст:", reply_markup=markup)
    bot.register_next_step_handler(msg, process_age)

def process_age(message):
    if message.text == "🔙 Назад":
        return show_edit_menu(message)
    
    try:
        age = int(message.text)
        cursor.execute('UPDATE saved_applications SET age=? WHERE user_id=?', 
                      (age, message.from_user.id))
        conn.commit()
        bot.send_message(message.chat.id, "✅ Возраст успешно обновлен!")
    except ValueError:
        bot.send_message(message.chat.id, "⚠️ Пожалуйста, введите число!")
        edit_age(message)
    except Exception as e:
        bot.send_message(message.chat.id, "❌ Ошибка при сохранении!")
    
    show_edit_menu(message)

# ========== ОБРАБОТКА НАВИГАЦИИ ==========
@bot.message_handler(func=lambda message: message.text == "🔙 Назад")
def handle_back(message):
    try:
        # Определяем текущий контекст
        if message.text == "🔙 Назад":
            if message.reply_to_message and "редактирования" in message.reply_to_message.text:
                show_edit_menu(message)
            else:
                show_profile_menu(message)
    except:
        show_main_menu(message)


# Обработка команды "Показать мероприятия"
@bot.message_handler(func=lambda message: message.text == "🟢 Список мероприятий")
def show_events(message):
    try:
        cursor.execute('SELECT name FROM events')
        events = cursor.fetchall()
        
        if events:
            markup = types.InlineKeyboardMarkup()
            for event in events:
                button = types.InlineKeyboardButton(event[0], callback_data=event[0])
                markup.add(button)
            bot.send_message(message.chat.id, "Ближайшие мероприятия:", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "Нет ближайших мероприятий.")
    
    except sqlite3.Error as e:
        print(f"Ошибка при получении списка мероприятий: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при получении данных.")
    
    except Exception as e:
        print(f"Общая ошибка при показе мероприятий: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")

@bot.callback_query_handler(func=lambda call: call.data in [event[0] for event in cursor.execute('SELECT name FROM events').fetchall()])
def handle_event_selection(call):
    try:
        selected_event = call.data
        cursor.execute('SELECT description FROM events WHERE name = ?', (selected_event,))
        event_info = cursor.fetchone()
        
        if event_info:
            bot.send_message(call.message.chat.id, f"Информация о мероприятии '{selected_event}':\n{event_info[0]}")
        else:
            bot.send_message(call.message.chat.id, "Выбранное мероприятие не найдено.")
    
    except sqlite3.Error as e:
        print(f"Ошибка при получении информации о мероприятии: {e}")
        bot.send_message(call.message.chat.id, "Произошла ошибка при получении данных.")
    
    except Exception as e:
        print(f"Общая ошибка при показе информации о мероприятии: {e}")
        bot.send_message(call.message.chat.id, "Произошла ошибка.")


@bot.message_handler(func=lambda message: message.text == "🟢 Список участников")
def show_participants_menu(message):
    try:
        if message.from_user.id in ADMIN_IDS:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.add(types.KeyboardButton("📅 Участники мероприятий"))
            markup.add(types.KeyboardButton("📋 Участники заданий"))
            markup.add(types.KeyboardButton("❌ Выйти в главное меню"))
            
            bot.send_message(message.chat.id, "Выберите тип списка участников:", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "Эта функция доступна только администраторам.")
    
    except Exception as e:
        print(f"Ошибка при отображении меню участников: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")
@bot.message_handler(func=lambda message: message.text in ["📅 Участники мероприятий", "📋 Участники заданий"])
def handle_participants_selection(message):
    try:
        if message.text == "📅 Участники мероприятий":
            show_events_for_participants(message)
        elif message.text == "📋 Участники заданий":
            show_tasks_for_participants(message)
    
    except Exception as e:
        print(f"Ошибка при обработке выбора списка участников: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")
def show_events_for_participants(message):
    try:
        cursor.execute('SELECT name FROM events')
        events = cursor.fetchall()
        
        if events:
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
            for event in events:
                markup.add(event[0])
            markup.add(types.KeyboardButton("❌ Выйти в главное меню"))
            
            bot.send_message(message.chat.id, "Выберите мероприятие для просмотра участников:", reply_markup=markup)
            bot.register_next_step_handler(message, select_event_for_participants)
        else:
            bot.send_message(message.chat.id, "Нет мероприятий.")
    
    except Exception as e:
        print(f"Ошибка при получении списка мероприятий: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")
def show_tasks_for_participants(message):
    try:
        cursor.execute('SELECT name FROM tasks')
        tasks = cursor.fetchall()
        
        if tasks:
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
            for task in tasks:
                markup.add(task[0])
            markup.add(types.KeyboardButton("❌ Выйти в главное меню"))
            
            bot.send_message(message.chat.id, "Выберите задание для просмотра участников:", reply_markup=markup)
            bot.register_next_step_handler(message, select_task_for_participants)
        else:
            bot.send_message(message.chat.id, "Нет заданий.")
    
    except Exception as e:
        print(f"Ошибка при получении списка заданий: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")
def select_event_for_participants(message):
    try:
        if message.text.strip() == "❌ Выйти в главное меню":
            cancel_action(message)
            return

        selected_event = message.text.strip()
        cursor.execute('SELECT id FROM events WHERE name = ?', (selected_event,))
        event_id_result = cursor.fetchone()

        if event_id_result:
            event_id = event_id_result[0]

            # Получаем участников с подтвержденными заявками
            cursor.execute('''
                SELECT full_name, group_name, faculty, user_id 
                FROM applications 
                WHERE event_id = ? AND status = "подтверждена"
            ''', (event_id,))
            
            participants = cursor.fetchall()
            
            if participants:
                participants_message = f"Участники мероприятия '{selected_event}':\n\n"
                for participant in participants:
                    full_name, group_name, faculty, user_id = participant
                    
                    # Получаем username пользователя из Telegram
                    try:
                        chat = bot.get_chat(user_id)
                        username = f"@{chat.username}" if chat.username else "Нет username"
                    except Exception as e:
                        print(f"Ошибка при получении username: {e}")
                        username = "Нет username"
                    
                    participants_message += f"{full_name} - {group_name} ({faculty}) - {username}\n"
                
                bot.send_message(message.chat.id, participants_message)
            else:
                bot.send_message(message.chat.id, "Нет участников для этого мероприятия.")
        else:
            bot.send_message(message.chat.id, "Выбранное мероприятие не найдено.")
    
    except Exception as e:
        print(f"Ошибка при показе участников мероприятия: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")
def show_tasks_for_participants(message):
    try:
        cursor.execute('SELECT name FROM tasks')
        tasks = cursor.fetchall()
        
        if tasks:
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
            for task in tasks:
                markup.add(task[0])
            markup.add(types.KeyboardButton("❌ Выйти в главное меню"))
            
            bot.send_message(message.chat.id, "Выберите задание для просмотра участников:", reply_markup=markup)
            bot.register_next_step_handler(message, select_task_for_participants)
        else:
            bot.send_message(message.chat.id, "Нет заданий.")
    
    except Exception as e:
        print(f"Ошибка при получении списка заданий: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")
def select_event_for_participants(message):
    try:
        if message.text.strip() == "❌ Выйти в главное меню":
            cancel_action(message)
            return

        selected_event = message.text.strip()
        cursor.execute('SELECT id FROM events WHERE name = ?', (selected_event,))
        event_id_result = cursor.fetchone()

        if event_id_result:
            event_id = event_id_result[0]

            # Получаем участников с подтвержденными заявками
            cursor.execute('''
                SELECT full_name, group_name, faculty, user_id 
                FROM applications 
                WHERE event_id = ? AND status = "подтверждена"
            ''', (event_id,))
            
            participants = cursor.fetchall()
            
            if participants:
                participants_message = f"Участники мероприятия '{selected_event}':\n\n"
                for participant in participants:
                    full_name, group_name, faculty, user_id = participant
                    
                    # Получаем username пользователя из Telegram
                    try:
                        chat = bot.get_chat(user_id)
                        username = f"@{chat.username}" if chat.username else "Нет username"
                    except Exception as e:
                        print(f"Ошибка при получении username: {e}")
                        username = "Нет username"
                    
                    participants_message += f"{full_name} - {group_name} ({faculty}) - {username}\n"
                
                bot.send_message(message.chat.id, participants_message)
            else:
                bot.send_message(message.chat.id, "Нет участников для этого мероприятия.")
        else:
            bot.send_message(message.chat.id, "Выбранное мероприятие не найдено.")
    
    except Exception as e:
        print(f"Ошибка при показе участников мероприятия: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")
def select_task_for_participants(message):
    try:
        if message.text.strip() == "❌ Выйти в главное меню":
            cancel_action(message)
            return

        selected_task = message.text.strip()
        cursor.execute('SELECT id FROM tasks WHERE name = ?', (selected_task,))
        task_id_result = cursor.fetchone()

        if task_id_result:
            task_id = task_id_result[0]

            # Получаем участников задания
            cursor.execute('''
                SELECT full_name, group_name, faculty, user_id 
                FROM task_applications 
                WHERE task_id = ?
            ''', (task_id,))
            
            participants = cursor.fetchall()
            
            if participants:
                participants_message = f"Участники задания '{selected_task}':\n\n"
                for participant in participants:
                    full_name, group_name, faculty, user_id = participant
                    
                    # Получаем username пользователя из Telegram
                    try:
                        chat = bot.get_chat(user_id)
                        username = f"@{chat.username}" if chat.username else "Нет username"
                    except Exception as e:
                        print(f"Ошибка при получении username: {e}")
                        username = "Нет username"
                    
                    participants_message += f"{full_name} - {group_name} ({faculty}) - {username}\n"
                
                bot.send_message(message.chat.id, participants_message)
            else:
                bot.send_message(message.chat.id, "Нет участников для этого задания.")
        else:
            bot.send_message(message.chat.id, "Выбранное задание не найдено.")
    
    except Exception as e:
        print(f"Ошибка при показе участников задания: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")
# Обработчик выбора мероприятия
@bot.callback_query_handler(func=lambda call: True)
def handle_event_selection(call):
    try:
        selected_event = call.data
        
        cursor.execute('SELECT description FROM events WHERE name = ?', (selected_event,))
        event_info = cursor.fetchone()

        if event_info:
            bot.send_message(call.message.chat.id, f"Информация о мероприятии '{selected_event}':\n{event_info[0]}")
        else:
            bot.send_message(call.message.chat.id, "Выбранное мероприятие не найдено.")
    
    except sqlite3.Error as e:
        print(f"Ошибка при получении информации о мероприятии: {e}")
        bot.send_message(call.message.chat.id, "Произошла ошибка при получении данных.")
    
    except Exception as e:
        print(f"Общая ошибка при показе информации о мероприятии: {e}")
        bot.send_message(call.message.chat.id, "Произошла ошибка.")

from telebot import types

# Функция для создания клавиатуры с кнопками "Да" и "Нет"
def create_yes_no_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn_yes = types.KeyboardButton("Да")
    btn_no = types.KeyboardButton("Нет")
    markup.add(btn_yes, btn_no)
    return markup

from telebot import types

# Функция для создания клавиатуры с факультетами
def create_faculty_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn_forest = types.KeyboardButton("Лесной")
    btn_forest_industry = types.KeyboardButton("Лесопромышленный")
    btn_economics = types.KeyboardButton("Экономический")
    btn_computer_science = types.KeyboardButton("Факультет компьютерных наук и технологий (ФКНиТ)")
    btn_mechanical = types.KeyboardButton("Машиностроительный")
    btn_automotive = types.KeyboardButton("Автомобильный")
    btn_cancel = types.KeyboardButton("❌ Выйти в главное меню")
    markup.add(btn_forest, btn_forest_industry, btn_economics, btn_computer_science, btn_mechanical, btn_automotive, btn_cancel)
    return markup

# Функция для создания клавиатуры с кнопками "Да", "Нет" и "❌ Выйти в главное меню"
def create_yes_no_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn_yes = types.KeyboardButton("Да")
    btn_no = types.KeyboardButton("Нет")
    btn_cancel = types.KeyboardButton("❌ Выйти в главное меню")
    markup.add(btn_yes, btn_no, btn_cancel)
    return markup

@bot.message_handler(func=lambda message: message.text == "🟢 Записаться на мероприятие")
def get_event_for_application(message):
    try:
        cursor.execute('SELECT name FROM events')
        events = cursor.fetchall()

        if events:
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
            for event in events:
                markup.add(event[0])
            markup.add(types.KeyboardButton("❌ Выйти в главное меню"))  
            bot.send_message(message.chat.id, "Выберите мероприятие для записи:", reply_markup=markup)
            bot.register_next_step_handler(message, handle_event_selection_for_application)
        else:
            bot.send_message(message.chat.id, "Нет мероприятий для записи.")
    
    except sqlite3.Error as e:
        print(f"Ошибка при получении списка мероприятий: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при получении данных.")
    
    except Exception as e:
        print(f"Общая ошибка при показе списка мероприятий: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")

def handle_event_selection_for_application(message):
    try:
        if message.text.strip() == "❌ Выйти в главное меню":  
            cancel_action(message)
            return

        selected_event = message.text.strip()
        cursor.execute('SELECT id FROM events WHERE name = ?', (selected_event,))
        event_id_result = cursor.fetchone()

        if event_id_result:
            event_id = event_id_result[0]

            # Проверка существующей заявки
            cursor.execute('SELECT id, status FROM applications WHERE event_id=? AND user_id=?', (event_id, message.from_user.id))
            existing_application = cursor.fetchone()

            if existing_application:
                if existing_application[1] == "отменена":
                    # Если заявка отменена, обновляем статус на "подтверждена"
                    cursor.execute('UPDATE applications SET status = "подтверждена" WHERE id = ?', (existing_application[0],))
                    conn.commit()
                    bot.send_message(message.chat.id, "Ваша заявка восстановлена.")
                    return
                elif existing_application[1] == "подтверждена":
                    bot.send_message(message.chat.id, "Вы уже подали заявку на это мероприятие.")
                    return
            else:
                # Если заявки нет, создаем новую
                cursor.execute('SELECT * FROM saved_applications WHERE user_id=?', (message.from_user.id,))
                saved_data = cursor.fetchone()

                if saved_data:
                    # Если возраст уже сохранен, пропускаем запрос возраста
                    if saved_data[4]:  # Проверяем, есть ли возраст в сохраненных данных
                        bot.send_message(
                            message.chat.id,
                            "Нужно ли вам освобождение?",
                            reply_markup=create_yes_no_keyboard()
                        )
                        bot.register_next_step_handler(message, lambda msg: ask_for_volunteer_hours(msg, saved_data[1], saved_data[2], saved_data[3], event_id, saved_data[4]))
                    else:
                        # Если возраст не сохранен, запрашиваем его
                        bot.send_message(message.chat.id, "Введите ваш возраст:")
                        bot.register_next_step_handler(message, lambda msg: save_age_and_continue(msg, saved_data[1], saved_data[2], saved_data[3], event_id))
                else:
                    bot.send_message(message.chat.id, "Введите ваше ФИО:")
                    bot.register_next_step_handler(message, lambda msg: ask_for_group(msg, event_id))
        else:
            bot.send_message(message.chat.id, "Выбранное мероприятие не найдено.")
    
    except sqlite3.Error as e:
        print(f"Ошибка при обработке выбора мероприятия: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при обработке данных.")
    
    except Exception as e:
        print(f"Общая ошибка при обработке выбора мероприятия: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")

def save_age_and_continue(message, full_name, group_name, faculty, event_id):
    try:
        if message.text.strip() == "❌ Выйти в главное меню":  
            cancel_action(message)
            return

        age = int(message.text.strip())
        
        # Сохраняем возраст в таблице saved_applications
        cursor.execute('UPDATE saved_applications SET age=? WHERE user_id=?', (age, message.from_user.id))
        conn.commit()

        bot.send_message(
            message.chat.id,
            "Нужно ли вам освобождение?",
            reply_markup=create_yes_no_keyboard()
        )
        bot.register_next_step_handler(message, lambda msg: ask_for_volunteer_hours(msg, full_name, group_name, faculty, event_id, age))
    
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректный возраст (число).")
        bot.register_next_step_handler(message, lambda msg: save_age_and_continue(msg, full_name, group_name, faculty, event_id))
    except Exception as e:
        print(f"Ошибка при сохранении возраста: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")

def ask_for_group(message, event_id):
    try:
        if message.text.strip() == "❌ Выйти в главное меню":  
            cancel_action(message)
            return

        full_name = message.text.strip()
        
        # Валидация ФИО (например, проверка на длину)
        if len(full_name) > 80:
            bot.send_message(message.chat.id, "ФИО слишком длинное. Пожалуйста, сократите.")
            return
        
        bot.send_message(message.chat.id, "Введите вашу группу:")
        bot.register_next_step_handler(message, lambda msg: ask_for_faculty(msg, full_name, event_id))
    
    except Exception as e:
        print(f"Ошибка при получении группы: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")

def ask_for_faculty(message, full_name, event_id):
    try:
        if message.text.strip() == "❌ Выйти в главное меню":  
            cancel_action(message)
            return

        group_name = message.text.strip()
        
        # Валидация группы (например, проверка на длину)
        if len(group_name) > 50:
            bot.send_message(message.chat.id, "Группа слишком длинная. Пожалуйста, сократите.")
            return
        
        # Отправляем клавиатуру с факультетами
        bot.send_message(
            message.chat.id,
            "Выберите ваш факультет:",
            reply_markup=create_faculty_keyboard()
        )
        bot.register_next_step_handler(message, lambda msg: handle_faculty_selection(msg, full_name, group_name, event_id))
    
    except Exception as e:
        print(f"Ошибка при получении факультета: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")

def handle_faculty_selection(message, full_name, group_name, event_id):
    try:
        if message.text.strip() == "❌ Выйти в главное меню":  
            cancel_action(message)
            return

        faculty = message.text.strip()
        
        # Проверяем, что выбранный факультет есть в списке
        valid_faculties = [
            "Лесной",
            "Лесопромышленный",
            "Экономический",
            "Факультет компьютерных наук и технологий (ФКНиТ)",
            "Машиностроительный",
            "Автомобильный"
        ]
        
        if faculty not in valid_faculties:
            bot.send_message(
                message.chat.id,
                "Пожалуйста, выберите факультет из списка.",
                reply_markup=create_faculty_keyboard()
            )
            bot.register_next_step_handler(message, lambda msg: handle_faculty_selection(msg, full_name, group_name, event_id))
            return
        
        # Если факультет выбран корректно, переходим к следующему шагу
        bot.send_message(message.chat.id, "Введите ваш возраст:")
        bot.register_next_step_handler(message, lambda msg: save_age_and_continue(msg, full_name, group_name, faculty, event_id))
    
    except Exception as e:
        print(f"Ошибка при выборе факультета: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")

def ask_for_volunteer_hours(message, full_name, group_name, faculty, event_id, age):
    try:
        if message.text.strip() == "❌ Выйти в главное меню":  
            cancel_action(message)
            return

        # Проверяем, какой ответ выбрал пользователь
        if message.text.strip().lower() == "да":
            needs_release = 1
        elif message.text.strip().lower() == "нет":
            needs_release = 0
        else:
            # Если пользователь ввел что-то другое, просим повторить
            bot.send_message(
                message.chat.id,
                "Пожалуйста, выберите 'Да' или 'Нет'.",
                reply_markup=create_yes_no_keyboard()
            )
            bot.register_next_step_handler(message, lambda msg: ask_for_volunteer_hours(msg, full_name, group_name, faculty, event_id, age))
            return

        # Задаем следующий вопрос с кнопками "Да", "Нет" и "❌ Выйти в главное меню"
        bot.send_message(
            message.chat.id,
            "Нужны ли вам волонтёрские часы?",
            reply_markup=create_yes_no_keyboard()
        )
        bot.register_next_step_handler(message, lambda msg: submit_application(msg, full_name, group_name, faculty, event_id, needs_release, age))
    
    except Exception as e:
        print(f"Ошибка при получении информации о волонтёрских часах: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")

def submit_application(message, full_name, group_name, faculty, event_id, needs_release, age):
    try:
        if message.text.strip() == "❌ Выйти в главное меню":  
            cancel_action(message)
            return

        user_id = message.from_user.id

        # Проверяем, какой ответ выбрал пользователь
        if message.text.strip().lower() == "да":
            needs_volunteer_hours = 1
        elif message.text.strip().lower() == "нет":
            needs_volunteer_hours = 0
        else:
            # Если пользователь ввел что-то другое, просим повторить
            bot.send_message(
                message.chat.id,
                "Пожалуйста, выберите 'Да' или 'Нет'.",
                reply_markup=create_yes_no_keyboard()
            )
            bot.register_next_step_handler(message, lambda msg: submit_application(msg, full_name, group_name, faculty, event_id, needs_release, age))
            return

        # Проверяем текущее количество заявок на мероприятие
        cursor.execute('SELECT COUNT(*) FROM applications WHERE event_id=?', (event_id,))
        current_count = cursor.fetchone()[0]

        cursor.execute('SELECT max_participants FROM events WHERE id=?', (event_id,))
        max_participants = cursor.fetchone()[0]

        # Проверка на None
        if max_participants is None:
            # Если max_participants равно None, считаем, что количество участников не ограничено
            pass
        elif current_count >= max_participants:
            bot.send_message(user_id, "Извините, максимальное количество участников на это мероприятие уже достигнуто.")
            return

        # Вставляем заявку в базу данных
        cursor.execute(
            'INSERT INTO applications (full_name, group_name, faculty, event_id, user_id, needs_release, needs_volunteer_hours, age) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (full_name, group_name, faculty, event_id, user_id, needs_release, needs_volunteer_hours, age)
        )
        
        conn.commit()

        # Получаем название мероприятия и ссылку на него
        cursor.execute('SELECT name, link FROM events WHERE id=?', (event_id,))
        event_info = cursor.fetchone()
        
        if event_info:
            event_name = event_info[0]
            event_link = event_info[1]  # Получаем ссылку на мероприятие

            cursor.execute('INSERT OR REPLACE INTO saved_applications (user_id, full_name, group_name, faculty, age) VALUES (?, ?, ?, ?, ?)', 
                           (user_id, full_name, group_name, faculty, age))
            
            conn.commit()

            # Получаем username пользователя
            username = message.from_user.username
            if not username:  # Если username отсутствует, используем first_name
                username = message.from_user.first_name

            # Отправляем заявку администратору с username пользователя
            for admin in ADMIN_IDS:
                bot.send_message(
                    admin,
                    f"Новая заявка:\n"
                    f"Пользователь: @{username}\n"
                    f"ФИО: {full_name}\n"
                    f"Группа: {group_name}\n"
                    f"Факультет: {faculty}\n"
                    f"Возраст: {age}\n"
                    f"Мероприятие: {event_name}\n"
                    f"Нужно освобождение: {'Да' if needs_release else 'Нет'}\n"
                    f"Нужны волонтёрские часы: {'Да' if needs_volunteer_hours else 'Нет'}"
                )
            
            # Отправляем пользователю сообщение о статусе заявки
            if needs_volunteer_hours == 1:
                bot.send_message(user_id, f"Ваша заявка отправлена!")
            else:
                bot.send_message(user_id, "Ваша заявка отправлена! Вы не запросили волонтёрские часы.")
        else:
            bot.send_message(user_id, "Произошла ошибка при получении информации о мероприятии.")
    
    except sqlite3.Error as e:
        print(f"Ошибка при отправке заявки: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при отправке заявки.")
    
    except Exception as e:
        print(f"Общая ошибка при отправке заявки: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")


import pandas as pd

@bot.message_handler(func=lambda message: message.text == "🟢 Экспорт данных о мероприятии")
def export_event_data(message):
    try:
        if message.from_user.id in ADMIN_IDS:
            cursor.execute('SELECT name FROM events')
            events = cursor.fetchall()

            if events:
                markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
                for event in events:
                    markup.add(event[0])
                markup.add(types.KeyboardButton("❌ Выйти в главное меню"))  
                bot.send_message(message.chat.id, "Выберите мероприятие для экспорта данных:", reply_markup=markup)
                bot.register_next_step_handler(message, handle_event_selection_for_export)
            else:
                bot.send_message(message.chat.id, "Нет мероприятий для экспорта данных.")
    
    except sqlite3.Error as e:
        print(f"Ошибка при получении списка мероприятий: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при получении данных.")
    
    except Exception as e:
        print(f"Общая ошибка при экспорте данных: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")

def handle_event_selection_for_export(message):
    try:
        if message.text.strip() == "❌ Выйти в главное меню":
            cancel_action(message)
            return

        selected_event = message.text.strip()
        cursor.execute('SELECT id FROM events WHERE name=?', (selected_event,))
        event_id_result = cursor.fetchone()

        if not event_id_result:
            bot.send_message(message.chat.id, "Выбранное мероприятие не найдено.")
            return

        event_id = event_id_result[0]

        # Получаем данные о заявках на выбранное мероприятие
        cursor.execute('''
            SELECT full_name, group_name, faculty, needs_release, needs_volunteer_hours, status 
            FROM applications 
            WHERE event_id=?
        ''', (event_id,))
        
        applications = cursor.fetchall()

        if not applications:
            bot.send_message(message.chat.id, "Нет заявок на это мероприятие.")
            return

        # Создание DataFrame и запись в Excel
        df = pd.DataFrame(applications, columns=["ФИО", "Группа", "Факультет", "Нужно освобождение", "Нужны волонтёрские часы", "Статус"])
        
        # Заменяем булевы значения на более читабельные
        df["Нужно освобождение"] = df["Нужно освобождение"].map({0: 'Нет', 1: 'Да'})
        df["Нужны волонтёрские часы"] = df["Нужны волонтёрские часы"].map({0: 'Нет', 1: 'Да'})
        df["Статус"] = df["Статус"].map({"подтверждена": "Подтверждена", "отменена": "Отменена"})

        # Сохранение DataFrame в Excel файл на диске
        file_path = f"{selected_event}.xlsx"
        df.to_excel(file_path, index=False, sheet_name='Заявки')

        # Отправка файла пользователю
        with open(file_path, 'rb') as file:
            bot.send_document(
                message.chat.id,
                file,
                caption=f"Данные по мероприятию '{selected_event}'"
            )

        # Удаление файла после отправки
        import os
        os.remove(file_path)
    
    except sqlite3.Error as e:
        print(f"Ошибка при получении заявок: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при получении данных.")
    
    except Exception as e:
        print(f"Общая ошибка при экспорте данных: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")



# Обработка нажатия кнопки "Выйти в главное меню"
@bot.message_handler(func=lambda message: message.text == "❌ Выйти в главное меню")
def cancel_action(message):
    bot.send_message(message.chat.id, "Вы вернулись в главное меню.")
    show_main_menu(message)


@bot.message_handler(func=lambda message: message.text == "🔗 Запросить ссылку на волонтерские часы")
def request_event_link(message):
    try:
        print("Запрос ссылки на мероприятие получен.")  # Отладочное сообщение
        cursor.execute('SELECT name FROM events')
        events = cursor.fetchall()

        if events:
            # Получаем список мероприятий, на которые пользователь записан и не отменил участие
            cursor.execute('''
                SELECT event_id 
                FROM applications 
                WHERE user_id = ? AND status != "отменена"
            ''', (message.from_user.id,))
            user_events = cursor.fetchall()
            user_event_ids = [event[0] for event in user_events]

            available_events = []
            for event in events:
                event_id = cursor.execute('SELECT id FROM events WHERE name = ?', (event[0],)).fetchone()[0]
                if event_id in user_event_ids:
                    available_events.append(event[0])

            if available_events:
                markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
                for event in available_events:
                    markup.add(event)
                markup.add(types.KeyboardButton("❌ Выйти в главное меню"))  
                bot.send_message(
                    message.chat.id, "Выберите мероприятие для запроса ссылки:", reply_markup=markup)
                bot.register_next_step_handler(message, handle_request_link)
            else:
                bot.send_message(message.chat.id, "Вы не зарегистрированы ни на одно мероприятие или отменили все свои заявки.")
        else:
            bot.send_message(message.chat.id, "Нет мероприятий для запроса ссылки.")
    
    except sqlite3.Error as e:
        print(f"Ошибка при получении списка мероприятий: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при получении данных.")
    
    except Exception as e:
        print(f"Общая ошибка при запросе ссылки: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")


def handle_request_link(message):
    try:
        print(f"Получен выбор мероприятия: {message.text}")  # Отладочное сообщение
        selected_event = message.text.strip()
        
        if selected_event == "❌ Выйти в главное меню":
            cancel_action(message)
            return

        cursor.execute('SELECT id FROM events WHERE name=?', (selected_event,))
        event_id_result = cursor.fetchone()

        if not event_id_result:
            bot.send_message(message.chat.id, "Выбранное мероприятие не найдено.")
            return

        event_id = event_id_result[0]

        # Проверяем, зарегистрирован ли пользователь на мероприятие
        cursor.execute('SELECT * FROM applications WHERE user_id=? AND event_id=?', (message.from_user.id, event_id))
        registration = cursor.fetchone()

        if not registration:
            print(f"Пользователь {message.from_user.id} не зарегистрирован на мероприятие {event_id}.")
            bot.send_message(message.chat.id, "Вы не зарегистрированы на это мероприятие. Запрос не может быть выполнен.")
            return

        # Если пользователь зарегистрирован, продолжаем с запросом ссылки
        for admin in ADMIN_IDS:
            bot.send_message(admin, f"Пользователь {message.from_user.first_name} запрашивает ссылку на мероприятие '{selected_event}'.")

        bot.send_message(message.chat.id, "Запрос на ссылку отправлен!")
    
    except sqlite3.Error as e:
        print(f"Ошибка при обработке запроса ссылки: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при обработке данных.")
    
    except Exception as e:
        print(f"Общая ошибка при запросе ссылки: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")


# Обработка команды "Отправить ссылку"
@bot.message_handler(func=lambda message: message.text == "🟢 Отправить ссылку на получение часов")
def prompt_send_link(message):
    try:
        if message.from_user.id in ADMIN_IDS:
            cursor.execute('SELECT name FROM events')
            events = cursor.fetchall()

            if events:
                markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
                for event in events:
                    markup.add(event[0])  
                markup.add(types.KeyboardButton("❌ Выйти в главное меню"))  
                bot.send_message(message.chat.id, "Выберите мероприятие для отправки ссылки:", reply_markup=markup)
                bot.register_next_step_handler(message, select_event_for_link)
            else:
                bot.send_message(message.chat.id, "Нет мероприятий для отправки ссылки.")
    
    except sqlite3.Error as e:
        print(f"Ошибка при получении списка мероприятий: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при получении данных.")
    
    except Exception as e:
        print(f"Общая ошибка при отправке ссылки: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")

def select_event_for_link(message):
    try:
        selected_event = message.text.strip()
        
        if selected_event == "❌ Выйти в главное меню":
            cancel_action(message)
            return

        cursor.execute('SELECT id FROM events WHERE name=?', (selected_event,))
        event_id_result = cursor.fetchone()

        if not event_id_result:
            bot.send_message(message.chat.id, "Выбранное мероприятие не найдено.")
            return

        event_id = event_id_result[0]
        
        # Получаем пользователей с подтвержденным участием
        cursor.execute('''
            SELECT user_id 
            FROM applications 
            WHERE event_id = ? AND status = "подтверждена"
        ''', (event_id,))
        users = cursor.fetchall()

        if users:
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
            for user in users:
                cursor.execute('SELECT full_name FROM applications WHERE user_id=? AND event_id=?', (user[0], event_id))
                full_name = cursor.fetchone()[0]
                markup.add(full_name)  # Отображаем полное ФИО
            markup.add(types.KeyboardButton("❌ Выйти в главное меню"))  
            bot.send_message(message.chat.id, "Выберите пользователя для отправки ссылки:", reply_markup=markup)
            bot.register_next_step_handler(message, lambda msg: ask_for_link(msg, event_id))
        else:
            bot.send_message(message.chat.id, "Нет пользователей с подтвержденным участием на это мероприятие.")
    
    except sqlite3.Error as e:
        print(f"Ошибка при получении пользователей: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при получении данных.")
    
    except Exception as e:
        print(f"Общая ошибка при выборе мероприятия: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")


def ask_for_link(message, event_id):
    try:
        selected_user_name = message.text.strip()
        
        if selected_user_name == "❌ Выйти в главное меню":
            cancel_action(message)
            return

        cursor.execute('SELECT user_id FROM applications WHERE event_id=?', (event_id,))
        users = cursor.fetchall()
        
        selected_user = None
        
        for user in users:
            cursor.execute('SELECT full_name FROM applications WHERE user_id=? AND event_id=?', (user[0], event_id))
            full_name = cursor.fetchone()[0]
            if full_name == selected_user_name:
                selected_user = user[0]  
                break

        if selected_user is None:
            bot.send_message(message.chat.id, "Пользователь не найден.")
            return

        # Добавляем кнопку отмены здесь
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("❌ Выйти в главное меню"))
        
        bot.send_message(message.chat.id, "Введите ссылку на мероприятие:", reply_markup=markup)
        
        bot.register_next_step_handler(message, lambda msg: send_link_to_user(msg, selected_user))
    
    except sqlite3.Error as e:
        print(f"Ошибка при получении пользователя: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при получении данных.")
    
    except Exception as e:
        print(f"Общая ошибка при запросе ссылки: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")

def send_link_to_user(message, selected_user):
    try:
        if message.text.strip() == '❌ Выйти в главное меню':
            cancel_action(message)
            return
        
        link = message.text.strip()
        
        # Валидация ссылки (например, проверка на длину)
        if len(link) > 200:
            bot.send_message(message.chat.id, "Ссылка слишком длинная. Пожалуйста, сократите.")
            return
        
        bot.send_message(selected_user, f"Ссылка на мероприятие: {link}")
       
        bot.send_message(message.chat.id, "Ссылка успешно отправлена выбранному пользователю!")
    
    except Exception as e:
        print(f"Общая ошибка при отправке ссылки: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")



def send_link_to_user(message, selected_user):
    if message.text.strip() == '❌ Выйти в главное меню':
        cancel_action(message)
        return
    
    link = message.text.strip()
    
    bot.send_message(selected_user, f"Ссылка на мероприятие: {link}")
   
    bot.send_message(message.chat.id, "Ссылка успешно отправлена выбранному пользователю!")

# Обработка нажатия кнопки "Выйти в главное меню"
@bot.message_handler(func=lambda message: message.text == "❌ Выйти в главное меню")
def cancel_action(message):
      bot.send_message(
          message.chat.id,"Вы вернулись в главное меню.")
      show_main_menu(message) 

@bot.message_handler(func=lambda message: message.text in ["🔢 Мои баллы"])
def show_user_points(message):
    try:
        user_id = message.from_user.id
        
        # Запрос к базе данных для получения баллов пользователя
        cursor.execute('SELECT points FROM user_points WHERE user_id=?', (user_id,))
        result = cursor.fetchone()

        if result:
            points = result[0]
            bot.send_message(message.chat.id, f"У тебя {points} баллов! 🎉 Как думаешь, сколько еще сможешь набрать? 😊")
        else:
            bot.send_message(message.chat.id, "У тебя пока нет баллов. 😔 Но ты можешь начать прямо сейчас! 💪")
    
    except sqlite3.Error as e:
        # Логирование ошибки базы данных
        print(f"Ошибка при получении баллов пользователя: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при получении данных. Пожалуйста, попробуйте позже.")
    
    except Exception as e:
        # Логирование общей ошибки
        print(f"Общая ошибка при показе баллов: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте позже.")

@bot.message_handler(func=lambda message: message.text == "🏆 Рейтинг")
def show_rating(message):
    try:
        cursor.execute('''
            SELECT u.full_name AS full_name, COALESCE(SUM(up.points), 0) AS total_points
            FROM saved_applications u LEFT JOIN user_points up ON u.user_id = up.user_id
            GROUP BY u.user_id
            ORDER BY total_points DESC
            LIMIT 30;
        ''')
        ratings = cursor.fetchall()

        if ratings:
            rating_list = "\n".join([f"{i + 1}. {r[0]} - {r[1]} баллов" for i, r in enumerate(ratings)])
            bot.send_message(
                message.chat.id, f"Топ 30 участников:\n{rating_list}"
            )
        else:
            bot.send_message(
                message.chat.id, "Нет данных для отображения рейтинга."
            )
    
    except sqlite3.Error as e:
        print(f"Ошибка при получении рейтинга: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при получении данных.")
    
    except Exception as e:
        print(f"Общая ошибка при показе рейтинга: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")



# Словарь для хранения данных мероприятия
# Словарь для хранения данных мероприятия
@bot.message_handler(func=lambda message: message.text == "🟢 Добавить мероприятие")
def prompt_add_event(message):
    if message.from_user.id in ADMIN_IDS:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button_name = types.KeyboardButton("Введите название")
        button_link = types.KeyboardButton("Введите ссылку")
        button_description = types.KeyboardButton("Введите описание")
        button_max_participants = types.KeyboardButton("Введите максимальное количество участников")
        button_start_time = types.KeyboardButton("Введите время начала")
        button_end_time = types.KeyboardButton("Введите время окончания")
        button_save = types.KeyboardButton("Сохранить")
        button_cancel = types.KeyboardButton("❌ Выйти в главное меню")
        
        markup.add(button_name, button_link)
        markup.add(button_description, button_max_participants)
        markup.add(button_start_time, button_end_time)
        markup.add(button_save)
        markup.add(button_cancel)
        
        bot.send_message(message.chat.id, "Выберите, что хотите ввести:", reply_markup=markup)
        
@bot.message_handler(func=lambda message: message.text == "🚫 Отказаться от участия")
def decline_participation(message):
    user_id = message.from_user.id
    
    # Получаем список мероприятий, на которые пользователь записан и не отменил участие
    cursor.execute('''
        SELECT event_id, name 
        FROM applications 
        JOIN events ON applications.event_id = events.id 
        WHERE user_id = ? AND status != "отменена"
    ''', (user_id,))
    events = cursor.fetchall()
    
    if events:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        for event in events:
            markup.add(event[1])  
        markup.add(types.KeyboardButton("❌ Выйти в главное меню"))  
        
        bot.send_message(message.chat.id, "Выберите мероприятие, от которого хотите отказаться:", reply_markup=markup)
        bot.register_next_step_handler(message, select_event_to_decline)
    else:
        bot.send_message(message.chat.id, "Вы не подали заявки на какие-либо мероприятия или уже отменили все свои заявки.")


def select_event_to_decline(message):
    if message.text.strip() == "❌ Выйти в главное меню":
        cancel_action(message)
        return

    cursor.execute('SELECT event_id, name FROM applications JOIN events ON applications.event_id = events.id WHERE user_id = ?', (message.from_user.id,))
    events = cursor.fetchall()
    
    selected_event_name = message.text.strip()
    
    for event in events:
        if event[1] == selected_event_name:
            event_id = event[0]
            break
    else:
        bot.send_message(message.chat.id, "Выбранное мероприятие не найдено.")
        return

    # Проверка времени до начала мероприятия
    cursor.execute('SELECT start_time FROM events WHERE id = ?', (event_id,))
    start_time_result = cursor.fetchone()

    if start_time_result and start_time_result[0]:  # Проверяем, что start_time_str не None
        start_time_str = start_time_result[0]
        start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M')
        current_time = datetime.now()
        
        if (start_time - current_time).total_seconds() / 3600 < 12:
            bot.send_message(message.chat.id, "Отмена участия невозможна менее чем за 12 часов до начала мероприятия. Обратитесь к администратору.")
            return
    else:
        # Если время начала не указано, автоматически отменяем участие
        cursor.execute('UPDATE applications SET status = "отменена" WHERE event_id = ? AND user_id = ?', (event_id, message.from_user.id))
        conn.commit()
        
        bot.send_message(message.chat.id, "Ваше участие в мероприятии автоматически отменено из-за отсутствия информации о времени начала.")
        
        # Отправка уведомления администратору
        cursor.execute('SELECT name FROM events WHERE id = ?', (event_id,))
        event_name = cursor.fetchone()[0]
        
        for admin in ADMIN_IDS:
            bot.send_message(
                admin,
                f"Пользователь {message.from_user.first_name} ({message.from_user.id}) отказался от участия в мероприятии '{event_name}'."
            )
        
        return

    bot.send_message(message.chat.id, "Введите причину отказа от участия:")
    bot.register_next_step_handler(message, lambda msg: decline_participation_reason(msg, event_id))


def decline_participation_reason(message, event_id):
    reason = message.text.strip()
    
    if reason == "❌ Выйти в главное меню":
        cancel_action(message)
        return

    cursor.execute('UPDATE applications SET status = "отменена" WHERE event_id = ? AND user_id = ?', (event_id, message.from_user.id))
    conn.commit()
    
    # Удаление пользователя из списка участников
    cursor.execute('SELECT full_name, group_name, faculty FROM applications WHERE event_id = ? AND user_id = ?', (event_id, message.from_user.id))
    participant_info = cursor.fetchone()
    
    if participant_info:
        cursor.execute('SELECT participants FROM events WHERE id = ?', (event_id,))
        participants = cursor.fetchone()[0]
        
        if participants:
            participants_list = participants.split(',')
            participant_string = f"{participant_info[0]} - {participant_info[1]} ({participant_info[2]})"
            
            if participant_string in participants_list:
                participants_list.remove(participant_string)
                updated_participants = ','.join(participants_list)
                cursor.execute('UPDATE events SET participants = ? WHERE id = ?', (updated_participants, event_id))
                conn.commit()
    
    # Отправка уведомления администратору
    cursor.execute('SELECT name FROM events WHERE id = ?', (event_id,))
    event_name = cursor.fetchone()[0]
    
    for admin in ADMIN_IDS:
        bot.send_message(
            admin,
            f"Пользователь {message.from_user.first_name} ({message.from_user.id}) отказался от участия в мероприятии '{event_name}'. Причина: {reason}"
        )
    
    bot.send_message(message.chat.id, "Ваше участие в мероприятии успешно отменено.")
    show_main_menu(message)



@bot.message_handler(func=lambda message: message.text in ["Введите название", "Введите ссылку", "Введите описание", "Введите максимальное количество участников", "Введите время начала", "Введите время окончания", "Сохранить", "❌ Выйти в главное меню"])
def handle_add_event_input(message):
    try:
        global event_data
        
        if message.text == "❌ Выйти в главное меню":
            bot.send_message(message.chat.id, "Вы отменили добавление мероприятия.")
            return
        
        if message.text == "Введите название":
            bot.send_message(message.chat.id, "Введите название мероприятия:")
            bot.register_next_step_handler(message, lambda msg: save_event_name(msg))
        elif message.text == "Введите ссылку":
            bot.send_message(message.chat.id, "Введите ссылку на мероприятие (или оставьте пустым):")
            bot.register_next_step_handler(message, lambda msg: save_event_link(msg))
        elif message.text == "Введите описание":
            bot.send_message(message.chat.id, "Введите описание мероприятия (или оставьте пустым):")
            bot.register_next_step_handler(message, lambda msg: save_event_description(msg))
        elif message.text == "Введите максимальное количество участников":
            bot.send_message(message.chat.id, "Введите максимальное количество участников (или оставьте пустым для неограниченного):")
            bot.register_next_step_handler(message, lambda msg: save_event_max_participants(msg))
        elif message.text == "Введите время начала":
            bot.send_message(message.chat.id, "Введите время начала мероприятия (формат: YYYY-MM-DD HH:MM):")
            bot.register_next_step_handler(message, lambda msg: save_event_start_time(msg))
        elif message.text == "Введите время окончания":
            bot.send_message(message.chat.id, "Введите время окончания мероприятия (формат: YYYY-MM-DD HH:MM) или напишите 'нет' для бесконечного мероприятия:")
            bot.register_next_step_handler(message, lambda msg: save_event_end_time(msg))
        elif message.text == "Сохранить":
            save_event_to_db(message)
            return
    
    except Exception as e:
        print(f"Общая ошибка при добавлении мероприятия: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")

def save_event_name(message):
    try:
        global event_data
        
        # Инициализируем event_data, если она еще не создана
        if 'event_data' not in globals():
            event_data = {}
        
        event_name = message.text.strip()
        
        # Валидация названия (например, проверка на длину)
        if len(event_name) > 100:
            bot.send_message(message.chat.id, "Название слишком длинное. Пожалуйста, сократите.")
            bot.register_next_step_handler(message, save_event_name)
            return
        
        if not event_name:
            bot.send_message(message.chat.id, "Название мероприятия не может быть пустым. Пожалуйста, введите название снова.")
            bot.register_next_step_handler(message, save_event_name)
            return
        
        event_data['name'] = event_name
        prompt_add_event(message)
    
    except Exception as e:
        print(f"Ошибка при сохранении названия: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")

    
    except Exception as e:
        print(f"Ошибка при сохранении названия: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")

def save_event_link(message):
    try:
        global event_data
        link = message.text.strip()
        
        # Валидация ссылки (например, проверка на длину)
        if link and len(link) > 200:
            bot.send_message(message.chat.id, "Ссылка слишком длинная. Пожалуйста, сократите.")
            bot.register_next_step_handler(message, save_event_link)
            return
        
        event_data['link'] = link or None
        prompt_add_event(message)
    
    except Exception as e:
        print(f"Ошибка при сохранении ссылки: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")

def save_event_description(message):
    try:
        global event_data
        description = message.text.strip()
        
        # Валидация описания (например, проверка на длину)
        if description and len(description) > 500:
            bot.send_message(message.chat.id, "Описание слишком длинное. Пожалуйста, сократите.")
            bot.register_next_step_handler(message, save_event_description)
            return
        
        event_data['description'] = description or None
        prompt_add_event(message)
    
    except Exception as e:
        print(f"Ошибка при сохранении описания: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")


def save_event_max_participants(message):
    try:
        global event_data
        max_participants_input = message.text.strip()
        
        if max_participants_input:
            try:
                event_data['max_participants'] = int(max_participants_input)
                if event_data['max_participants'] <= 0:
                    bot.send_message(message.chat.id, "Максимальное количество участников должно быть больше нуля.")
                    bot.register_next_step_handler(message, save_event_max_participants)
                    return
            except ValueError:
                bot.send_message(message.chat.id, "Неверный формат. Пожалуйста, введите целое число.")
                bot.register_next_step_handler(message, save_event_max_participants)
                return
        else:
            event_data['max_participants'] = None
        prompt_add_event(message)
    
    except Exception as e:
        print(f"Ошибка при сохранении максимального количества участников: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")

event_data = {}
def safe_strptime(input_str, format, message):
    try:
        return datetime.strptime(input_str, format)
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат даты и времени. Пожалуйста, введите дату и время в формате 'ГГГГ-ММ-ДД ЧЧ:ММ'.")
        bot.register_next_step_handler(message, save_event_start_time)
        return None

def save_event_start_time(message):
    start_time_input = message.text.strip()
    event_data['start_time'] = safe_strptime(start_time_input, '%Y-%m-%d %H:%M', message)
    if event_data['start_time'] is not None:
        bot.send_message(message.chat.id, "Время начала успешно сохранено.")
        prompt_add_event(message)  # Переход к следующему шагу




def save_event_end_time(message):
    end_time_input = message.text.strip()
    try:
        if end_time_input.lower() == 'нет':
            # Если пользователь вводит "нет", конец события не указывается
            event_data['end_time'] = None
            bot.send_message(message.chat.id, "Время окончания не указано.")
            prompt_add_event(message)  # Переход к следующему шагу
        else:
            # Попытка преобразования строки в дату и время
            event_data['end_time'] = datetime.strptime(end_time_input, '%Y-%m-%d %H:%M')
            bot.send_message(message.chat.id, "Время окончания успешно сохранено.")
            prompt_add_event(message)
    except ValueError:
        # Обработка ошибки ввода времени
        bot.send_message(
            message.chat.id,
            "Неверный формат даты и времени. Пожалуйста, введите дату и время в формате 'ГГГГ-ММ-ДД ЧЧ:ММ' или напишите 'нет'."
        )
        bot.register_next_step_handler(message, save_event_end_time)  # Перезапуск функции
    except Exception as e:
        # Общий перехват ошибок с перезапуском функции
        print(f"Ошибка при обработке времени окончания: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте снова.")
        bot.register_next_step_handler(message, save_event_end_time)  # Перезапуск функции
    
    except Exception as e:
        print(f"Ошибка при сохранении времени окончания: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте снова.")
        bot.register_next_step_handler(message, save_event_end_time)

    
    except Exception as e:
        print(f"Ошибка при сохранении времени окончания: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")

    
    except Exception as e:
        print(f"Ошибка при сохранении времени окончания: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")


def save_event_to_db(message):
    try:
        global event_data
        required_fields = ['name', 'start_time']
        
        for field in required_fields:
            if field not in event_data:
                bot.send_message(message.chat.id, f"Поле '{field}' обязательно для заполнения.")
                return
        
        cursor.execute('INSERT INTO events (name, link, description, max_participants, start_time, end_time) VALUES (?, ?, ?, ?, ?, ?)', 
                       (event_data.get('name', ''), event_data.get('link', None), event_data.get('description', None), 
                        event_data.get('max_participants', None),
                        event_data['start_time'].strftime('%Y-%m-%d %H:%M'), 
                        event_data['end_time'].strftime('%Y-%m-%d %H:%M') if event_data.get('end_time') else None))
        
        conn.commit()

        # Уведомление подписчиков о новом мероприятии
        notify_subscribers(event_data['name'])

        bot.send_message(message.chat.id,
                         f"Мероприятие '{event_data['name']}' успешно добавлено с началом в {event_data['start_time'].strftime('%Y-%m-%d %H:%M')}!")
        event_data.clear()
    
    except sqlite3.Error as e:
        print(f"Ошибка при сохранении мероприятия в базу данных: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при сохранении данных.")
    
    except Exception as e:
        print(f"Общая ошибка при сохранении мероприятия: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")



@bot.message_handler(func=lambda message: message.text == "🟢 Редактировать мероприятие")
def prompt_edit_event(message):
    try:
        if message.from_user.id in ADMIN_IDS:
            cursor.execute('SELECT name FROM events')
            events = cursor.fetchall()
            
            if events:
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                for event in events:
                    markup.add(event[0])
                markup.add(types.KeyboardButton("❌ Выйти в главное меню"))
                bot.send_message(message.chat.id, "Выберите мероприятие для редактирования:", reply_markup=markup)
                bot.register_next_step_handler(message, handle_edit_event_selection)
            else:
                bot.send_message(message.chat.id, "Нет мероприятий для редактирования.")
    
    except sqlite3.Error as e:
        print(f"Ошибка при получении списка мероприятий: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при получении данных.")
    
    except Exception as e:
        print(f"Общая ошибка при редактировании мероприятия: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")

def handle_edit_event_selection(message):
    try:
        if message.text.strip() == "❌ Выйти в главное меню":
            bot.send_message(message.chat.id, "Вы отменили редактирование мероприятия.")
            return
        
        selected_event = message.text.strip()
        cursor.execute('SELECT * FROM events WHERE name = ?', (selected_event,))
        event_data = cursor.fetchone()
        
        if event_data:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            button_name = types.KeyboardButton("Изменить название")
            button_link = types.KeyboardButton("Изменить ссылку")
            button_description = types.KeyboardButton("Изменить описание")
            button_max_participants = types.KeyboardButton("Изменить максимальное количество участников")
            button_start_time = types.KeyboardButton("Изменить время начала")
            button_end_time = types.KeyboardButton("Изменить время окончания")
            button_save = types.KeyboardButton("Сохранить изменения")
            button_cancel = types.KeyboardButton("❌ Выйти в главное меню")
            
            markup.add(button_name, button_link)
            markup.add(button_description, button_max_participants)
            markup.add(button_start_time, button_end_time)
            markup.add(button_save)
            markup.add(button_cancel)
            
            bot.send_message(message.chat.id, "Выберите, что хотите изменить:", reply_markup=markup)
            bot.register_next_step_handler(message, lambda msg: handle_edit_event_input(msg, selected_event))
        else:
            bot.send_message(message.chat.id, "Выбранное мероприятие не найдено.")
    
    except sqlite3.Error as e:
        print(f"Ошибка при получении данных мероприятия: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при получении данных.")
    
    except Exception as e:
        print(f"Общая ошибка при выборе мероприятия: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")

def handle_edit_event_input(message, event_name):
    try:
        if message.text.strip() == "❌ Выйти в главное меню":
            bot.send_message(message.chat.id, "Вы отменили редактирование мероприятия.")
            return
        
        if message.text == "Изменить название":
            bot.send_message(message.chat.id, "Введите новое название мероприятия:")
            bot.register_next_step_handler(message, lambda msg: update_event_name(msg, event_name))
        elif message.text == "Изменить ссылку":
            bot.send_message(message.chat.id, "Введите новую ссылку на мероприятие (или оставьте пустым):")
            bot.register_next_step_handler(message, lambda msg: update_event_link(msg, event_name))
        elif message.text == "Изменить описание":
            bot.send_message(message.chat.id, "Введите новое описание мероприятия (или оставьте пустым):")
            bot.register_next_step_handler(message, lambda msg: update_event_description(msg, event_name))
        elif message.text == "Изменить максимальное количество участников":
            bot.send_message(message.chat.id, "Введите новое максимальное количество участников (или оставьте пустым для неограниченного):")
            bot.register_next_step_handler(message, lambda msg: update_event_max_participants(msg, event_name))
        elif message.text == "Изменить время начала":
            bot.send_message(message.chat.id, "Введите новое время начала мероприятия (формат: YYYY-MM-DD HH:MM):")
            bot.register_next_step_handler(message, lambda msg: update_event_start_time(msg, event_name))
        elif message.text == "Изменить время окончания":
            bot.send_message(message.chat.id, "Введите новое время окончания мероприятия (формат: YYYY-MM-DD HH:MM) или напишите 'нет' для бесконечного мероприятия:")
            bot.register_next_step_handler(message, lambda msg: update_event_end_time(msg, event_name))
        elif message.text == "Сохранить изменения":
            bot.send_message(message.chat.id, "Изменения успешно сохранены!")
            show_main_menu(message)
    
    except Exception as e:
        print(f"Общая ошибка при редактировании мероприятия: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")

def update_event_name(message, event_name):
    try:
        new_name = message.text.strip()
        
        # Валидация названия (например, проверка на длину)
        if len(new_name) > 100:
            bot.send_message(message.chat.id, "Название слишком длинное. Пожалуйста, сократите.")
            bot.register_next_step_handler(message, lambda msg: update_event_name(msg, event_name))
            return
        
        cursor.execute('UPDATE events SET name = ? WHERE name = ?', (new_name, event_name))
        conn.commit()
        prompt_edit_event(message)
    
    except sqlite3.Error as e:
        print(f"Ошибка при обновлении названия: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при обновлении данных.")
    
    except Exception as e:
        print(f"Общая ошибка при обновлении названия: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")

def update_event_link(message, event_name):
    try:
        new_link = message.text.strip() or None
        
        # Валидация ссылки (например, проверка на длину)
        if new_link and len(new_link) > 200:
            bot.send_message(message.chat.id, "Ссылка слишком длинная. Пожалуйста, сократите.")
            bot.register_next_step_handler(message, lambda msg: update_event_link(msg, event_name))
            return
        
        cursor.execute('UPDATE events SET link = ? WHERE name = ?', (new_link, event_name))
        conn.commit()
        prompt_edit_event(message)
    
    except sqlite3.Error as e:
        print(f"Ошибка при обновлении ссылки: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при обновлении данных.")
    
    except Exception as e:
        print(f"Общая ошибка при обновлении ссылки: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")

def update_event_description(message, event_name):
    try:
        new_description = message.text.strip() or None
        
        # Валидация описания (например, проверка на длину)
        if new_description and len(new_description) > 500:
            bot.send_message(message.chat.id, "Описание слишком длинное. Пожалуйста, сократите.")
            bot.register_next_step_handler(message, lambda msg: update_event_description(msg, event_name))
            return
        
        cursor.execute('UPDATE events SET description = ? WHERE name = ?', (new_description, event_name))
        conn.commit()
        prompt_edit_event(message)
    
    except sqlite3.Error as e:
        print(f"Ошибка при обновлении описания: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при обновлении данных.")
    
    except Exception as e:
        print(f"Общая ошибка при обновлении описания: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")


def update_event_max_participants(message, event_name):
    max_participants_input = message.text.strip()
    
    if max_participants_input:
        try:
            max_participants = int(max_participants_input)
            if max_participants <= 0:
                bot.send_message(message.chat.id, "Максимальное количество участников должно быть больше нуля.")
                bot.register_next_step_handler(message, lambda msg: update_event_max_participants(msg, event_name))
                return
        except ValueError:
            bot.send_message(message.chat.id, "Неверный формат. Пожалуйста, введите целое число.")
            bot.register_next_step_handler(message, lambda msg: update_event_max_participants(msg, event_name))
            return
    else:
        max_participants = None
    cursor.execute('UPDATE events SET max_participants = ? WHERE name = ?', (max_participants, event_name))
    conn.commit()
    prompt_edit_event(message)

def update_event_start_time(message, event_name):
    start_time_input = message.text.strip()
    
    try:
        start_time = datetime.strptime(start_time_input, '%Y-%m-%d %H:%M')
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат даты и времени. Пожалуйста, попробуйте снова.")
        bot.register_next_step_handler(message, lambda msg: update_event_start_time(msg, event_name))
        return
    cursor.execute('UPDATE events SET start_time = ? WHERE name = ?', (start_time.strftime('%Y-%m-%d %H:%M'), event_name))
    conn.commit()
    prompt_edit_event(message)

def update_event_end_time(message, event_name):
    end_time_input = message.text.strip()
    
    if end_time_input.lower() == 'нет':
        end_time = None
    else:
        try:
            end_time = datetime.strptime(end_time_input, '%Y-%m-%d %H:%M')
        except ValueError:
            bot.send_message(message.chat.id, "Неверный формат даты и времени. Пожалуйста, попробуйте снова.")
            bot.register_next_step_handler(message, lambda msg: update_event_end_time(msg, event_name))
            return
    cursor.execute('UPDATE events SET end_time = ? WHERE name = ?', (end_time.strftime('%Y-%m-%d %H:%M') if end_time else None, event_name))
    conn.commit()
    prompt_edit_event(message)




@bot.message_handler(commands=['subscribe'])
def subscribe(message):
    try:
        user_id = message.from_user.id
        cursor.execute('INSERT OR IGNORE INTO subscribers (user_id) VALUES (?)', (user_id,))
        conn.commit()
        bot.send_message(message.chat.id,
                         "Вы успешно подписались на уведомления о новых мероприятиях!")
    
    except sqlite3.Error as e:
        print(f"Ошибка при подписке на уведомления: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при подписке.")
    
    except Exception as e:
        print(f"Общая ошибка при подписке: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")

@bot.message_handler(commands=['unsubscribe'])
def unsubscribe(message):
    try:
        user_id = message.from_user.id
        cursor.execute('DELETE FROM subscribers WHERE user_id = ?', (user_id,))
        conn.commit()
        bot.send_message(message.chat.id,
                         "Вы успешно отписались от уведомлений о новых мероприятиях.")
    
    except sqlite3.Error as e:
        print(f"Ошибка при отписке от уведомлений: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при отписке.")
    
    except Exception as e:
        print(f"Общая ошибка при отписке: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")


# Функция для уведомления подписчиков о новом мероприятии
def notify_subscribers(event_name):
    subscribers = cursor.execute('SELECT user_id FROM subscribers').fetchall()
    for subscriber in subscribers:
        bot.send_message(subscriber[0], f"Новое мероприятие добавлено: '{event_name}'.")

# Функция для удаления истекших мероприятий
def remove_expired_events():
    # Создаем новое соединение и курсор для работы с базой данных
    conn = sqlite3.connect('/app/data/volunter_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    
    while True:
        try:
            current_time = datetime.now()
            
            # Получаем все мероприятия, которые истекли
            cursor.execute('SELECT id FROM events WHERE end_time IS NOT NULL AND end_time < ?', (current_time,))
            expired_events = cursor.fetchall()
            
            for event in expired_events:
                event_id = event[0]
                
                # Удаляем мероприятие из базы данных
                cursor.execute('DELETE FROM events WHERE id = ?', (event_id,))
                print(f"Мероприятие с ID {event_id} было удалено.")  # Отладочное сообщение
            
            conn.commit()
        
        except sqlite3.Error as e:
            print(f"Ошибка при удалении истекших мероприятий: {e}")
        
        except Exception as e:
            print(f"Общая ошибка при удалении мероприятий: {e}")
        
        time.sleep(60)  # Проверяем каждую минуту
    
    conn.close()  # Закрываем соединение после завершения работы

# Запускаем поток для удаления истекших мероприятий
threading.Thread(target=remove_expired_events, daemon=True).start()


# Функция для отмены действия
def cancel_action(message):
    bot.send_message(message.chat.id,"Вы вернулись в главное меню.")



# Обработка команды "Удалить мероприятие"
@bot.message_handler(func=lambda message: message.text == "🟢 Удалить мероприятие")
def delete_event(message):
    if message.from_user.id in ADMIN_IDS:
        cursor.execute('SELECT name FROM events')
        events = cursor.fetchall()

        if events:
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
            for event in events:
                markup.add(event[0])
            markup.add(types.KeyboardButton("❌ Выйти в главное меню"))  # Добавляем кнопку отмены здесь
            bot.send_message(
                message.chat.id, "Выберите мероприятие для удаления:", reply_markup=markup
            )
            bot.register_next_step_handler(message, confirm_delete_event)
        else:
            bot.send_message(
                message.chat.id, "Нет мероприятий для удаления."
            )


# Подтверждение удаления мероприятия
def confirm_delete_event(message):
    selected_event = message.text.strip()

    if selected_event == "❌ Выйти в главное меню":
        cancel_action(message)
        return

    cursor.execute('DELETE FROM events WHERE name=?', (selected_event,))
    conn.commit()

    for admin in ADMIN_IDS:
        for user in user_ids:
            bot.send_message(user, f"Мероприятие '{selected_event}' было удалено.")

    bot.send_message(
        message.chat.id, f"Мероприятие '{selected_event}' успешно удалено."
    )

@bot.message_handler(func=lambda message: message.text == "🟢 Отправить баллы")
def send_points_menu(message):
    try:
        if message.from_user.id in ADMIN_IDS:
            cursor.execute('SELECT name FROM events')
            events = cursor.fetchall()

            if events:
                markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
                for event in events:
                    markup.add(event[0])
                markup.add(types.KeyboardButton("❌ Выйти в главное меню"))  
                bot.send_message(message.chat.id, "Выберите мероприятие для отправки баллов:", reply_markup=markup)
                bot.register_next_step_handler(message, select_user_for_points)
            else:
                bot.send_message(message.chat.id, "Нет мероприятий для отправки баллов.")
    
    except sqlite3.Error as e:
        print(f"Ошибка при получении списка мероприятий: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при получении данных.")
    
    except Exception as e:
        print(f"Общая ошибка при отправке баллов: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")

def select_user_for_points(message):
    try:
        selected_event = message.text.strip()
        
        if selected_event == "❌ Выйти в главное меню":
            cancel_action(message)  
            return
        
        cursor.execute('SELECT id FROM events WHERE name=?', (selected_event,))
        event_id_result = cursor.fetchone()

        if not event_id_result:
            bot.send_message(message.chat.id, "Мероприятие не найдено.")
            return

        event_id = event_id_result[0]
        
        # Получаем заявки, где статус не "отменено"
        cursor.execute('SELECT full_name FROM applications WHERE event_id=? AND status != "отменена"', (event_id,))
        applicants = cursor.fetchall()

        if applicants:
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
            for app in applicants:
                markup.add(app[0])
            markup.add(types.KeyboardButton("❌ Выйти в главное меню"))  
            bot.send_message(message.chat.id, "Выберите пользователя для начисления баллов:", reply_markup=markup)
            bot.register_next_step_handler(message, lambda msg: set_points(msg, event_id))
        else:
            bot.send_message(message.chat.id, "Нет активных заявок на это мероприятие.")
    
    except sqlite3.Error as e:
        print(f"Ошибка при получении заявок: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при получении данных.")
    
    except Exception as e:
        print(f"Общая ошибка при выборе пользователя: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")


def set_points(message, selected_event_id):
    try:
        if message.text.strip() == "❌ Выйти в главное меню":
            cancel_action(message)  
            return
        
        selected_user_full_name = message.text.strip()
        
        cursor.execute('SELECT user_id FROM applications WHERE full_name=? AND event_id=?',
                       (selected_user_full_name.strip(), selected_event_id))
        
        user_data = cursor.fetchone()
        
        if user_data:
            user_id = user_data[0]
            
            bot.send_message(
                message.chat.id, "Введите количество баллов:")
            bot.register_next_step_handler(
                message, lambda msg: update_points(msg, selected_event_id, user_id))
        else:
            bot.send_message(message.chat.id, "Пользователь не найден.")
    
    except sqlite3.Error as e:
        print(f"Ошибка при получении пользователя: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при получении данных.")
    
    except Exception as e:
        print(f"Общая ошибка при начислении баллов: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")

def update_points(message, event_id, user_id):
    try:
        if message.text.strip() == "❌ Выйти в главное меню":
            cancel_action(message)  
            return

        points = message.text.strip()
        
        # Валидация количества баллов (например, проверка на целое число)
        if not points.isdigit():
            bot.send_message(message.chat.id, "Пожалуйста, введите корректное число. Попробуйте еще раз:")
            bot.register_next_step_handler(message, lambda msg: update_points(msg, event_id, user_id))  
            return
        
        points = int(points)
        
        if points <= 0:
            bot.send_message(message.chat.id, "Количество баллов должно быть больше нуля.")
            bot.register_next_step_handler(message, lambda msg: update_points(msg, event_id, user_id))  
            return
        
        cursor.execute('SELECT points FROM user_points WHERE user_id=?', (user_id,))
        result = cursor.fetchone()

        if result:
            cursor.execute('UPDATE user_points SET points=points+? WHERE user_id=?', (points, user_id))
        else:
            cursor.execute('INSERT INTO user_points (user_id, points) VALUES (?, ?)', (user_id, points))

        conn.commit()

        cursor.execute('SELECT name FROM events WHERE id=?', (event_id,))
        event_name = cursor.fetchone()[0]

        bot.send_message(user_id,
                         f"Вам начислено {points} баллов за участие в мероприятии '{event_name}'.")

        for admin in ADMIN_IDS:
            bot.send_message(admin,
                             f"Баллы за мероприятие '{event_name}' обновлены.")
        
    except sqlite3.Error as e:
        print(f"Ошибка при обновлении баллов: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при обновлении данных.")
    
    except Exception as e:
        print(f"Общая ошибка при начислении баллов: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")


def cancel_action(message):
    bot.send_message(message.chat.id, "Вы вернулись в главное меню.")
    show_main_menu(message)  # Возвращаем в главное меню

def send_message_with_retry(message, text):
    max_retries = 3
    retries = 0
    while retries < max_retries:
        try:
            bot.send_message(message.chat.id, text)
            break
        except ConnectionResetError as e:
            print(f"Ошибка при отправке сообщения: {e}. Повторная попытка...")
            retries += 1
            time.sleep(1)  # Ждем секунду перед повторной попыткой
    else:
        print("Не удалось отправить сообщение после нескольких попыток.")
        
# Обработка команды "Отправить отчет"
@bot.message_handler(func=lambda message: message.text == "📝 Отправить отчет")
def prompt_send_report(message):
    try:
        cursor.execute('SELECT name FROM events')
        events = cursor.fetchall()

        if events:
            # Получаем список мероприятий, на которые пользователь записан
            cursor.execute('SELECT event_id FROM applications WHERE user_id = ?', (message.from_user.id,))
            user_events = cursor.fetchall()
            user_event_ids = [event[0] for event in user_events]

            # Удаляем мероприятия, с которых пользователь отказался
            cursor.execute('SELECT event_id FROM applications WHERE user_id = ? AND status = "отменена"', (message.from_user.id,))
            cancelled_events = cursor.fetchall()
            cancelled_event_ids = [event[0] for event in cancelled_events]

            # Формируем список мероприятий для отображения
            available_events = []
            for event in events:
                event_id = cursor.execute('SELECT id FROM events WHERE name = ?', (event[0],)).fetchone()[0]
                if event_id in user_event_ids and event_id not in cancelled_event_ids:
                    available_events.append(event[0])

            if available_events:
                markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
                for event in available_events:
                    markup.add(event)
                markup.add(types.KeyboardButton("❌ Выйти в главное меню"))  
                bot.send_message(
                    message.chat.id, "Выберите мероприятие для отправки отчета:", reply_markup=markup)
                bot.register_next_step_handler(message, check_application_before_report)  
            else:
                bot.send_message(message.chat.id, "Вы не можете отправить отчет ни на одно мероприятие.")
        else:
            bot.send_message(message.chat.id, "Нет мероприятий для выбора.")
    
    except sqlite3.Error as e:
        print(f"Ошибка при получении списка мероприятий: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при получении данных.")
    
    except Exception as e:
        print(f"Общая ошибка при отправке отчета: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")


def check_application_before_report(message):
    try:
        selected_event = message.text.strip()     
        if selected_event == "❌ Выйти в главное меню":
            cancel_action(message)
            return
        
        cursor.execute('SELECT id FROM events WHERE name = ?', (selected_event,))
        event_id_result = cursor.fetchone()

        if not event_id_result:
            bot.send_message(message.chat.id, "Выбранное мероприятие не найдено.")
            return
        
        event_id = event_id_result[0]
        
        cursor.execute('SELECT * FROM applications WHERE event_id = ? AND user_id = ?', (event_id, message.from_user.id))
        
        application_exists = cursor.fetchone()
        
        if application_exists and application_exists[6] != "отменена":  
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(types.KeyboardButton("❌ Выйти в главное меню"))  
            
            bot.send_message(
                message.chat.id,
                "Введите содержание вашего отчета или отправьте фото/видео:",
                reply_markup=markup
            )
            
            bot.register_next_step_handler(
                message,
                lambda msg: handle_report_content(msg, event_id)
            )
        else:  
            bot.send_message(message.chat.id, "Вы не можете отправить отчет на это мероприятие. Сначала подайте заявку или отмените отказ.")
    
    except sqlite3.Error as e:
        print(f"Ошибка при проверке заявки: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при проверке данных.")
    
    except Exception as e:
        print(f"Общая ошибка при проверке заявки: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")


def handle_report_content(message, event_id):
    try:
        # Проверка на кнопку "Выйти в главное меню"
        if message.text and message.text.strip() == '❌ Выйти в главное меню':
            cancel_action(message)
            return

        report_content = ""

        if message.content_type == 'text':
            report_content += message.text.strip()
        
        elif message.content_type in ['photo', 'video']:
            media_file_id = message.photo[-1].file_id if message.content_type == 'photo' else message.video.file_id
            report_content += f"Отчет с медиафайлом. ID медиафайла: {media_file_id}\n"
        
        # Валидация содержания отчета (например, проверка на длину)
        if report_content and len(report_content) > 1000:
            bot.send_message(message.chat.id, "Отчет слишком длинный. Пожалуйста, сократите.")
            bot.register_next_step_handler(message, lambda msg: handle_report_content(msg, event_id))  
            return
        
        # Уведомление админа о новом отчете
        cursor.execute('SELECT name FROM events WHERE id = ?', (event_id,))
        event_name = cursor.fetchone()[0]
        
        for admin in ADMIN_IDS:
            bot.send_message(admin,
                             f"Новый отчет от пользователя {message.from_user.first_name}:\n"
                             f"Мероприятие ID: {event_id}\n"
                             f"Название мероприятия: {event_name}\n"
                             f"Содержание отчета:\n{report_content}")

            # Отправляем администратору медиафайл
            if message.content_type in ['photo', 'video']:
                file_info = bot.get_file(media_file_id)
                downloaded_file = bot.download_file(file_info.file_path)

                file_extension = 'jpg' if message.content_type == 'photo' else 'mp4'
                with open(f"temp_file.{file_extension}", 'wb') as new_file:
                    new_file.write(downloaded_file)

                with open(f"temp_file.{file_extension}", 'rb') as new_file:
                    if file_extension == 'jpg':
                        bot.send_photo(admin, new_file)
                    else:
                        bot.send_video(admin, new_file)

                # Удаляем временный файл после отправки
                try:
                    os.remove(f"temp_file.{file_extension}")
                except OSError as e:
                    print(f"Ошибка при удалении файла: {e}")

        bot.send_message(message.chat.id, "Ваш отчет успешно отправлен админу!")
    
    except sqlite3.Error as e:
        print(f"Ошибка при отправке отчета: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при отправке данных.")
    
    except Exception as e:
        print(f"Общая ошибка при отправке отчета: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")



# Обработка нажатия кнопки "Выйти в главное меню"
@bot.message_handler(func=lambda message: message.text == "❌ Выйти в главное меню")
def cancel_action(message):
      bot.send_message(
          message.chat.id,"Вы вернулись в главное меню.")
      show_main_menu(message) 





# Обработка текстовых сообщений и кнопок меню
# Обработчик для всех текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_menu(message):
    try:
        # Проверка на слишком быстрые команды и повторяющиеся сообщения.
        if message.from_user.id in last_message_time:
            if time.time() - last_message_time[message.from_user.id] < 1:  
                handle_unusual_behavior(message.from_user.id)
                return
            
            if repeat_count.get(message.text) and repeat_count[message.text] >= 3:  
                handle_unusual_behavior(message.from_user.id)
                return
            
            if message.text not in repeat_count:
                repeat_count[message.text] = 0
            repeat_count[message.text] += 1 
        
        last_message_time[message.from_user.id] = time.time()

        # Если сообщение не соответствует ни одной из известных команд, отправляем сообщение об ошибке
        bot.send_message(message.chat.id, "Извините, я не понял вашу команду. Пожалуйста, выберите действие из меню.")
        show_main_menu(message)
    
    except Exception as e:
        print(f"Общая ошибка при обработке меню: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка.")

def handle_unusual_behavior(user_id):
    try:
        bot.send_message(user_id, "Вы отправляете сообщения слишком быстро или повторяете одну и ту же команду. Пожалуйста, сделайте паузу.")
    
    except Exception as e:
        print(f"Общая ошибка при обработке необычного поведения: {e}")
        bot.send_message(user_id, "Произошла ошибка.")


if __name__ == "__main__":
    print("Бот запущен...")
    atexit.register(lambda: conn.close())  # Закрытие соединения с БД при завершении работы
    
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Произошла ошибка: {e}")
            print("Перезапуск бота...")
            os.execv(sys.executable, ['python'] + sys.argv)  # Перезапускаем текущий скрипт






