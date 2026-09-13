Списки и вложенные модели
=========================

Несколько значений одного типа
------------------------------

Пользователь может состоять в нескольких группах:

.. testcode::

   from bytespec import ProtoModel, field

   class User(ProtoModel):
       name: str
       groups: list[str]

   user = User(name="Anna", groups=["readers", "editors"])
   decoded = User.decode(user.encode())
   print(decoded.groups)  # ['readers', 'editors']

.. testoutput::
   :hide:

   ['readers', 'editors']

``list[str]`` означает список строк. Так же работают ``list[UInt32]``
и списки других поддерживаемых типов. Список может быть пустым.

Отдельный пустой список для каждого пользователя
------------------------------------------------

Чтобы не передавать ``groups=[]`` вручную, используйте ``default_factory``:

.. testcode::

   class User(ProtoModel):
       name: str
       groups: list[str] = field(default_factory=list)

   anna = User(name="Anna")
   boris = User(name="Boris")
   anna.groups.append("editors")

   print(anna.groups)   # ['editors']
   print(boris.groups)  # []

.. testoutput::
   :hide:

   ['editors']
   []

Фабрика ``list`` вызывается без аргументов при создании каждого экземпляра,
если поле не передали. Так пользователи получают разные списки.
``default=[]`` вместо этого использовал бы один общий объект.

Фабрикой может быть и другая функция без аргументов: например, ``uuid4``
для поля типа ``UUID``. Она не вызывается при объявлении класса.
Задавайте либо ``default``, либо ``default_factory`` — одновременно нельзя.
Правила проверки их значений собраны в :ref:`default-rules`.

Модель как поле другой модели
-----------------------------

Используем уже объявленный ``User`` как автора сообщения:

.. testcode::

   class Message(ProtoModel):
       author: User
       text: str

   message = Message(author=anna, text="Hello!")
   decoded = Message.decode(message.encode())
   print(decoded.author.name)    # Anna
   print(decoded.author.groups)  # ['editors']
   print(decoded.text)           # Hello!

.. testoutput::
   :hide:

   Anna
   ['editors']
   Hello!

Передавайте экземпляр ``User``, а не словарь. При чтении ``Message``
библиотека сама восстановит вложенный ``User``. Объявляйте вложенный класс
раньше того, который его использует: аннотации разрешаются сразу.

Список моделей
--------------

Для нескольких пользователей достаточно ``list[User]``:

.. testcode::

   class Packet(ProtoModel):
       users: list[User]

   packet = Packet(users=[anna, boris])
   decoded = Packet.decode(packet.encode())
   print([user.name for user in decoded.users])  # ['Anna', 'Boris']

.. testoutput::
   :hide:

   ['Anna', 'Boris']

Поддерживаются и вложенные списки, например ``list[list[str]]``.
Сам список можно сделать optional-полем:
``groups: list[str] | None = field(flag=0)``. При этом ``None`` и ``[]``
будут разными значениями. Optional-элементы ``list[str | None]``
не поддерживаются, как и автоматическая сериализация ``dict``, ``tuple`` и ``set``.

Вложенная модель сохраняет своё framing, пропуская только constructor:
её тип уже известен из аннотации. Настройки внешнего класса не заменяют
настройки вложенного. Точные байты разобраны позже в :ref:`nested-headers`.

Обычные списки и вложенные модели не требуют настройки формата.
Если нужно изменить кодировку текста или префикс длины, переходите к
:doc:`field-configuration`. Полное устройство вложенных данных описано
отдельно в :doc:`wire-format`.
