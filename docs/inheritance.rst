Наследование моделей
====================

Чтобы несколько сообщений использовали одинаковое framing, вынесите
настройки в базовый класс, а поля объявите в конкретных моделях:

.. testcode::

   from bytespec import Constructor, Flags, PayloadLength, ProtoModel, SchemaError
   from bytespec.types import UInt8

   class Compact(ProtoModel):
       __header__ = (Constructor(1), PayloadLength(1))

   class Reading(Compact):
       __constructor__ = 7
       value: UInt8

   reading = Reading(value=42)
   assert Reading.decode(reading.encode()) == reading
   print(reading.encode().hex(" "))

.. testoutput::

   07 01 2a

Наследуются ``__header__``, ``__constructor__``, ``__byte_order__`` и правила
``configure_codecs()``. Framing-настройки можно переопределить и в подклассе
без собственных полей: каждый подкласс получает заново собранную схему.

Несколько базовых классов
-------------------------

При отсутствии явного ``__header__`` учитываются custom headers прямых баз
``ProtoModel``. Стандартный header не конкурирует с пользовательским:

.. testcode::

   class DefaultBase(ProtoModel):
       pass

   class Mixed(DefaultBase, Compact):
       value: UInt8

   assert Mixed.__header__ is Compact.__header__
   assert Mixed.decode(Mixed(value=1).encode()) == Mixed(value=1)

Diamond inheritance одного header тоже допустим:

.. testcode::

   class Left(Compact):
       pass

   class Right(Compact):
       pass

   class Diamond(Left, Right):
       value: UInt8

   assert Diamond.__header__ is Compact.__header__
   assert Diamond.decode(Diamond(value=2).encode()) == Diamond(value=2)

Два разных custom headers требуют явного выбора:

.. testcode::

   class Other(ProtoModel):
       __header__ = (PayloadLength(2),)

   try:
       class Conflict(Compact, Other):
           value: UInt8
   except SchemaError as error:
       print(error)

   class Resolved(Compact, Other):
       __header__ = Compact.__header__
       value: UInt8

   assert Resolved.decode(Resolved(value=3).encode()) == Resolved(value=3)

.. testoutput::

   Conflict: conflicting inherited headers; define __header__ explicitly

Сравнивается **идентичность tuple**, а не эквивалентность элементов.
Два независимо созданных ``(Constructor(1), PayloadLength(1))`` конфликтуют
даже при одинаковом wire format. Чтобы переиспользовать один header,
наследуйте его или присвойте существующий tuple. Пустой tuple ``()`` тоже
считается custom header. Специальное объединение применяется только к
header; остальные настройки следуют обычному порядку поиска Python.

Поля не объединяются
--------------------

Подкласс с собственными полями строит схему **только из них**:

.. testcode::

   class Parent(ProtoModel):
       __header__ = ()
       first: UInt8

   class Child(Parent):
       second: UInt8

   child = Child(second=2)
   print(child.encode().hex(" "))

.. testoutput::

   02

``first`` в схему ``Child`` не попадает. Для структуры «родительские данные
плюс новые данные» используйте :doc:`collections` или явно объявите весь
набор полей дочерней модели.

Изменить framing, сохранив поля
-------------------------------

Подкласс без собственных сериализуемых полей сохраняет унаследованные поля,
их codecs, defaults и factories. Для него создаётся отдельная схема с его
``__constructor__``, ``__header__`` и ``__byte_order__``. Повторять поля
ради смены framing не нужно:

.. testcode::

   from bytespec import ByteOrder
   from bytespec.types import UInt16

   class ReadingBase(ProtoModel):
       __constructor__ = 2
       __header__ = (Constructor(1), PayloadLength(1))
       value: UInt16

   class LittleReading(ReadingBase):
       __constructor__ = 3
       __header__ = (PayloadLength(1), Constructor(2))
       __byte_order__ = ByteOrder.LITTLE

   reading = LittleReading(value=0x1234)
   assert LittleReading.decode(reading.encode()) == reading
   print(reading.encode().hex(" "))
   print(ReadingBase(value=0x1234).encode().hex(" "))

.. testoutput::

   02 03 00 34 12
   02 02 12 34

В первой строке длина идёт перед двухбайтовым constructor, а число записано
little-endian. Формат родителя не изменился. Если в унаследованных полях есть
optional, новый header тоже должен содержать ``Flags`` достаточной ширины:
иначе объявление подкласса завершается ``SchemaError``.

При multiple inheritance без собственных полей используется первый
доступный набор полей по MRO, без объединения схем базовых классов.
Правило выбора custom header при этом остаётся описанным выше.

Автоматический вызов ``__validate__`` имеет отдельное правило: метод
родителя сам не вызывается для дочернего экземпляра. Как явно переиспользовать
проверку — :doc:`validation`.
