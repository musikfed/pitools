# PITOOLS

PITOOLS — ықшам `.prj` форматы арқылы бірнеше SSH серверіне файлдар мен каталогтарды параллель орналастыратын жеңіл DevOps-фреймворк. SSH/SFTP, asyncio және SHA-256 тексеруін қолданады, мақсатты хостта агент қажет емес.

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
