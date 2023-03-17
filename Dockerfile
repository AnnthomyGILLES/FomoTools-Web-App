FROM python:3.9

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install MySQL server and client
RUN apt-get update && apt-get install -y mysql-server
RUN apt-get update && apt-get install -y libmysqlclient-dev

# set working directory
WORKDIR /app

# copy requirements file
COPY requirements.txt .

# install python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# copy app files
COPY . .

# MySQL configuration
ENV MYSQL_ROOT_PASSWORD=root
ENV MYSQL_DATABASE=appseed_db
ENV MYSQL_USER=appseed_db_usr
ENV MYSQL_PASSWORD=pass
RUN echo "CREATE USER '${MYSQL_USER}'@'%' IDENTIFIED BY '${MYSQL_PASSWORD}';" \
    && echo "GRANT ALL PRIVILEGES ON ${MYSQL_DATABASE}.* TO '${MYSQL_USER}'@'%';" \
    | mysql -u root --password=${MYSQL_ROOT_PASSWORD}

# gunicorn
CMD ["gunicorn", "--config", "gunicorn-cfg.py", "run:app"]

