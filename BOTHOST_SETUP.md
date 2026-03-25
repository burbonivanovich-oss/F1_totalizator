# Развёртывание на bothost.ru

## Проблема

bothost.ru автоматически детектирует тип проекта по файлам. Так как в репозитории есть `.js` файлы (фронтенд для Mini App), платформа ошибочно определяет проект как **Node.js**, а не Python.

В результате:
- Platform использует Node.js контейнер вместо Python
- Ошибка: `python3: not found`

## Решение

### Вариант 1: Используй dashboard bothost.ru (рекомендуется)

1. **Логин** в аккаунт bothost.ru
2. **Перейди** в настройки бота
3. **Найди** параметр "Runtime", "Language" или "Environment" в разделе конфигурации
4. **Измени** с **Node.js** на **Python** (или Python 3.11)
5. **Сохрани** и **перезагрузи** бота

### Вариант 2: Используй Custom Dockerfile

Если в dashboard доступна опция "Docker" или "Custom Dockerfile":

1. **Открой** настройки бота
2. **Выбери** режим "Docker" или "Custom Dockerfile"
3. Платформа должна использовать файл `Dockerfile` в корне репозитория
4. **Перезагрузи** бота

Файл `Dockerfile` уже присутствует в репозитории:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "bot.py"]
```

### Вариант 3: Контакт с поддержкой bothost.ru

Если ни один из вариантов не сработал:
- Свяжись с поддержкой bothost.ru
- Сообщи, что проект требует Python, а платформа силой используется Node.js
- Попроси помощи с принудительным переводом на Python runtime

## Технические детали

### Почему это происходит?

bothost.ru имеет встроенную систему автодетекции:
- Видит `.js` файлы → выбирает Node.js контейнер
- Видит `.py` файлы → выбирает Python контейнер (если нет JS)
- Если оба есть → приоритет обычно у Node.js

В этом проекте:
- **JavaScript**: `webapp/static/webapp.js` (фронтенд для Telegram Mini App)
- **Python**: `bot.py`, `requirements.txt` (основной бот)

Платформа видит оба и выбирает Node.js по умолчанию.

### Как работает текущее решение?

Добавлены файлы для совместимости с Node.js окружением:

1. **`package.json`** — говорит платформе "это может быть Node.js проект"
2. **`index.js`** — Node.js обёртка, которая:
   - Проверяет наличие Python3
   - Пытается установить его (apt-get или apk)
   - Запускает Python бот через `python3 bot.py`
   - Показывает ясные инструкции, если Python невозможно установить
3. **`runtime.txt`** — подсказка платформе о предпочитаемой версии Python

### Файлы проекта

После переименования:
- ✅ `webapp/static/webapp.js` (было `app.js`)
- ✅ `webapp/static/index.html` — обновлён скрипт
- ✅ `index.js` — Node.js обёртка
- ✅ `package.json` — конфигурация
- ✅ `runtime.txt` — подсказка версии
- ✅ `Dockerfile` — Python контейнер (если платформа его поддерживает)
- ✅ `.bothost_setup.md` — этот файл

## Разработка локально

Для локального запуска используй Python напрямую:

```bash
# Установи зависимости
pip install -r requirements.txt

# Запусти бота
python bot.py
```

Для запуска Node.js обёртки:

```bash
npm install  # если нужна пустая node_modules/
node index.js
```

## Если ничего не помогает

Если bothost.ru окончательно не переходит на Python:

1. Рассмотри использование других хостингов:
   - Heroku (было, но бесплатный уровень закрыт)
   - Railway
   - Render
   - PythonAnywhere
   - VPS с Docker

2. Или создай отдельное Node.js приложение, которое запускает Python через API/RPC

3. Или полностью переделай проект на Node.js (большая работа)
