# PITOOLS

PITOOLS एक हल्का DevOps फ्रेमवर्क है जो कॉम्पैक्ट `.prj` फ़ॉर्मेट से कई SSH सर्वरों पर फ़ाइलें और निर्देशिकाएँ समानांतर रूप से तैनात करता है। यह SSH/SFTP, asyncio और SHA-256 सत्यापन का उपयोग करता है तथा लक्ष्य होस्ट पर एजेंट नहीं मांगता।

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
