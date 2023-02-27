#!/usr/bin/env python3
import requests
import config
import calendar_handler

prefix = 'https://api.telegram.org/bot'
geturl = prefix + config.TELEGRAM_KEY + '/getUpdates'
sendurl = prefix + config.TELEGRAM_KEY + '/sendMessage'
timeout = 60


def main():
    offset = 0
    while True:
        dt = dict(offset=offset, timeout=timeout)
        try:
            poll = requests.post(geturl, data=dt, timeout=None).json()
        except ValueError:  # incomplete data
            continue
        if not poll['ok'] or not poll['result']:
            continue
        for response in poll['result']:
            message = response['message']
            chat_id = message['chat']['id']
            if 'text' in message:
                dt = dict(chat_id=chat_id, text=message['text'])
                requests.post(sendurl, data=dt).json()
            offset = response['update_id'] + 1


if __name__ == '__main__':
    try:
        html = calendar_handler.get_calendar(calendar_handler.login())
        calendar_handler.parse_calendar(html)
        # main()
    except KeyboardInterrupt:
        exit()
