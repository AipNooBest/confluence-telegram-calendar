import logging

import telebot
import config
import calendar_handler as ch
from telebot import types
from datetime import date

import database

bot = telebot.TeleBot(config.TELEGRAM_KEY)


@bot.message_handler(content_types=['text'])
def info(message: types.Message):
    if message.text == '/id':
        bot.send_message(message.from_user.id, str(message.from_user.id))
    if message.text == '/notif':
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
    date_parts = call.data.split(';')[0].split('-')
    mark_date = date(int(date_parts[0]), int(date_parts[1]), int(date_parts[2]))
    hours = call.data.split(';')[1]

    owner = database.get_owner_name(call.from_user.id)
    if not owner:
        return bot.send_message(call.message.chat.id, "Вас нет в списке тех, кто может отмечаться. Обратитесь к @aipnoobest")

    if hours == -1:
        bot.edit_message_text(f"Пока не реализовано",
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=None)

    if not ch.update_day({
        "owner": owner,
        "day": mark_date.day,
        "month": mark_date.month,
        "weekday": mark_date.weekday(),
        "hours": hours
    }):
        logging.error("Ошибка во время обновления на этапе телеги")
        return bot.send_message(call.message.chat.id, "Произошла ошибка во время обработки запроса. Обратитесь к @aipnoobest")

    bot.edit_message_text(f"Успешно отмечено в календаре!\nОтработано часов сегодня: {hours}",
                          call.message.chat.id,
                          call.message.message_id,
                          reply_markup=None)


bot.polling(none_stop=True)
