Header и framing
================

Протокол может хранить длину перед flags или обходиться без идентификатора
сообщения. ``__header__`` задаёт служебную часть перед полями модели:

.. testcode::

   from bytespec import Constructor, Flags, PayloadLength, ProtoModel, field
   from bytespec.types import UInt8, VarUInt

   class Packet(ProtoModel):
       __constructor__ = 0x12
       __header__ = (Constructor(1), PayloadLength(1), Flags(1))

       number: UInt8
       note: str | None = field(flag=0, prefix_length=1)

   packet = Packet(number=7, note="A")
   encoded = packet.encode()
   assert Packet.decode(encoded) == packet
   print(encoded.hex(" "))

.. testoutput::

   12 03 01 07 01 41

Здесь ``12`` — constructor, ``03`` — длина **всех полей**, ``01`` — flags.
Body занимает три байта: ``07`` и строка ``01 41``. В длину не входит
ни один элемент header, даже если ``PayloadLength`` стоит перед ``Flags``.

Без настройки используется ``(Constructor(2), Flags(8), PayloadLength(4))``:
14 байт перед полями. По умолчанию ``__constructor__ = 1`` и
``__byte_order__ = ByteOrder.BIG``.

Что можно включить в header
---------------------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Элемент
     - Значение
   * - ``Constructor(encoding)``
     - Записывает ``__constructor__`` модели; при чтении сверяет его
   * - ``PayloadLength(encoding)``
     - Вычисляет число байтов body; при чтении ограничивает ими поля
   * - ``Flags(encoding)``
     - Вычисляет bitmap присутствующих optional-полей по ``field(flag=...)``

``encoding`` — ``1``, ``2``, ``4`` или ``8`` байт без знака, либо
аннотация ``VarUInt``. Например, ``Constructor(VarUInt)`` кодирует число 300
как ``ac 02``. ``VarInt``, ``UInt16`` и экземпляр codec вместо этих параметров
не поддерживаются. Фиксированные числа используют порядок байтов модели;
varint от него не зависит. Те же варианты доступны для всех трёх элементов.

.. testcode::

   class CompactPacket(ProtoModel):
       __constructor__ = 300
       __header__ = (Constructor(VarUInt), Flags(VarUInt), PayloadLength(VarUInt))
       number: UInt8
       note: str | None = field(flag=7, prefix_length=1)

   compact = CompactPacket(number=7, note="A")
   assert CompactPacket.decode(compact.encode()) == compact
   print(compact.encode().hex(" "))

.. testoutput::

   ac 02 80 01 03 07 01 41

Constructor 300 занимает два байта, bitmap с битом 7 — ещё два,
длина body 3 — один. Кодирование unsigned чисел здесь отличается от
``VarInt``, используемого по умолчанию для обычных ``int``-полей.

Constructor — числовой идентификатор формата, а не вызов Python-конструктора.
Библиотека проверяет его только после выбора класса приложением: реестра
моделей и автоматического dispatch нет.

Изменить порядок
----------------

Переставьте элементы tuple; поля body при этом сохраняют свой порядок:

.. testcode::

   class Reordered(ProtoModel):
       __constructor__ = 0x12
       __header__ = (Flags(1), Constructor(1), PayloadLength(VarUInt))

       number: UInt8
       note: str | None = field(flag=0, prefix_length=1)

   packet = Reordered(number=7, note="A")
   assert Reordered.decode(packet.encode()) == packet
   print(packet.encode().hex(" "))

.. testoutput::

   01 12 03 07 01 41

Header задаётся при объявлении класса. Менять его элементы и настройки
после создания схемы не следует. Правила переиспользования между классами:
:doc:`inheritance`.

Убрать ненужные элементы
------------------------

Если optional-полей нет, bitmap не нужен:

.. testcode::

   class Reading(ProtoModel):
       __header__ = (Constructor(1), PayloadLength(1))
       value: UInt8

   reading = Reading(value=7)
   assert Reading.decode(reading.encode()) == reading
   print(reading.encode().hex(" "))

.. testoutput::

   01 01 07

Можно аналогично убрать ``Constructor``: например,
``__header__ = (PayloadLength(2),)`` для обязательных полей, когда тип
сообщения уже определён транспортом.

Без PayloadLength
-----------------

Если граница сообщения определяется полями, общую длину можно не передавать:

.. testcode::

   class Reading(ProtoModel):
       __header__ = (Constructor(1),)
       value: UInt8

   buffer = b"xx" + Reading(value=7).encode() + Reading(value=8).encode()
   first, end = Reading.decode_from(buffer, 2)
   second, end = Reading.decode_from(buffer, end)
   print(first.value, second.value, end)

.. testoutput::

   7 8 6

``decode_from()`` возвращает конец последнего прочитанного поля. Он больше
не пропускает неизвестный хвост body и не знает отдельную границу сообщения:
codec видит весь переданный буфер, включая следующее сообщение. Для входа
с внешней границей передавайте только разрешённый срез. Проверки собственных
размеров полей остаются; ``decode()`` по-прежнему запрещает байты после
прочитанных полей. Prefix строки, bytes или списка не исчезает вместе с
``PayloadLength``.

Вообще без framing
------------------

Для записи структуры в уже существующий формат задайте пустой tuple:

.. testcode::

   from bytespec import ByteOrder
   from bytespec.types import UInt16

   class Point(ProtoModel):
       __header__ = ()
       __byte_order__ = ByteOrder.LITTLE
       x: UInt16
       y: UInt16

   point = Point(x=1, y=256)
   assert Point.decode(point.encode()) == point
   print(point.encode().hex(" "))

.. testoutput::

   01 00 00 01

Здесь ровно четыре байта полей. Модели без полей тоже поддерживаются:
например, сообщение-подтверждение может содержать только framing.

.. testcode::

   class Ack(ProtoModel):
       __constructor__ = 0x12
       __header__ = (Constructor(1), PayloadLength(1))

   class Empty(ProtoModel):
       __header__ = ()

   assert Ack.decode(Ack().encode()) == Ack()
   assert Empty.decode(b"") == Empty()
   print(Ack().encode().hex(" "))
   print(Empty().encode())

.. testoutput::

   12 00
   b''

``Ack`` записывает constructor и нулевую длину body. ``Empty`` без полей
и header записывает пустые bytes. Такой объект не подходит для элемента
списка: по нулю байтов нельзя восстановить количество элементов
(см. :ref:`codec-contract`).

.. _nested-headers:

Как записывается header вложенной модели
----------------------------------------

Вложенная модель использует свой порядок байтов и свой ``__header__``,
но её ``Constructor`` автоматически пропускается: тип уже известен из
аннотации поля. Остальные элементы остаются в указанном порядке:

.. testcode::

   from bytespec import ByteOrder, Constructor, Flags, PayloadLength
   from bytespec.types import UInt8, UInt16

   class Reading(ProtoModel):
       __constructor__ = 0x34
       __byte_order__ = ByteOrder.LITTLE
       __header__ = (PayloadLength(1), Constructor(1), Flags(1))
       value: UInt16

   class Frame(ProtoModel):
       __header__ = ()
       reading: Reading
       tail: UInt8

   reading = Reading(value=0x1234)
   frame = Frame(reading=reading, tail=9)
   assert Frame.decode(frame.encode()) == frame
   print(reading.encode().hex(" "))
   print(frame.encode().hex(" "))

.. testoutput::

   02 34 00 34 12
   02 00 34 12 09

Отдельная запись: длина ``02``, constructor ``34``, flags ``00``, value
``34 12``. Во вложенной записи отсутствует только constructor; ``09`` —
следующее поле внешней модели. Пустой header внешнего класса не убирает
framing вложенного. При стандартных настройках вложенный header занимает
12 байт: 8 байт flags и 4 байта длины.

Для ``list[Reading]`` действует то же правило:

.. testcode::

   class Batch(ProtoModel):
       __header__ = ()
       readings: list[Reading] = field(prefix_length=1)

   batch = Batch(readings=[reading])
   assert Batch.decode(batch.encode()) == batch
   print(batch.encode().hex(" "))

.. testoutput::

   04 02 00 34 12

``04`` — размер закодированного элемента вместе с оставшимся framing.
Вложенный ``__header__ = ()`` убирает и его; пример структурных полей
``ver/cmd/opcode/seq`` показан ниже. Собственные правила длины
вложенной модели сохраняются; без ``PayloadLength`` конец определяется
её известными полями.

Данные протокола остаются полями
--------------------------------

``ver``, ``cmd``, ``opcode`` и ``seq`` — значения приложения, а не вычисляемое
framing. Вынесите их в обычную вложенную модель:

.. testcode::

   class Header(ProtoModel):
       __header__ = ()
       ver: UInt8
       cmd: UInt8
       opcode: UInt16
       seq: UInt16

   class Envelope(ProtoModel):
       __header__ = (PayloadLength(2),)
       header: Header
       payload: bytes = field(prefix_length=1)

   packet = Envelope(header=Header(ver=1, cmd=2, opcode=18, seq=22), payload=b"OK")
   assert Envelope.decode(packet.encode()) == packet
   print(packet.encode().hex(" "))

.. testoutput::

   00 09 01 02 00 12 00 16 02 4f 4b

``00 09`` — длина body; дальше шесть байтов ``Header``, затем
``02 4f 4b`` — bytes с собственным префиксом. Объект ``packet.header``
содержит данные приложения; ``Envelope.__header__`` описывает framing.
Вложенная модель сохраняет свой header **без Constructor**:
точный пример — :ref:`nested-headers`.

.. _header-validation:

Что проверяется в 0.1.0
-----------------------

При создании элемента проверяется поддерживаемое ``encoding``. При сборке
модели ``Constructor`` требует обычный ``int`` (не ``bool``), а ``Flags``
проверяет вместимость bitmap. Например, бит 8 не помещается в один байт:

.. testcode::

   from bytespec import SchemaError

   try:
       class TooManyFlags(ProtoModel):
           __header__ = (Flags(1),)
           note: str | None = field(flag=8)
   except SchemaError as error:
       print(error)

.. testoutput::

   Flags encoding provides 8 bits, model has field with flag 8

Номера flags всегда ограничены 0–63, в том числе для ``Flags(VarUInt)``.
Диапазон самого constructor проверяется при **encode**, с ``EncodeError``;
неверный constructor в сообщении даёт ``DecodeError``.

Для optional-полей требуется ``Flags`` в итоговом header. Это проверяется
при объявлении класса, в том числе для унаследованных полей:

.. testcode::

   try:
       class MissingFlags(ProtoModel):
           __header__ = (PayloadLength(1),)
           note: str | None = field(flag=0)
   except SchemaError as error:
       print(error)

   class WithFlags(ProtoModel):
       __header__ = (Flags(1), PayloadLength(1))
       note: str | None = field(flag=0)

   try:
       class WithoutFlags(WithFlags):
           __header__ = (PayloadLength(1),)
   except SchemaError as error:
       print(error)

.. testoutput::

   Found optional fields in model but no Flags presented in header
   Found optional fields in model but no Flags presented in header

Задавайте каждый вид элемента не более одного раза: уникальность видов
элементов header отдельно не проверяется. Изменённый header подкласса
проверяется заново, даже если подкласс не объявляет собственных полей.

Далее — :doc:`codecs`: как задать представление отдельного значения.
