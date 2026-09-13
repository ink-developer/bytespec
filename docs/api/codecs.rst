Codecs
======

Имена на этой странице импортируются из ``bytespec.codecs``.
Codec принимает и возвращает отдельное значение; заголовок модели он
добавляет только в случае ``ModelCodec``. Примеры: :doc:`../codecs`.

Общий интерфейс
---------------

.. autoclass:: bytespec.codecs.ICodec
   :members: encode, decode
   :undoc-members:

   ``decode`` возвращает значение и абсолютный offset после него. При прямом
   использовании оставшиеся байты проверяет вызывающий код. При реализации
   собственного codec передавайте ошибки данных через ``EncodeError`` и
   ``DecodeError``.

.. _codec-contract:

Требования к реализации
-----------------------

``decode()`` должен возвращать абсолютную позицию после значения в том же
буфере, проверяя доступность нужных байтов. Экземпляр codec может
переиспользоваться: храните позицию в аргументах и результате, а не в
изменяемом внутреннем счётчике.

Для элемента списка обязательно продвижение на положительное число байтов
в пределах переданного буфера. ``ListCodec`` повторяет чтение до конца
своего содержимого и сам не проверяет продвижение offset. Элементы нулевой
длины, например ``FixedBytesCodec(0)``, не подходят: их количество невозможно
восстановить из пустого содержимого.

Ошибки данных передавайте через ``EncodeError`` и ``DecodeError``.
Ошибки реализации вроде ``TypeError`` или ``ValueError`` не оборачиваются.
Проверка протокола ``ICodec`` устанавливает наличие методов, но не
корректность их сигнатур или реализации.

Фиксированные числа
-------------------

У всех числовых codecs интерфейс ``encode``/``decode`` из ``ICodec``.
Используйте приведённые значения ``struct_format`` и ``length`` по умолчанию:
их ручное изменение требует согласовать размер ``struct`` и шаг decoder.
Конструктор проверяет синтаксис формата, но не согласованность этих параметров.

.. autoclass:: bytespec.codecs.UInt8Codec
.. autoclass:: bytespec.codecs.UInt16Codec
.. autoclass:: bytespec.codecs.UInt32Codec
.. autoclass:: bytespec.codecs.UInt64Codec
.. autoclass:: bytespec.codecs.Int8Codec
.. autoclass:: bytespec.codecs.Int16Codec
.. autoclass:: bytespec.codecs.Int32Codec
.. autoclass:: bytespec.codecs.Int64Codec
.. autoclass:: bytespec.codecs.Float32Codec
.. autoclass:: bytespec.codecs.Float64Codec

Varint и bool
-------------

.. autoclass:: bytespec.codecs.VarUIntCodec

   Канонический unsigned varint, диапазон ``UInt64``.

.. autoclass:: bytespec.codecs.VarIntCodec

   ZigZag + unsigned varint, диапазон ``Int64``.

.. autoclass:: bytespec.codecs.BoolCodec

   Записывает истинность значения как 0/1; принимает при чтении только 0/1.

Строки, bytes, дата и UUID
--------------------------

.. autoclass:: bytespec.codecs.StrCodec

   Префикс числа закодированных байтов и текст в выбранной кодировке.

.. autoclass:: bytespec.codecs.BytesCodec

   Префикс длины и содержимое ``bytes``.

.. autoclass:: bytespec.codecs.FixedBytesCodec

   Ровно ``length`` байт без префикса. Длина должна быть неотрицательной.

.. autoclass:: bytespec.codecs.DatetimeCodec

   ``datetime.isoformat()`` через ``StrCodec``;
   чтение через ``datetime.fromisoformat()``.

.. autoclass:: bytespec.codecs.UUIDCodec

   Ровно 16 байт ``UUID.bytes`` независимо от порядка байтов модели.

Составные значения
------------------

.. autoclass:: bytespec.codecs.ListCodec

   Префикс длины общего payload в байтах. ``item_codec`` должен читать один
   элемент за вызов и продвигать offset в границах буфера.

.. autoclass:: bytespec.codecs.EnumCodec

   Кодирует ``.value`` через переданный ``value_codec``, восстанавливает
   элемент вызовом ``enum_type(value)``.

.. autoclass:: bytespec.codecs.ModelCodec

   Вызывает ``encode(include_constructor=False)`` и
   ``model_type.decode_from(..., expect_constructor=False)``. Модель
   использует свой порядок байтов и header, пропуская Constructor.
   Другие элементы сохраняются. Тип вложенной модели определяется аннотацией.
