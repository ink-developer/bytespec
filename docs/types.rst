Числа и другие типы
===================

У пользователя уже есть имя. Добавим идентификатор:

.. testcode::

   from bytespec import ProtoModel, field
   from bytespec.types import UInt32

   class User(ProtoModel):
       id: UInt32
       name: str
       active: bool = field(default=True)

   user = User(id=42, name="Anna")
   decoded = User.decode(user.encode())
   print(decoded.id)  # 42

.. testoutput::
   :hide:

   42

``UInt32`` означает целое без знака размером 32 бита — 4 байта.
Значение ``42`` остаётся обычным Python ``int``; аннотация выбирает способ
записи. Обычный ``int`` использует знаковый ``VarInt`` (ZigZag), а фиксированный
размер выбирается явно. Для ``float`` нужно указать ``Float32`` или ``Float64``.

.. tab-set::

   .. tab-item:: Python

      .. testcode:: uint32-bytes

         from bytespec import ProtoModel
         from bytespec.types import UInt32

         class Counter(ProtoModel):
             value: UInt32

         counter = Counter(value=42)
         assert Counter.decode(counter.encode()) == counter

   .. tab-item:: Байты

      Первые 14 байт — стандартный заголовок из :doc:`getting-started`.
      Здесь покажем только поле:

      .. testcode:: uint32-bytes

         print(counter.encode()[14:].hex(" "))

      .. testoutput:: uint32-bytes

         00 00 00 2a

   .. tab-item:: Разбор

      .. container:: wire-bytes

         .. dropdown:: ``value=42`` · ``00 00 00 2a``

            ``2a`` — шестнадцатеричная запись числа 42. ``UInt32`` всегда выделяет
            четыре байта; для такого маленького числа первые три равны нулю.
            В Python значение остаётся обычным ``int``.

Как выбрать целое число
-----------------------

.. list-table::
   :header-rows: 1
   :widths: 35 20 45

   * - Аннотация
     - Размер
     - Значения
   * - ``UInt8``, ``UInt16``, ``UInt32``, ``UInt64``
     - 1, 2, 4, 8 байт
     - От ``0`` до ``2**N - 1``, где ``N`` — число бит
   * - ``Int8``, ``Int16``, ``Int32``, ``Int64``
     - 1, 2, 4, 8 байт
     - От ``-2**(N-1)`` до ``2**(N-1) - 1``
   * - ``VarUInt``
     - 1–10 байт
     - Диапазон ``UInt64``; малые значения занимают меньше места
   * - ``VarInt``
     - 1–10 байт
     - Диапазон ``Int64``; поддерживает отрицательные значения

Например, ``UInt8`` подходит для чисел от 0 до 255. Значение вне диапазона
будет отклонено при ``encode()``, а не при создании экземпляра.
Все эти аннотации импортируются из ``bytespec.types``.

Малые числа переменной длины
----------------------------

``int`` и ``VarInt`` используют одинаковый формат; ``VarUInt`` подходит для
неотрицательных значений. Посмотрим на байты полей:

.. testcode::

   from bytespec.types import VarUInt

   class Counters(ProtoModel):
       delta: int
       total: VarUInt

   counters = Counters(delta=-2, total=300)
   assert Counters.decode(counters.encode()) == counters
   print(counters.encode()[14:].hex(" "))

.. testoutput::

   03 ac 02

``03`` — запись -2 через ``VarInt``, ``ac 02`` — запись 300 через ``VarUInt``.
:term:`varint` экономит место на небольших значениях.

.. dropdown:: Почему -2 записано как ``03``?

   ``VarInt`` сначала сопоставляет каждому знаковому числу неотрицательное:
   0 → 0, -1 → 1, 1 → 2, -2 → 3. Этот порядок называется ZigZag.
   Затем результат записывается как ``VarUInt``. Поэтому форматы ``VarInt``
   и ``VarUInt`` различаются даже для положительных значений.

Срез ``[14:]`` пропускает стандартный header, как в первой модели.
Все varints ограничены 64-битными диапазонами, даже для обычного Python ``int``.

Числа с дробной частью
----------------------

.. testcode::

   from bytespec.types import Float32

   class Point(ProtoModel):
       x: Float32
       y: Float32

   point = Point.decode(Point(x=1.25, y=3.5).encode())
   print(point.x, point.y)  # 1.25 3.5

.. testoutput::
   :hide:

   1.25 3.5

``Float32`` занимает 4 байта, ``Float64`` — 8. При записи в ``Float32``
Python ``float`` округляется до 32-битного представления, поэтому для
сравнения произвольных дробных значений используйте допуск.

Строки и байты
--------------

``str`` и ``bool`` уже знакомы из первой модели. Для бинарных данных
есть ``bytes``:

.. testcode::

   class Packet(ProtoModel):
       data: bytes

   packet = Packet.decode(Packet(data=b"ABC").encode())
   print(packet.data)  # b'ABC'

.. testoutput::
   :hide:

   b'ABC'

По умолчанию строки используют UTF-8. Длина строк и ``bytes`` записывается
автоматически; настраивать её для обычного использования не нужно.
Позже изменим эти параметры в :doc:`field-configuration`.

UUID и дата
-----------

Типы стандартной библиотеки можно использовать прямо в аннотациях:

.. testcode::

   from datetime import datetime, timezone
   from uuid import UUID

   class Message(ProtoModel):
       id: UUID
       created_at: datetime

   message = Message(
       id=UUID("12345678-1234-5678-1234-567812345678"),
       created_at=datetime(2026, 9, 7, 12, 0, tzinfo=timezone.utc),
   )
   decoded = Message.decode(message.encode())
   print(decoded.id)                      # 12345678-1234-5678-1234-567812345678
   print(decoded.created_at.isoformat())  # 2026-09-07T12:00:00+00:00

.. testoutput::
   :hide:

   12345678-1234-5678-1234-567812345678
   2026-09-07T12:00:00+00:00

UUID занимает ровно 16 байт. Дата записывается строкой ISO, сохраняя
представленное в ней смещение UTC. Имя часовой зоны не передаётся;
дата без ``tzinfo`` после чтения тоже остаётся без него.
Отдельные ``datetime.date`` и ``datetime.time`` не поддерживаются
автоматически: используйте свой codec, если формат требует именно их.
``DatetimeCodec`` восстанавливает ``datetime``, а не эти типы.

Набор именованных значений
--------------------------

Для статуса сообщения подходит строковый enum:

.. testcode::

   from enum import Enum

   class Status(str, Enum):
       READY = "ready"
       BUSY = "busy"

   class Message(ProtoModel):
       status: Status

   message = Message(status=Status.READY)
   decoded = Message.decode(message.encode())
   print(decoded.status.value)  # ready

.. testoutput::
   :hide:

   ready

Записывается строковое значение ``"ready"``, а при чтении восстанавливается
``Status.READY``. Неизвестное значение вызывает ``DecodeError``.
Числовой ``IntEnum`` тоже поддерживается автоматически:

.. testcode::

   from enum import IntEnum

   class Command(IntEnum):
       READ = 1
       WRITE = 2

   class Request(ProtoModel):
       command: Command

   request = Request(command=Command.WRITE)
   restored = Request.decode(request.encode())
   assert restored.command is Command.WRITE
   print(request.encode()[14:].hex(" "))

.. testoutput::

   04

По умолчанию числовое ``.value`` кодируется через **VarInt**, поэтому
значение 2 занимает байт ``04``, а не ``02``. При чтении восстанавливается
член enum. Для фиксированного unsigned byte используйте
``EnumCodec(Command, UInt8Codec())`` — :ref:`numeric-enum`.
Обычный ``Enum`` без наследования от ``str`` или ``int`` требует явного codec.

Мы разобрали отдельные значения. Далее — :doc:`optional-defaults`:
как выразить, что значения может не быть. Полная таблица поддерживаемых
аннотаций доступна в :ref:`supported-types`.
