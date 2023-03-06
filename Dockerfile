FROM python:3.10.10-alpine3.17
WORKDIR /app
COPY ./src config.py requirements.txt ./
RUN pip install -r requirements.txt && echo "0 19 * * 1-5 python /app/main.py" >> /var/spool/cron/crontabs/root
