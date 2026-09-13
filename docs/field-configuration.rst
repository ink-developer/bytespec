Строки, длины и настройки полей
===============================

До сих пор мы использовали формат по умолчанию. Теперь рассмотрим случаи,
когда для поля нужны другие настройки.

Выбрать кодировку
-----------------

Например, сообщение должно содержать только ASCII-текст:

.. testcode::

   from bytespec import ProtoModel, field

   class Message(ProtoModel):
       text: str = field(encoding="ascii")

   message = Message(text="Hello!")
   print(Message.decode(message.encode()).text)  # Hello!

.. testoutput::
   :hide:

   Hello!

Без ``encoding`` используется UTF-8. В ASCII нельзя записать кириллицу —
``encode()`` выдаст ``EncodeError``. Неизвестное имя кодировки вызывает
``SchemaError``. Те же настройки применяются к строковым enum и ``datetime``.

Изменить префикс длины
----------------------

Перед строкой библиотека записывает её длину в байтах. Это число называется
*префиксом длины* и по умолчанию занимает 4 байта. Для короткого текста
можно выбрать более узкий префикс:

.. testcode::

   class Message(ProtoModel):
       text: str = field(prefix_length=1)

   message = Message(text="Hello!")
   print(Message.decode(message.encode()).text)  # Hello!

.. testoutput::
   :hide:

   Hello!

``prefix_length=1`` отводит один байт **для длины**, не для самого текста.
Теперь поле вмещает до 255 закодированных байтов. Для UTF-8 это не всегда
255 символов: например, ``"я"`` занимает 2 байта.

.. list-table::
   :header-rows: 1
   :widths: 25 30 45

   * - ``prefix_length``
     - Размер префикса
     - Максимальная длина данных
   * - ``1``
     - 1 байт
     - 255 байт
   * - ``2``
     - 2 байта
     - 65 535 байт
   * - ``4`` (по умолчанию)
     - 4 байта
     - ``2**32 - 1`` байт
   * - ``8``
     - 8 байт
     - ``2**64 - 1`` байт
   * - ``VarUInt``
     - 1–10 байт
     - ``2**64 - 1`` байт

Это предел префикса поля. Размер содержимого всей модели имеет отдельный
предел, заданный ``PayloadLength`` в :doc:`headers` (по умолчанию
``2**32 - 1`` байт). Сам префикс в записанное им число не входит.

Для ``bytes`` действуют те же правила. Вот префикс переменной длины:

.. testcode::

   from bytespec.types import VarUInt

   class Packet(ProtoModel):
       data: bytes = field(prefix_length=VarUInt)

   packet = Packet(data=b"ABC")
   print(Packet.decode(packet.encode()).data)  # b'ABC'

.. testoutput::
   :hide:

   b'ABC'

Передаётся именно ``VarUInt``. ``VarInt`` как префикс не поддерживается.
``prefix_length=None`` в ``field()`` оставляет значение по умолчанию,
а не отключает префикс. Для фиксированного количества байтов без префикса
есть готовое решение — :ref:`fixed-bytes`.

Переиспользовать настройку
--------------------------

Когда несколько полей имеют одинаковый формат, его удобно назвать.
``Annotated`` связывает Python-тип с настройками ``bytespec``:

.. testcode::

   from typing import Annotated
   from bytespec.types import CodecSpec

   ShortText = Annotated[str, CodecSpec(prefix_length=1, encoding="ascii")]

   class User(ProtoModel):
       name: ShortText
       city: ShortText

   user = User(name="Anna", city="Oslo")
   print(User.decode(user.encode()).city)  # Oslo

.. testoutput::
   :hide:

   Oslo

``ShortText`` остаётся строкой для Python-кода, но каждое такое поле
записывается в ASCII с однобайтовой длиной. ``CodecSpec`` объединяет
настройки, которые до этого мы передавали в ``field()``.

Настроить элементы списка
-------------------------

Теперь можно использовать ``ShortText`` внутри списка:

.. testcode::

   class Message(ProtoModel):
       tags: list[ShortText] = field(prefix_length=2)

   message = Message(tags=["red", "blue"])
   print(Message.decode(message.encode()).tags)  # ['red', 'blue']

.. testoutput::
   :hide:

   ['red', 'blue']

Здесь длина всего списка записывается в 2 байта, длина каждой строки —
в 1 байт. Длина списка означает общий размер закодированных элементов
**в байтах**, не их количество.

``field()`` списка настраивает только сам список. Поэтому
``list[str] = field(prefix_length=2, encoding="ascii")`` оставил бы элементы
в UTF-8 с четырёхбайтовыми длинами. Настройки элементов задаются через их тип,
как в примере выше.

Для чисел и UUID ``prefix_length`` ничего не меняет. Вложенные модели тоже
сохраняют собственные настройки. Если совместить ``field()`` и ``CodecSpec``
на одном поле, применяются :ref:`spec-priority`.

Далее — :doc:`examples`: соберём знакомые возможности в одно сообщение.
