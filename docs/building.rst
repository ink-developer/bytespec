Сборка и проверка документации
==============================

Из корня checkout выполните:

.. code-block:: console

   uv sync --locked --group docs
   uv run --no-sync python -m sphinx -E -a -n -W --keep-going -b html -D language=ru docs docs/_build/html/ru
   uv run --no-sync python -m sphinx -E -a -n -W --keep-going -b html -D language=en docs docs/_build/html/en
   uv run --no-sync python -m sphinx -E -a -n -W --keep-going -b doctest -D language=ru docs docs/_build/doctest/ru
   uv run --no-sync python -m sphinx -E -a -n -W --keep-going -b doctest -D language=en docs docs/_build/doctest/en
   uv run --no-sync python -m sphinx -E -a -n -W --keep-going -b gettext docs docs/_build/gettext
   uv run --no-sync python docs/check.py

Русская версия находится в ``docs/_build/html/ru/index.html``, английская —
в ``docs/_build/html/en/index.html``. При HTML-сборке в каталог ``ru`` или ``en``
рядом автоматически создаётся общий ``index.html``. Публикуйте весь каталог
``docs/_build/html``: общий вход выбирает русский для основного языка браузера
``ru`` или ``ru-*``, английский — для остальных языков и при отсутствии настройки.
Прямые ссылки на ``ru/`` и ``en/`` не перенаправляются; переключатель языка
открывает ту же страницу соседней версии. Без JavaScript на общем входе
доступны ссылки на оба языка.
``-E -a`` заставляет
перечитать все исходники, ``-n`` проверяет ссылки на API, ``-W`` превращает
предупреждения в ошибки. ``--keep-going`` собирает все найденные проблемы
за один запуск. Для Python intersphinx нужен доступ к
``https://docs.python.org/3/objects.inv``; ошибка его загрузки тоже прерывает
строгую проверку.

Doctest исполняет примеры, проверяя assertions и точный вывод, включая hex.
``docs/check.py`` дополнительно проверяет файлы и anchors внутренних
HTML-ссылок, включая переходы между языками, наличие целей для публичных
exports в каждой версии, полноту перевода по свежим gettext-каталогам,
относительные README-ссылки и Python-пример README. Комментарии у ``print`` в README задают ожидаемый
вывод. Проверка локальных ссылок не обращается к внешним сайтам.

Как добавлять примеры
---------------------

Используйте ``testcode`` для обычного Python-кода и ``testoutput`` для
ожидаемого вывода. Несколько блоков на странице могут продолжать один пример;
независимым сценариям можно назначить отдельные группы. ``:hide:`` скрывает
ожидаемый вывод, но не отключает его проверку. Примеры без вывода проверяйте
через ``assert``. Вычисляйте hex исполнением примера, затем фиксируйте
ожидаемое значение в документации.

Construct нужен только для исполняемого сравнения на :doc:`why-bytespec`.
Он включён в группу ``docs`` и не является runtime-зависимостью bytespec.
Не заменяйте его пример непроверяемым псевдокодом.

Конфигурация использует Sphinx, Furo, autodoc и явный перечень публичных
точек входа. ``conf.py`` добавляет ``src`` в путь импорта; после установки
зависимостей команды можно запускать через ``.venv/bin/python``.
Версия берётся из metadata дистрибутива, а без установки — из
``pyproject.toml`` через ``tomllib`` (для этого fallback нужен Python 3.11+).
Требование самой библиотеки — Python 3.10+.

Как обновлять перевод
---------------------

Исходные ``.rst`` написаны на русском, docstrings библиотеки — на английском.
Английский перевод страниц хранится в ``docs/locale/en/LC_MESSAGES/*.po``
и подкаталоге ``api/``. Русский перевод docstrings для API находится в
``docs/locale/ru/LC_MESSAGES/api/*.po``. Sphinx применяет переводы при сборке;
docstrings в установленной библиотеке всегда остаются английскими.

После изменения исходников обновите каталоги:

.. code-block:: console

   uv run --no-sync python -m sphinx -E -a -n -W --keep-going -b gettext docs docs/_build/gettext
   uv run --no-sync sphinx-intl update -p docs/_build/gettext -d docs/locale -l en -l ru

Переведите новые ``msgstr`` и проверьте строки с пометкой ``fuzzy``;
после проверки уберите эту пометку. Не меняйте ``msgid``, имена API,
цели ссылок и wire-значения. При переводе кода сохраняйте согласованность
с ``testoutput``: скрытый ожидаемый вывод общий для обоих языков.
Затем повторите обе HTML- и doctest-сборки и ``docs/check.py``.
Sphinx сам компилирует ``.po`` в ``.mo``; сгенерированные ``.mo`` и ``_build``
не хранятся в репозитории. ``sphinx-intl`` нужен только для сопровождения
переводов и входит в группу ``docs``.
