#!/usr/bin/env python3
import requests
import telegram
import database


def main():
    response = requests.get("https://isdayoff.ru/today")
    if response.content == '1':
        return print('Сегодня нерабочий день')

    employees = database.get_all_employees()
    for employee in employees:
        telegram.send_notification(employee.get('user_id'))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()
