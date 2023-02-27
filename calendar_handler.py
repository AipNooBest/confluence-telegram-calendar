import requests
import config
import json
import database
from bs4 import BeautifulSoup

all_users = []


def get_calendar(cookies):
    response = requests.get(config.CONF_API + f'/content/{config.CALENDAR_PAGE}?expand=body.view',
                            cookies=cookies)
    if response.status_code != 200:
        return None
    return json.loads(response.content)["body"]["view"]["value"]


def parse_calendar(html_string):
    html = BeautifulSoup(html_string)
    for expander in html.findAll("div", attrs={'class': 'expand-container'}):
        for table in expander.findAll("table"):
            tbody = table.find("tbody")
            rows = tbody.findAll("tr")
            for i in range(1, len(rows)):
                j = 0
                for cell in rows[i]:
                    cell = cell.contents[0]
                    if cell.text[:1].isnumeric():
                        day = {
                            "owner": expander.find("span", attrs={'class': 'expand-control-text'}).text,
                            "day": int(cell.contents[0].text) if hasattr(cell, "contents") else int(cell.text),
                            # "month": month_to_number(expander.contents[].contents[0].text),
                            "month": month_to_number(table.parent.previous_sibling.text),
                            "weekday": j,
                            "hours": get_hours(cell)
                        }
                        all_users.append(day)
                        database.check_and_update({"owner": day["owner"], "day": day["day"], "month": day["month"], "weekday": day["weekday"]},
                                                  {"$set": day})
                    j += 1


def login():
    response = requests.post(config.CONF_ADDRESS + '/dologin.action',
                             data={
                                 'os_username': config.CONF_LOGIN,
                                 'os_password': config.CONF_PASSWORD
                             },
                             headers={
                                 'Content-Type': 'application/x-www-form-urlencoded'
                             })
    if response.status_code != 200:
        raise Exception("Произошла ошибка во время авторизации")
    return response.cookies


def month_to_number(name):
    months = {'Январь': 1, 'Февраль': 2, 'Март': 3, 'Апрель': 4, 'Май': 5, 'Июнь': 6, 'Июль': 7, 'Август': 8,
              'Сентябрь': 9, 'Октябрь': 10, 'Ноябрь': 11, 'Декабрь': 12}
    return months[name]


def get_hours(ctx):
    colour = ctx.parent.attrs['data-highlight-colour'] if 'data-highlight-colour' in ctx.parent.attrs else None
    match colour:
        case '#36b37e':
            return 8
        case '#ffe380':
            return float(ctx.parent.contents[1].text[:1]) if len(ctx.parent.contents) > 1 else 4
        case '#de350b':
            return 0
        case '#00b8d9':     # Отпуск
            return 0
    return 0

