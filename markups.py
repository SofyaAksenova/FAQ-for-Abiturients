import telebot


def get_start_markup():
    markup_start = telebot.types.InlineKeyboardMarkup()
    button_start = telebot.types.InlineKeyboardButton('Главное меню', callback_data='start')
    button_faq = telebot.types.InlineKeyboardButton('FAQ', callback_data='faq')
    button_search = telebot.types.InlineKeyboardButton('Поиск по FAQ', callback_data='search_faq')
    button_contact = telebot.types.InlineKeyboardButton('Тех. поддержка', callback_data='contact_help')
    markup_start.add(button_start)
    markup_start.add(button_faq)
    # markup_start.add(button_search)
    # markup_start.add(button_contact)
    return markup_start


def get_faq_markup(faq):
    markup_faq = telebot.types.InlineKeyboardMarkup()

    for i in range(len(faq)):
        button = telebot.types.InlineKeyboardButton(str(i+1), callback_data=f'faq{i+1}')
        # button = telebot.types.InlineKeyboardButton(f'Здесь будет вопрос номер {i+1} :)', callback_data=f'faq{i + 1}')
        markup_faq.add(button)

    button_start = telebot.types.InlineKeyboardButton('Главное меню', callback_data='start')
    markup_faq.add(button_start)

    return markup_faq


def get_reply_markup(faq, i):
    reply_mg = f"""
                Ответ на этот вопрос:
❗ {faq[i-1]['reply']}
                        """
#     reply_mg = f"""
#                     Ответ на этот вопрос:
# ❗ Здесь будет ответ на вопрос номер {i}.
#                             """
    markup_reply = telebot.types.InlineKeyboardMarkup()
    button_faq = telebot.types.InlineKeyboardButton('Назад к вопросам', callback_data='faq')
    button_start = telebot.types.InlineKeyboardButton('Главное меню', callback_data='start')
    markup_reply.add(button_faq)
    markup_reply.add(button_start)

    return {'mg': reply_mg, 'markup': markup_reply}