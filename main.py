#!/usr/bin/env python3
import requests
import config

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


def get_calendar():
    # В будущем сделать поиск лучше
    response = requests.get(config.CONF_API + '/content/12345678?expand=body.view').json()


def login():
    pass


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()
