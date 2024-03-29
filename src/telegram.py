import logging
import telebot
import config
import calendar_handler as ch
from telebot import types
from datetime import date
from requests import exceptions
import database

bot = telebot.TeleBot(config.TELEGRAM_KEY)


@bot.message_handler(content_types=['text'])
def commands(message: types.Message):
    if message.text == '/id':
        bot.send_message(message.from_user.id, str(message.from_user.id))
    if message.text == '/notify':
        if not database.get_owner_name(message.from_user.id):
            return bot.send_message(message.chat.id, "Вас нет в списке тех, кто может отмечаться")
        send_notification(message.from_user.id)


def send_notification(user_id):
    keyboard = types.InlineKeyboardMarkup()
    data = date.today().__str__() + ";"
    key_full_day = types.InlineKeyboardButton(text='Полный день', callback_data=data + "8")
    key_half_day = types.InlineKeyboardButton(text='Половину дня', callback_data=data + "4")
    key_part_day = types.InlineKeyboardButton(text='N часов (указать)', callback_data=data + "-1")
    key_none = types.InlineKeyboardButton(text='Не работал(а)', callback_data=data + "0")
    keyboard.row(key_full_day, key_half_day)
    keyboard.row(key_part_day, key_none)
    bot.send_message(user_id, text="Сколько сегодня проработал?", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call: types.CallbackQuery):
    hours = int(call.data.split(';')[1])

    if hours == -1:
        bot.edit_message_text(f"Сколько часов?",
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=None)
        return bot.register_next_step_handler_by_chat_id(call.message.chat.id, hours_handler, call)

    update_calendar(call, hours)


def hours_handler(message: types.Message, call):
    hours = message.text
    try:
        hours = float(hours)
    except ValueError:
        hours = -2
    if hours == -1:
        bot.delete_message(message.chat.id, message.id)
        bot.delete_message(message.chat.id, call.message.id)
        send_notification(call.from_user.id)
        return
    if hours < 0 or hours > 12:
        bot.send_message(message.chat.id, "Некорректное количество часов (>12 или <0). Напиши ещё раз. Если нужно отменить отметку, напиши -1")
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, hours_handler, call)
        return
    update_calendar(call, hours)


def update_calendar(call, hours):
    owner = database.get_owner_name(call.from_user.id).get('full_name')
    date_parts = call.data.split(';')[0].split('-')
    mark_date = date(int(date_parts[0]), int(date_parts[1]), int(date_parts[2]))
    if not ch.update_day({
        "owner": owner,
        "day": mark_date.day,
        "month": mark_date.month,
        "weekday": mark_date.weekday(),
        "hours": hours
    }):
        logging.error("Ошибка во время обновления на этапе телеги")
        return bot.send_message(call.message.chat.id, "Произошла ошибка во время обработки запроса")

    bot.edit_message_text(f"Успешно отмечено в календаре!\nОтработано часов сегодня: {hours}",
                          call.message.chat.id,
                          call.message.message_id,
                          reply_markup=None)


if __name__ == '__main__':
    try:
        logging.basicConfig(level=logging.INFO, filename='telegram_log.txt',
                            format="[%(asctime)s] %(levelname)s\t| %(message)s")
        if not (config.CONF_ADDRESS and config.TELEGRAM_KEY and config.CALENDAR_PAGE
                and config.CONF_LOGIN and config.CONF_PASSWORD):
            logging.critical("Файл config.py не заполнен!")
            exit(1)
        bot.infinity_polling(timeout=15, long_polling_timeout=10)
    except (TimeoutError, exceptions.ConnectTimeout, exceptions.ReadTimeout):
        logging.info("В очередной раз пропало соединение с телегой.")
