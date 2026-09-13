Необязательные поля
===================

Email может быть неизвестен. Опишем это через ``str | None``:

.. testcode::

   from bytespec import ProtoModel, field

   class User(ProtoModel):
       name: str
       email: str | None = field(flag=0)

   user = User(name="Anna")
   decoded = User.decode(user.encode())
   print(decoded.email)  # None

.. testoutput::
   :hide:

   None

``str | None`` разрешает строку или отсутствие значения. Аргумент ``email``
теперь можно пропустить; без default он получит ``None``.
``Optional[str]`` из ``typing`` означает то же самое.

``flag=0`` назначает полю бит присутствия в сообщении. Библиотека сама
устанавливает его, когда значение передано, и сбрасывает для ``None``.
Читателю не нужно вычислять или передавать flags вручную.

Увидеть присутствие поля в байтах
----------------------------------

В коротком примере заголовок содержит только ``Flags(1)`` и
``PayloadLength(1)``: один байт флагов и один байт длины полей.
Так разницу между именем и ``None`` проще увидеть. Настройка такого
заголовка подробно разобрана в :doc:`headers`.

.. testcode:: presence

   from bytespec import Flags, PayloadLength, ProtoModel, field

   class Contact(ProtoModel):
       __header__ = (Flags(1), PayloadLength(1))
       name: str | None = field(flag=0, prefix_length=1)

.. tab-set::

   .. tab-item:: name="Anna"

      .. testcode:: presence

         present = Contact(name="Anna").encode()
         assert Contact.decode(present).name == "Anna"
         print(present.hex(" "))
         print(f"Flags: {present[0]:08b}")

      .. testoutput:: presence

         01 05 04 41 6e 6e 61
         Flags: 00000001

      Крайний правый бит равен **1**: имя присутствует.

      .. container:: wire-bytes

         .. dropdown:: ① Flags · ``01``

            ``flag=0`` — крайний правый бит. bytespec включил его, потому что имя задано.

         .. dropdown:: ② PayloadLength · ``05``

            Пять байт поля: один байт длины строки и четыре байта имени.

         .. dropdown:: ③ name · ``04 41 6e 6e 61``

            Четыре байта текста ``Anna`` с однобайтовой длиной перед ними.

   .. tab-item:: name=None

      .. testcode:: presence

         absent = Contact(name=None).encode()
         assert Contact.decode(absent).name is None
         print(absent.hex(" "))
         print(f"Flags: {absent[0]:08b}")

      .. testoutput:: presence

         00 00
         Flags: 00000000

      Крайний правый бит равен **0**: имени нет. Остались только два байта заголовка.

      .. container:: wire-bytes

         .. dropdown:: ① Flags · ``00``

            Все биты выключены. Поле ``name`` отсутствует.

         .. dropdown:: ② PayloadLength · ``00``

            После заголовка нет байтов полей. При чтении получится ``name=None``.

.. dropdown:: Что такое бит и почему ``flag=0``?

   Байт содержит восемь битов; каждый может быть 0 или 1. Их нумеруют справа
   налево, начиная с нуля. Полю с ``flag=0`` соответствует ``00000001``,
   полю с ``flag=1`` — ``00000010``, двум присутствующим полям — ``00000011``.
   Это :term:`битовая маска <bitmask>`. Вы выбираете номера; bytespec вычисляет число.

Передать значение
-----------------

.. testcode::

   user = User(name="Anna", email="anna@example.com")
   decoded = User.decode(user.encode())
   print(decoded.email)  # anna@example.com

.. testoutput::
   :hide:

   anna@example.com

При ``None`` байты поля вообще не записываются. Пустая строка, напротив,
остаётся присутствующим значением:

.. testcode::

   user = User(name="Anna", email="")
   decoded = User.decode(user.encode())
   print(repr(decoded.email))  # ''

.. testoutput::
   :hide:

   ''

Так же различаются ``None`` и числовой ноль или ``False``. Только ``None``
означает отсутствие.

Добавить ещё одно необязательное поле
-------------------------------------

Каждому полю нужен отдельный номер бита:

.. testcode::

   class User(ProtoModel):
       name: str
       email: str | None = field(flag=0)
       nickname: str | None = field(flag=1)

   user = User(name="Anna", nickname="ann")
   decoded = User.decode(user.encode())
   print(decoded.email, decoded.nickname)  # None ann

.. testoutput::
   :hide:

   None ann

``flag`` — номер бита, не битовая маска. По умолчанию доступны номера
от ``0`` до ``63``; повторять их нельзя. Optional без ``flag`` и обычное
поле с ``flag`` вызывают ``SchemaError`` при объявлении класса.
Размер bitmap задаётся элементом ``Flags`` в :doc:`headers`. Если меняете
header, оставляйте ``Flags`` для optional-полей: его отсутствие вызывает
``SchemaError`` при объявлении класса. Проверка учитывает и унаследованные поля.

Необязательное поле со значением по умолчанию
---------------------------------------------

``default`` по-прежнему действует только для пропущенного аргумента:

.. testcode::

   class Message(ProtoModel):
       note: str | None = field(flag=0, default="draft")

   print(Message().note)           # draft
   print(Message(note=None).note)  # None

   encoded = Message(note=None).encode()
   print(Message.decode(encoded).note)  # None

.. testoutput::
   :hide:

   draft
   None
   None

Явное ``None`` не заменяется на ``"draft"``. При чтении отсутствие поля
также даёт ``None``, независимо от default. Значения по умолчанию помогают
создавать экземпляры; они не восстанавливают недостающие байты сообщения.

Далее — :doc:`collections`: добавим пользователю список и вложим его
в другую модель.
