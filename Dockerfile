FROM python:3.8-slim-buster
ENV STREAMLIT_SERVER_PORT=8001
ENV USER_RWX=adm
ENV USER_RX=usr
ENV PASS_RWX=adm9999
ENV PASS_RX=usr9999
ENV PASS_RWX_ENC=md5096fffbf7ac4f62e6d58f5cb4ec8b58d
ENV PASS_RX_ENC=md5ebc3cdc601f21d3a293faaec4d4bc007

RUN mkdir /app
WORKDIR /app
RUN apt-get update
RUN apt-get install -y bash bash-builtins gnupg2 software-properties-common wget supervisor curl build-essential -y
RUN apt-get update 
RUN apt-get install postgresql postgresql-contrib postgresql-11-postgis-2.5 postgresql-11-postgis-2.5-scripts libpq-dev vim strace lsof -y
RUN apt-get install gdal-bin -y
RUN apt-get autoclean && apt-get clean
RUN python3 -m venv .
RUN mkdir /app/log
COPY requirements.txt /app/
COPY start.sh /app/
COPY create_db.sh /var/lib/postgresql/
COPY import_data.sh /var/lib/postgresql/
COPY *.sql /var/lib/postgresql/
COPY supervisor.conf /app/
COPY *.csv /var/lib/postgresql/
COPY *.vrt /var/lib/postgresql/
RUN . bin/activate && pip3 install -r /app/requirements.txt
COPY *.py /app/
COPY supervisor.conf /app/
ENTRYPOINT ["/app/start.sh"]
EXPOSE 8000
EXPOSE 8001
