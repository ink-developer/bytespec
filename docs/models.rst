Файлы и несколько сообщений
===========================

После ``encode()`` у вас обычные байты. Их можно сохранить или соединить
с другими сообщениями. Для примеров используем небольшую модель:

.. testcode::

   from bytespec import ProtoModel

   class Message(ProtoModel):
       text: str

Сохранить и прочитать файл
--------------------------

.. testsetup::

   import os
   from tempfile import TemporaryDirectory
   _previous_directory = os.getcwd()
   _directory = TemporaryDirectory(prefix="bytespec-docs-")
   os.chdir(_directory.name)

.. testcode::

   from pathlib import Path

   message = Message(text="Hello")
   path = Path("message.bin")
   path.write_bytes(message.encode())

   restored = Message.decode(path.read_bytes())
   print(restored.text)  # Hello

.. testoutput::
   :hide:

   Hello

Используйте бинарные операции ``write_bytes()`` и ``read_bytes()``:
дополнительная текстовая кодировка здесь не нужна.

Изменить и записать заново
--------------------------

.. testcode::

   restored.text = "Updated"
   print(Message.decode(restored.encode()).text)  # Updated

.. testoutput::
   :hide:

   Updated

Атрибуты модели изменяемы. Каждый вызов ``encode()`` читает их текущие
значения, в том числе заново определяет присутствие optional-полей.
Байты, полученные предыдущим вызовом, не меняются.

Прочитать два сообщения из одного буфера
----------------------------------------

``decode()`` ожидает ровно одно сообщение. Если в буфере их несколько,
используйте ``decode_from()``:

.. testcode::

   buffer = Message(text="One").encode() + Message(text="Two").encode()

   first, offset = Message.decode_from(buffer, 0)
   second, offset = Message.decode_from(buffer, offset)

   print(first.text, second.text)  # One Two
   print(buffer[offset:])         # b''

.. testoutput::
   :hide:

   One Two
   b''

Второй результат — абсолютная позиция после прочитанного сообщения.
Передавайте её следующему вызову. Начальная позиция должна быть
неотрицательной.

Начать чтение после префикса транспорта
---------------------------------------

.. testcode::

   buffer = b"MSG:" + Message(text="Hello").encode() + b"NEXT"
   message, end = Message.decode_from(buffer, 4)

   print(message.text)  # Hello
   print(buffer[end:])  # b'NEXT'

.. testoutput::
   :hide:

   Hello
   b'NEXT'

``end`` относится ко всему ``buffer``, а не к срезу после ``MSG:``.
Следующие байты остаются вызывающему коду.

Оба метода читают готовый буфер. Они не накапливают сетевые фрагменты
между вызовами: если сообщение неполное, возникает ``DecodeError``.
Сначала соберите его средствами своего транспорта. Проверки размеров и
правила дополнительных данных описаны в :ref:`unknown-wire-data`.

Если в буфере сообщения разных типов, приложение должно выбрать правильный
класс для каждого вызова. Автоматического выбора модели по её идентификатору
нет; детали заголовка — :doc:`wire-format`.

Запись с пропуском Constructor
------------------------------

Если внешний слой уже записывает идентификатор, можно пропустить этот
элемент, сохранив остальные части header:

.. testcode::

   from bytespec import Constructor, Flags, PayloadLength
   from bytespec.types import UInt8

   class Reading(ProtoModel):
       __header__ = (Flags(1), Constructor(1), PayloadLength(1))
       value: UInt8

   reading = Reading(value=7)
   encoded = reading.encode(include_constructor=False)
   restored, end = Reading.decode_from(b"xx" + encoded, 2, expect_constructor=False)
   assert restored == reading
   print(encoded.hex(" "), end)

.. testoutput::

   00 01 07 5

Оба параметра означают полное отсутствие байтов ``Constructor``, где бы
он ни стоял в header. ``expect_constructor=False`` не читает и не игнорирует
произвольный идентификатор во входе. ``decode()`` такого параметра не имеет;
используйте ``decode_from()`` и при необходимости проверьте итоговый offset.
``ModelCodec`` применяет эту пару параметров автоматически при вложении.

Далее — :doc:`wire-format`: точные байты, границы и неизвестные данные.

.. testcleanup::

   os.chdir(_previous_directory)
   _directory.cleanup()
