import telebot


def get_token():
    v_token = ''
    with open('config') as file:
        v_token = file.readline()
    print(v_token)
    return v_token


bot = telebot.TeleBot(get_token())


def main():
    bot.polling(none_stop=True, interval=0)


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    if message.text == "Привет":
        bot.send_message(message.from_user.id, "Привет, сейчас я расскажу тебе гороскоп на сегодня.")
    elif message.text == 'Пока':
        bot.send_message(message.from_user.id, 'Пока, скоро увидимся!')
    elif message.text == "/help":
        bot.send_message(message.from_user.id, "Напиши Привет или Пока")
    else:
        bot.send_message(message.from_user.id, "Я тебя не понимаю. Напиши /help.")


if __name__ == '__main__':
    main()
