# django-telegram-nginx-proxy
My Django + python-telegram-bot + Celery + Redis + Postgres + LetsEncrypt-Nginx-Proxy-Companion + Dokku + GitHub Actions template. Production-ready Telegram bot with database, admin panel and a bunch of useful built-in methods.

[![Sparkline](https://stars.medv.io/Naereen/badges.svg)](https://stars.medv.io/Naereen/badges)


### Check the example bot that uses the code from Main branch: [t.me/djangotelegrambot](https://t.me/djangotelegrambot)

## Features

* Database: Postgres, Sqlite3, MySQL - you decide!
* Admin panel (thanks to [Django](https://docs.djangoproject.com/en/3.1/intro/tutorial01/))
* Background jobs using [Celery](https://docs.celeryproject.org/en/stable/)
* [Production-ready](https://github.com/ohld/django-telegram-bot/wiki/Production-Deployment-using-Dokku) deployment using [Dokku](https://dokku.com)
* Telegram API usage in pooling or [webhook mode](https://core.telegram.org/bots/api#setwebhook)
* Reverse geocode of user via [ArcGis](https://www.arcgis.com/)
* Export all users in `.csv`
* Native telegram [commands in menu](https://github.com/ohld/django-telegram-bot/blob/main/.github/imgs/bot_commands_example.jpg)

Built-in Telegram bot methods:
* `/broadcast` — send message to all users (admin command)
* `/export_users` — bot sends you info about your users in .csv file (admin command)
* `/stats` — show basic bot stats 
* `/ask_for_location` — log user location when received and reverse geocode it to get country, city, etc.

Check out our [Wiki](https://github.com/ohld/django-telegram-bot/wiki) for more info.

# How to run

## Quickstart: Pooling & SQLite

The fastest way to run the bot is to run it in pooling mode using SQLite database without all Celery workers for background jobs. This should be enough for quickstart:

``` bash
git clone https://github.com/Wmag-team/lanka_bot
cd lanka_bot
```

Create virtual environment (optional)
``` bash
python3 -m venv dtb_venv
source dtb_venv/bin/activate
```

Install all requirements:
```
pip install -r requirements.txt
```

Create `.env` file in root directory and copy-paste in .env_example:
``` bash 
DJANGO_DEBUG=False
DATABASE_URL=sqlite:///db.sqlite3
TELEGRAM_TOKEN=<ENTER YOUR TELEGRAM TOKEN HERE>
...
```

Run migrations to setup SQLite database:
``` bash
python manage.py migrate
```

Create superuser to get access to admin panel:
``` bash
python manage.py createsuperuser
```

Run bot in pooling mode:
``` bash
python run_pooling.py 
```

If you want to open Django admin panel which will be located on http://localhost:8000/tgadmin/:
``` bash
python manage.py runserver
```

## Run locally using docker-compose

If you like docker-compose you can check [full instructions in our Wiki](https://github.com/ohld/django-telegram-bot/wiki/Run-locally-using-Docker-compose).

## Deploy to Production 

Read Wiki page on how to [deploy production-ready](https://github.com/ohld/django-telegram-bot/wiki/Production-Deployment-using-Dokku) scalable Telegram bot using Dokku.

----


##  Deploy c нуля

Ставим Python 3.10

``` bash
apt update -y && apt upgrade -y
apt install software-properties-common -y
add-apt-repository ppa:deadsnakes/ppa
apt update -y
apt remove python3.8 python3.8-dev python3.8-venv python3.8-distutils python3.8-lib2to3 python3.8-gdbm python3.8-tk python-is-python3  python3-pip -y
sudo apt --fix-missing purge $(dpkg -l | grep 'python3' | awk '{print $2}')
rm /usr/bin/pip*
rm /usr/bin/python*
apt install python3.10 python3.10-dev python3.10-venv python3.10-distutils python3.10-lib2to3 python3.10-gdbm python3.10-tk -y
update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1
update-alternatives --install /usr/bin/python3 python3 /usr/bin/python 10
curl -sS https://bootstrap.pypa.io/get-pip.py | python
cp /usr/local/bin/*pip* /usr/bin/
python -m pip install --upgrade pip
python --version
python3 --version
pip --version
pip3 --version
```

Ставим Docker

``` bash
apt-get remove docker docker-engine docker.io containerd runc
apt-get update -y
apt-get install ca-certificates curl gnupg lsb-release -y
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
apt-get update -y
apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin -y
echo   "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update -y
apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin -y
docker --version
curl -L "https://github.com/docker/compose/releases/download/v2.6.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/bin/docker-compose
chmod +x /usr/bin/docker-compose
docker-compose --version
```


Колонируем:

``` bash
git clone https://github.com/mitagmio/django-telegram-nginx-proxy.git
cd lanka_bot
```

Create virtual environment (optional)
``` bash
python -m venv dtb_venv
source dtb_venv/bin/activate
python -m pip install --upgrade pip
```

Install all requirements:
```
pip install -r requirements.txt
```

Создаем `.env` файл в корне папки и копируем содержимое файла .env_example 
Далее заполняем переменные:
``` bash 
DJANGO_DEBUG=False
DATABASE_URL=sqlite:///db.sqlite3
TELEGRAM_TOKEN=<ENTER YOUR TELEGRAM TOKEN HERE>
...
```

В системе должен быть установлен Docker версии не ниже 20.10.7:
docker version
```
Client:
 Version:           20.10.7
 API version:       1.41
 Go version:        go1.13.8
 Git commit:        20.10.7-0ubuntu5~20.04.2
 Built:             Mon Nov  1 00:34:17 2021
 OS/Arch:           linux/amd64
 Context:           default
 Experimental:      true

Server:
 Engine:
  Version:          20.10.7
  API version:      1.41 (minimum version 1.12)
  Go version:       go1.13.8
  Git commit:       20.10.7-0ubuntu5~20.04.2
  Built:            Fri Oct 22 00:45:53 2021
  OS/Arch:          linux/amd64
  Experimental:     false
 containerd:
  Version:          1.5.5-0ubuntu3~20.04.2
  GitCommit:        
 runc:
  Version:          1.0.1-0ubuntu2~20.04.1
  GitCommit:        
 docker-init:
  Version:          0.19.0
  GitCommit:  
```

Запускаем наш комплекс контейнеров в первый раз находясь в корневой дирректории проекта:
```
docker compose up -d --build
```

Для остановки комплекса контейнеров:
```
docker compose down
```

Для если нам не требуется пересобирать контейнеры и для последующих запусков используем комманду:
```
docker compose up -d
```

Проверить как собрались контейнеры и все ли наместе можно коммандой:
```
docker ps -a
```
Будет выведено следующее
```
CONTAINER ID   IMAGE                             COMMAND                  CREATED      STATUS      PORTS                                                                      NAMES
374fcfcbbd19   django-telegram-bot_celery-beat   "celery -A dtb beat …"   2 days ago   Up 2 days                                                                              dtb_beat
7dfc3d0e35d9   django-telegram-bot_celery        "celery -A dtb worke…"   2 days ago   Up 2 days                                                                              dtb_celery
aae382aafa05   django-telegram-bot_nginx-proxy   "/docker-entrypoint.…"   2 days ago   Up 2 days   0.0.0.0:80->80/tcp, :::80->80/tcp, 0.0.0.0:443->443/tcp, :::443->443/tcp   nginx-proxy
19bb0c201cae   django-telegram-bot_web           "bash -c 'python man…"   2 days ago   Up 2 days   0.0.0.0:8000->8000/tcp, :::8000->8000/tcp                                  dtb_django
a597bc7fc13e   postgres:12                       "docker-entrypoint.s…"   2 days ago   Up 2 days   0.0.0.0:5433->5432/tcp, :::5433->5432/tcp                                  dtb_postgres
188ad2fe42d9   redis:alpine                      "docker-entrypoint.s…"   2 days ago   Up 2 days   6379/tcp                                                                   dtb_redis
```


Заходи в оболочку контейнера с Django для выполнения миграций и создания пользователя в админку Django:
1. вход в оболочку контейнера
```
docker exec -it dtb_django bash
```
2. создаем суперпользователя для админ панели Django http://host_or_ip/tgadmin/:
```
python manage.py createsuperuser
```
3. создаем миграции из моделей
```
python manage.py makemigrations
```
4. выполняем миграции в для DB
```
python manage.py migrate
```

Заходим в адмнку Django http://host_or_ip/tgadmin/ и планируем задачи:
1. Periodic tasks - для планирование периодических задач
раз в минуту ORDERS_CHANGE_MAILING
раз в час p2p_cource

Должно быть так:
```
ORDERS_CHANGE_MAILING: every minute
p2p_cource: 0 */1 * * * (m/h/dM/MY/d) UTC
```


БЕКАПИТЬ БАЗУ ОТСЮДА:
```
/var/lib/docker/volumes/django-telegram-bot_postgres_data/_data
```
Эту папку сохранить для переноса на другой сервер.


----
