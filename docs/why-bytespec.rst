Зачем bytespec?
===============

Устройство присылает пакет: четырёхбайтовый ``user_id`` и необязательное
UTF-8 имя с однобайтовой длиной. Перед полями — идентификатор сообщения,
флаги и длина тела сообщения. В приложении нужны ``packet.user_id`` и ``packet.name``,
а в сети — именно этот формат байтов.

Опишите его одной моделью для чтения и записи:

.. tab-set::

   .. tab-item:: Python

      .. testcode::

         from bytespec import Constructor, Flags, PayloadLength, ProtoModel, field
         from bytespec.types import UInt32

         class Packet(ProtoModel):
             __constructor__ = 0x1234
             __header__ = (Constructor(2), Flags(1), PayloadLength(2))

             user_id: UInt32
             name: str | None = field(flag=0, prefix_length=1)

         packet = Packet(user_id=42, name="Anna")
         wire = packet.encode()
         assert Packet.decode(wire) == packet
         print(wire.hex(" "))

   .. tab-item:: Байты

      .. testoutput::

         12 34 01 00 09 00 00 00 2a 04 41 6e 6e 61

   .. tab-item:: Разбор

      .. container:: wire-bytes

         .. dropdown:: ① Constructor · ``12 34``

            Идентификатор ``0x1234`` занимает два байта. Получатель сверяет его с моделью.

         .. dropdown:: ② Flags · ``01``

            Крайний правый бит равен 1: ``name`` присутствует. Для ``None`` здесь будет ``00``.

         .. dropdown:: ③ PayloadLength · ``00 09``

            После заголовка идут девять байт: четыре для ``user_id`` и пять для ``name``.

         .. dropdown:: ④ user_id · ``00 00 00 2a``

            Число 42. ``UInt32`` остаётся обычным ``int`` в Python, но всегда занимает четыре байта.

         .. dropdown:: ⑤ name · ``04 41 6e 6e 61``

            Длина 4 в одном байте, затем четыре байта UTF-8 текста ``Anna``.

В Python это обычные ``int`` и ``str``. В сообщении ``UInt32`` занимает
четыре байта, а ``prefix_length=1`` отводит один байт для длины строки.

.. container:: code-notes

   .. dropdown:: ① ``class Packet(ProtoModel)``

      Один класс задаёт чтение и запись. Имена полей доступны в Python;
      в сообщение записываются их значения.

   .. dropdown:: ② ``__header__``

      Три элемента задают заголовок слева направо. Числа в скобках — размеры
      в байтах. Здесь заголовок занимает 2 + 1 + 2 = 5 байт.

   .. dropdown:: ③ ``field(flag=0, prefix_length=1)``

      ``flag=0`` назначает имени крайний правый бит присутствия.
      ``prefix_length=1`` выделяет один байт для длины текста.
      ``name=None`` убирает имя из сообщения.

Сохранять формат, работать с моделями
-------------------------------------

bytespec подходит для существующего или собственного **последовательного
бинарного формата**, который хочется описать типизированными Python-моделями.
Вы выбираете размеры целых чисел, префиксы, порядок байтов и заголовок, а библиотека
сама находит границы полей, читает вложенные модели и отмечает присутствующие необязательные поля.
Собственный codec полностью заменяет запись и чтение конкретного поля.

Например, уберём имя — маску и длину вручную менять не нужно:

.. testcode::

   absent = Packet(user_id=42).encode()
   assert Packet.decode(absent).name is None
   print(absent.hex(" "))

.. testoutput::

   12 34 00 00 04 00 00 00 2a

Тело сообщения теперь содержит только ``user_id``. Такое управление последовательными
полями — ниша bytespec. Произвольные переходы по файлу и сложные битовые
структуры не входят в её встроенную модель. Подробные настройки собраны в
:doc:`headers`, :doc:`field-configuration` и :doc:`codecs`.

Как выбрать инструмент
----------------------

.. list-table::
   :header-rows: 1
   :widths: 18 82

   * - Инструмент
     - Когда брать
   * - bytespec
     - Нужны типизированные Python-модели поверх явно заданного
       последовательного бинарного формата
   * - msgspec
     - Нужен быстрый типизированный сериализатор для JSON, MessagePack, YAML или TOML
   * - Construct
     - Нужен гибкий DSL для разбора и построения бинарных данных, в том числе сложных структур
   * - protobuf
     - Вы выбираете протокол и нужна зрелая экосистема схем и компиляторов
       для обмена между разными языками
   * - struct
     - Формат состоит из нескольких фиксированных скалярных полей

У `msgspec <https://msgspec.dev/usage>`_ удобный типизированный API и высокая
производительность сериализаторов готовых форматов. Он не предназначен для
описания произвольного существующего бинарного формата.
`Protocol Buffers <https://protobuf.dev/overview/>`_ объединяет схемы,
компилятор и библиотеки разных языков, но использует собственный бинарный формат,
а не описывает расположение байтов чужого протокола.

`Construct <https://construct.readthedocs.io/en/latest/intro.html>`_
значительно мощнее bytespec как DSL для разбора и построения данных. Его отправная точка —
бинарная схема и логика разбора; у bytespec — типизированная Python-модель.
DSL полезен, когда формат требует условного расположения полей, указателей, переходов,
битовых структур или чтения с зависимостью от других частей файла.

Один формат: struct и Construct
-------------------------------

Посмотрим, как прочитать тот же ``wire`` другими средствами. Сравниваем
способ описания задачи; преимущества в скорости или размере здесь не заявлены.

Ручное чтение через struct
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. testcode::

   import struct

   def parse_packet(data):
       constructor, flags, size = struct.unpack_from(">HBH", data)
       offset = 5
       user_id, = struct.unpack_from(">I", data, offset)
       offset += 4
       name = None
       if flags & 1:
           length = data[offset]
           offset += 1
           name = data[offset:offset + length].decode("utf-8")
       return user_id, name

   assert parse_packet(wire) == (42, "Anna")
   assert parse_packet(absent) == (42, None)

Для нескольких фиксированных чисел ``struct`` вполне достаточно.
Здесь переменная строка добавила ручное отслеживание смещения, проверку флагов и чтение
префикса. Это учебный декодер для корректного пакета: рабочий вариант
потребует проверки границ буфера, constructor и длины тела сообщения, обработки ошибок
и отдельной логики записи.

Описание через Construct
~~~~~~~~~~~~~~~~~~~~~~~~

Для выполнения следующего блока нужен пакет ``construct``:

.. testcode::

   from construct import (
       Byte, Const, If, Int16ub, Int32ub, PascalString,
       Prefixed, Rebuild, Struct, this,
   )

   PacketSchema = Struct(
       "constructor" / Const(0x1234, Int16ub),
       "flags" / Rebuild(Byte, lambda ctx: int(ctx.body.name is not None)),
       "body" / Prefixed(Int16ub, Struct(
           "user_id" / Int32ub,
           "name" / If(this._.flags & 1, PascalString(Byte, "utf8")),
       )),
   )

   parsed = PacketSchema.parse(wire)
   assert (parsed.body.user_id, parsed.body.name) == (42, "Anna")
   assert PacketSchema.build(parsed) == wire
   assert PacketSchema.parse(absent).body.name is None
   assert PacketSchema.build(PacketSchema.parse(absent)) == absent

Construct описывает этот пакет и вычисляет длину через ``Prefixed``;
``If`` выражает условие через контекст. Разница с bytespec — в API и модели
работы: в нашей Python-модели логический тип и настройки бинарного представления стоят рядом:

.. literalinclude:: why-bytespec.rst
   :language: python
   :start-at:        user_id: UInt32
   :end-at:        name: str | None = field(flag=0, prefix_length=1)
   :dedent: 13

Вложенные данные можно описать другой моделью, а codec отдельного поля —
полностью заменить:
:doc:`collections` и :doc:`codecs`.

Когда bytespec не нужен
-----------------------

* Нужен типизированный сериализатор JSON/MessagePack — начните с msgspec.
* Контролируете обе стороны протокола и хотите зрелую экосистему схем
  для обмена между разными языками — рассмотрите protobuf.
* Нужен очень гибкий DSL для разбора бинарных данных со сложными условиями, указателями
  и битовыми полями — Construct зачастую правильнее.
* Формат состоит из нескольких фиксированных скалярных полей — ``struct``
  может быть проще.

Попробуйте на одном пакете
--------------------------

Одного известного бинарного пакета и его ожидаемого hex достаточно для
первой проверки. Опишите поля и заголовок, вызовите ``decode()``, затем
убедитесь, что ``encode()`` воспроизводит исходные байты:

.. testcode::

   known_packet = bytes.fromhex("12 34 01 00 09 00 00 00 2a 04 41 6e 6e 61")
   restored = Packet.decode(known_packet)
   assert restored.user_id == 42
   assert restored.name == "Anna"
   assert restored.encode() == known_packet

:doc:`getting-started` поможет объявить первую модель; :doc:`headers` —
согласовать служебные байты; :doc:`codecs` — полностью заменить codec поля,
если встроенное представление не подходит вашему формату.
