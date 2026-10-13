# PITOOLS

PITOOLS — `.prj` форматы көмөтүнэн хас да SSH-серверга файллары уонна каталогтары параллельнай тарҕатар судургутук DevOps-фреймворк. SSH/SFTP, asyncio уонна SHA-256 тургутуутун туһанар, target host-ка agent наадата суох.

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
