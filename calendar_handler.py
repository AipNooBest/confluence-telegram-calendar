import requests
import config
import json
import database
import calendar
from bs4 import BeautifulSoup


def get_calendar(cookies):
    response = requests.get(config.CONF_API + f'/content/{config.CALENDAR_PAGE}?expand=body.storage',
                            cookies=cookies)
    if response.status_code != 200:
        return None
    return json.loads(response.content)["body"]["storage"]["value"]


def sync_calendar(html_string):
    html = BeautifulSoup(html_string)
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
                            "owner": expander.find("ac:parameter", attrs={'ac:name': 'title'}).text,
                            "day": int(cell.contents[0].text) if hasattr(cell, "contents") else int(cell.text),
                            "month": month_to_number(table.parent.previous_sibling.text),
                            "weekday": j,
                            "hours": get_hours(cell)
                        }
                        database.check_and_update(
                            {"owner": day_object["owner"], "day": day_object["day"], "month": day_object["month"],
                             "weekday": day_object["weekday"]},
                            {"$set": day_object})
                    j += 1


def gen_month_table(month, year):
    template = f'<h1><strong>{number_to_month(month)}</strong></h1><table class="wrapped"><colgroup><col style="width: 40.0px;"><col style="width: 40.0px;"><col style="width: 40.0px;"><col style="width: 40.0px;"><col style="width: 40.0px;"><col style="width: 40.0px;"><col style="width: 40.0px;"></colgroup><tbody><tr><th>ПН</th><th>ВТ</th><th>СР</th><th>ЧТ</th><th>ПТ</th><th>СБ</th><th>ВС</th></tr>'
    first_weekday, days = calendar.monthrange(year, month)

    offset = 8 - first_weekday
    template += "<tr>"
    for _ in range(first_weekday):
        template += "<td><br></td>"
    for i in range(1, offset):
        template += f"""<td{' class="highlight-#ffebe6" data-highlight-colour="#ffebe6"' if i >= 6 else ''}>"""
        template += f"{i}</td>"
    template += "</tr>"

    for i in range(1, 5):
        template += "<tr>"
        for j in range(1, 8):
            if 7*i + j - first_weekday <= days:
                template += f"""<td {'class="highlight-#ffebe6" data-highlight-colour="#ffebe6"' if j >= 6 else ''}>"""
                template += f"{7*i + j - first_weekday}</td>"
            else:
                template += "<td><br></td>"
        template += "</tr>"
    template += "</tbody></table>"
    return template


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


def update_day(day_object):
    try:
        calendar = BeautifulSoup(get_calendar(login()))
        expander = calendar.find("ac:parameter", attrs={'ac:name': 'title'},
                                 text={day_object["owner"]}).parent
        month_div = expander.find("h1", text=number_to_month(day_object["month"])).next_sibling
        if not month_div: return False
        # noinspection PyUnresolvedReferences
        cell = month_div.find("td", text=day_object["day"])
        match day_object["hours"]:
            case 8:
                cell.attrs['data-highlight-colour'] = '#36b37e'
                cell.attrs['class'] = 'highlight-#36b37e'
            case 0:
                cell.attrs['data-highlight-colour'] = '#de350b'
                cell.attrs['class'] = 'highlight-#de350b'
            case _:
                cell.attrs['data-highlight-colour'] = '#ffe380'
                cell.attrs['class'] = 'highlight-#ffe380'
        database.check_and_update({"owner": day_object["owner"], "day": day_object["day"], "month": day_object["month"]},
                                  {"$set": day_object})
        cookie = login()
        page = json.loads(requests.get(config.CONF_API + f'/content/{config.CALENDAR_PAGE}',
                                          cookies=cookie).content)
        data = json.JSONEncoder().encode({
            "id": config.CALENDAR_PAGE,
            "title": page["title"],
            "version": {
                "number": page["version"]["number"] + 1
            },
            "type": "page",
            "body": {
                "storage": {
                    "value": calendar.__str__(),
                    "representation": "storage"
                }
            }
        })
        response = requests.put(config.CONF_API + f'/content/{config.CALENDAR_PAGE}', data=data, cookies=cookie, headers={
            "Content-Type": "application/json"
        })
        if response.status_code != 200:
            raise Exception("Ошибка во время обновления страницы")
        return True
    except Exception as e:
        # Я начну отлавливать ошибки, честно-честно!
        print(e)
        return False


def month_to_number(name):
    months = {'Январь': 1, 'Февраль': 2, 'Март': 3, 'Апрель': 4, 'Май': 5, 'Июнь': 6, 'Июль': 7, 'Август': 8,
              'Сентябрь': 9, 'Октябрь': 10, 'Ноябрь': 11, 'Декабрь': 12}
    return months[name]


def number_to_month(number):
    months = {1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель', 5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август',
              9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'}
    return months[number]


def get_hours(ctx):
    colour = ctx.parent.attrs['data-highlight-colour'] if 'data-highlight-colour' in ctx.parent.attrs else None
    match colour:
        case '#36b37e':
            return 8
        case '#ffe380':
            return float(ctx.parent.contents[1].text[:1]) if len(ctx.parent.contents) > 1 else 4
        case '#de350b':
            return 0
    return 0
