Зачем bytespec?
===============

Устройство присылает пакет: четырёхбайтовый ``user_id`` и необязательное
UTF-8 имя с однобайтовой длиной. Перед полями — идентификатор сообщения,
flags и длина body. В приложении нужны ``packet.user_id`` и ``packet.name``,
а в сети — именно этот формат байтов.

Опишите его одной моделью для чтения и записи:

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

.. testoutput::

   12 34 01 00 09 00 00 00 2a 04 41 6e 6e 61

.. code-block:: text

   12 34       | 01    | 00 09          | 00 00 00 2a | 04 41 6e 6e 61
   constructor | flags | payload length | user_id     | string length + UTF-8

Библиотека сама выставила бит имени и вычислила длину body: 9 байт.
``UInt32`` задал размер числа; ``prefix_length=1`` — ширину длины строки.
В Python значения остались обычными ``int`` и ``str``.

Сохранять формат, работать с моделями
-------------------------------------

bytespec подходит для существующего или собственного **последовательного
бинарного формата**, который хочется описать типизированными Python-моделями.
Вы выбираете размеры integer, prefixes, byte order и framing, а библиотека
перемещает offsets, читает вложенные модели и обрабатывает optional flags.
Custom codec полностью заменяет encode/decode конкретного поля.

Например, уберём имя — маску и длину вручную менять не нужно:

.. testcode::

   absent = Packet(user_id=42).encode()
   assert Packet.decode(absent).name is None
   print(absent.hex(" "))

.. testoutput::

   12 34 00 00 04 00 00 00 2a

Body теперь содержит только ``user_id``. Такое управление последовательными
полями — ниша bytespec. Произвольные переходы по файлу и сложные битовые
layout не входят в её встроенную модель. Подробные настройки собраны в
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
     - Нужен быстрый typed serializer для JSON, MessagePack, YAML или TOML
   * - Construct
     - Нужен гибкий binary parser/builder DSL, в том числе для сложных layout
   * - protobuf
     - Вы выбираете протокол и нужна зрелая schema/compiler-экосистема
       для обмена между разными языками
   * - struct
     - Формат состоит из нескольких фиксированных scalar-полей

У `msgspec <https://msgspec.dev/usage>`_ удобный typed API и высокая
производительность serializers готовых форматов. Он не предназначен для
описания произвольного существующего binary layout.
`Protocol Buffers <https://protobuf.dev/overview/>`_ объединяет схемы,
compiler и runtimes разных языков, но использует собственный wire format,
а не описывает расположение байтов чужого протокола.

`Construct <https://construct.readthedocs.io/en/latest/intro.html>`_
значительно мощнее bytespec как parser/builder DSL. Его отправная точка —
бинарная схема и логика parsing; у bytespec — типизированная Python-модель.
DSL полезен, когда формат требует conditional layouts, pointers, jumps,
bit-level структур или чтения с зависимостью от других частей файла.

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
Здесь переменная строка добавила ручной offset, проверку flags и чтение
префикса. Это учебный decoder для корректного пакета: production parser
потребует bounds checks, проверки constructor и длины body, обработки ошибок
и отдельной логики encode.

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
работы: в нашей Python-модели логический тип и wire-настройки стоят рядом:

.. literalinclude:: why-bytespec.rst
   :language: python
   :start-at:        user_id: UInt32
   :end-at:        name: str | None = field(flag=0, prefix_length=1)
   :dedent: 7

Вложенные данные можно описать другой моделью, а codec отдельного поля —
полностью заменить:
:doc:`collections` и :doc:`codecs`.

Когда bytespec не нужен
-----------------------

* Нужен JSON/MessagePack typed serializer — начните с msgspec.
* Контролируете обе стороны протокола и хотите зрелую cross-language
  schema-экосистему — рассмотрите protobuf.
* Нужен очень гибкий binary parser DSL со сложными условиями, указателями
  и битовыми полями — Construct зачастую правильнее.
* Формат состоит из нескольких фиксированных scalar-полей — ``struct``
  может быть проще.

Попробуйте на одном пакете
--------------------------

Одного известного бинарного пакета и его ожидаемого hex достаточно для
первой проверки. Опишите поля и framing, вызовите ``decode()``, затем
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
