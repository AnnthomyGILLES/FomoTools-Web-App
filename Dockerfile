FROM python:3.9

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /fomocode
COPY requirements.txt /fomocode

# install python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# install mysql dependencies
RUN apt-get update && \
    apt-get install -y default-libmysqlclient-dev

RUN apt-get update && \
    apt-get install python3-mysqldb

COPY . /fomocode

RUN pip install -r requirements.txt

ENV PYTHONPATH /fomocode

# gunicorn
CMD ["gunicorn", "--config", "gunicorn-cfg.py", "run:app"]

