import re
import requests
import config
import json
import database
import calendar
import logging
from datetime import date
from bs4 import BeautifulSoup


def get_calendar(cookies):
    response = requests.get(config.CONF_API + f'/content/{config.CALENDAR_PAGE}?expand=body.storage',
                            cookies=cookies)
    if response.status_code != 200:
        logging.error("Не удалось получить календарь. Ответ сервера: " + response.text)
        return None
    return json.loads(response.content)["body"]["storage"]["value"]


def sync_calendar():
    try:
        html = BeautifulSoup(get_calendar(login()), 'html.parser')
        for expander in html.findAll("ac:structured-macro", attrs={'ac:name': 'expand'}):
            for table in expander.findAll("table"):
                tbody = table.find("tbody")
                rows = tbody.findAll("tr")
                for i in range(1, len(rows)):
                    j = 0
                    for cell in rows[i]:
                        cell = cell.contents[0]
                        if cell.text[:1].isnumeric():
                            day_object = {
                                "owner": expander.find("ac:parameter", attrs={'ac:name': 'title'}).text.strip(),
                                "day": int(cell.contents[0].text) if hasattr(cell, "contents") else int(cell.text),
                                "month": _month_to_number(table.previous_sibling.text),
                                "weekday": j,
                                "hours": _get_hours(cell)
                            }
                            database.check_and_update(
                                {"owner": day_object["owner"], "day": day_object["day"], "month": day_object["month"],
                                 "weekday": day_object["weekday"]},
                                {"$set": day_object})
                        j += 1
        return True
    except Exception:
        logging.exception("Ошибка при синхронизации календаря.")
    return False


def is_day_off(day, month, employee):
    sync_calendar()
    page = BeautifulSoup(get_calendar(login()), 'html.parser')
    expander = page.find("ac:parameter", attrs={'ac:name': 'title'},
                         text={employee}).parent
    month_div = expander.find("h1", text=_number_to_month(month)).next_sibling
    if not month_div: raise Exception("Ошибка при обработке календаря")
    # noinspection PyUnresolvedReferences
    cell = month_div.find("td", text=day)
    if 'data-highlight-colour' in cell.attrs and cell.attrs['data-highlight-colour'] == '#ffebe6':
        logging.info("Сегодня выходной по приказу начальства")
        return True
    return False


def _gen_month_table(month, year):
    header = f'<h1><strong>{_number_to_month(month)}</strong></h1>'
    header = BeautifulSoup(header, 'html.parser').contents[0]
    template = '<table class="wrapped"><colgroup><col style="width: 40.0px;"><col style="width: 40.0px;"><col style="width: 40.0px;"><col style="width: 40.0px;"><col style="width: 40.0px;"><col style="width: 40.0px;"><col style="width: 40.0px;"></colgroup><tbody><tr><th>ПН</th><th>ВТ</th><th>СР</th><th>ЧТ</th><th>ПТ</th><th>СБ</th><th>ВС</th></tr>'
    first_weekday, days = calendar.monthrange(year, month)

    offset = 8 - first_weekday
    template += "<tr>"
    for _ in range(first_weekday):
        template += "<td><br></td>"
    for i in range(1, offset):
        template += f"""<td{' class="highlight-#ffebe6" data-highlight-colour="#ffebe6"' if i + first_weekday >= 6 else ''}>"""
        template += f"{i}</td>"
    template += "</tr>"

    for i in range(1, 5):
        template += "<tr>"
        for j in range(1, 8):
            if 7 * i + j - first_weekday <= days:
                template += f"""<td {'class="highlight-#ffebe6" data-highlight-colour="#ffebe6"' if j >= 6 else ''}>"""
                template += f"{7 * i + j - first_weekday}</td>"
            else:
                template += "<td><br></td>"
        template += "</tr>"
    template += "</tbody></table>"
    template = BeautifulSoup(template, 'html.parser').contents[0]
    return header, template


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


def update_month():
    sync_calendar()
    page = BeautifulSoup(get_calendar(login()), 'html.parser')
    for expander in page.findAll("ac:structured-macro", attrs={'ac:name': 'expand'}):
        current_month = expander.contents[1].contents[2]
        next_month = expander.contents[1].contents[4]
        today = date.today()
        if next_month.text == _number_to_month(today.month):
            expander.contents[1].contents[0] = current_month
            expander.contents[1].contents[1] = current_month.next_sibling
            expander.contents[1].contents[2] = next_month
            expander.contents[1].contents[3] = next_month.next_sibling
            expander.contents[1].contents[4], expander.contents[1].contents[5] = \
                _gen_month_table(today.month + 1, today.year if today.month != 12 else today.year + 1)
    _upload_page(page)


def update_day(day_object):
    try:
        sync_calendar()
        page = BeautifulSoup(get_calendar(login()))
        expander = page.find("ac:parameter", attrs={'ac:name': 'title'},
                             text={day_object["owner"]}).parent
        month_div = expander.find("h1", text=_number_to_month(day_object["month"])).next_sibling
        if not month_div: return False
        hours = float(f"{day_object['hours']:.1f}") if not int(day_object['hours']) == float(day_object['hours']) else int(day_object['hours'])
        # noinspection PyUnresolvedReferences
        cell: Tag = month_div.find(text=re.compile(str(day_object["day"]))).parent
        if len(cell.contents) > 1:
            for i in range(1, len(cell.contents)):
                cell.contents[i].extract()
        match day_object["hours"]:
            case 8:
                cell.attrs['data-highlight-colour'] = '#36b37e'
                cell.attrs['class'] = 'highlight-#36b37e'
            case 0:
                cell.attrs['data-highlight-colour'] = '#de350b'
                cell.attrs['class'] = 'highlight-#de350b'
            case _:
                cell.attrs['data-highlight-colour'] = '#ffc400'
                cell.attrs['class'] = 'highlight-#ffc400'
                sub = page.new_tag("sub")
                sub.string = str(hours) + "ч"
                cell.append(sub)

        database.check_and_update(
            {"owner": day_object["owner"], "day": day_object["day"], "month": day_object["month"],
             "weekday": day_object["weekday"]},
            {"$set": day_object})
        _upload_page(page)
        return True
    except Exception as e:
        # Я начну отлавливать ошибки, честно-честно!
        logging.exception("Ошибка во время обновления дня")
    return False


def _upload_page(content: BeautifulSoup):
    cookie = login()
    current_page = json.loads(requests.get(config.CONF_API + f'/content/{config.CALENDAR_PAGE}',
                                           cookies=cookie).content)
    data = json.JSONEncoder().encode({
        "id": config.CALENDAR_PAGE,
        "title": current_page["title"],
        "version": {
            "number": current_page["version"]["number"] + 1
        },
        "type": "page",
        "body": {
            "storage": {
                "value": content.__str__(),
                "representation": "storage"
            }
        }
    })
    response = requests.put(config.CONF_API + f'/content/{config.CALENDAR_PAGE}', data=data, cookies=cookie, headers={
        "Content-Type": "application/json"
    })
    if response.status_code != 200:
        raise Exception("Ошибка во время обновления страницы")


def _month_to_number(name):
    months = {'Январь': 1, 'Февраль': 2, 'Март': 3, 'Апрель': 4, 'Май': 5, 'Июнь': 6, 'Июль': 7, 'Август': 8,
              'Сентябрь': 9, 'Октябрь': 10, 'Ноябрь': 11, 'Декабрь': 12}
    return months[name]


def _number_to_month(number):
    months = {1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель', 5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август',
              9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'}
    return months[number]


def _get_hours(ctx):
    colour = ctx.parent.attrs['data-highlight-colour'] if 'data-highlight-colour' in ctx.parent.attrs else None
    match colour:
        case '#36b37e':
            return 8
        case '#ffc400':
            return float(ctx.parent.contents[1].text[:1]) if len(ctx.parent.contents) > 1 else 4
        case '#de350b':
            return 0
    return 0
