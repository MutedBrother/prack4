import logging
import re
import paramiko
import psycopg2
import os
from dotenv import load_dotenv
from psycopg2 import Error

from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, \
    ConversationHandler

load_dotenv()

TOKEN = os.getenv('TOKEN')

logging.basicConfig(
    filename='logfile.txt',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def get_conn():
    return psycopg2.connect(user=os.getenv('DB_USER'),
                     password=os.getenv('DB_PASSWORD'),
                     host=os.getenv('DB_HOST'),
                     port=os.getenv('DB_PORT'),
                     database=os.getenv('DB_DATABASE'))


def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'Здраствуйте проверяющий {user.full_name}! Я вас так долго ждал. Напишите /help для вашего удобства(там есть пасхалка) !')

def cmd_find_phone_numbers(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')
    return 'find_phone_numbers'

def helpCommand(update: Update, context):
    update.message.reply_text('Для упрощения, вот список команд: /find_email /find_phone_number /verify_password /get_emails /get_phone_numbers /get_repl_logs /get_release /get_uname /get_uptime /get_df /get_free /get_mpstat /get_w /get_auths /get_critical /get_ps /get_ss /get_apt_list /get_services /what_is_it')

def superCommand(update: Update, context):
    update.message.reply_text('  ( ͝ಠ ʖ ಠ)=ε/̵͇̿̿/’̿’̿ ̿  А чего вы ожидали?   ')


def cmd_find_email(update: Update, context):
    update.message.reply_text('Введите текст для поиска email адресов: ')
    return 'find_emails'


def cmd_verify_pswd(update: Update, context):
    update.message.reply_text('Введите пароль: ')
    return 'verify_pswd'


def verify_pswd(update: Update, context):
    user_input = update.message.text

    pswd_regex = re.compile(
        r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()]).{8,}$')
    strong = pswd_regex.findall(user_input)

    if strong:
        update.message.reply_text('Пароль сложный')
    else:
        update.message.reply_text('Пароль простой')
        return

    return ConversationHandler.END


found_phone_numbers = ''


def confirm_phones_database_write(update, context):
    if update.message.text.lower() in ["да", "д"]:
        try:
            connection = get_conn()
            cursor = connection.cursor()
            cleaned_numbers_list = re.findall(r'\d+\.\s*(\d+)', found_phone_numbers)
            for phone_number in cleaned_numbers_list:
                cursor.execute("INSERT INTO phone_numbers (phone_number) VALUES (%s);",
                               (phone_number,))
            connection.commit()
            cursor.close()
            connection.close()
            logging.info("Команда успешно выполнена")
        except (Exception, Error) as error:
            logging.error("Ошибка при работе с PostgreSQL: %s", error)
        update.message.reply_text("Найденные номера успешно записаны в базу данных.")
    else:
        update.message.reply_text("Ок, не будем записывать.")

    return ConversationHandler.END


found_emails = ''


def confirm_emails_database_write(update, context):
    if update.message.text.lower() in ["да", "д"]:
        try:
            connection = get_conn()
            cursor = connection.cursor()
            cleaned_email_list = re.findall(r'[\w\.-]+@[\w\.-]+', found_emails)
            for email_adr in cleaned_email_list:
                cursor.execute("INSERT INTO emails (email) VALUES (%s);", (email_adr,))
            connection.commit()
            cursor.close()
            connection.close()
            logging.info("Команда успешно выполнена")
        except (Exception, Error) as error:
            logging.error("Ошибка при работе с PostgreSQL: %s", error)
        update.message.reply_text(
            "Найденные email адреса успешно записаны в базу данных.")
    else:
        update.message.reply_text("Ок, не будем записывать.")

    return ConversationHandler.END


def find_phone_numbers(update: Update, context):
    regex_a = re.compile(r'(?:\+?7|8)\s?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2}')
    regex_b = re.compile(r'\+?7-\d{3}-\d{3}-\d{2}-\d{2}|8-\d{3}-\d{3}-\d{2}-\d{2}')
    phone_list_a = regex_a.findall(update.message.text)  
    phone_list_b = regex_b.findall(update.message.text)

    if phone_list_b:
        phone_list_a.extend(phone_list_b)

    if not phone_list_a:
        update.message.reply_text('Телефонные номера не найдены')
        return ConversationHandler.END


    numbers = ''
    for i in range(len(phone_list_a)):
        numbers += f'{i + 1}. {phone_list_a[i]}\n'
    global found_phone_numbers
    found_phone_numbers = numbers
    update.message.reply_text(numbers)
    update.message.reply_text("Хотите записать найденные номера в БД  [Да] / [Нет]:")
    return 'confirm_database_write'


def find_emails(update: Update, context):
    regex = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    emails = regex.findall(update.message.text)

    if not emails:
        update.message.reply_text('Email адреса не найдены')
        return

    addrs = ''
    for i in range(len(emails)):
        addrs += f'{i + 1}. {emails[i]}\n'

    global found_emails
    found_emails = addrs
    update.message.reply_text(addrs)
    update.message.reply_text(
        "Хотите записать найденные email адреса в БД  [Да] / [Нет]:")
    return 'confirm_emails_database_write'



def r_exec(command) -> str:
    host = os.getenv('RM_HOST')
    port = os.getenv('RM_PORT')
    username = os.getenv('RM_USER')
    password = os.getenv('RM_PASSWORD')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)

    stdin, stdout, stderr = client.exec_command(command)
    data = stdout.read() + stderr.read()

    client.close()

    data = str(data, 'utf-8').strip()
    return data


def prt(update: Update, data):
    max_message_length = 4096
    parts = [data[i:i + max_message_length] for i in
             range(0, len(data), max_message_length)]
    for part in parts:
        update.message.reply_text(part)


def get_emails(update: Update, context):
    try:
        connection = get_conn()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM emails;")
        data = cursor.fetchall()
        cursor.close()
        connection.close()
        for row in data:
            update.message.reply_text(row)
        logging.info("Команда успешно выполнена")
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)


def get_phone_numbers(update: Update, context):
    try:
        connection = get_conn()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM phone_numbers;")
        data = cursor.fetchall()
        cursor.close()
        connection.close()
        for row in data:
            update.message.reply_text(row)
        logging.info("Команда успешно выполнена")
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)


def get_apt_list(update: Update, context):
    if context.args:
        package_name = ' '.join(context.args)
        prt(update, r_exec(f'dpkg -l | grep "{package_name}"'))
    else:
        prt(update, r_exec('dpkg -l'))


def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    phone_handler = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', cmd_find_phone_numbers)],
        states={
            'find_phone_numbers': [
                MessageHandler(Filters.text & ~Filters.command, find_phone_numbers)],
            'confirm_database_write': [MessageHandler(Filters.text & ~Filters.command,
                                                      confirm_phones_database_write)]
        },
        fallbacks=[]
    )

    email_handler = ConversationHandler(
        entry_points=[CommandHandler('find_email', cmd_find_email)],
        states={
            'find_emails': [MessageHandler(Filters.text & ~Filters.command, find_emails)],
            'confirm_emails_database_write': [
                MessageHandler(Filters.text & ~Filters.command,
                               confirm_emails_database_write)]
        },
        fallbacks=[]
    )


    pswd_handler = ConversationHandler(
        entry_points=[CommandHandler('verify_password', cmd_verify_pswd)],
        states={
            'verify_pswd': [MessageHandler(Filters.text & ~Filters.command, verify_pswd)],
        },
        fallbacks=[]
    )

    dp.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text(f'Здраствуйте проверяющий {u.effective_user.full_name}! Я вас так долго ждал. Напишите /help для вашего удобства(там есть пасхалка) !')))
    dp.add_handler(CommandHandler("help", lambda u, c: u.message.reply_text('Для упрощения, вот список команд: /find_email /find_phone_number /verify_password /get_emails /get_phone_numbers /get_repl_logs /get_release /get_uname /get_uptime /get_df /get_free /get_mpstat /get_w /get_auths /get_critical /get_ps /get_ss /get_apt_list /get_services /what_is_it')))
    dp.add_handler(CommandHandler("what_is_it", lambda u, c: u.message.reply_text(f' ( ͝ಠ ʖ ಠ)=ε/̵͇̿̿/’̿’̿ ̿  А чего вы ожидали?   ')))
    dp.add_handler(phone_handler)
    dp.add_handler(email_handler)
    dp.add_handler(pswd_handler)
    dp.add_handler(CommandHandler("get_emails", get_emails))
    dp.add_handler(CommandHandler("get_release", lambda u, c: prt(u, r_exec('lsb_release -a'))))
    dp.add_handler(CommandHandler("get_uname", lambda u, c: prt(u, r_exec('uname -a'))))
    dp.add_handler(CommandHandler("get_uptime", lambda u, c: prt(u, r_exec('uptime'))))
    dp.add_handler(CommandHandler("get_df", lambda u, c: prt(u, r_exec('df -h'))))
    dp.add_handler(CommandHandler("get_free", lambda u, c: prt(u, r_exec('free -h'))))
    dp.add_handler(CommandHandler("get_mpstat", lambda u, c: prt(u, r_exec('mpstat'))))
    dp.add_handler(CommandHandler("get_w", lambda u, c: prt(u, r_exec('w'))))
    dp.add_handler(CommandHandler("get_auths", lambda u, c: prt(u, r_exec('last -n 10'))))
    dp.add_handler(CommandHandler("get_critical", lambda u, c: prt(u, r_exec('journalctl -p 2 -n 5'))))
    dp.add_handler(CommandHandler("get_ps", lambda u, c: prt(u, r_exec('ps aux'))))
    dp.add_handler(CommandHandler("get_ss", lambda u, c: prt(u, r_exec('ss -tuln'))))
    dp.add_handler(CommandHandler("get_services", lambda u, c: prt(u, r_exec('service --status-all'))))
    dp.add_handler(CommandHandler("get_apt_list", get_apt_list))
    dp.add_handler(CommandHandler("get_repl_logs", lambda u, c: prt(u, r_exec('echo -e "Qq1234" | sudo -S cat /var/log/postgresql/postgresql-14-main.log\n'))))
    dp.add_handler(CommandHandler("get_emails", get_emails))
    dp.add_handler(CommandHandler("get_phone_numbers", get_phone_numbers))
    dp.add_handler(CommandHandler("get_replica_logs", lambda u, c:  prt(u, r_exec('cd /home/daax/devops_bot && docker compose logs postgres_primary'))))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, lambda u, c: u.message.reply_text(u.message.text)))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
