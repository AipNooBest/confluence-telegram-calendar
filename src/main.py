#!/usr/bin/env python3
import logging
import requests
import telegram
import database
import calendar_handler as ch
from datetime import date


def main():
    response = requests.get("https://isdayoff.ru/today")
    if response.content == '1':
        return logging.info('Сегодня нерабочий день')

    today = date.today()
    employees = database.get_all_employees()
    for employee in employees:
        if ch.is_day_off(today.day, today.month, employee.get('full_name')):
            logging.info(f"Сегодня у {employee.get('full_name')} выходной")
            continue
        telegram.send_notification(employee.get('user_id'))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()
