# PITOOLS

PITOOLS는 간결한 `.prj` 형식을 사용해 여러 SSH 서버에 파일과 디렉터리를 병렬 배포하는 경량 DevOps 프레임워크입니다. SSH/SFTP, asyncio, SHA-256 검증을 사용하며 대상 호스트에 에이전트가 필요하지 않습니다.

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
