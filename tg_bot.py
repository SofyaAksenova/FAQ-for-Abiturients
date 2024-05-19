from project_secrets import bot_token, password_db
import telebot
import psycopg2
import markups
bot = telebot.TeleBot(bot_token)

conn = psycopg2.connect(database="abitmobot", user="postgres", password=password_db, host="localhost", port="5432")
cur = conn.cursor()
cur.execute(f"""SELECT DISTINCT question, reply
                FROM posts 
                WHERE abit = 1
                AND question NOT LIKE '%test%'
                AND reply NOT LIKE '%test%'
            """)

res = cur.fetchall()

faq = [{'question': question, 'reply': reply} for question, reply in res]

@bot.message_handler(commands=['start', 'help'])
def get_start(message):
    start_mg = """
        Привет! Я Abitmobot, помощник по поступлению в ИТМО 🙂

Со мной ты сможешь:
💡 Ознакомиться с FAQ, где перечислены самые популярные вопросы от абитуриентов
🔎 Искать по базе интересующий тебя, вопрос, который не получилось найти в FAQ
🤝 Связаться с тех. поддержкой бота, если что-то поломалось

Выбирай кнопку ниже, чтобы продолжить работу
            """
    start_mg = """
        Привет! Я Abitmobot, помощник по поступлению в ИТМО 🙂

Со мной ты сможешь:
💡 Ознакомиться с FAQ, где перечислены самые популярные вопросы от абитуриентов

Выбирай кнопку ниже, чтобы продолжить работу
                """

    bot.send_message(message.from_user.id, start_mg, reply_markup=markups.get_start_markup())

@bot.callback_query_handler(func = lambda callback: True)
def callback_message(callback):
    if callback.data == 'start':
        get_start(callback)
    if callback.data == 'faq':
        questions = """"""
        for i in range(len(faq)):
            questions = questions + str(i+1) + ". " + faq[i]['question'] + "\n"
        faq_mg = f"""
         FAQ:
{questions}
Чтобы увидеть ответ, просто нажми на номер вопроса ниже 🙂
        """

        bot.send_message(callback.from_user.id, faq_mg, reply_markup=markups.get_faq_markup(faq))

    for i in range(len(faq)):
        if callback.data == f'faq{i+1}':
            res = markups.get_reply_markup(faq, i+1)
            bot.send_message(callback.from_user.id, res['mg'], reply_markup=res['markup'])
        else:
            pass

bot.polling(none_stop=True, interval=0)