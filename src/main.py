#!/usr/bin/env python3
import logging
import time
import requests
import telegram
import database
import calendar_handler as ch
from datetime import date


def main():
    today = date.today()
    if today.day == 1:
        ch.update_month()
    response = requests.get("https://isdayoff.ru/today")
    if response.content == '1':
        return logging.info('Сегодня нерабочий день')

    employees = database.get_all_employees()
    for employee in employees:
        if ch.is_day_off(today.day, today.month, employee.get('full_name')):
            logging.info(f"{employee.get('full_name')}: выходной")
            continue
        while True:
            try:
                telegram.send_notification(employee.get('user_id'))
                logging.info(f"{employee.get('full_name')}: уведомление отправлено")
                time.sleep(2)
                break
            except requests.exceptions.ConnectionError:
                logging.debug("Ошибка во время отправки запроса, пробую снова...")
                time.sleep(5)
                continue


if __name__ == '__main__':
    try:
        logging.basicConfig(level=logging.INFO, filename='main_log.txt',
                            format="[%(asctime)s] %(levelname)s\t| %(message)s")
        main()
    except KeyboardInterrupt:
        exit()
