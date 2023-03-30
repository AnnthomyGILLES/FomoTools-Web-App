FROM certbot/certbot:latest

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
    apt-get install -y python3-mysqldb

# Certbot official installation procedure https://certbot.eff.org/instructions?ws=nginx&os=ubuntufocal
RUN apt-get update && \ 
    apt-get install -y snapd && \

RUN apt-get update && \
    apt-get install -y sudo

RUN echo 'RpEEnjeq7VSyOZvkC3G6' | sudo -S snap install core
    
RUN echo 'RpEEnjeq7VSyOZvkC3G6' | sudo -S snap refresh core
   
RUN echo 'RpEEnjeq7VSyOZvkC3G6' | sudo -S snap install --classic certbot
   
RUN echo 'RpEEnjeq7VSyOZvkC3G6' | sudo -S  ln -s /snap/bin/certbot /usr/bin/certbot


COPY . /fomocode

RUN pip install -r requirements.txt

ENV PYTHONPATH /fomocode

# gunicorn
CMD ["gunicorn", "--config", "gunicorn-cfg.py", "run:app"]

