\# PITOOLS



\*\*DevOps-фреймворк для параллельного деплоя файлов и структур на несколько SSH-серверов через интерпретацию `.prj`-файлов.\*\*



Автор: Федор

Свидетельство о государственной регистрации программы для ЭВМ № 2026610793 от 15.01.2026



\---



\## Откуда название



`PITOOLS` — от `pit` (яма, шахта, углубление) + `tools` (инструменты).



Идея в том, что фреймворк работает на «нижнем» слое инфраструктуры — там, где обычно копают руками: раскладка файлов, структур, конфигов по серверам. Это не надстройка над оркестраторами, а \*\*прямой инструмент доставки\*\* — как кирка для деплоя.



`PITOOLS` не пытается быть Ansible, Kubernetes или Terraform. Он делает одну вещь — \*\*кладёт файлы туда, куда сказано\*\*, и делает это параллельно.



\---



\## Что умеет



\- \*\*Парсит `.prj`-файлы\*\* с командами `MLT`, `PRJ`, `FL`

\- \*\*Деплоит параллельно\*\* через SSH/SFTP (`asyncio.gather`)

\- \*\*Создаёт директории рекурсивно\*\* на удалённых серверах

\- \*\*Проверяет целостность\*\* деплоенных файлов по SHA256

\- \*\*Самопроверка\*\* — SHA256 самого `pitools.py` через `checksum.txt`



\---



\## Преимущества системы



\### 1. Плоский текст вместо YAML



`.prj` — это три команды: `MLT`, `PRJ`, `FL`. Никаких отступов, вложенности, якорей и шаблонов. Скрипт читается с первого взгляда, даже если писал его не ты.



\### 2. Параллельность из коробки



`asyncio.gather` разбрасывает задачи по всем хостам одновременно. Не нужно настраивать `forks`, `serial`, `strategy` — оно параллельно по умолчанию.



\### 3. Нет инвентори



Хосты задаются прямо в `.prj`, в строке `MLT`. Никаких отдельных файлов, групп, `host\\\\\\\_vars`, `group\\\\\\\_vars`. Всё в одном месте.



\### 4. Нет ролей и тасков



`PRJ` — целевая папка, `FL` — файл. Всё. Никаких `become`, `when`, `loop`, `register`, `handlers`. Если нужно сложное — разбиваешь на блоки.



\### 5. Понятная отладка



Каждая операция логируется: хост, файл, путь, checksum. Видно, что куда легло и совпало ли с оригиналом.



\### 6. Работает на голом SSH



Никаких агентов на целевых серверах. Только SSH-ключ и `paramiko` на машине, откуда запускаешь. Это значит — работает даже там, где нельзя ставить ничего лишнего.



\---



\## Почему не Podman



Podman — это \*\*контейнерный движок\*\*. PITOOLS — это \*\*деплой файлов\*\*. Они решают разные задачи, но пересекаются в одном: \*\*доставка содержимого на серверы\*\*.



| Критерий | Podman | PITOOLS |

|---|---|---|

| Что делает | Запускает контейнеры | Кладёт файлы по SSH |

| Нужен на хосте | Да, движок | Нет, только SSH |

| Работает без демона | Да (rootless) | Да (вообще без демона) |

| Параллельность | Через `podman play` | Через `asyncio.gather` |

| Формат описания | YAML / Quadlet | `.prj` (3 команды) |

| Порог входа | Движок, образы, сети | SSH + `paramiko` |



\*\*Podman хорош\*\* для запуска контейнеров, особенно rootless и без демона. Но если задача — \*\*разложить файлы и структуры по серверам\*\*, Podman для этого не предназначен. Он не умеет «вот эти файлы в эту папку на эти хосты» без сборки образа или `podman cp` по одному.



\*\*PITOOLS закрывает именно эту нишу.\*\* Podman — про то, \*\*что запускать\*\*. PITOOLS — про то, \*\*как доставить\*\*.



\---



\## Докубер: Docker + kubectl + поды



\*\*Докубер\*\* — это архитектурный паттерн, который PITOOLS обслуживает в примерах ниже:



\- \*\*Docker + Compose\*\* — базовая платформа (гибко, экосистема)

\- \*\*Голый `kubectl` в контейнере\*\* — пульт управления

\- \*\*Поды рядом\*\* — группы сервисов в одной сети, лёгкие

\- \*\*minikube, Helm, CNI, Podman — не нужны\*\*



Смысл: берём концепцию подов из Kubernetes, реализуем через Docker Compose, рулим через `kubectl`. Дёшево, легко, предсказуемо. PITOOLS в этой схеме — \*\*инструмент доставки\*\*: раскидывает Dockerfile, compose-файлы, базы, конфиги, лицензии по подам и VM.



\*\*Почему не Podman в Докубере:\*\* Docker даёт гибкость и экосистему, которой у Podman нет. Поды у Podman — это группы контейнеров с общим namespace, но не кубер-поды. В Докубере нам важна \*\*гибкость сборки\*\* (Compose, сети, volume, лимиты) и \*\*совместимость\*\* с kubectl и подами. Docker это даёт.



\---



\## Установка



```bash

pip install paramiko

```



Или через venv:



```bash

python3 -m venv venv

source venv/bin/activate

pip install -r requirements.txt

```



Требования: \*\*Python 3.8+\*\*, Linux, SSH-ключи.



\---



\## Формат `.prj`



```

MLT: server1.ru,server2.ru

PRJ: /var/www/myapp

FL: index.html

FL: config.py

```



\- `MLT:` — список хостов через запятую

\- `PRJ:` — целевая папка на серверах

\- `FL:` — файл для деплоя (относительно папки, где лежит `.prj`)



Файлы на удалённой стороне сохраняются с префиксом хоста: `server1\\\\\\\_index.html`, `server2\\\\\\\_index.html`.



\*\*Как различать хосты:\*\* новый `MLT:` закрывает предыдущий блок и начинает новый. Внутри блока все `PRJ` и `FL` применяются ко \*\*всем\*\* хостам из этого `MLT`.



\---



\## Запуск



```bash

python3 pitools.py pitools.prj --key \\\\\\\~/.ssh/id\\\\\\\_rsa

python3 pitools.py pitools.prj --key \\\\\\\~/.ssh/id\\\\\\\_rsa --user deploy

```



\---



\## Примеры `.prj`



\### Пример 1. Одинаковое на все серверы



```

\\\\# deploy-configs.prj

MLT: server-alpha,server-beta,server-gamma

PRJ: /etc/myapp

FL: app.conf

FL: db.conf

FL: logging.conf

```



→ `app.conf`, `db.conf`, `logging.conf` попадут на все три сервера.



\### Пример 2. Разное на разные серверы (Докубер)



```

\\\\# dokkuber-full.prj

\\\\# Раскладка Докубера на четыре VM: web, redis, ones, storage



\\\\# Web-под

MLT: dokkuber-web

PRJ: /home/user/dokkuber/ones-web

FL: Dockerfile

FL: compose.yml



\\\\# Redis-под

MLT: dokkuber-redis

PRJ: /home/user/dokkuber/data/redis

FL: redis.conf



\\\\# 1С-под

MLT: dokkuber-ones

PRJ: /home/user/dokkuber/data/1c/base

FL: karkasUNF.dt



\\\\# Хранилище конфигураций

MLT: dokkuber-storage

PRJ: /home/user/dokkuber/data/1c/configs

FL: config-storage.tar.gz



\\\\# Лицензии — на два хоста

MLT: dokkuber-ones,dokkuber-storage

PRJ: /home/user/dokkuber/licenses

FL: 1c-license.lic

```



\### Пример 3. Кластер 1С: 5 серверов, одна база



```

\\\\# ones-cluster-5.prj

MLT: ones-master,ones-worker-1,ones-worker-2,ones-worker-3,ones-worker-4

PRJ: /var/1c/bases/erp

FL: erp.dt

FL: erp-config.tar.gz

```



→ \*\*10 операций\*\* (5 хостов × 2 файла) — все параллельно.



\*\*В Ansible:\*\* инвентори + плейбук + роли ≈ 100 строк YAML.

\*\*В PITOOLS:\*\* 3 строки плоского текста.



\### Пример 4. Кластер + специфика (мастер vs воркеры)



```

\\\\# ones-cluster-mixed.prj



\\\\# ВСЕ — общие базы

MLT: ones-master,ones-worker-1,ones-worker-2,ones-worker-3,ones-worker-4

PRJ: /var/1c/bases/erp

FL: erp.dt



PRJ: /var/1c/bases/zup

FL: zup.dt



\\\\# ТОЛЬКО мастер — хранилище конфигураций

MLT: ones-master

PRJ: /var/1c/configs

FL: config-storage.tar.gz



\\\\# ТОЛЬКО мастер — лицензии

MLT: ones-master

PRJ: /var/1c/licenses

FL: 1c-license.lic



\\\\# ВСЕ воркеры — логи

MLT: ones-worker-1,ones-worker-2,ones-worker-3,ones-worker-4

PRJ: /var/1c/logs

FL: logcfg.xml

```



\### Пример 5. Полный Докубер на кластере



```

\\\\# dokkuber-cluster.prj

\\\\# 2 web, 3 redis, 5 ones, 1 storage



\\\\# Web-поды

MLT: dokkuber-web-1,dokkuber-web-2

PRJ: /home/user/dokkuber/ones-web

FL: Dockerfile

FL: compose.yml



\\\\# Redis-поды

MLT: dokkuber-redis-1,dokkuber-redis-2,dokkuber-redis-3

PRJ: /home/user/dokkuber/data/redis

FL: redis.conf



\\\\# 1С-поды

MLT: dokkuber-ones-1,dokkuber-ones-2,dokkuber-ones-3,dokkuber-ones-4,dokkuber-ones-5

PRJ: /home/user/dokkuber/data/1c/base

FL: karkasUNF.dt



\\\\# Хранилище конфигураций

MLT: dokkuber-storage

PRJ: /home/user/dokkuber/data/1c/configs

FL: config-storage.tar.gz



\\\\# Лицензии

MLT: dokkuber-ones-1,dokkuber-ones-2,dokkuber-ones-3,dokkuber-ones-4,dokkuber-ones-5

PRJ: /home/user/dokkuber/licenses

FL: 1c-license.lic

```



\*\*Итого: 18 операций — все параллельно.\*\*



\---



\## Скрипты для создания и запуска `.prj`



\### Создание `.prj` из шаблона



```bash

\\\\#!/usr/bin/env bash

\\\\# new-prj.sh — создать .prj по имени

\\\\# Использование: ./new-prj.sh myproject "host1,host2" /var/www/app



set -e



NAME="${1:?Укажи имя проекта}"

HOSTS="${2:?Укажи хосты через запятую}"

TARGET="${3:?Укажи целевую папку}"



cat > "${NAME}.prj" <<EOF

\\\\# ${NAME}.prj

\\\\# Создано: $(date +%Y-%m-%d)



MLT: ${HOSTS}

PRJ: ${TARGET}

\\\\# FL: file1

\\\\# FL: file2

EOF



echo "Создан ${NAME}.prj"

```



\### Запуск деплоя



```bash

\\\\#!/usr/bin/env bash

\\\\# deploy.sh — запуск PITOOLS с проверкой

\\\\# Использование: ./deploy.sh myproject.prj



set -e



PRJ="${1:?Укажи .prj файл}"

KEY="${SSH\\\\\\\_KEY:-$HOME/.ssh/id\\\\\\\_rsa}"

USER="${SSH\\\\\\\_USER:-deploy}"



if \\\\\\\[ ! -f "$PRJ" ]; then

\\\&#x20;   echo "Файл $PRJ не найден"

\\\&#x20;   exit 1

fi



if \\\\\\\[ ! -f "$KEY" ]; then

\\\&#x20;   echo "SSH ключ $KEY не найден"

\\\&#x20;   exit 1

fi



echo "Запуск PITOOLS: $PRJ"

echo "Пользователь: $USER"

echo "Ключ: $KEY"

echo "---"



python3 pitools.py "$PRJ" --key "$KEY" --user "$USER"

```



\### Генерация `checksum.txt`



```bash

\\\\#!/usr/bin/env bash

\\\\# gen-checksum.sh — обновить checksum для pitools.py



set -e



sha256sum pitools.py | awk '{print $1}' > checksum.txt

echo "checksum.txt обновлён:"

cat checksum.txt

```



\### Проверка целостности



```bash

\\\\#!/usr/bin/env bash

\\\\# verify.sh — проверить, что pitools.py не изменён



set -e



EXPECTED=$(cat checksum.txt)

ACTUAL=$(sha256sum pitools.py | awk '{print $1}')



if \\\\\\\[ "$EXPECTED" = "$ACTUAL" ]; then

\\\&#x20;   echo "OK: pitools.py не изменён"

else

\\\&#x20;   echo "ВНИМАНИЕ: pitools.py изменён"

\\\&#x20;   echo "  ожидалось: $EXPECTED"

\\\&#x20;   echo "  получено:  $ACTUAL"

\\\&#x20;   exit 1

fi

```



\---



\## Структура репозитория



```

pitools/

├── README.md

├── LICENSE

├── requirements.txt

├── pitools.py

├── checksum.txt

└── scripts/

\\\&#x20;   ├── new-prj.sh

\\\&#x20;   ├── deploy.sh

\\\&#x20;   ├── gen-checksum.sh

\\\&#x20;   └── verify.sh

```



\---



\## Почему не Ansible



Ansible — мощный, но тяжёлый. Для задачи «разложить 3 файла на 5 хостов» писать плейбук, поднимать инвентори и держать Python-окружение — оверкилл. PITOOLS решает это одним файлом и одной командой.



Ansible оправдан, когда есть роли, сложные условия, шаблоны, интеграции с облаками. PITOOLS оправдан, когда нужно \*\*быстро и параллельно положить файлы\*\* — без всего этого.



\---



\## Лицензия



Авторское право: Федор, 2025.

Свидетельство № 2026610793.



структура папок проекта

pitools/
├── README.md
├── LICENSE
├── requirements.txt
├── pitools.py
├── checksum.txt
└── scripts/
├── new-prj.sh
├── deploy.sh
├── gen-checksum.sh
└── verify.sh
🔧 Финальные шаги

1. Создай структуру:

bash
mkdir -p \~/pitools/scripts
cd \~/pitools

## Contact / Контакты

- Email: [feudor.lab@yandex.ru](mailto:feudor.lab@yandex.ru)
- Telegram: [@Feudorlab1](https://t.me/Feudorlab1)

