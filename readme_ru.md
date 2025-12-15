## Установка Flask-скрипта для автоматического `git pull` через GitHub Webhook на Raspberry Pi с использованием ngrok (порт 5000)

Этот файл описывает, как развернуть скрипт `flask-pi.py` на Raspberry Pi, настроить GitHub Webhook и использовать ngrok как «мост» к локальному Flask-серверу на порту 5000.

---

### 1. Предварительные требования

- **Raspberry Pi** с установленной **Raspberry Pi OS / другой Linux-подобной системой**.
- Доступ по **SSH** или физический доступ к терминалу.
- Установленный **Git**.
- Установленный **Python 3** (обычно есть по умолчанию).
- Аккаунт GitHub и **репозиторий**, который нужно автоматически обновлять (`git pull`).
- Установленный **ngrok** или готовность его установить (см. раздел ниже).

---

### 2. Подготовка Git-репозитория на Raspberry Pi

1. Перейдите в директорию, где хотите держать ваш код:

```bash
cd /home/pi
```

2. Клонируйте репозиторий, который должен обновляться по `git pull`:

```bash
git clone https://github.com/USERNAME/REPO_NAME.git
```

3. Запомните путь к репозиторию (он нужен в `flask-pi.py`), например:

```bash
REPO_PATH="/home/pi/REPO_NAME"
```

4. Убедитесь, что всё работает:

```bash
cd "$REPO_PATH"
git status
```

---

### 3. Установка Python-зависимостей (Flask)

1. Обновите пакеты:

```bash
sudo apt update
```

2. Установите `pip` и Flask (если ещё не установлены):

```bash
sudo apt install -y python3-pip python3-venv
python3 -m venv venv
source venv/bin/activate
pip install flask
```

При желании можно использовать виртуальное окружение, но для простоты здесь всё ставится глобально.

---

### 4. Настройка скрипта `flask-pi.py`

1. Скопируйте файл `flask-pi.py` в отдельную директорию, например:

```bash
mkdir -p /home/pi/webhook-server
cp /Users/phenix/Downloads/111/flask-pi.py /home/pi/webhook-server/
cd /home/pi/webhook-server
```

> **Важно:** путь в команде `cp` подправьте под ваш реальный путь, если вы копируете не с macOS, а уже на самом Raspberry Pi.

2. Откройте файл `flask-pi.py` для редактирования:

```bash
nano flask-pi.py
```

3. Измените две важные переменные в начале файла:

- **`WEBHOOK_SECRET`** – секретный ключ, который вы зададите в настройках GitHub Webhook.
- **`REPO_PATH`** – путь к вашему клонированному репозиторию на Raspberry Pi.

Например:

```python
WEBHOOK_SECRET = "my_super_secret_token"
REPO_PATH = "/home/pi/REPO_NAME"
```

4. Сохраните изменения и выйдите из редактора (`Ctrl+O`, `Enter`, затем `Ctrl+X` в nano).

---

### 5. Тестовый запуск Flask-сервера (порт 5000)

1. В директории `webhook-server` выполните:

```bash
cd /home/pi/webhook-server
python3 flask-pi.py
```

2. В логах вы должны увидеть, что сервер запущен на `0.0.0.0:5000`.

3. Локальная проверка (опционально, если есть браузер или curl):

```bash
curl http://localhost:5000/
```

Ожидаемый ответ: `Webhook server is running!`.

Оставьте этот процесс пока запущенным (или позже настроите systemd/screen/tmux для автозапуска).

---

### 6. Установка и настройка ngrok (порт 5000)

#### 6.1. Установка ngrok на Raspberry Pi

1. Перейдите на сайт ngrok (на любом ПК) и зарегистрируйтесь:

- Откройте браузер и зайдите на сайт `https://ngrok.com`.
- Создайте аккаунт и скопируйте ваш **Auth Token**.

2. Скачайте ngrok на Raspberry Pi:

```bash
cd /home/pi
wget https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-arm.zip
unzip ngrok-stable-linux-arm.zip
sudo mv ngrok /usr/local/bin/
rm ngrok-stable-linux-arm.zip
```

> Если URL устарел — возьмите актуальный ARM-бинар с сайта ngrok и подставьте его в команду `wget`.

3. Подключите ваш Auth Token:

```bash
ngrok config add-authtoken YOUR_AUTH_TOKEN_HERE
```

---

#### 6.2. Запуск ngrok на порт 5000

1. Убедитесь, что Flask-сервер всё ещё слушает порт 5000 на Raspberry Pi.
2. В **новом терминале/сессии** на Raspberry Pi выполните:

```bash
ngrok http 5000
```

3. В выводе ngrok появится что-то вроде:

```text
Forwarding  https://abcd-1234-5678.eu.ngrok.io -> http://localhost:5000
```

4. Скопируйте **https-URL** (например, `https://abcd-1234-5678.eu.ngrok.io`) — он понадобится для GitHub Webhook.

> **Важно:** при каждом новом запуске ngrok URL меняется, если не использовать платный статический домен. После перезапуска ngrok не забудьте обновить URL в настройках Webhook на GitHub.

---

### 7. Настройка GitHub Webhook

1. Зайдите в ваш репозиторий на GitHub.
2. Откройте:

- **Settings** → **Webhooks** → **Add webhook**.

3. Заполните поля:

- **Payload URL**:  
  `https://ВАШ_NGROK_АДРЕС/webhook`  
  Например:  
  `https://abcd-1234-5678.eu.ngrok.io/webhook`

- **Content type**:  
  `application/json`

- **Secret**:  
  Тот же самый секрет, который вы записали в `WEBHOOK_SECRET` в `flask-pi.py` (например, `my_super_secret_token`).

- **Which events would you like to trigger this webhook?**  
  Выберите **"Just the push event"**.

4. Нажмите **Add webhook**.

5. GitHub отправит тестовый запрос `ping` / `push`. В логах Flask на Raspberry Pi вы увидите соответствующие сообщения. Если подпись или JSON неверные — смотрите вывод в консоли (скрипт их печатает).

---

### 8. Проверка работы: автоматический `git pull`

1. Внесите изменения в репозитории (на GitHub или локально с последующим `git push` в нужную ветку, как правило `main` или `master`).
2. Сделайте `git push` на GitHub.
3. На Raspberry Pi в терминале, где запущен `flask-pi.py`, вы должны увидеть:

- Лог о полученном событии `push`.
- Команду `git pull origin <branch>`.
- Результат выполнения `git pull`.

4. Проверьте, что локальный репозиторий действительно обновился:

```bash
cd /home/pi/REPO_NAME
git log -1
```

---

### 9. Автозапуск (опционально)

Чтобы не запускать Flask и ngrok вручную после каждого перезапуска Raspberry Pi, можно:

- Использовать **`tmux` или `screen`** и держать процессы в них.
- Создать **systemd-сервисы**:
  - один для `python3 /home/pi/webhook-server/flask-pi.py`
  - второй для `ngrok http 5000`

Это выходит за рамки базового мануала, но общая идея — оформить оба процесса как службы, стартующие при загрузке системы.

---

### 10. Краткое резюме

- **Flask-сервер** (`flask-pi.py`) слушает `0.0.0.0:5000` и обрабатывает `POST /webhook`.
- **ngrok** пробрасывает публичный `https`-адрес к `http://localhost:5000`.
- **GitHub Webhook** отправляет `push`-события на `https://ВАШ_NGROK_АДРЕС/webhook` с секретом.
- Скрипт проверяет подпись, анализирует `push` и делает `git pull` в заданной директории репозитория.


