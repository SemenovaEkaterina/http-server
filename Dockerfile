FROM python:3

USER root

WORKDIR /

ADD . /

EXPOSE 80

RUN mkdir -p /var/www/html

CMD [ "ls" ]
CMD [ "python", "./server.py" ]