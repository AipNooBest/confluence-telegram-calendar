FROM python:3.10.10-alpine3.17
WORKDIR /app
RUN echo 'http://dl-cdn.alpinelinux.org/alpine/v3.6/main' >> /etc/apk/repositories
RUN echo 'http://dl-cdn.alpinelinux.org/alpine/v3.6/community' >> /etc/apk/repositories
RUN apk add mongodb
RUN mkdir -p "/data/db"
COPY . .
RUN mongod --bind-ip 0.0.0.0 &
RUN pip install -r requirements.txt
RUN echo "0 19 * * 1-5 python /app/main.py" >> /var/spool/cron/crontabs/root
EXPOSE 27017
ENTRYPOINT ["python", "telegram.py"]
