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

Добавить ещё одно optional-поле
-------------------------------

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

Optional со значением по умолчанию
----------------------------------

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
