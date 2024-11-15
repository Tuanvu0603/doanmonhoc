version: '3.8'

services:
  web:
    build: .
    ports:
      - "5001:5001"
    volumes:
      - .:/app
    environment:
      - FLASK_ENV=development
      - FLASK_APP=app.py
      - SECRET_KEY=default_secret_key
      - SALT=default_salt
    command: >
      sh -c "
        flask db init &&
        flask db migrate &&
        flask db upgrade &&
        flask run --host=0.0.0.0 --port=5001
      "
    depends_on:
      - db

  db:
    image: mysql:8.0
    environment:
      MYSQL_DATABASE: music_streaming
      MYSQL_USER: root
      MYSQL_PASSWORD: 123456
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql

volumes:
  mysql_data: mysql_data:/var/lib/mysql
