# Анализ системы распределения заявок

## Логика распределения заявок

Система распределения заявок работает по следующему алгоритму:

1. **Проверка условий для распределения:**
   - Заявка не должна быть распределена максимальное количество раз (DEFAULT_MAX_DISTRIBUTIONS = 5)
   - С момента последнего распределения должно пройти достаточно времени (DEFAULT_DISTRIBUTION_INTERVAL = 3 часа)

2. **Поиск подходящих пользователей:**
   - Сначала система ищет пользователей, у которых есть и категория заявки, и город заявки
   - Если таких нет, ищет пользователей только с категорией заявки
   - Если и таких нет, ищет пользователей только с городом заявки
   - В крайнем случае, берет всех активных пользователей

3. **Выбор пользователей для распределения:**
   - Пользователи сортируются по количеству полученных заявок (в порядке возрастания)
   - Выбирается DEFAULT_USERS_PER_REQUEST (3) пользователей
   - Если не хватает основных пользователей, добавляются резервные (RESERVE_USERS_PER_REQUEST = 2)
   - Чередуется прямой и обратный порядок распределения

## Результаты тестирования

### Тест 1: Заявка с категорией "Ремонт квартир" (ID=1)
- Заявка была распределена 1 пользователю (ID=3)
- Пользователь имеет соответствующую категорию и город

### Тест 2: Заявка с категорией "Сантехника" (ID=2)
- Заявка была распределена 1 пользователю (ID=3)
- Пользователь имеет соответствующую категорию и город

### Тест 3: Заявка с категорией "Электрика" (ID=3), для которой нет пользователей
- Заявка была распределена 3 пользователям (ID=3, ID=4, ID=5)
- Ни у одного из пользователей нет категории "Электрика"
- Система выбрала пользователей по городу (все они из города с ID=1)

### Тест 4: Заявка без категории
- Заявка была распределена 3 пользователям (ID=3, ID=4, ID=5)
- Система выбрала пользователей по городу (все они из города с ID=1)

## Выводы

1. **Система корректно распределяет заявки** между пользователями в соответствии с их категориями и городами.

2. **Если нет точного совпадения**, система использует частичное совпадение (только категория или только город).

3. **В крайнем случае**, система распределяет заявки между всеми активными пользователями.

4. **Система учитывает нагрузку** на пользователей, отдавая приоритет тем, у кого меньше заявок.

5. **Система соблюдает ограничения** по максимальному количеству распределений и интервалу между распределениями.

## Рекомендации

1. Добавить логирование причин выбора пользователей для распределения.
2. Рассмотреть возможность настройки приоритетов для разных критериев выбора пользователей.
3. Добавить возможность ручного распределения заявок администратором.
4. Реализовать механизм уведомления администратора, если заявка не может быть распределена. 