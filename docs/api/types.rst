Типы и спецификации
===================

Числовые аннотации и спецификации импортируются из ``bytespec.types``;
``datetime`` и ``UUID`` — из стандартной библиотеки. Значения остаются
обычными Python-объектами. Практические примеры: :doc:`../types`.

.. _supported-types:

Поддерживаемые аннотации
------------------------

Таблица описывает автоматический выбор представления. Собственный тип
поддерживается через явный codec или ``configure_codecs()``.

.. list-table::
   :header-rows: 1
   :widths: 28 44 28

   * - Python-тип / аннотация
     - Представление
     - Настройки
   * - ``UInt8/16/32/64``, ``Int8/16/32/64``
     - Фиксированное целое, одноимённый ``…Codec``
     - Порядок байтов модели
   * - ``int``
     - ``VarIntCodec``: ZigZag + varint, диапазон Int64
     - Для другого формата выберите числовую аннотацию
   * - ``Float32``, ``Float64``
     - IEEE 754 binary32/binary64
     - Порядок байтов модели
   * - ``VarUInt``, ``VarInt``
     - Unsigned varint / ZigZag + varint, 1–10 байт
     - Независимы от порядка байтов
   * - ``bool``
     - ``BoolCodec``: один байт 0/1
     - Нет
   * - ``str``
     - ``StrCodec``: длина в байтах и текст
     - ``encoding``, ``prefix_length``
   * - ``bytes``
     - ``BytesCodec``: длина и байты
     - ``prefix_length``
   * - ``datetime.datetime``
     - ``DatetimeCodec``: строка ``isoformat()``
     - ``encoding``, ``prefix_length``
   * - ``uuid.UUID``
     - ``UUIDCodec``: ровно 16 байт ``UUID.bytes``
     - Без префикса, не зависит от порядка байтов
   * - Подкласс ``str`` и ``Enum``
     - ``EnumCodec`` + ``StrCodec``: строковое ``.value``
     - ``encoding``, ``prefix_length``
   * - ``IntEnum`` / подкласс ``int`` и ``Enum``
     - ``EnumCodec`` + ``VarIntCodec``: числовое ``.value``
     - Для другого представления — явный ``EnumCodec``
   * - ``list[T]``
     - ``ListCodec``: длина в байтах и элементы
     - Префикс списка; тип ``T`` настраивается отдельно
   * - Подкласс ``ProtoModel``
     - ``ModelCodec``: свой header без Constructor
     - Настройки вложенного класса
   * - ``T | None`` / ``Optional[T]``
     - Значение ``T`` при установленном бите присутствия
     - Обязательный ``field(flag=...)``
   * - ``Annotated[T, ...]``
     - Представление ``T`` с одной поддерживаемой спецификацией
     - Спецификации ниже

По умолчанию текст использует UTF-8, префиксы переменной длины занимают
4 байта. ``StrEnum`` подходит на версиях Python, где он доступен.
Обычный ``Enum`` без наследования от ``str`` или ``int`` требует явного codec.

Нет встроенного выбора для голых ``float``, ``list``, ``datetime.date``,
``datetime.time``, а также
``dict``, ``tuple``, ``set``, ``Any``, ``Literal`` и union нескольких
ненулевых типов. ``list[T | None]`` не поддерживается.

Целые
-----

.. autodata:: bytespec.types.UInt8
.. autodata:: bytespec.types.UInt16
.. autodata:: bytespec.types.UInt32
.. autodata:: bytespec.types.UInt64
.. autodata:: bytespec.types.Int8
.. autodata:: bytespec.types.Int16
.. autodata:: bytespec.types.Int32
.. autodata:: bytespec.types.Int64

Float и varint
--------------

.. autodata:: bytespec.types.Float32
.. autodata:: bytespec.types.Float64
.. autodata:: bytespec.types.VarUInt
.. autodata:: bytespec.types.VarInt

``VarUInt`` ограничен диапазоном ``0 .. 2**64 - 1``; ``VarInt`` —
``-2**63 .. 2**63 - 1``. Каноническое представление описано в
:doc:`../wire-format`. ``Float32`` может округлять значение; отдельного запрета
на ``NaN`` и бесконечности нет. ``BoolCodec.encode()`` использует истинность
значения, а decoder принимает строго байты 0/1.

Спецификации Annotated
----------------------

.. autoclass:: bytespec.types.IntegerSpec

   Фиксированное целое: ``bits`` равен 8, 16, 32 или 64, ``signed`` задаёт знак.

.. autoclass:: bytespec.types.FloatSpec

   Число IEEE 754: ``bits`` равен 32 или 64.

.. autoclass:: bytespec.types.VarIntSpec

   Varint; при ``signed=True`` сначала используется ZigZag.

.. autoclass:: bytespec.types.CodecSpec

   Настройки для переиспользования через ``Annotated``. ``codec`` принимает
   экземпляр ``ICodec``. Приоритет настроек: :doc:`../field-configuration`.

.. autodata:: bytespec.types.Spec

   Объединение четырёх поддерживаемых видов спецификаций.

.. _spec-priority:

Совместное использование настроек
---------------------------------

В одном ``Annotated`` допускается только одна распознаваемая спецификация;
посторонние metadata игнорируются. Числовые аннотации уже содержат spec:
например, ``UInt16`` — ``Annotated[int, IntegerSpec(16, signed=False)]``.
Добавлять к нему второй spec через внешний ``Annotated`` нельзя.

``CodecSpec`` перезаписывает ``prefix_length`` поля, если он не ``None``,
и ``encoding``, если она непустая; переданный в spec codec выбирается явно.
``field(codec=...)`` применяется раньше metadata и имеет приоритет.
Остальные параметры ``field()`` не перенастраивают готовый экземпляр codec.

Произвольный ``struct``-формат поля задавайте через свой codec,
см. :doc:`../codecs`. Замена codec полностью определяет результат decode:
аннотация логического типа не преобразует его автоматически обратно.

Вспомогательная аннотация
-------------------------

.. autodata:: bytespec.types.UIntUnion

   Union беззнаковых числовых аннотаций для типизации Python-кода.
   Сам по себе не является допустимой аннотацией сериализуемого поля:
   автоматический выбор между несколькими числовыми форматами не поддержан.
