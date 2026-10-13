# PITOOLS

PITOOLS — лёгкі DevOps-фрэймворк для паралельнага разгортвання файлаў і каталогаў на некалькі SSH-сервераў праз кампактны фармат `.prj`. Выкарыстоўвае SSH/SFTP, asyncio і праверку SHA-256 без агентаў на мэтавых хостах.

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
