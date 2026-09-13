Codecs: свой формат и свои типы
===============================

Обычно тип поля уже определяет, как записать его в байты. Если нужно
другое представление, полю можно назначить *codec* — объект с правилами
записи и чтения одного значения.

.. _fixed-bytes:

Взять готовый codec
-------------------

Допустим, подпись пакета занимает ровно 4 байта и не должна иметь
префикса длины:

.. testcode::

   from bytespec import ProtoModel, field
   from bytespec.codecs import FixedBytesCodec

   class Packet(ProtoModel):
       signature: bytes = field(codec=FixedBytesCodec(4))

   packet = Packet(signature=b"ABCD")
   print(Packet.decode(packet.encode()).signature)  # b'ABCD'

.. testoutput::
   :hide:

   b'ABCD'

``FixedBytesCodec(4)`` уже реализует такой формат. При записи он проверит
длину значения, при чтении — наличие четырёх байтов. ``field(codec=...)``
принимает готовый **экземпляр** codec; писать свой класс здесь не требуется.
Другие готовые варианты перечислены в :doc:`api/codecs`.

.. _numeric-enum:

Составить codec из готовых частей
---------------------------------

По умолчанию ``IntEnum`` использует ``VarInt``. Если протокол требует один
unsigned byte, соедините ``EnumCodec`` и ``UInt8Codec``:

.. testcode::

   from enum import IntEnum
   from bytespec.codecs import EnumCodec, UInt8Codec

   class Status(IntEnum):
       READY = 1
       BUSY = 2

   class Message(ProtoModel):
       status: Status = field(codec=EnumCodec(Status, UInt8Codec()))

   message = Message(status=Status.BUSY)
   print(Message.decode(message.encode()).status.name)  # BUSY

.. testoutput::
   :hide:

   BUSY

``EnumCodec`` берёт ``.value``, а ``UInt8Codec`` записывает число в один байт.
Так же ``ListCodec`` принимает codec элемента. Готовые объекты можно
комбинировать, не реализуя чтение байтов заново.

Замена codec меняет и результат decode
--------------------------------------

Явный codec **полностью заменяет** автоматический выбор. Аннотация поля
сама по себе не оборачивает результат обратно в логический тип:

.. testcode::

   from typing import Annotated
   from bytespec.types import CodecSpec

   class RawStatus(ProtoModel):
       __header__ = ()
       first: Status = field(codec=UInt8Codec())
       second: Annotated[Status, CodecSpec(codec=UInt8Codec())]

   raw = RawStatus(first=Status.BUSY, second=Status.BUSY)
   decoded = RawStatus.decode(raw.encode())
   assert type(decoded.first) is int
   assert type(decoded.second) is int
   print(raw.encode().hex(" "))

.. testoutput::

   02 02

Оба поля после чтения содержат ``int``, несмотря на аннотацию ``Status``.
Для сохранения enum используйте ``EnumCodec`` из предыдущего примера.
Это же правило действует для ``CodecSpec`` и любых других логических типов:
объект восстанавливает сам codec.

Поддержать собственный тип
--------------------------

Пусть приложение хранит идентификатор в отдельном классе:

.. testcode::

   from dataclasses import dataclass

   @dataclass(frozen=True)
   class UserId:
       value: int

Для записи ``UserId`` достаточно передать его число готовому ``UInt32Codec``;
при чтении — обернуть число обратно:

.. testcode::

   from bytespec import ByteOrder
   from bytespec.codecs import ICodec, UInt32Codec

   class UserIdCodec(ICodec[UserId]):
       def encode(self, value: UserId, byte_order: ByteOrder) -> bytes:
           return UInt32Codec().encode(value.value, byte_order)

       def decode(self, buffer: bytes, byte_order: ByteOrder,
                  offset: int) -> tuple[UserId, int]:
           value, end = UInt32Codec().decode(buffer, byte_order, offset)
           return UserId(value), end

``encode()`` возвращает байты одного значения. ``decode()`` получает позицию
начала и возвращает новую абсолютную позицию в том же буфере.
``byte_order`` — порядок байтов модели; здесь мы передаём его числовому codec.

Теперь подключим реализацию к полю:

.. testcode::

   class User(ProtoModel):
       id: UserId = field(codec=UserIdCodec())

   user = User(id=UserId(42))
   decoded = User.decode(user.encode())
   print(decoded.id.value)  # 42

.. testoutput::
   :hide:

   42

``ICodec[T]`` описывает интерфейс codec. Наследоваться от него удобно для
типизации, но подходит и объект с методами ``encode`` и ``decode``.
Проверка наличия этих методов не проверяет правильность реализации.

Проверки размеров и числового диапазона в примере выполняет ``UInt32Codec``.
Если читаете байты самостоятельно, проверяйте доступность данных и сообщайте
о повреждении через ``DecodeError``, о непредставимом значении —
через ``EncodeError``. Произвольные исключения из custom codec не оборачиваются.
Требования к offset, в том числе для элементов списка: :ref:`codec-contract`.

Назначить codec всем полям своего типа
--------------------------------------

Когда ``UserId`` используется часто, можно не повторять ``field(codec=...)``.
Добавьте правило через ``configure_codecs()``:

.. testcode::

   class User(ProtoModel):
       @classmethod
       def configure_codecs(cls):
           return {UserId: lambda annotation, field_info: UserIdCodec()}

       id: UserId

   user = User(id=UserId(7))
   print(User.decode(user.encode()).id.value)  # 7

.. testoutput::
   :hide:

   7

Ключ — тип поля. Значение — фабрика, возвращающая codec для него.
Она получает аннотацию и настройки поля и вызывается при объявлении
класса модели. В этом примере дополнительных настроек нет, поэтому
фабрика просто создаёт ``UserIdCodec``.

Возвращённые правила дополняют встроенные. Уже существующий ключ заменяет
правило для этого типа; правила наследуются подклассами. Для аннотации
собственной фабрики и точных приоритетов есть :doc:`api/extensions`.
Работать с внутренним registry напрямую не требуется.

Переиспользовать настройку через Annotated
------------------------------------------

Как и префикс строки, явный codec можно поместить в ``CodecSpec``:

.. testcode::

   from typing import Annotated
   from bytespec.types import CodecSpec

   Signature = Annotated[bytes, CodecSpec(codec=FixedBytesCodec(4))]

   class Message(ProtoModel):
       signature: Signature

   message = Message(signature=b"ABCD")
   print(Message.decode(message.encode()).signature)  # b'ABCD'

.. testoutput::
   :hide:

   b'ABCD'

Эту аннотацию можно использовать в нескольких моделях и в ``list[Signature]``.
Явный ``field(codec=...)`` имеет приоритет перед аннотацией. Настройки
готового codec задаются его конструктором: ``field(prefix_length=1,
codec=StrCodec())`` не перенастроит переданный ``StrCodec()``.

Вызвать codec без модели
------------------------

.. testcode::

   from bytespec.codecs import ListCodec, StrCodec

   codec = ListCodec(StrCodec(prefix_length=1), prefix_length=2)
   encoded = codec.encode(["red", "blue"], ByteOrder.BIG)
   values, end = codec.decode(encoded, ByteOrder.BIG, 0)

   print(values)         # ['red', 'blue']
   print(encoded[end:])  # b''

.. testoutput::
   :hide:

   ['red', 'blue']
   b''

Такой вызов возвращает только представление значения, без заголовка модели.
За оставшиеся байты отвечает вызывающий код. ``ModelCodec`` составляет
исключение: он использует framing вложенной модели, пропуская её
``Constructor``. ``Flags`` и ``PayloadLength``, если они объявлены, остаются.
Сравнение отдельной и вложенной записи — :ref:`nested-headers`.

Далее — :doc:`inheritance` для переиспользования настроек или
:doc:`validation` для проверки значений. Точное устройство байтов:
:doc:`wire-format`.
