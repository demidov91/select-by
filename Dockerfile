FROM python:3.7

RUN mkdir /app
ADD manage.py /app/manage.py
ADD requirements.txt /app/requirements.txt

WORKDIR /app
RUN pip install -r requirements.txt

CMD ["./start_docker.sh"]
