# Django MVP: контроль подання фінансової звітності

MVP для контролю XML-файлів фінансової звітності комунальних підприємств: організації, звітні періоди, очікувані форми, XML-валідація, статуси, Excel-контроль і ZIP-архіви по формах.

## Швидкий запуск

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_report_forms
python manage.py runserver
```

Локально `manage.py` за замовчуванням використовує:

```text
config.settings.dev
```

За замовчуванням використовується SQLite для швидкого локального старту. Для PostgreSQL задайте env-змінні перед `migrate`:

```bash
set POSTGRES_DB=zvit_system
set POSTGRES_USER=postgres
set POSTGRES_PASSWORD=postgres
set POSTGRES_HOST=localhost
set POSTGRES_PORT=5432
python manage.py migrate
```

## Docker запуск

```bash
copy .env.example .env
docker compose up --build
```

В іншому терміналі:

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py seed_report_forms
```

Сайт буде доступний на `http://127.0.0.1:8000/`.

## Settings

Налаштування розділені по середовищах:

- `config.settings.base` — спільна основа;
- `config.settings.dev` — локальна розробка, `DEBUG`, SQLite fallback або PostgreSQL з env;
- `config.settings.prod` — production, `DEBUG=False`, PostgreSQL і security-прапорці;
- `config.settings.test` — швидкі тести на SQLite з тимчасовим `MEDIA_ROOT`.

Приклад явного запуску:

```bash
set DJANGO_SETTINGS_MODULE=config.settings.dev
python manage.py runserver
```

## Створення бази PostgreSQL

Приклад через `psql`:

```sql
CREATE DATABASE zvit_system;
CREATE USER zvit_user WITH PASSWORD 'strong_password';
GRANT ALL PRIVILEGES ON DATABASE zvit_system TO zvit_user;
```

Після цього:

```bash
set POSTGRES_DB=zvit_system
set POSTGRES_USER=zvit_user
set POSTGRES_PASSWORD=strong_password
python manage.py migrate
```

## Основний workflow

1. Створіть superuser:

```bash
python manage.py createsuperuser
```

2. Додайте стандартні `ReportForm`:

```bash
python manage.py seed_report_forms
```

Команда створює форми:

- `J0901107 / S0110014`
- `J0900108 / S0100115`
- `J0900207 / S0100215`
- `J0900904 / S0100311`
- `J0901005 / S0104010`
- `J0901301 / S0105009`

3. Додайте `Organization` в Django Admin: `http://127.0.0.1:8000/admin/`.

Поле `report_type` визначає набір очікуваних форм:

- `small`: тільки `S0110014`
- `full`: обов'язково `S0100115` і `S0100215`

Опційні форми для `full`:

- `S0100311` / `J0900904`
- `S0104010` / `J0901005`
- `S0105009` / `J0901301`

4. Згенеруйте очікувані звіти:

```bash
python manage.py generate_expected_reports --year 2025 --quarter Q2
```

Або через сайт для адміністратора:

```text
/dashboard/generate/
```

На сторінці потрібно вибрати рік, квартал і за потреби конкретні організації або форми.

Додатково можна вибрати конкретні організації та конкретні форми:

- якщо організації не вибрані, генерація буде для всіх активних організацій;
- якщо форми не вибрані, система використає правило за типом організації;
- якщо форми вибрані, система створить саме ці форми для вибраних організацій.

Команда створить `ReportingPeriod`, якщо його ще немає, і не створюватиме дублікати `ExpectedReport`.

За замовчуванням генеруються тільки обов'язкові звіти:

- для `small`: `J0901107`
- для `full`: `J0900108`, `J0900207`

Щоб одразу додати опційні форми для `full`, використайте:

```bash
python manage.py generate_expected_reports --year 2025 --quarter Q2 --include-optional
```

Якщо опційна форма потрібна тільки окремому підприємству, її можна додати вручну в Django Admin як `ExpectedReport`.

5. Прив'яжіть користувача до підприємства через `OrganizationUser`.

Після входу користувач бачить тільки звіти своїх організацій на головній сторінці `/`.

6. Завантажте XML:

- представник підприємства: `/`
- адміністратор: через `ExpectedReport` у Django Admin

Система перевіряє:

- розширення `.xml`
- коректність XML
- ЄДРПОУ
- рік
- квартал
- XML-схему форми

Успішний файл отримує normalized filename: `ЄДРПОУ-рік-квартал.XML`, наприклад `20809229-2025-Q2.XML`.

## Dashboard адміністратора

Сторінка: `/dashboard/`

Доступна staff-користувачам. Є фільтри по періоду, статусу, формі й організації. Список має пагінацію.

У таблиці доступні дії:

- `Прийняти` — змінює статус звіту на `accepted`;
- `Відхилити` — відкриває форму, де адміністратор вказує причину відхилення.

Кожна ручна зміна статусу записується в `ReportStatusLog`: хто змінив, коли змінив, старий статус, новий статус і коментар.

Якщо вибрано період, доступна кнопка Excel-експорту. ZIP-експорт доступний і для вибраного періоду, і для всіх періодів.

## Excel-експорт

Через браузер:

```text
/dashboard/export-xlsx/?period=<period_id>
```

Через management command:

```bash
python manage.py export_control_report --year 2025 --quarter Q2
```

Файл створюється як `exports/control_report_2025_Q2.xlsx` і має листи:

- `received_files`
- `missing_reports`
- `duplicates`
- `summary`

## ZIP-експорт

Через сайт: відкрийте `/dashboard/` і натисніть кнопку `ZIP`.

- якщо період вибраний, буде створено архів тільки за цей період;
- якщо вибрано `Усі періоди`, буде створено `archives_all_periods.zip` без підпапок: один ZIP на кожен тип звіту з файлами за всі періоди.

```bash
python manage.py export_archives --year 2025 --quarter Q2
```

Архіви створюються в `exports/2025_Q2/`:

- `J0901107.zip`
- `J0900108.zip`
- `J0900207.zip`
- `J0900904.zip`
- `J0901005.zip`
- `J0901301.zip`

У ZIP потрапляють тільки звіти зі статусом `uploaded` або `accepted`. Файли всередині мають назву `ЄДРПОУ-рік-квартал.XML`.

## Тести

```bash
python manage.py test
```

Покрито:

- парсинг XML
- визначення кварталу
- успішну валідацію
- помилку при невідповідності ЄДРПОУ
- помилку при невідповідності форми
- генерацію ExpectedReport для `small` і `full`
- normalized filename

## Lint і CI

Локальна перевірка стилю:

```bash
python -m pip install ruff
ruff check .
```

У репозиторії є GitHub Actions workflow `.github/workflows/ci.yml`. Він запускає:

- `ruff check .`
- `python manage.py check`
- `python manage.py test`

## Production checklist

Перед реальним production-запуском:

- встановіть `DJANGO_DEBUG=0`;
- задайте сильний `DJANGO_SECRET_KEY`;
- заповніть `DJANGO_ALLOWED_HOSTS`;
- запускайте з `DJANGO_SETTINGS_MODULE=config.settings.prod`;
- використовуйте PostgreSQL, а не SQLite;
- налаштуйте reverse proxy та HTTPS;
- зберігайте `media/` на persistent storage;
- додайте регулярний backup PostgreSQL і `media/`.
