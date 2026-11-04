# Network

Source: [`local_ai_starter.py`](../../../local_ai_starter.py)

## Purpose
Надёжные загрузки на плохих и ограниченных сетях: заранее понятное сообщение, если ресурс
недоступен, докачка вместо перезапуска, проверка целостности.

## Key API
- `check_network(urls)` — `local_ai_starter.py:677`. До начала загрузок запрашивает
  `Range: bytes=0-0` у каждого URL с таймаутом `NET_CHECK_TIMEOUT` = 15 с. Так проверяются и
  редиректы на CDN (GitHub → release-assets, Hugging Face → xethub/CDN).
- `network_error(url, error, sec)` — `local_ai_starter.py:663` и `_net_reason` — `:647`.
  Причина по типу исключения: таймаут, DNS (`gaierror`), отказ/сброс, SSL (вероятен перехват
  прокси), HTTP-код. 404/410 — отдельное сообщение «закреплённой версии больше нет», а не
  «сеть заблокирована». К сетевым причинам добавляется совет: другая сеть, VPN, `HTTPS_PROXY`.
- `download(url, target, sha256, name)` — `local_ai_starter.py:713`. Пишет в `<target>.part`,
  докачивает через `Range`. Если сервер ответил 200 вместо 206, начинает заново; 416 значит
  «уже скачано». `STALL_TIMEOUT` = 30 с на чтение, до `DOWNLOAD_ATTEMPTS` = 5 повторов подряд
  (счётчик сбрасывается, как только пошли байты). SHA-256 проверяется до переименования.
- `_progress` — `local_ai_starter.py:693`: полоса, %, объём, скорость, оставшееся время;
  перерисовка не чаще раза в 0,3 с.
- `extract` / `_write_members` — `local_ai_starter.py:771`, `:790`. Снимают общую верхнюю
  папку, отклоняют пути и цели symlink-ов за пределами папки, воссоздают symlink-и из tar.

## Collaborators
- [llama-engine](llama-engine.md), [opencode-integration](opencode-integration.md),
  [profiles](profiles.md) — что качается.
- [wizard-flow](wizard-flow.md) — вызывает `check_network` перед шагами.
- Прокси: `urllib` сам учитывает `HTTPS_PROXY`/`HTTP_PROXY`.

## Known Issues
- Если заблокирован только CDN после редиректа, `URLError` не всегда содержит его имя:
  в сообщении может стоять исходный хост.
- Проверка SHA-256 модели на 5 ГБ занимает 10–20 с без прогресса (только «Проверяю файл…»).

## Related Pages
[debugging_log](../debugging_log.md), [test](../workflows/test.md)
