# PITOOLS

PITOOLS 是一个轻量 DevOps 框架，通过紧凑的 `.prj` 格式并行向多台 SSH 服务器部署文件和目录。它使用 SSH/SFTP、asyncio 和 SHA-256 校验，不需要在目标主机安装代理。

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
