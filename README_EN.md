## 🌐 PITOOLS · Интерактивная схема параллельного деплоя / Live source-based flow

**[Открыть сайт PITOOLS — SSH/SFTP и SHA-256: визуализация по исходникам](https://musikfed.github.io/view_my_prj/pitools/)**

[Общая инженерная галерея](https://musikfed.github.io/view_my_prj/) · [Разбор реального выполнения и ограничений](docs/WEB-DEMO-RU.md)

Веб-сайт — безопасная иллюстрация программы: без настоящих SSH-подключений и без изменения скрипта. Ограничения проверки целостности открыто указаны на сайте.

---

# PITOOLS

PITOOLS is a lightweight DevOps framework for parallel file and directory deployment to multiple SSH servers using a compact `.prj` format. It uses SSH/SFTP, asyncio concurrency and SHA-256 verification without requiring agents on target hosts.

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
