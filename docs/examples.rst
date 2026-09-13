Собираем сообщение
==================

Теперь соединим уже знакомые возможности: модель автора, список тегов
и необязательную заметку. Этот пример можно выполнить целиком.

.. testcode::

   from bytespec import ProtoModel, field
   from bytespec.types import UInt32

   class User(ProtoModel):
       id: UInt32
       name: str

   class Message(ProtoModel):
       author: User
       text: str
       tags: list[str] = field(default_factory=list)
       note: str | None = field(flag=0)

   message = Message(
       author=User(id=42, name="Anna"),
       text="Hello!",
       tags=["news"],
   )
   encoded = message.encode()
   decoded = Message.decode(encoded)

   print(decoded.author.name)  # Anna
   print(decoded.text)         # Hello!
   print(decoded.tags)         # ['news']
   print(decoded.note)         # None

.. testoutput::
   :hide:

   Anna
   Hello!
   ['news']
   None

Создание и чтение остались такими же, как у первой модели. Список тегов
восстановился как список, автор — как ``User``, а пропущенная заметка —
как ``None``. Для этих структур не понадобились отдельные вызовы сериализации.

Изменим заметку и запишем сообщение ещё раз:

.. testcode::

   decoded.note = "Updated"
   updated = Message.decode(decoded.encode())
   print(updated.note)  # Updated

.. testoutput::
   :hide:

   Updated

Полезно попробовать этот пример с пустым ``tags`` и с ``note=""``:
оба значения будут сохранены. Только ``note=None`` убирает optional-поле
из сообщения.

Теперь можно попробовать модель на одном пакете своего протокола.
:doc:`headers` показывает, как настроить служебные байты; :doc:`validation` —
как проверить связи между полями; :doc:`errors` — как обработать ошибки.
Если нужно читать несколько сообщений из одного буфера, откройте :doc:`models`.
