# Debugging log

Найденные и исправленные проблемы с причиной. Известные, но не исправленные риски — в Known
Issues сущностей.

## 2026-11-04 — llama-server не запускается после распаковки на macOS
Симптом: `dyld: Library not loaded … libllama-common.0.dylib (no such file)`.
Причина: в tar-архиве llama.cpp библиотеки подключены через symlink-и
(`libllama-common.0.dylib -> libllama-common.0.9.0.dylib`, 18 штук), а `extract` брал только
обычные файлы (`m.isfile()`). Ошибка была и в первой версии мастера, просто её не запускали.
Исправление: `_write_members` воссоздаёт symlink-и и проверяет, что цель не выходит за папку
(`local_ai_starter.py:790`), см. [network](entities/network.md).

## 2026-11-04 — HTTP 404 описывался как «ресурс заблокирован в сети»
Причина: все `HTTPError` шли в общий текст с советом про VPN.
Исправление: 404/410 — отдельное сообщение «закреплённой версии больше нет»
(`local_ai_starter.py:663`).
