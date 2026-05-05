# WorkSafeCenter

**WorkSafeCenter** — это автоматизированная информационная система для управления процессами охраны труда (ОТ) и обеспечения техносферной безопасности на предприятии. Система помогает оцифровать рутинные задачи специалиста по ОТ: от учёта сотрудников и планирования медосмотров до оценки профессиональных рисков и управления инцидентами.

## 📋 Оглавление

- [Основной функционал](#основной-функционал)
- [Архитектура проекта](#архитектура-проекта)
- [Модули системы](#модули-системы)
- [Management-команды](#management-команды)
- [Безопасность и аутентификация](#безопасность-и-аутентификация)
- [Технологический стек](#технологический-стек)
- [Установка и запуск](#установка-и-запуск)
- [Настройка окружения](#настройка-окружения)
- [API и URL-маршруты](#api-и-url-маршруты)
- [План развития](#план-развития)

---

## Основной функционал

Система построена по модульному принципу, охватывая все ключевые аспекты безопасности:

### 👥 Управление персоналом (employees)
- **Иерархическая структура**: Ведение базы данных подразделений (отделов) и должностей
- **Карточки сотрудников**: Полный учёт ФИО, даты рождения, статусов (работает, уволен, декрет, и.о. директора, специалист по ОТ и др.)
- **Связи**: Автоматическая привязка сотрудников к рабочим местам для последующей оценки рисков
- **Шифрование данных**: Email и телефон хранятся в зашифрованном виде (encrypted_model_fields)
- **Массовый импорт**: Загрузка данных из Excel с интерактивным режимом обработки ошибок

### 🎓 Обучение и инструктажи (trainings)
- **Программы обучения**: Создание и хранение учебных программ с категориями (ОТ, ПБ, Первая помощь, Электробезопасность)
- **Журнал инструктажей**: Регистрация вводных, первичных, повторных и целевых инструктажей
- **Контроль сроков**: Отслеживание периодичности обучения и автоматическое информирование о необходимости переаттестации
- **Проверка соответствия**: Автоматическая проверка требований по 4 основным категориям обучения
- **Электробезопасность**: Учёт групп по электробезопасности (Приказ № 811) с проверкой последовательности
- **Стажировки**: Учёт стажировок на рабочем месте для рабочих профессий

### 🏥 Медицинские осмотры (medical_checks)
- **Мониторинг здоровья**: Учёт периодических и предварительных медосмотров
- **Ручное планирование**: Пользователь задаёт дату следующего осмотра; система автоматически вычисляет статусы («просрочен», «истекает», «действует»)
- **Шифрование результатов**: Результаты осмотров хранятся в зашифрованном виде

### ⚖️ СОУТ и Риски (assessments)
- **Специальная оценка (СОУТ)**: Ведение реестра рабочих мест с указанием классов условий труда (1, 2, 3.1-3.4, 4)
- **Автоматический расчёт**: Дата следующей СОУТ рассчитывается автоматически (5 лет), если не указана вручную
- **Оценка рисков**: Регистрация идентифицированных опасностей и оценка уровня профессиональных рисков
- **Планирование**: Экспорт плана СОУТ в Excel
- **Статусы**: "Не проводилась", "Просрочена", "Срок подходит", "Актуальна"

### 📂 Документооборот (documents)
- **Архив документов**: Категоризированное хранилище приказов, инструкций и скан-копий
- **Типы документов**: НПА, ЛНА, Инструкции, Приказы, Сертификаты, Дипломы, Протоколы
- **Контроль сроков**: Отслеживание сроков действия документов
- **Фильтрация**: Поиск по названию, типу, категории, сотруднику

### 🚨 Инциденты (incidents)
- **Регистратор происшествий**: Учёт несчастных случаев и микротравм
- **Классификация**: Типы инцидентов (Несчастный случай, Микротравма)
- **Статистика**: Отчёты по типам и частоте инцидентов
- **Принятые меры**: Документирование действий после инцидента

### 🏢 Организация (organization)
- **Реквизиты**: Хранение данных организации (ИНН, КПП, ОГРН, адрес)
- **Структура**: Отделы с иерархией (подразделения могут иметь вышестоящие отделы)
- **Должности**: Привязка должностей к отделам
- **Площадки**: Учёт филиалов и производственных площадок
- **Ответственные**: Назначение директора, специалиста по ОТ, членов комиссии

### 📊 Отчёты (reports)
- **Панель соответствия**: Общий процент соответствия требованиям по обучению
- **Просроченные медосмотры**: Список сотрудников с истекающими осмотрами
- **Просроченные инструктажи**: Список сотрудников с просроченным обучением
- **План-график обучения**: Формирование списков на обучение с приоритетами
- **Статистика инцидентов**: Анализ по типам
- **СОУТ отчёт**: Статус проведения по рабочим местам
- **Профессиональные риски**: Анализ идентифицированных рисков

### 🔔 Уведомления (notifications)
- **Автоматическая генерация**: Создание уведомлений о приближающихся сроках
- **Типы**: Медосмотры, Инструктажи, СОУТ
- **Период**: Уведомления за 30-60 дней до истечения срока

---
## Архитектура проекта

```
WorkSafeCenter/
├── accounts/ # Аутентификация и профили пользователей
│ ├── management/ # Команды: create_portal_user, generate_keys, migrate_tokens
│ ├── templates/ # Шаблоны входа
│ ├── backends.py # CertificateAuthBackend (2FA по файлу-ключу)
│ ├── middleware.py # LoginRequiredMiddleware
│ └── models.py # UserProfile, LoginAudit
│
├── employees/ # Управление сотрудниками
│ ├── management/ # Команды: import, export, cleanup, setup_training_data
│ ├── models.py # Employee (с шифрованием полей)
│ └── views.py # CRUD операции
│
├── trainings/ # Обучение и инструктажи
│ ├── models.py # TrainingProgram, Training, Instruction, InstructionType
│ ├── services.py # check_employee_compliance (проверка соответствия)
│ ├── forms.py # Валидация групп по электробезопасности
│ └── validators.py # validate_pdf_or_image
│
├── medical_checks/ # Медосмотры
│ └── models.py # MedicalCheck (is_overdue, days_to_expire)
│
├── assessments/ # СОУТ и риски
│ ├── models.py # Workplace, SOUTAssessment, RiskAssessment
│ ├── services.py # check_sout_deadlines, export_sout_plan_to_excel
│ └── views.py # SOUTPlanningListView
│
├── documents/ # Документы
│ └── models.py # Document, Category (с контролем сроков)
│
├── incidents/ # Инциденты
│ └── models.py # Incident (ACCIDENT, MICROTRAUMA)
│
├── organization/ # Структура организации
│ ├── models.py # OrganizationSafetyInfo, Department, Position, Site
│ └── management/ # load_organization_info
│
├── reports/ # Отчёты и аналитика
│ ├── views.py # ComplianceDashboardView, training_plan_report
│ └── templates/ # compliance_dashboard, training_plan
│
├── notifications/ # Уведомления
│ └── management/ # generate_notifications
│
├── config/ # Настройки Django
│ ├── settings/ # base.py, development.py, production.py
│ └── urls.py # Маршрутизация
│
└── static/ # CSS, JS, favicon
```
---
---

## Модули системы

### accounts (Аутентификация)

**Модели:**
- `UserProfile` — Расширение пользователя (auth_token_hash, public_key)
- `LoginAudit` — Журнал попыток входа (IP, timestamp, success)

**Бэкенды:**
- `CertificateAuthBackend` — Двухфакторная аутентификация по файлу-ключу
  - Проверяет логин/пароль
  - Читает файл-ключ (.key)
  - Сравнивает хэш токена с сохранённым в БД (SHA-256)
  - Использует `secrets.compare_digest` для безопасного сравнения

**Middleware:**
- `LoginRequiredMiddleware` — Принудительная авторизация для всех страниц кроме:
  - `/admin/`
  - `/static/`
  - `/media/`
  - Страницы входа

**Команды:**

| Команда| Описание | Пример |
|---------|----------|--------|
| `create_portal_user` | Создание пользователя с профилем | `python manage.py create_portal_user` |
| `generate_keys` | Генерация файла-ключа для 2FA | `python manage.py generate_keys username --force` |
| `migrate_tokens` | Хэширование существующих токенов | `python manage.py migrate_tokens` |

---

### employees (Сотрудники)

**Модель Employee** включает все необходимые поля для кадрового учёта и охраны труда:
```python
class Employee(models.Model):
    first_name, last_name, middle_name, previous_last_name
    position, department, workplace
    birth_date, hire_date, termination_date, termination_order_number
    email, phone                        # Зашифрованы
    is_active                           # Активен
    is_executive                        # Руководящий состав
    on_parental_leave                   # Декретный отпуск
    is_safety_specialist                # Специалист по ОТ
    is_safety_committee_member          # Член комиссии по ОТ
    is_safety_committee_chair           # Председатель комиссии
    is_acting_director                  # И.о. директора
    is_pedagogical                      # Педагогический работник
    is_electrical_responsible           # Отв. за электрохозяйство
    is_electrical_personnel             # Электротехнический персонал
    exempt_from_safety_instruction      # Освобождён от первичного инструктажа
```

**Команды:**

| Команда | Описание | Параметры |
|---------|----------|-----------|
| `import_employee_data` | Импорт из Excel | `file_path`, `--scans-dir`, `--interactive`, `--dry-run`, `--auto-create-employees` |
| `export_employee_template` | Экспорт шаблона Excel | — |
| `cleanup_categories` | Очистка категорий обучения | `--dry-run`, `--force-all`, `--reassign-training`, `--show-remaining` |
| `setup_training_data` | Создание стандартных программ | — |

**Пример импорта:**
```bash
# Режим проверки
python manage.py import_employee_data data.xlsx --dry-run

# Интерактивный режим с загрузкой сканов
python manage.py import_employee_data data.xlsx --scans-dir ./scans --interactive

# Автоматическое создание отсутствующих сотрудников
python manage.py import_employee_data data.xlsx --auto-create-employees
```

---

### trainings (Обучение)

**Модели:**
- `TrainingCategory` — Категории (SAFETY, FIRE, FIRST_AID, ELECTRICAL)
- `TrainingProgram` — Программы обучения (часы, периодичность, обязательность)
- `Training` — Записи о прохождении обучения
- `InstructionType` — Типы инструктажей
- `Instruction` — Проведённые инструктажи
- `TrainingCenter` — Учебные центры
- `Internship` — Стажировки на рабочем месте
- `ElectricalSafetyGroup` — Группы по электробезопасности

**Сервисы:**
- `check_employee_compliance()` — Проверка соответствия требованиям
  - Проверяет 4 основные категории
  - Учитывает статус сотрудника (руководитель, педагог, электротехнический)
  - Возвращает: missing_programs, expired_programs, missing_instructions, expired_instructions

**Валидация:**
- `validate_pdf_or_image` — Разрешены только .pdf, .jpg, .png (макс. 10 МБ)
- Проверка последовательности групп по электробезопасности
- Проверка минимальной группы для ответственных за электрохозяйство (IV группа)

**URL-маршруты:**
```
/trainings/                                 # Список программ
/trainings/programs/create/                 # Создать программу
/trainings/employee/<pk>/training/add/      # Добавить обучение
/trainings/employee/<pk>/instruction/add/   # Добавить инструктаж
/trainings/centers/                         # Учебные центры
/trainings/internships/                     # Стажировки
```

---

### medical_checks (Медосмотры)

**Модель MedicalCheck:**
```python
class MedicalCheck(models.Model):
    employee           # Сотрудник
    check_date         # Дата осмотра
    next_check_date    # Дата следующего (заполняется вручную)
    result             # Зашифрованные результаты
    is_valid           # Действителен
    
    @property
    def is_overdue     # Просрочен ли (на основе next_check_date)
    @property
    def days_to_expire # Дней до истечения
```

**URL-маршруты:**
```
/medical-checks/              # Список
/medical-checks/create/       # Добавить
/medical-checks/<pk>/update/  # Редактировать
/medical-checks/<pk>/delete/  # Удалить
```

---

### assessments (СОУТ и Риски)

**Модели:**
- `Workplace` — Рабочее место (номер, должность, площадка)
- `SOUTAssessment` — Результаты СОУТ (класс, даты, отчёт)
- `RiskAssessment` — Оценка рисков (источник, уровень, меры)

**Классы условий труда:**
- 1 (Оптимальный)
- 2 (Допустимый)
- 3.1-3.4 (Вредный 1-4 ст.)
- 4 (Опасный)

**Уровни рисков:**
- low (Низкий)
- medium (Средний)
- high (Высокий)
- critical (Критический)

**Команды:**

| Команда | Описание |
|---------|----------|
| `check_sout` | Проверка сроков СОУТ и генерация уведомлений |

**Сервисы:**
- `check_sout_deadlines()` — Проверка сроков и создание уведомлений
- `export_sout_plan_to_excel()` — Экспорт плана в Excel

**URL-маршруты:**
```
/assessments/workplaces/                   # Реестр РМ
/assessments/workplaces/create/            # Создать РМ
/assessments/workplaces/<pk>/sout/manage/  # Управление СОУТ
/assessments/planning/                     # Планирование СОУТ
```

---

### documents (Документы)

**Модели:**
- `Category` — Категории документов (Пожарная, Электробезопасность, и т.д.)
- `Document` — Документы с контролем сроков

**Типы документов:**
- FEDERAL (НПА РФ)
- LOCAL (Локальные акты)
- INSTRUCTION (Инструкции по ОТ)
- ORDER (Приказы)
- CERTIFICATE (Сертификаты)
- DIPLOMA (Дипломы)
- PROTOCOL (Протоколы)

**Команды:**

| Команда | Описание |
|---------|----------|
| `setup_categories` | Создание начальных категорий документов |

**URL-маршруты:**
```
/documents/              # Список
/documents/upload/       # Загрузить
/documents/<pk>/delete/  # Удалить
```

---

### incidents (Инциденты)

**Модель Incident:**
```python
class Incident(models.Model):
    INCIDENT_TYPES = (
        ('ACCIDENT', 'Несчастный случай'),
        ('MICROTRAUMA', 'Микротравма'),
    )
    employee         # Пострадавший
    incident_type    # Тип
    incident_date    # Дата и время
    description      # Описание
    actions_taken    # Принятые меры
```

**URL-маршруты:**
```
/incidents/              # Журнал
/incidents/create/       # Зарегистрировать
/incidents/<pk>/update/  # Редактировать
/incidents/<pk>/delete/  # Удалить
```

---

### organization (Организация)

**Модели:**

- `OrganizationSafetyInfo` — Реквизиты организации (синглтон, pk=1)
- `Department` — Отделы (с иерархией parent)
- `Position` — Должности
- `Site` — Площадки/филиалы

**Команды:**

| Команда | Описание |
|---------|----------|
| `load_organization_info` | Загрузка из .env (ORG_NAME_FULL, ORG_STRUCTURE_JSON) |

**Пример ORG_STRUCTURE_JSON:**
```json
{
  "Руководство": ["Директор", "Заместитель директора"],
  "Отдел №1": ["Руководитель отдела", "Работник"],
  "Отдел №2": ["Руководитель отдела", "Работник"]
}
```

**URL-маршруты:**
```
/organization/                    # Структура и реквизиты
/organization/safety-info/edit/   # Редактировать реквизиты
/organization/department/create/  # Добавить отдел
/organization/position/create/    # Добавить должность
/organization/site/create/        # Добавить площадку
```

---

### reports (Отчёты)

**Виды отчётов:**

| Отчёт | URL | Описание |
|-------|-----|----------|
| Главная отчётов | `/reports/` | Индекс всех отчётов |
| Просроченные инструктажи | `/reports/overdue-trainings/` | Сотрудники с просрочкой |
| Просроченные медосмотры | `/reports/overdue-medical-checks/` | Сотрудники с просрочкой |
| Статистика инцидентов | `/reports/incident-statistics/` | По типам инцидентов |
| План-график обучения | `/reports/training-plan/` | С фильтрами и приоритетами |
| СОУТ отчёт | `/reports/sout/` | Статус по рабочим местам |
| Документы | `/reports/documents/` | Реестр документов |
| Риски | `/reports/risks/` | Профессиональные риски |
| Панель соответствия | `/reports/compliance/` | % соответствия требованиям |
| Отчёт сотрудника | `/reports/compliance/employee/<pk>/` | Детальный отчёт |

**Панель соответствия:**
- `total_employees` — Всего сотрудников
- `compliant_count` — Соответствуют всем требованиям
- `violations_count` — Есть просроченные программы/инструктажи
- `warnings_count` — Есть отсутствующие программы/инструктажи
- `compliance_rate` — Процент соответствия

**План-график обучения:**
- Фильтры: категория, программа, горизонт планирования (3/6/12 мес)
- Приоритеты: 1 (Просрочено), 2 (Истекает в месяц), 3-5 (Плановое)
- Причина: "Просрочено", "Истекает", "Первичное обучение"

---

### notifications (Уведомления)

**Модель Notification:**
```python
class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('MEDICAL', 'Медосмотр'),
        ('TRAINING', 'Инструктаж'),
    )
    employee          # Получатель
    notification_type # Тип
    message           # Текст
    sent_date         # Дата создания
    is_sent           # Отправлено
```

**Команды:**

| Команда | Описание |
|---------|----------|
| `generate_notifications` | Генерация уведомлений о приближающихся сроках |

**Периоды:**
- Медосмотры: за 30 дней
- Инструктажи: за 30 дней
- СОУТ: за 60 дней

---

## Management-команды (Полный список)

### 🔐 Безопасность и пользователи (accounts)

#### `create_portal_user`
Создание пользователя портала с профилем.
```bash
python manage.py create_portal_user
```
**Интерактивный процесс:**
1. Ввод логина
2. Ввод пароля (скрытый)
3. Создание пользователя (is_staff=True)
4. Создание UserProfile
5. Инструкция по настройке прав в админке

#### `generate_keys`
Генерация файла-ключа для двухфакторной аутентификации.
```bash
python manage.py generate_keys <username> [опции]
```
**Параметры:**
- `username` — Имя пользователя (обязательно)
- `--output-dir` — Директория для сохранения (по умолчанию: `<BASE_DIR>/keys/`)
- `--force` — Перезаписать существующий файл без подтверждения

**Примеры:**
```bash
# Базовое использование
python manage.py generate_keys ivanov

# С указанием директории
python manage.py generate_keys ivanov --output-dir /secure/keys/

# Принудительная перезапись
python manage.py generate_keys ivanov --force
```

**Формат файла-ключа:**
```
# Файл-ключ для входа в WorkSafeCenter
# НЕ ПЕРЕДАВАЙТЕ ЭТОТ ФАЙЛ ДРУГИМ ЛИЦАМ!
# Username: ivanov
KEY=<64-символьный_токен>
```

**Важно:**
- В БД сохраняется только SHA-256 хэш токена
- Файл передаётся пользователю только безопасным каналом

#### `migrate_tokens`
Хэширование существующих токенов аутентификации.
```bash
python manage.py migrate_tokens
```
**Процесс:**
1. Находит профили с незахэшированными токенами
2. Пропускает уже захэшированные (длина 64, hex-символы)
3. Хэширует остальные через SHA-256
4. Выводит статистику: обработано/пропущено

---

### 📥 Импорт и экспорт данных (employees)

#### `import_employee_data`
Импорт данных организации и сотрудников из Excel.
```bash
python manage.py import_employee_data <file_path> [опции]
```
**Параметры:**
- `file_path` — Путь к Excel файлу (обязательно)
- `--scans-dir` — Папка с PDF-файлами удостоверений
- `--dry-run` — Режим проверки без сохранения
- `--interactive` — Запрашивать действия при ошибках
- `--auto-create-employees` — Автоматически создавать отсутствующих сотрудников

**Структура Excel файла:**

| Лист | Описание |
|------|----------|
| 0. Организация | Название, ИНН, КПП, ОГРН, адрес, телефон |
| 1. Площадки | Название, адрес, ответственный за ОТ |
| 2. Подразделения | Название, описание, вышестоящий отдел |
| 3. Должности | Название, отдел, описание |
| 4. Сотрудники | ФИО, должность, отдел, даты, флаги |
| 5. Программы | Название, тип, часы, периодичность |
| 6. Обучение | ФИО, категория, тип документа, дата, номер, файл |

**Примеры:**
```bash
# Проверка без изменений
python manage.py import_employee_data data.xlsx --dry-run

# Интерактивный режим
python manage.py import_employee_data data.xlsx --interactive

# С загрузкой сканов
python manage.py import_employee_data data.xlsx --scans-dir ./scans

# Полностью автоматический
python manage.py import_employee_data data.xlsx --auto-create-employees
```

**Интерактивный режим — варианты действий:**
1. ⏭️ Пропустить эту запись
2. ⏭️⏭️ Пропустить ВСЕ записи для этого сотрудника
3. 🔍 Показать похожих сотрудников для выбора
4. ✏️ Ввести правильное ФИО вручную
5. ➕ Создать нового сотрудника (только ФИО)
6. 🛑 Остановить импорт

#### `export_employee_template`
Создание Excel-шаблона для заполнения данных.
```bash
python manage.py export_employee_template
```
**Результат:** `full_system_template.xlsx` с 7 листами (0-6)

#### `cleanup_categories`
Очистка базы от лишних категорий обучения.
```bash
python manage.py cleanup_categories [опции]
```
**Параметры:**
- `--dry-run` — Режим проверки
- `--reassign-training` — Переназначить записи на новые категории
- `--show-remaining` — Показать оставшиеся категории
- `--force-all` — Удалить ВСЕ категории кроме 4 основных

**Сохраняемые категории:**
- SAFETY (Охрана труда)
- FIRE (Пожарная безопасность)
- FIRST_AID (Первая помощь)
- ELECTRICAL (Электробезопасность)

#### `setup_training_data`
Создание стандартных программ обучения.
```bash
python manage.py setup_training_data
```
**Создаёт:**
- 4 категории обучения
- 10 стандартных программ (ОТ, ПБ, Первая помощь, Электробезопасность 1-5 группа)

---

### 📋 Документы и организация

#### `setup_categories` (documents)
Создание начальных категорий документов.
```bash
python manage.py setup_categories
```
**Категории:**
- Пожарная безопасность
- Электробезопасность
- Гигиена и санитария
- Работы на высоте
- Офисная работа
- Прочее

#### `load_organization_info` (organization)
Загрузка данных организации из .env.
```bash
python manage.py load_organization_info
```
**Требует в .env:**
- `ORG_NAME_FULL` — Полное название
- `ORG_INN` — ИНН
- `ORG_KPP` — КПП
- `ORG_OGRN` — ОГРН
- `ORG_ADDRESS_LEGAL` — Юридический адрес
- `ORG_CONTACT_PHONE` — Телефон
- `ORG_STRUCTURE_JSON` — JSON структура отделов и должностей

---

### 🔍 Проверки и уведомления

#### `check_sout` (assessments)
Проверка сроков СОУТ и генерация уведомлений.
```bash
python manage.py check_sout
```
**Проверяет:**
- РМ без СОУТ
- РМ с просроченной СОУТ
- РМ с истекающей СОУТ (60 дней)

#### `generate_notifications` (notifications)
Генерация уведомлений о приближающихся сроках.
```bash
python manage.py generate_notifications
```
**Проверяет:**
- Медосмотры (30 дней)
- Инструктажи (30 дней)
- СОУТ (60 дней)

**Рекомендация:** Настроить запуск раз в сутки через cron:
```bash
# /etc/crontab
0 2 * * * user /path/to/venv/bin/python /path/to/manage.py generate_notifications
```

---

## Безопасность и аутентификация

### 🔐 Двухфакторная аутентификация

**Механизм:**
1. Пользователь вводит логин и пароль
2. Пользователь загружает файл-ключ (.key)
3. Система читает токен из файла (KEY=<value>)
4. Вычисляется SHA-256 хэш токена
5. Хэш сравнивается с сохранённым в БД (`secrets.compare_digest`)
6. При совпадении — вход разрешён

**Файлы:**
- `accounts/backends.py` — CertificateAuthBackend
- `accounts/forms.py` — LoginForm с auth_file
- `accounts/templates/accounts/login.html` — Форма входа

**Хранение ключей:**
- В БД: только хэш токена (auth_token_hash)
- На диске: файл .key у пользователя
- В админке: кнопка генерации ключей в профиле пользователя

### 🛡 Защита данных

**Шифрование полей:**
- `Employee.email` — EncryptedEmailField
- `Employee.phone` — EncryptedCharField
- `MedicalCheck.result` — EncryptedTextField

**Настройка:**
```env
FIELD_ENCRYPTION_KEY='ваш_32-символьный_ключ'
```

**Middleware:**
- `LoginRequiredMiddleware` — Принудительная авторизация
- Исключения: /admin/, /static/, /media/, /accounts/login/

---

## Технологический стек

| Компонент | Технология |
|-----------|------------|
| Backend | Python 3.10+ |
| Framework | Django 4.2+ / 5.x |
| Database | PostgreSQL 13+ |
| ORM | Django ORM |
| Security | encrypted_model_fields |
| Excel | openpyxl |
| Dates | python-dateutil |
| Env config | python-dotenv |
| Frontend | Django Templates |
| CSS | Custom (Design Tokens) |
| JS | Vanilla JS |

---

## Установка и запуск

### Шаг 1. Клонирование и окружение
```bash
git clone https://github.com/your-repo/worksafe-center.git
cd worksafe-center
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Шаг 2. Настройка .env
```bash
cp env.sample .env
```

**Минимальная конфигурация:**
```env
# Django
DJANGO_SECRET_KEY='ваш_секретный_ключ'
DJANGO_ENV=development
ALLOWED_HOSTS=127.0.0.1,localhost

# Database
DB_NAME=worksafe_db
DB_USER=postgres
DB_PASSWORD=ваш_пароль
DB_HOST=localhost
DB_PORT=5432

# Encryption
FIELD_ENCRYPTION_KEY='32-символьный_ключ_для_шифрования'

# Organization
ORG_NAME_FULL="ООО «Пример»"
ORG_INN="0000000000"
ORG_KPP="000000000"
ORG_OGRN="0000000000000"
ORG_ADDRESS_LEGAL="000000, город, улица, д. 1"
ORG_CONTACT_PHONE="+7 (000) 000-00-00"
ORG_STRUCTURE_JSON='{"Руководство": ["Директор"], "Отдел": ["Работник"]}'
```

### Шаг 3. Инициализация БД
```bash
python manage.py migrate
python manage.py load_organization_info
python manage.py setup_categories
python manage.py setup_training_data
```

### Шаг 4. Создание пользователей
```bash
# Суперпользователь (админка)
python manage.py createsuperuser

# Пользователь портала
python manage.py create_portal_user

# Генерация ключа для пользователя
python manage.py generate_keys <username>
```

### Шаг 5. Запуск
```bash
# Разработка
python manage.py runserver

# Продакшн (gunicorn)
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

---

## API и URL-маршруты

### Основные маршруты

| Префикс | Модуль | Описание |
|---------|--------|----------|
| `/` | config | Главная панель |
| `/admin/` | Django Admin | Админ-панель |
| `/accounts/` | accounts | Аутентификация |
| `/employees/` | employees | Сотрудники |
| `/trainings/` | trainings | Обучение |
| `/medical-checks/` | medical_checks | Медосмотры |
| `/incidents/` | incidents | Инциденты |
| `/documents/` | documents | Документы |
| `/organization/` | organization | Организация |
| `/assessments/` | assessments | СОУТ и риски |
| `/reports/` | reports | Отчёты |
| `/notifications/` | notifications | Уведомления |

### Детальные маршруты (примеры)
```
# Сотрудники
/employees/                                  # Список
/employees/<pk>/                             # Карточка
/employees/create/                           # Создать
/employees/<pk>/update/                      # Редактировать
/employees/<pk>/delete/                      # Удалить

# Обучение
/trainings/employee/<pk>/training/add/       # Добавить обучение
/trainings/employee/<pk>/instruction/add/    # Добавить инструктаж
/trainings/programs/create/                  # Создать программу

# Отчёты
/reports/compliance/                         # Панель соответствия
/reports/compliance/employee/<pk>/           # Отчёт сотрудника
/reports/training-plan/                      # План-график
```

---

## План развития (Roadmap)

### 🎯 Ближайшие задачи
- [ ] **Дашборд аналитики**: Визуализация статистики (Chart.js)
- [ ] **Ролевая модель**: Права (Специалист ОТ, Инженер, Наблюдатель)

### 📋 В разработке
- [ ] **Календарь событий**: Визуальное отображение сроков на календаре
- [ ] **Массовые операции**: Проведение инструктажей для групп сотрудников
- [ ] **Шаблоны документов**: Генерация приказов и распоряжений

### 🔮 Долгосрочные цели
- [ ] **Машинное обучение**: Предсказание рисков травматизма
