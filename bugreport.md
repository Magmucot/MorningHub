Ты профессиональный программист и ревьюер кода. Твоя задача максимально детально и подробно проверить проект: https://github.com/Magmucot/MorningHub Проверь детально фронт, конфликты имен, бекенд, работу с базой данных и все остальное, проведи проверку 2 раза и составь список ошибок и и как их исправить. 
Напиши отдельно список того, что легко и желательно улучшить. Также проверь логику проекта! НЕ ПЕРЕУСЛОЖНЯЙ КОД! Сейчас проект при хосте на render.com по адресу https://morninghub.onrender.com дает ошибку 500

Я проверю репозиторий как код-ревью: сначала подтвержу состояние публичного проекта и деплоя, затем клонирую код, пройду фронт/бекенд/БД/конфиги, запущу статические проверки и повторно сверю самые критичные места.

Думал на протяжении 3m 35s

Проверил проект в 2 прохода: сначала деплой/старт/БД/бекенд, затем фронт/API/названия/логику. Локально полноценно прогнать проект не смог: из контейнера не удалось склонировать GitHub из-за DNS, поэтому ревью основано на публичном коде репозитория, страницах файлов GitHub и проверке внешнего деплоя. Точный stack trace Render без логов я не вижу, но причин для 500 в коде достаточно.

Главный вывод

500 на Render почти наверняка связан не с фронтом, а со стартом приложения, конфигом окружения, БД или экспортом. Внешняя проверка деплоя сейчас не возвращает нормальный ответ приложения.

Самые критичные проблемы:

FLASK_ENV должен быть строго dev или prod, иначе create_app() падает на config_by_name[config_name]. При обычном значении production будет ошибка.
В проде требуется DB_URL, но в requirements.txt нет PostgreSQL-драйвера (psycopg2-binary/psycopg). Если Render DB — Postgres, приложение упадёт при подключении.
start.sh не подходит для Render: требует локальную .venv, генерирует новый SECRET_KEY при каждом старте, ставит SQLite fallback и биндит Gunicorn на 0.0.0.0:5000, тогда как Render рекомендует биндиться на порт из PORT; дефолтный ожидаемый порт Render — 10000.
db.create_all() в run.py выполняется только при прямом запуске python run.py, а при gunicorn run:app блок if __name__ == "__main__" не выполняется. Значит, таблицы могут не создаваться.
Экспорт /api/v1/export вызывает синхронный агрегатор, а тот вызывает async-функцию get_ai_summary() без await / asyncio.run(). Это реальный runtime-баг.
Что исправить в первую очередь, чтобы убрать 500
1. Исправить конфиг окружения

Сейчас:

config_obj = config_by_name[config_name]

Это опасно. Нужно сделать мягкое сопоставление:

# app/config.py

config_by_name = {
    "dev": DevConfig,
    "development": DevConfig,
    "prod": ProdConfig,
    "production": ProdConfig,
}

И в create_app:

def create_app(config_name: str = "dev") -> Flask:
    app = Flask(__name__)

    config_name = (config_name or "dev").lower()
    config_obj = config_by_name.get(config_name, DevConfig)

    app.config.from_object(config_obj)

На Render поставь переменные:

FLASK_ENV=prod
SECRET_KEY=<постоянный длинный ключ>
DB_URL=<строка подключения к БД>

SECRET_KEY нельзя генерировать при каждом запуске: пользователи будут терять сессии, CSRF-токены станут невалидными.

2. Добавить драйвер Postgres

В requirements.txt добавь один из вариантов:

psycopg2-binary

или современный вариант:

psycopg[binary]

Сейчас зависимости содержат Flask, SQLAlchemy и Gunicorn, но драйвера PostgreSQL нет.

3. Исправить start.sh под Render

Сейчас скрипт падает, если нет .venv, а на Render при обычном Python Runtime зависимости ставятся в окружение сервиса, а не обязательно в .venv. Также порт захардкожен на 5000.

Минимальный вариант:

#!/bin/bash
set -e

export FLASK_ENV=${FLASK_ENV:-prod}

python init_db.py

exec gunicorn \
  -w "${WEB_CONCURRENCY:-2}" \
  --bind "0.0.0.0:${PORT:-10000}" \
  --access-logfile - \
  "run:app"

Создай init_db.py:

from app import create_app
from app.extensions import db

from app.models.user import User
from app.models.widget import WidgetConfig
from app.models.bookmark import Bookmark

app = create_app("prod")

with app.app_context():
    db.create_all()

Это не переусложняет проект. Да, миграции через Alembic лучше, но для текущего состояния init_db.py проще и достаточно, чтобы убрать 500 из-за отсутствующих таблиц.

4. Проверить Render Start Command

В Render лучше поставить:

bash start.sh

или без start.sh:

python init_db.py && gunicorn --bind 0.0.0.0:$PORT "run:app"

Build Command:

pip install -r requirements.txt
Критичные ошибки в бекенде
1. /api/v1/export может падать из-за async-функции

В api.py экспорт вызывает:

tekst = sobr_summary_t(act_wid_lst)

А внутри sobr_summary_t():

res = get_ai_summary(w.user)

Но get_ai_summary объявлена как async def. Значит res — coroutine, а не dict. После этого код делает:

if "error" in res:

Это может дать 500.

Исправить просто:

# app/services/aggregator.py

import asyncio

...

if w.w_tip == "ai_summary":
    summary.append("\n--- ИИ-Пересказ Новостей ---")
    res = asyncio.run(get_ai_summary(w.user))

    if "error" in res:
        summary.append(f"Ошибка: {res['error']}")
    else:
        summary.append(res.get("summary", ""))

Ещё лучше — сделать отдельную sync-обёртку, но для текущего Flask/Gunicorn варианта asyncio.run() достаточно.

2. _safe_commit() возвращает False, но результат почти везде игнорируется

Например, добавление закладки:

db.session.add(bm)
_safe_commit()
return jsonify({"success": True, "id": bm.id})

Даже если commit упал, API вернёт success: true. То же самое есть в удалении закладки, сохранении сетки, lock-grid и toggle.

Исправить шаблонно:

if not _safe_commit():
    return jsonify({"success": False, "error": "Ошибка сохранения в БД"}), 500

Пример:

db.session.add(bm)

if not _safe_commit():
    return jsonify({"success": False, "error": "Ошибка сохранения закладки"}), 500

return jsonify({"success": True, "id": bm.id})
3. Неправильная обработка boolean

Сейчас:

current_user.setka_lock = bool(data["is_grid_locked"])
w.is_act = bool(data["is_active"])

Если вдруг фронт или сторонний клиент отправит строку "false", Python сделает bool("false") == True.

Исправление:

value = data.get("is_active")

if not isinstance(value, bool):
    return jsonify({"error": "is_active должен быть boolean"}), 400

w.is_act = value

Для lock-grid аналогично.

4. Сетка сохраняет координаты без валидации

save-grid принимает x, y, w, h из JSON и сразу пишет в БД. Можно отправить отрицательные значения, огромные размеры или строки.

Простой фикс:

def _int_range(value, default, min_v, max_v):
    try:
        value = int(value)
    except (TypeError, ValueError):
        return default
    return max(min_v, min(max_v, value))

И использовать:

w.x = _int_range(i.get("x"), w.x, 0, 11)
w.y = _int_range(i.get("y"), w.y, 0, 100)
w.w = _int_range(i.get("w"), w.w, 1, 12)
w.h = _int_range(i.get("h"), w.h, 1, 20)
5. Экспорт CSV сделан неправильно

Сейчас CSV строится заменой переносов строк:

csv_t = tekst.replace("\n", '","')
csv_t = f'"{csv_t}"'

Это ломается на кавычках, запятых, переносах и русских текстах.

Простой фикс:

import csv
from io import StringIO

buf = StringIO()
writer = csv.writer(buf)
for line in tekst.splitlines():
    writer.writerow([line])

return Response(
    buf.getvalue(),
    mimetype="text/csv",
    headers={"Content-disposition": "attachment; filename=morning_summary.csv"},
)
Ошибки и риски в БД
1. Названия в README не совпадают с реальной моделью

README описывает поля username, password_hash, background_image, user_id, widget_type, is_active, position, а в коде используются usr_name, pass_hash, back_img, usr_id, w_tip, is_act, poz. Это не runtime-баг, но это прямой источник путаницы, ошибок в миграциях, тестах и API-клиентах.

Не надо переименовывать всё прямо сейчас. Достаточно привести README к реальному коду или наоборот выбрать один стиль для новых участков.

2. Не все модели гарантированно импортируются перед create_all()

В create_app() внутри app context импортируется только User. Таблицы WidgetConfig и Bookmark создадутся только если они импортированы где-то ещё до db.create_all(). Это хрупко.

В init_db.py явно импортируй все модели:

from app.models.user import User
from app.models.widget import WidgetConfig
from app.models.bookmark import Bookmark
3. API-ключ пользователя хранится открытым текстом

В модели User есть поле ai_key, и настройки прямо записывают туда ключ.

Минимальный фикс без усложнения:

# не показывать ключ обратно в форме полностью
# в форме оставить placeholder: "ключ сохранён"
# менять ключ только если поле не пустое
new_key = request.form.get("ai_api_key", "").strip()
if new_key:
    current_user.ai_key = new_key

Лучше — шифровать ключи, но это уже следующий этап.

Ошибки логики проекта
1. Новым пользователям включается ai_summary, хотя API-ключа может не быть

При регистрации всем пользователям создаётся активный ai_summary.
Если ключ не настроен, виджет будет показывать ошибку. Хуже: экспорт с активным ai_summary сейчас может падать из-за async-багa.

Простой фикс:

w = WidgetConfig(
    usr_id=usr.id,
    w_tip=tip,
    poz=idx,
    is_act=(tip != "ai_summary")
)
2. _prover_wid_def() говорит “расставляем ниже существующих”, но не расставляет

Код добавляет новые виджеты так:

WidgetConfig(usr_id=usr_id, w_tip=tip, is_act=True)

То есть poz, x, y остаются дефолтными. Все новые виджеты могут оказаться в одной позиции.

Фикс:

start_pos = len(est_wid)

for offset, tip in enumerate(wid_def):
    if tip not in est_tipi:
        pos = start_pos + offset
        nov_wid.append(
            WidgetConfig(
                usr_id=usr_id,
                w_tip=tip,
                is_act=True,
                poz=pos,
                x=(pos % 4) * 3,
                y=(pos // 4) * 3,
                w=3,
                h=3,
            )
        )
3. Дашборд не сортирует виджеты

На главной странице активные виджеты берутся через .all() без сортировки.

Исправить:

wid_lst = (
    WidgetConfig.query
    .filter_by(usr_id=current_user.id, is_act=True)
    .order_by(WidgetConfig.poz.asc(), WidgetConfig.y.asc(), WidgetConfig.x.asc())
    .all()
)
4. Настройки ИИ могут случайно стереть ключ

В settings каждый POST делает:

current_user.ai_key = request.form.get("ai_api_key", "").strip() or None

Если пользователь отправит форму с пустым полем, старый ключ удалится.

Лучше:

new_key = request.form.get("ai_api_key", "").strip()
if new_key:
    current_user.ai_key = new_key

И добавить отдельную кнопку “Удалить ключ”.

5. Погода использует час сервера, а не час города

Open-Meteo вызывается с timezone=auto, но текущий час берётся как datetime.datetime.now().hour, то есть по timezone сервера, а не города.

Простой вариант: брать первые 12 значений из hourly после текущего времени, сравнивая строки ISO, или хотя бы не использовать локальный час сервера.

Фронтенд
Что хорошо

CSRF-токен есть в base.html, и JS отправляет X-CSRFToken в fetch-запросах. Это правильно.

Названия виджетов на фронте в основном совпадают с бекендом: data-widget="{{ widget.w_tip }}", затем JS отправляет widget_type: w_tip, а API ищет по w_tip.

Что плохо
1. XSS-риск через новости

JS вставляет внешние заголовки и ссылки через template string в innerHTML:

<a href="${i.link}" ...>${i.title}</a>

Данные приходят из внешних источников, поэтому лучше создавать DOM-элементы через textContent и setAttribute.

Простой фикс:

const item = document.createElement("div");
item.className = "news-item";

const a = document.createElement("a");
a.target = "_blank";
a.rel = "noopener noreferrer";
a.href = i.link || "#";
a.textContent = i.title || "Без названия";

item.appendChild(a);
list.appendChild(item);
2. Fetch не проверяет HTTP-статус

Сейчас:

fetch(u)
  .then(r => r.json())

Если API вернёт HTML-страницу ошибки 500, r.json() упадёт, но пользователь увидит только общую ошибку.

Добавь общий helper:

async function apiJson(url, options = {}) {
  const r = await fetch(url, options);

  let data = null;
  try {
    data = await r.json();
  } catch {
    data = { error: "Сервер вернул не JSON" };
  }

  if (!r.ok) {
    throw new Error(data.error || `HTTP ${r.status}`);
  }

  return data;
}
3. После добавления закладки перезагружается вся страница

Это не критично, но легко улучшить. Сейчас после успешного POST:

if (d.success) window.location.reload();

Можно просто добавить закладку в DOM без reload.

Конфликты имён
1. it-news vs it_news

В README указан тип it-news, а в БД и коде используется it_news. API endpoint действительно /widgets/it-news, но тип виджета — it_news. Это нужно явно задокументировать, иначе легко сломать toggle/save-grid.

Рекомендация: завести один словарь:

WIDGETS = {
    "it_news": {
        "title": "IT Новости",
        "api": "/api/v1/widgets/it-news",
        "default_active": True,
    },
    "game_news": {
        "title": "Игровые Новости",
        "api": "/api/v1/widgets/game-news",
        "default_active": True,
    },
}

И использовать его в регистрации, _prover_wid_def, settings template, dashboard template и JS. Это не переусложнение, а удаление дублирования.

2. SQLALCHEMY_DB_URI vs SQLALCHEMY_DATABASE_URI

В конфиге используется кастомное имя SQLALCHEMY_DB_URI, потом оно мапится в SQLALCHEMY_DATABASE_URI.

Лучше сразу:

SQLALCHEMY_DATABASE_URI = os.environ.get(...)
Безопасность
Загрузка файлов проверяет f.mimetype, который приходит от клиента. Это лучше, чем ничего, но не настоящая MIME-проверка. README говорит про python-magic, но в зависимостях его нет, а uploader его не использует.
Фоновые изображения сохраняются в app/static/uploads. На Render файловая система без persistent disk может быть непостоянной между деплоями/рестартами. Render поддерживает persistent disks, но их нужно явно подключать.
Нет ограничения количества закладок. Пользователь может создать очень много записей.
Нет URL-валидации закладок. Нужно разрешить хотя бы только http:// и https://.
AI-ключ хранится открытым текстом. Минимально — не показывать его обратно и не затирать пустым полем.
Лёгкие и желательные улучшения
Добавить /healthz:
@bp.route("/healthz")
def healthz():
    return {"status": "ok"}
Добавить render.yaml, чтобы не настраивать Render руками:
services:
  - type: web
    name: morninghub
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: bash start.sh
    envVars:
      - key: FLASK_ENV
        value: prod
Обновить README под реальный код: реальные поля БД, реальные env vars, реальный старт на Render.
Добавить .env.example:
FLASK_ENV=dev
SECRET_KEY=change-me
DB_URL=sqlite:///db/morninghub_dev.db
OPENAI_API_KEY=
OPENAI_BASE_URL=
OPENAI_MODEL_NAME=
Добавить нормальные логи ошибок API:
logger.exception("Failed to save bookmark")
Уменьшить Gunicorn workers на бесплатном Render:
WEB_CONCURRENCY=2
Вынести список виджетов в один файл, чтобы не повторять его в auth.py, dashboard.py, templates и JS.
Добавить простые тесты хотя бы на:
регистрацию;
login;
/api/v1/widgets/save-grid;
/api/v1/widgets/<w_tip>/toggle;
/api/v1/export.
Добавить error pages для 500/404, чтобы пользователь видел нормальное сообщение, а не голую ошибку.
Исправить опечатки в UI: например “вклюключить”.
Минимальный порядок исправлений
Добавить Postgres-драйвер в requirements.txt.
Исправить config_by_name, чтобы поддерживались production и development.
Переделать start.sh: убрать .venv, использовать $PORT, не генерировать SECRET_KEY.
Создать init_db.py и явно импортировать все модели.
Исправить async-баг в aggregator.py.
Проверять результат _safe_commit().
Исправить boolean-поля.
Потом уже фронт: XSS через новости, fetch helper, README, единый словарь виджетов.

После этих пунктов вероятность текущей 500 на Render должна резко снизиться. Самые подозрительные конкретно для Render: DB_URL/Postgres-драйвер, FLASK_ENV, отсутствие создания таблиц при gunicorn run:app, и несовместимый start.sh.

Ты профессиональный программист и ревьюер кода. Твоя задача максимально детально и подробно проверить проект: https://github.com/Magmucot/MorningHub Проверь детально фронт, конфликты имен, бекенд, работу с базой данных и все остальное, проведи проверку 2 раза и составь список ошибок и и как их исправить. 
Напиши отдельно список того, что легко и желательно улучшить. Также проверь логику проекта! НЕ ПЕРЕУСЛОЖНЯЙ КОД! Сейчас проект при хосте на render.com по адресу https://morninghub.onrender.com дает ошибку 500

Проверю проект в два прохода: сначала Render/старт/конфиг/БД и вероятные причины 500, затем backend, API, frontend, имена, безопасность и бизнес-логику.

Публичный корень сейчас редиректит на вход, а регистрация открывается, поэтому сужаю 500 до авторизованной части, API/экспорта, записи в БД или старта Render.

Думал на протяжении 7m 25s

Проверил проект в 2 прохода: сначала деплой/старт/БД/бекенд, потом фронт/названия/логика пользовательских сценариев. Важное уточнение: на момент моей внешней проверки https://morninghub.onrender.com/ не отдавал 500 на публичной странице, а редиректил на страницу логина; /auth/register тоже открывался. Значит, 500, который ты видишь, вероятнее возникает после авторизации, при обращении к API-виджетам, экспорту, регистрации с записью в БД или на другом состоянии деплоя.

Ниже — максимально практичный список проблем и исправлений без лишнего усложнения.

Короткий вердикт

Самые вероятные причины 500 на Render:

Неправильный старт под Render: start.sh требует .venv, генерирует новый SECRET_KEY, ставит SQLite fallback и запускает Gunicorn на 0.0.0.0:5000. Render рекомендует привязываться к 0.0.0.0 и порту из переменной PORT, дефолт — 10000.
Конфиг окружения слишком хрупкий: create_app() делает config_by_name[config_name], а config_by_name содержит только dev и prod. Если на Render стоит привычное FLASK_ENV=production, будет KeyError и падение приложения.
PostgreSQL-драйвер отсутствует: прод-конфиг ждёт DB_URL, но в requirements.txt нет psycopg2-binary или psycopg. Если DB_URL указывает на Postgres, SQLAlchemy не сможет подключиться без DBAPI-драйвера.
Таблицы создаются не всегда: в run.py db.create_all() выполняется только при прямом python run.py, но не при gunicorn run:app.
Экспорт может гарантированно падать: aggregator.py вызывает async-функцию get_ai_summary() без await / asyncio.run(), а регистрация включает ai_summary всем новым пользователям по умолчанию.
Что исправить первым делом, чтобы убрать 500
1. Исправить requirements.txt

Сейчас есть Flask, Flask-SQLAlchemy, SQLAlchemy, Gunicorn, OpenAI и т.д., но нет PostgreSQL-драйвера.

Минимально добавь:

psycopg2-binary

Это самый простой вариант, потому что обычный URL вида postgresql://... в SQLAlchemy исторически идёт через psycopg2. Если хочешь использовать новый psycopg, тогда надо не только добавить зависимость:

psycopg[binary]

но и привести URL к виду:

postgresql+psycopg://user:password@host:port/dbname

SQLAlchemy отдельно документирует psycopg / psycopg2 как DBAPI-варианты для PostgreSQL.

2. Исправить конфиг окружения

Сейчас:

config_obj = config_by_name[config_name]

и:

config_by_name = dict(dev=DevConfig, prod=ProdConfig)

Это хрупко: production, development, пустая строка или неправильное значение убивают приложение.

Исправь так:

# app/config.py

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-replace-in-prod")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = BASE_DIR / "app" / "static" / "uploads"
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024


class DevConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DB_URL",
        f"sqlite:///{BASE_DIR / 'db' / 'morninghub_dev.db'}",
    )


class ProdConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DB_URL")

    @classmethod
    def init_app(cls, app):
        if not cls.SQLALCHEMY_DATABASE_URI:
            raise ValueError("Переменная среды DB_URL требуется в рабочей среде.")
        if not os.environ.get("SECRET_KEY"):
            raise ValueError("Переменная среды SECRET_KEY требуется в рабочей среде.")


config_by_name = {
    "dev": DevConfig,
    "development": DevConfig,
    "prod": ProdConfig,
    "production": ProdConfig,
}

И в app/__init__.py:

def create_app(config_name: str = "dev") -> Flask:
    app = Flask(__name__)

    config_name = (config_name or "dev").lower()
    config_obj = config_by_name.get(config_name, DevConfig)

    app.config.from_object(config_obj)

    if hasattr(config_obj, "init_app"):
        config_obj.init_app(app)

    ...

Я бы убрал кастомное имя SQLALCHEMY_DB_URI и везде использовал стандартное SQLALCHEMY_DATABASE_URI. Сейчас проект сначала задаёт SQLALCHEMY_DB_URI, а потом вручную перекладывает его в SQLALCHEMY_DATABASE_URI; это работает, но лишний источник путаницы.

3. Исправить start.sh под Render

Текущий start.sh:

падает, если нет .venv;
принудительно ставит FLASK_ENV=prod;
генерирует новый SECRET_KEY, если он не задан;
ставит SQLite fallback;
запускает Gunicorn на 0.0.0.0:5000;
использует 4 воркера независимо от тарифа/CPU.

Render ожидает, что веб-сервис будет слушать порт на 0.0.0.0, а рекомендуемый порт надо брать из PORT; дефолт PORT — 10000.

Замени start.sh на простой:

#!/bin/bash
set -e

export FLASK_ENV=${FLASK_ENV:-prod}

python init_db.py

exec gunicorn \
  --workers "${WEB_CONCURRENCY:-2}" \
  --bind "0.0.0.0:${PORT:-10000}" \
  --access-logfile - \
  "run:app"

На Render в Environment Variables поставь:

FLASK_ENV=prod
SECRET_KEY=<длинный-постоянный-секрет>
DB_URL=<строка-подключения-к-БД>
WEB_CONCURRENCY=2

SECRET_KEY должен быть постоянным. Если он меняется при каждом старте, сессии пользователей будут инвалидироваться, CSRF-токены станут ломаться, а поведение логина будет нестабильным.

4. Добавить init_db.py

Сейчас db.create_all() в run.py выполняется только при python run.py, но при gunicorn run:app блок if __name__ == "__main__" не выполняется.

Добавь отдельный файл:

# init_db.py

import os

from app import create_app
from app.extensions import db

# Явные импорты моделей полезны для регистрации metadata.
from app.models.user import User
from app.models.widget import WidgetConfig
from app.models.bookmark import Bookmark


app = create_app(os.getenv("FLASK_ENV", "prod"))

with app.app_context():
    db.create_all()

Да, миграции через Alembic/Flask-Migrate правильнее для взрослого продакшена, но для текущего проекта init_db.py — нормальный простой шаг, чтобы не переусложнять.

5. Исправить экспорт: async-баг в aggregator.py

В ai_summary.py функция объявлена так:

async def get_ai_summary(user: User) -> Dict[str, Any]:

А в aggregator.py она вызывается синхронно:

res = get_ai_summary(w.user)

После этого код проверяет:

if "error" in res:

Но res в этот момент — coroutine, а не dict. Это может давать 500 при экспорте, особенно потому что новые пользователи получают активный ai_summary по умолчанию.

Минимальный фикс:

# app/services/aggregator.py

import asyncio

...

if w.w_tip == "ai_summary":
    summary.append("\n--- ИИ-Пересказ Новостей ---")

    res = asyncio.run(get_ai_summary(w.user))

    if "error" in res:
        summary.append(f"Ошибка: {res['error']}")
    else:
        summary.append(res.get("summary", ""))

И лучше отключить AI summary по умолчанию при регистрации:

for idx, tip in enumerate(wid_def):
    w = WidgetConfig(
        usr_id=usr.id,
        w_tip=tip,
        poz=idx,
        is_act=(tip != "ai_summary"),
    )
    db.session.add(w)

Так новый пользователь не будет сразу получать ошибку “API-ключ не настроен”.

Проход 1: бекенд, БД, деплой
Ошибка 1. _safe_commit() почти везде игнорируется

В api.py есть хорошая функция:

def _safe_commit() -> bool:
    try:
        db.session.commit()
        return True
    except SQLAlchemyError as err:
        db.session.rollback()
        logger.error("Ошибка транзакции БД: %s", err)
        return False

Но результат часто не проверяется. Например, создание закладки делает commit и всё равно возвращает success: True; удаление, сохранение сетки, lock-grid и toggle делают то же самое.

Исправление:

db.session.add(bm)

if not _safe_commit():
    return jsonify({"success": False, "error": "Ошибка сохранения закладки"}), 500

return jsonify({"success": True, "id": bm.id})

То же самое для:

api_weather()
api_delete_bookmark()
save_grid_widgets()
lock_grid()
toggle_widget()
Ошибка 2. Boolean-поля обрабатываются через bool(...)

Сейчас:

current_user.setka_lock = bool(data["is_grid_locked"])
w.is_act = bool(data["is_active"])

Проблема: bool("false") == True. Если когда-нибудь фронт или внешний клиент отправит строку "false", виджет включится, а не выключится.

Простой фикс:

value = data.get("is_active")

if not isinstance(value, bool):
    return jsonify({"error": "is_active должен быть boolean"}), 400

w.is_act = value

Для is_grid_locked аналогично:

value = data.get("is_grid_locked")

if not isinstance(value, bool):
    return jsonify({"error": "is_grid_locked должен быть boolean"}), 400

current_user.setka_lock = value
Ошибка 3. save-grid принимает любые координаты и размеры

Сейчас API берёт x, y, w, h из JSON и пишет в БД без проверки:

w.x = i.get("x", w.x)
w.y = i.get("y", w.y)
w.w = i.get("w", w.w)
w.h = i.get("h", w.h)

Можно отправить строки, отрицательные значения, огромные размеры. Это легко ломает GridStack-раскладку.

Простой helper:

def _int_range(value, default, min_v, max_v):
    try:
        value = int(value)
    except (TypeError, ValueError):
        return default

    return max(min_v, min(max_v, value))

Использование:

w.x = _int_range(i.get("x"), w.x, 0, 11)
w.y = _int_range(i.get("y"), w.y, 0, 100)
w.w = _int_range(i.get("w"), w.w, 1, 12)
w.h = _int_range(i.get("h"), w.h, 1, 20)
Ошибка 4. CSV-экспорт сделан небезопасно и некорректно

Сейчас CSV строится так:

csv_t = tekst.replace("\n", '","')
csv_t = f'"{csv_t}"'

Это ломается на кавычках, запятых, переносах строк и русскоязычном тексте с нестандартными символами.

Исправь через стандартный csv:

import csv
from io import StringIO

...

elif fmt == "csv":
    buf = StringIO()
    writer = csv.writer(buf)

    for line in tekst.splitlines():
        writer.writerow([line])

    return Response(
        buf.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-disposition": "attachment; filename=morning_summary.csv"
        },
    )
Ошибка 5. Регистрация пишет в БД без обработки ошибок

Регистрация создаёт пользователя, делает flush(), создаёт виджеты и делает commit() без try/except. Если таблицы не созданы, БД недоступна или возникает другая SQL-ошибка — пользователь получит 500.

Минимальный фикс:

try:
    db.session.add(usr)
    db.session.flush()

    for idx, tip in enumerate(wid_def):
        db.session.add(
            WidgetConfig(
                usr_id=usr.id,
                w_tip=tip,
                poz=idx,
                is_act=(tip != "ai_summary"),
            )
        )

    db.session.commit()

except Exception:
    db.session.rollback()
    flash("Ошибка регистрации. Попробуйте позже.", "danger")
    return render_template("auth/register.html", form=form), 500

Лучше ловить SQLAlchemyError, но даже такой вариант уже лучше голого 500.

Ошибка 6. Настройки ИИ могут случайно стереть ключ

В settings():

current_user.ai_key = request.form.get("ai_api_key", "").strip() or None

Если пользователь откроет настройки и сохранит форму с пустым полем API key, старый ключ удалится.

Исправление:

new_ai_key = request.form.get("ai_api_key", "").strip()

if new_ai_key:
    current_user.ai_key = new_ai_key

Для удаления ключа лучше сделать отдельную кнопку “Удалить API-ключ”.

Ошибка 7. API-ключ хранится открытым текстом

В модели User есть поле ai_key, которое хранит ключ пользователя в БД.

Минимально сейчас:

Не показывать ключ обратно в форме.
Не затирать его пустым значением.
В UI показывать “ключ сохранён”.
Менять ключ только если пользователь ввёл новый.

Шифрование ключей — правильнее, но это уже следующий уровень. Сейчас достаточно не ухудшать безопасность случайным отображением и затиранием.

Ошибка 8. SQLite fallback на Render опасен

start.sh ставит:

export DB_URL=${DB_URL:-sqlite:///$(pwd)/db/morninghub_prod.db}

На Render файловая система по умолчанию ephemeral: без persistent disk локальные изменения файлов теряются при redeploy/restart.

Для Render лучше:

данные пользователей — в Render Postgres;
загруженные обои — либо persistent disk, либо внешнее хранилище;
не использовать SQLite fallback в prod.

Если пока хочешь оставить SQLite, то хотя бы подключи Render Persistent Disk и пиши БД/загрузки туда, например в /var/data.

Ошибка 9. Загрузка файлов проверяет MIME недостаточно надёжно

uploader.py проверяет f.mimetype и расширение. UUID-имя — хорошо, но mimetype приходит от клиента и не является полноценной проверкой содержимого файла.

README обещает python-magic, но в requirements.txt его нет. README прямо указывает python-magic, а requirements его не содержит.

Простой вариант без усложнения:

from PIL import Image

def _is_real_image(file_storage):
    try:
        pos = file_storage.stream.tell()
        Image.open(file_storage.stream).verify()
        file_storage.stream.seek(pos)
        return True
    except Exception:
        return False

Но тогда надо добавить Pillow. Если не хочешь новую зависимость — хотя бы честно убери из README обещание про python-magic.

Проход 2: фронт, имена, логика проекта
Ошибка 10. XSS-риск через innerHTML, новости и AI summary

В dashboard.js данные виджетов собираются в HTML-строки и вставляются через innerHTML / outerHTML. Там же AI summary рендерится через marked.parse(...).

Marked официально предупреждает, что не санитизирует HTML и при обработке потенциально небезопасных строк нужен DOMPurify или аналог. MDN также указывает innerHTML как частый вектор XSS при вставке небезопасных строк.

Для новостей лучше не собирать HTML строкой:

function renderNewsItem(item) {
  const div = document.createElement("div");
  div.className = "news-item";

  if (item.error) {
    div.textContent = item.error;
    return div;
  }

  const a = document.createElement("a");
  a.href = item.link || "#";
  a.target = "_blank";
  a.rel = "noopener noreferrer";
  a.textContent = item.title || "Без названия";

  div.appendChild(a);
  return div;
}

Для AI summary два варианта:

Вариант простой и безопасный, без Markdown:

kon.textContent = d.summary || "";

Вариант с Markdown:

<script src="https://cdn.jsdelivr.net/npm/dompurify@3.2.3/dist/purify.min.js"></script>
const rawHtml = marked.parse(d.summary || "");
const safeHtml = DOMPurify.sanitize(rawHtml);
kon.innerHTML = safeHtml;
Ошибка 11. Fetch не проверяет HTTP-статус

В dashboard.js часто используется схема:

fetch(u)
  .then(r => r.json())

Если сервер вернёт HTML-страницу 500, r.json() упадёт, и пользователь увидит не реальную ошибку, а общее “ошибка загрузки”.

Добавь общий helper:

async function apiJson(url, options = {}) {
  const response = await fetch(url, options);

  let data = null;
  try {
    data = await response.json();
  } catch {
    data = { error: "Сервер вернул не JSON" };
  }

  if (!response.ok) {
    throw new Error(data.error || `HTTP ${response.status}`);
  }

  return data;
}

И дальше:

apiJson(u)
  .then(d => {
    risuy_wid(tip, d, div_kon);
  })
  .catch(err => {
    showWidgetError(div_kon, err.message);
  });
Ошибка 12. Конфликты имён в README, БД и API

README описывает поля:

username
password_hash
background_image
user_id
widget_type
is_active
position

А реальные модели используют:

usr_name
pass_hash
back_img
usr_id
w_tip
is_act
poz

README также пишет тип виджета it-news, а в БД и коде используется it_news; при этом endpoint действительно /api/v1/widgets/it-news.

Не надо сейчас массово переименовывать все поля. Это рискованно. Лучше сделать один словарь виджетов и использовать его в auth, dashboard, settings, API и шаблонах:

# app/widgets.py

WIDGETS = {
    "it_news": {
        "title": "IT Новости",
        "endpoint": "/api/v1/widgets/it-news",
        "default_active": True,
    },
    "game_news": {
        "title": "Игровые Новости",
        "endpoint": "/api/v1/widgets/game-news",
        "default_active": True,
    },
    "currency": {
        "title": "Курсы валют",
        "endpoint": "/api/v1/widgets/currency",
        "default_active": True,
    },
    "ai_summary": {
        "title": "ИИ-Сводка Новостей",
        "endpoint": "/api/v1/widgets/ai-summary",
        "default_active": False,
    },
}

Потом в регистрации:

for idx, (tip, cfg) in enumerate(WIDGETS.items()):
    db.session.add(
        WidgetConfig(
            usr_id=usr.id,
            w_tip=tip,
            poz=idx,
            is_act=cfg["default_active"],
        )
    )

Это не усложнение, а удаление дублирования.

Ошибка 13. _prover_wid_def() добавляет новые виджеты поверх старых

В dashboard.py комментарий говорит “расставляем новые виджеты ниже существующих”, но реально новые виджеты создаются только так:

WidgetConfig(usr_id=usr_id, w_tip=tip, is_act=True)

То есть poz, x, y остаются дефолтными. У нескольких виджетов может быть одна позиция.

Исправление:

start_pos = len(est_wid)

for offset, tip in enumerate(wid_def):
    if tip not in est_tipi:
        pos = start_pos + offset

        nov_wid.append(
            WidgetConfig(
                usr_id=usr_id,
                w_tip=tip,
                is_act=(tip != "ai_summary"),
                poz=pos,
                x=(pos % 4) * 3,
                y=(pos // 4) * 3,
                w=3,
                h=3,
            )
        )
Ошибка 14. Дашборд не сортирует активные виджеты

В index():

wid_lst = WidgetConfig.query.filter_by(usr_id=current_user.id, is_act=True).all()

Порядок не гарантирован. В settings сортировка уже есть через order_by(WidgetConfig.poz), а на главной нет.

Исправление:

wid_lst = (
    WidgetConfig.query
    .filter_by(usr_id=current_user.id, is_act=True)
    .order_by(WidgetConfig.poz.asc(), WidgetConfig.y.asc(), WidgetConfig.x.asc())
    .all()
)
Ошибка 15. Экспорт не соответствует обещанной логике

README говорит, что агрегатор собирает данные всех активных виджетов.

Но aggregator.py обрабатывает только:

ai_summary
currency
it_news
game_news
ai_models
politics

В экспорт не попадают:

weather
crypto
bookmarks
calendar
analog_clock

Для календаря и часов это нормально, но weather, crypto, bookmarks пользователь ожидает видеть в сводке.

Минимальное расширение:

elif w.w_tip == "weather":
    summary.append("\n--- Погода ---")
    # лучше вызвать weath_prog(w.user)

elif w.w_tip == "crypto":
    summary.append("\n--- Криптовалюты ---")
    # вызвать get_crypto_kurs(w.user.crypto_lst)

elif w.w_tip == "bookmarks":
    summary.append("\n--- Закладки ---")
    for bm in w.user.bookmarks:
        summary.append(f"- {bm.title}: {bm.url}")
Ошибка 16. Криптовалюты: есть словарь alias, но он не используется

В crypto.py есть IPUT_NAMES:

"btc": "bitcoin",
"eth": "ethereum",
"ton": "the-open-network",
...

Но get_crypto_kurs() берёт пользовательский ввод и сразу отправляет его в CoinGecko:

c_lst = [c.strip().lower() for c in crypto_lst_str.split(",") if c.strip()]
id_lst = ",".join(c_lst)

То есть если пользователь введёт btc, eth, API получит btc,eth, а не bitcoin,ethereum.

Исправление:

INPUT_NAMES = {
    "btc": "bitcoin",
    "eth": "ethereum",
    "ton": "the-open-network",
    "sol": "solana",
    "bnb": "binancecoin",
    "xrp": "ripple",
    "doge": "dogecoin",
    "ada": "cardano",
    "trx": "tron",
    "dot": "polkadot",
    "ltc": "litecoin",
    "not": "notcoin",
}

raw_lst = [c.strip().lower() for c in crypto_lst_str.split(",") if c.strip()]
c_lst = [INPUT_NAMES.get(c, c) for c in raw_lst][:10]

Заодно исправить опечатку IPUT_NAMES → INPUT_NAMES.

Ошибка 17. Погода берёт текущий час сервера, а не города

Open-Meteo вызывается с timezone=auto, но потом код делает:

curr_h = datetime.datetime.now().hour
chas_vremya = [t.split("T")[1] for t in hourly["time"][curr_h : curr_h + 12]]

Если сервер на Render в другом часовом поясе, прогноз по часам будет смещён.

Простой фикс: использовать время из массива hourly["time"], а не час сервера. Например:

from datetime import datetime

now_iso = datetime.now().strftime("%Y-%m-%dT%H:00")

times = hourly["time"]
start = 0

for idx, time_value in enumerate(times):
    if time_value >= now_iso:
        start = idx
        break

chas_vremya = [t.split("T")[1] for t in times[start:start + 12]]
chas_temp = hourly["temperature_2m"][start:start + 12]

Это всё ещё не идеально по timezone, но лучше, чем брать час сервера.

Ошибка 18. Тесты сейчас больше похожи на ручные скрипты

В папке tests есть много файлов, но пример test_api.py делает requests на http://127.0.0.1:5000, логинится как admin/password, печатает ответы и не содержит нормальных pytest assertions/fixtures.

Минимально полезный тест:

def test_register_login(client):
    response = client.post(
        "/auth/register",
        data={
            "username": "TestUser",
            "password": "Password123",
            "confirm_password": "Password123",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

Но для этого надо добавить pytest fixture с app/test DB. Это желательно, но не первый шаг для исправления Render.

Логика проекта: что работает неправильно с точки зрения пользователя
1. Новый пользователь сразу получает активный AI summary

Проблема: без API-ключа он увидит ошибку. А экспорт может падать из-за async-багa.

Исправление: ai_summary по умолчанию выключен.

2. Виджеты дублируются в нескольких местах

Список виджетов повторяется в:

auth.py;
dashboard.py;
шаблонах index.html;
шаблонах settings.html;
dashboard.js.

Это уже привело к конфликтам it_news / it-news и разным названиям. Нужен один словарь WIDGETS.

3. Экспорт обещает “все активные виджеты”, но экспортирует не все

Нужно либо:

добавить weather, crypto, bookmarks в экспорт;
либо честно написать в README, что экспортируются только новости/валюты/AI.

Лучше добавить, это несложно.

4. Закладки не валидируются

Сейчас проверяется только наличие url и title; URL можно отправить любой строкой.

Минимальный фикс:

from urllib.parse import urlparse

def _is_http_url(url):
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

Использование:

url = data.get("url", "").strip()

if not _is_http_url(url):
    return jsonify({"error": "URL должен начинаться с http:// или https://"}), 400
5. Закладки после добавления перезагружают всю страницу

В dashboard.js после добавления закладки вызывается window.location.reload(). Это не баг, но UX слабый.

Можно оставить на потом. Это не причина 500.

Конфликты имён
Критичные
Где	Сейчас	Проблема	Что сделать
README	username, password_hash	В модели usr_name, pass_hash	Обновить README или переименовать поля через миграцию позже
README	user_id, widget_type, is_active, position	В модели usr_id, w_tip, is_act, poz	README привести к коду
README/API	it-news	В БД it_news, endpoint /it-news	Ввести словарь WIDGETS
config	SQLALCHEMY_DB_URI	Flask-SQLAlchemy ожидает SQLALCHEMY_DATABASE_URI; сейчас есть ручное перекладывание	Использовать стандартное имя сразу
crypto	IPUT_NAMES	Опечатка и словарь не используется	Переименовать в INPUT_NAMES и применять
Лёгкие и желательные улучшения

Это не обязательно для исправления 500, но сделать стоит.

1. Добавить /healthz
@bp.route("/healthz")
def healthz():
    return {"status": "ok"}

Лучше отдельный blueprint или route в create_app():

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

На Render можно поставить Health Check Path:

/healthz
2. Добавить .env.example
FLASK_ENV=dev
SECRET_KEY=change-me
DB_URL=sqlite:///db/morninghub_dev.db

OPENAI_API_KEY=
OPENAI_BASE_URL=
OPENAI_MODEL_NAME=
3. Добавить render.yaml
services:
  - type: web
    name: morninghub
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: bash start.sh
    envVars:
      - key: FLASK_ENV
        value: prod
      - key: WEB_CONCURRENCY
        value: 2

SECRET_KEY и DB_URL лучше задавать через Render Dashboard как секреты.

4. Обновить README

README сейчас говорит про pyproject.toml, но в корне репозитория видны requirements.txt, run.py, start.sh, uv.lock, а pyproject.toml в списке корневых файлов не отображается.

README нужно привести к реальному способу установки:

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py

И отдельно:

bash start.sh

для Render/production.

5. Добавить нормальные логи исключений

В местах с except лучше использовать:

logger.exception("Не удалось сохранить настройки")

а не только logger.error(...), чтобы видеть stack trace.

6. Ограничить размер пользовательских списков

Для crypto_lst и val_lst уже в UI написано “до 10 шт”, но на бекенде это надо реально ограничить.

items = [x.strip() for x in raw.split(",") if x.strip()]
items = items[:10]
7. Удалять старые фоновые изображения

Сейчас новый фон сохраняется, старый файл остаётся. Это постепенно замусорит storage.

Минимально после успешной загрузки:

old_img = current_user.back_img

current_user.back_img = imya_f
db.session.commit()

if old_img:
    old_path = os.path.join(current_app.config["UPLOAD_FOLDER"], old_img)
    if os.path.exists(old_path):
        os.remove(old_path)
8. CDN-скрипты лучше закрепить

base.html подключает Bootstrap, GridStack, FontAwesome, Chart.js и Marked.js с CDN.

Для учебного проекта нормально. Для продакшена лучше:

либо хранить локально;
либо использовать integrity/crossorigin;
либо хотя бы зафиксировать версии, что частично уже сделано.
Минимальный порядок исправлений

Делай в таком порядке:

Добавить Postgres-драйвер в requirements.txt: psycopg2-binary.
Исправить config.py: поддержать prod, production, dev, development; использовать SQLALCHEMY_DATABASE_URI.
Исправить start.sh: убрать обязательную .venv, убрать генерацию SECRET_KEY, использовать $PORT.
Добавить init_db.py и вызывать его перед Gunicorn.
Поставить Render env vars: FLASK_ENV=prod, SECRET_KEY, DB_URL, WEB_CONCURRENCY=2.
Исправить async-баг в aggregator.py.
Отключить ai_summary по умолчанию для новых пользователей.
Начать проверять результат _safe_commit().
Исправить boolean и save-grid validation.
Потом фронт: apiJson, безопасный render новостей, DOMPurify или отказ от innerHTML для AI summary.

Самые подозрительные конкретно для Render: порт, DB_URL/Postgres-драйвер, FLASK_ENV, создание таблиц при Gunicorn, и экспорт с активным AI summary.