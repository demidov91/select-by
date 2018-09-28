FROM dzmitry/rate

RUN apt-get update -y && apt-get install -y cron postgresql-client awscli

ADD crontab /etc/cron.d/crontab
RUN chmod 644 /etc/cron.d/crontab

CMD env > /home/cron-env.sh && chmod u+x /home/cron-env.sh && cron -f