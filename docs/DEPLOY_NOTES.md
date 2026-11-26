# Нотатки деплою

## Резерви оплати

Сервіс `payment-holds` кожні 5 хвилин запускає `python manage.py release_payment_holds`.

Логи:

```
docker compose logs payment-holds
```

Без онлайн-оплати команда безпечна: скасовує лише замовлення в статусі очікування оплати з простроченим `reserved_until`. Таких замовлень немає, тож нічого не скасовується.

## WebP і міграції

`convert_images_webp` на старті контейнера не запускається. Після деплою один раз:

```
docker compose exec backend python manage.py convert_images_webp
```

Щоб увімкнути конвертацію на кожному старті gunicorn, задайте `CONVERT_IMAGES_ON_START=1`.

Міграції виконує лише entrypoint backend (коли команда — `gunicorn`). Команда сервісу в compose їх не дублює. На сервері перевірте, що локальний override не задає `command` з `migrate`.
