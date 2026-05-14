# MorningHub

## 1. Структура директорий проекта

```text
morninghub/
├── requirements.txt        # Файл зависимостей
├── run.py                   # Точка входа приложения
└── app/
    ├── __init__.py          # Фабрика приложения (create_app)
    ├── config.py            # Конфигурационные классы
    ├── extensions.py        # Инициализация db, login_manager, csrf
    ├── models/              # Слой данных (SQLAlchemy 2.0)
    │   ├── __init__.py
    │   ├── user.py          # Модель пользователя
    │   └── widget.py        # Модель настроек виджетов
    ├── forms/               # WTForms
    │   ├── __init__.py
    │   ├── auth.py          # Формы логина и регистрации
    │   └── settings.py      # Форма настроек (загрузка фона)
    ├── blueprints/          # Роуты (MVC Controller)
    │   ├── __init__.py
    │   ├── auth.py          # Авторизация
    │   ├── dashboard.py     # Главная страница и настройки
    │   └── api.py           # REST эндпоинты для JS и экспорта
    ├── services/            # Бизнес-логика (Сервисный слой)
    │   ├── __init__.py
    │   ├── aggregator.py    # Оркестратор для сбора сводки (экспорт)
    │   ├── currency.py      # Клиент API курсов валют (с кэшированием)
    │   ├── it_news.py       # Парсер новостей IT (Habr/RSS)
    │   ├── politics.py      # Парсер политических новостей
    │   └── uploader.py      # Сервис безопасной загрузки файлов (UUID, проверка MIME)
    ├── static/
    │   ├── css/
    │   │   └── custom.css   # Специфичные стили поверх Bootstrap
    │   ├── js/
    │   │   └── dashboard.js # Fetch API логика для виджетов
    │   └── uploads/         # Директория для фоновых изображений
    └── templates/           # Jinja2 шаблоны
        ├── base.html        
        ├── auth/
        │   ├── login.html
        │   └── register.html
        └── dashboard/
            ├── index.html   
            └── settings.html
```

## 2. Схема базы данных (SQLAlchemy 2.0)

**Таблица `users`**
- `id`: Mapped[int] (Primary Key)
- `username`: Mapped[str] (String(64), Unique, Index, Not Null)
- `password_hash`: Mapped[str] (String(256), Not Null)
- `background_image`: Mapped[str | None] (String(255), Nullable)
- `created_at`: Mapped[datetime] (DateTime, Not Null)
- Связь: `widgets` = relationship("WidgetConfig", back_populates="user", cascade="all, delete-orphan")

**Таблица `widget_configs`**
- `id`: Mapped[int] (Primary Key)
- `user_id`: Mapped[int] (Foreign Key `users.id`, Index, Not Null)
- `widget_type`: Mapped[str] (String(50), Not Null)
- `is_active`: Mapped[bool] (Boolean, Default True, Not Null)
- `position`: Mapped[int] (Integer, Default 0)
- `user` = relationship("User", back_populates="widgets")
- Уникальный Constraint: `UniqueConstraint('user_id', 'widget_type')`

## 3. Маршрутизация (REST API эндпоинты и Views)

**Blueprints: Auth (`/auth`)**
- `GET, POST /auth/login`
- `GET, POST /auth/register`
- `GET /auth/logout`

**Blueprints: Dashboard (`/`)**
- `GET /` — Рендеринг дашборда.
- `GET, POST /settings` — Настройки виджетов и загрузка фона.

**Blueprints: API (`/api/v1`)**
- `GET /api/v1/widgets/it-news` — JSON с новостями.
- `GET /api/v1/widgets/currency` — JSON с курсами валют.
- `GET /api/v1/widgets/politics` — JSON с политическими новостями.
- `PATCH /api/v1/widgets/<widget_type>/toggle` — Переключение состояния виджета.
- `GET /api/v1/export?format=<txt|csv>` — Генерация утренней сводки.
