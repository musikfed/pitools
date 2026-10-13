# PITOOLS

PITOOLS — лёгкий DevOps-фреймворк для параллельного деплоя файлов и директорий на несколько SSH-серверов через компактный формат `.prj`. Использует SSH/SFTP, asyncio и проверку SHA-256 без агентов на целевых хостах.

## Architecture / Архитектура

```text
.prj file -> PITOOLS parser -> asyncio task fan-out -> SSH/SFTP targets -> remote files/directories -> SHA256 verification
```

## Project structure / Структура проекта

- `pitools.py` — parser, SSH/SFTP deployment and verification logic
- `.prj` files — deployment description
- `checksum.txt` — self-check hash
- README/docs — usage and format description

## Author / Автор

Федор / Fedor

## Contact / Контакты

- Email: feudor.lab@yandex.ru
- Telegram: @Feudorlab1
