# PITOOLS

PITOOLS нь `.prj` форматаар олон SSH сервер рүү файл, директорийг зэрэг байршуулдаг хөнгөн DevOps framework. SSH/SFTP, asyncio, SHA-256 шалгалт ашигладаг бөгөөд target host дээр agent суулгах шаардлагагүй.

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
