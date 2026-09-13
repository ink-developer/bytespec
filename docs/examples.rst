Практические задачи
====================

Выберите задачу и начните с готовых байтов. Примеры не требуют подключения
к сети; все пакеты уже находятся в памяти.

.. .. contents:: На этой странице
..    :local:
..    :depth: 1

.. .. _recipe-tcp:

Прочитать пакет устройства из TCP
---------------------------------

Устройство прислало ``10 00 04 01 02 4f 4b``. По его протоколу это:
один байт команды, два байта длины полей, версия и данные с однобайтовой длиной.
Опишем ответ команды ``0x10``:

.. testcode:: tcp

   from bytespec import Constructor, PayloadLength, ProtoModel, field
   from bytespec.types import UInt8

   class Reply(ProtoModel):
       __constructor__ = 0x10
       __header__ = (Constructor(1), PayloadLength(2))
       version: UInt8
       data: bytes = field(prefix_length=1)

   received = bytes.fromhex("10 00 04 01 02 4f 4b")
   reply = Reply.decode(received)
   print(reply.version, reply.data)
   assert reply.encode() == received

.. testoutput:: tcp

   1 b'OK'

.. container:: wire-bytes

   .. dropdown:: ① Команда · ``10``

      Значение ``__constructor__ = 0x10``. Сообщение другой команды не пройдёт проверку ``Reply``.

   .. dropdown:: ② Длина полей · ``00 04``

      Четыре байта после заголовка: версия, длина данных и два байта ``OK``.

   .. dropdown:: ③ Версия · ``01``

      ``UInt8`` читает один байт и возвращает обычное целое число 1.

   .. dropdown:: ④ Данные · ``02 4f 4b``

      Длина 2, затем байты ``OK``. ``data`` остаётся ``bytes``, а не строкой.

Здесь ``received`` уже содержит полный пакет. Один вызов ``recv()`` в TCP
может вернуть часть пакета или несколько пакетов сразу: сначала накопите
нужные байты. bytespec разбирает буфер, а не управляет сокетом.

.. _recipe-buffer:

Прочитать несколько сообщений из одного буфера
----------------------------------------------

В буфер попали два ответа предыдущего формата. Продолжаем с классом ``Reply``:

.. testcode:: tcp

   buffer = received + received
   first, offset = Reply.decode_from(buffer, 0)
   print(first.data, offset)
   second, offset = Reply.decode_from(buffer, offset)
   print(second.data, offset)
   assert offset == len(buffer)

.. testoutput:: tcp

   b'OK' 7
   b'OK' 14

Первый ответ занимает байты 0–6. Возвращённое :term:`смещение <offset>` 7
указывает начало второго. После второго получаем 14 — конец буфера.
``decode()`` принимает ровно одно сообщение; для нескольких нужен ``decode_from()``.
Правила работы с остатком буфера: :doc:`models`.

.. _recipe-no-header:

Прочитать формат без заголовка bytespec
---------------------------------------

Датчик отправляет ровно два байта: температуру 23 и заряд 87.
Добавлять служебные байты нельзя:

.. testcode:: sensor

   from bytespec import ProtoModel
   from bytespec.types import UInt8

   class SensorReading(ProtoModel):
       __header__ = ()
       temperature: UInt8
       battery: UInt8

   received = bytes.fromhex("17 57")
   reading = SensorReading.decode(received)
   print(reading.temperature, reading.battery)
   assert reading.encode() == received

.. testoutput:: sensor

   23 87

``__header__ = ()`` убирает все элементы заголовка. Первый байт сразу
принадлежит ``temperature``, второй — ``battery``. Для такого фиксированного
формата границы определяются размерами полей. Другие варианты: :doc:`headers`.

.. _recipe-little-endian:

Прочитать число в little-endian
-------------------------------

Устройство хранит счётчик 258 в двух байтах ``02 01``, младший байт первым.
Укажем этот :term:`порядок байтов <byte order>`:

.. testcode:: little-endian

   from bytespec import ByteOrder, ProtoModel
   from bytespec.types import UInt16

   class DeviceCounter(ProtoModel):
       __header__ = ()
       __byte_order__ = ByteOrder.LITTLE
       value: UInt16

   received = bytes.fromhex("02 01")
   counter = DeviceCounter.decode(received)
   print(counter.value)
   assert counter.encode() == received

.. testoutput:: little-endian

   258

Число равно ``2 + 1 * 256``. При стандартном big-endian те же два байта
означали бы 513. Настройка действует на числа фиксированного размера и
префиксы этой модели; байты текста она не переставляет.

.. _recipe-codec:

Сохранить собственный тип приложения
------------------------------------

В приложении идентификатор представлен объектом ``UserId``, а устройство
ожидает четыре байта целого числа. :doc:`codecs` показывает полный пример:
класс ``UserId``, его кодек и подключение через ``field(codec=...)``.
:term:`Кодек <codec>` отвечает только за преобразование отдельного поля.

Собрать вложенное сообщение
---------------------------

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
