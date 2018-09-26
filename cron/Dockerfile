FROM dzmitry/rate

RUN apt-get update && apt-get install -y cron
ADD crontab /etc/cron.d/crontab
RUN chmod 0644 /etc/cron.d/crontab

CMD printenv | sed 's/^\(.*\)$/export \1/g' > /home/cron-env.sh && chmod u+x /home/cron-env.sh && cron -f