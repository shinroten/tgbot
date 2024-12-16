import telebot
import re

import psycopg2 # Импортируем psycopg2 для PostgreSQL
import psutil 


API_TOKEN = '7352442248:AAH9iCQ63EBR9fZ7n4Nm9wb2Jzu8eEPq9mg'

# Данные для подключения к PostgreSQL
# DATABASE_URL = "postgres://postgres:123@localhost:5432/tele_bot"

# logging.basicConfig(filename='bot.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

bot = telebot.TeleBot(API_TOKEN)

EMAIL_REGEX = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
PHONE_REGEX = r'(\+7\d{10}|8\d{10})'
PASSWORD_REGEX = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()]).{8,}$'

# Подключение к PostgreSQL
conn = psycopg2.connect(
  dbname="tele_bot",
  user="root",
  password="root",
  host="postgres",
  port="5432"
)
cursor = conn.cursor()

# Создание таблиц (если они не существуют)
cursor.execute("""
  CREATE TABLE IF NOT EXISTS emails (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE
  );
""")

cursor.execute("""
  CREATE TABLE IF NOT EXISTS phones (
    id SERIAL PRIMARY KEY,
    phone TEXT UNIQUE
  );
""")
conn.commit()

def add_email(email):
  """
  Добавляет email в базу данных (если его еще нет).
  """
  try:
    cursor.execute("INSERT INTO emails (email) VALUES (%s) ON CONFLICT (email) DO NOTHING", (email,))
    conn.commit()
    print(f"Added email: {email}")
  except Exception as e:
    print(f"Error adding email: {e}")

def get_emails():
  """
  Возвращает список всех emails из базы данных.
  """
  cursor.execute("SELECT email FROM emails")
  return [row[0] for row in cursor.fetchall()]

def add_phone(phone):
  """
  Добавляет номер телефона в базу данных (если его еще нет).
  """
  try:
    cursor.execute("INSERT INTO phones (phone) VALUES (%s) ON CONFLICT (phone) DO NOTHING", (phone,))
    conn.commit()
    print(f"Added phone number: {phone}")
  except Exception as e:
    print(f"Error adding phone number: {e}")

def get_phones():
  """
  Возвращает список всех номеров телефонов из базы данных.
  """
  cursor.execute("SELECT phone FROM phones")
  return [row[0] for row in cursor.fetchall()]

@bot.message_handler(commands=['start'])
def send_welcome(message):
  bot.reply_to(message, "Привет! 👋 Я бот, который поможет тебе найти информацию в тексте.\n"
             "Чтобы узнать больше, введи команду /help.")

@bot.message_handler(commands=['help'])
def send_help(message):
  bot.reply_to(message, "Я умею следующее:\n""/find_email: Найди email-адреса в тексте.\n"
             "/find_phone_number: Найди номера телефонов в тексте.\n"
             "/verify_password: Проверь, насколько сложным является пароль.\n"
             "/add_email: Добавь новый email-адрес в базу данных.\n"
             "/add_phone: Добавь новый номер телефона в базу данных.\n"
             "/system_info: Системная информация.\n"
             "Например, введи /find_email, а затем отправь текст, в котором нужно найти email-адреса.")

@bot.message_handler(commands=['add_email'])
def handle_add_email(message):
  bot.send_message(message.chat.id, "Пожалуйста, отправьте email-адрес для добавления.")
  bot.register_next_step_handler(message, add_email_to_db)

def add_email_to_db(message):
  email = message.text
  add_email(email)
  bot.send_message(message.chat.id, "Email-адрес добавлен.")

@bot.message_handler(commands=['add_phone'])
def handle_add_phone(message):
  bot.send_message(message.chat.id, "Пожалуйста, отправьте номер телефона для добавления.")
  bot.register_next_step_handler(message, add_phone_to_db)

def add_phone_to_db(message):
  phone = message.text
  add_phone(phone)
  bot.send_message(message.chat.id, "Номер телефона добавлен.")

@bot.message_handler(commands=['find_email'])
def handle_find_email(message):
  bot.send_message(message.chat.id, "Пожалуйста, отправьте текст для поиска email-адресов.")
  bot.register_next_step_handler(message, find_email)

def find_email(message):
  text = message.text
  emails = re.findall(EMAIL_REGEX, text)
  if emails:
    bot.send_message(message.chat.id, "Найденные email-адреса:\n" + "\n".join(emails))
  else:
    bot.send_message(message.chat.id, "Email-адреса не найдены.")

@bot.message_handler(commands=['find_phone_number'])
def handle_find_phone(message):
  bot.send_message(message.chat.id, "Пожалуйста, отправьте текст для поиска номеров телефонов.")
  bot.register_next_step_handler(message, find_phone)

def find_phone(message):
  text = message.text
  phones = re.findall(PHONE_REGEX, text)
  if phones:
    bot.send_message(message.chat.id, "Найденные номера телефонов:\n" + "\n".join(phones))
  else:
    bot.send_message(message.chat.id, "Номера телефонов не найдены.")

@bot.message_handler(commands=['verify_password'])
def handle_verify_password(message):
  bot.send_message(message.chat.id, "Пожалуйста, отправьте пароль для проверки.")
  bot.register_next_step_handler(message, verify_password)

def verify_password(message):
  password = message.text
  if re.match(PASSWORD_REGEX, password):
    bot.send_message(message.chat.id, "Пароль достаточно сложный.")
  else:
    bot.send_message(message.chat.id, "Пароль недостаточно сложный. Он должен содержать:\n"
                    " - Минимум 8 символов\n"
                    " - Строчные и прописные буквы\n"
                    " - Числа\n"
                    " - Специальные символы.")

@bot.message_handler(commands=['system_info'])
def handle_system_info(message):
  cpu_percent = psutil.cpu_percent()
  memory_percent = psutil.virtual_memory().percent
  disk_usage_percent = psutil.disk_usage('/').percent # Проверяем использование диска на корневом разделе
  bot.send_message(message.chat.id, f"Системная информация:\n"
                    f"Загрузка процессора: {cpu_percent}%\n"
                    f"Использование памяти: {memory_percent}%\n"
                    f"Использование диска: {disk_usage_percent}%")

# Запускаем бота
bot.polling()

# Закрываем соединение с PostgreSQL
cursor.close()
conn.close()