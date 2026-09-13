Проверка значений модели
========================

У диапазона начало не должно превышать конец. Это правило связывает два
поля и не выражается выбором числового codec:

.. testcode::

   from bytespec import ProtoModel
   from bytespec.types import UInt16

   class Window(ProtoModel):
       __header__ = ()
       start: UInt16
       end: UInt16

       def __validate__(self) -> None:
           if self.start > self.end:
               raise ValueError("start must not exceed end")

   window = Window(start=10, end=20)
   assert Window.decode(window.encode()) == window

   try:
       Window(start=20, end=10)
   except ValueError as error:
       print(error)

.. testoutput::

   start must not exceed end

Библиотека сама проверяет **бинарную схему**: известен ли тип, корректны ли
индексы и настройки. Ошибка схемы — ``SchemaError``. ``__validate__``
проверяет **значения приложения**. Это обычный метод экземпляра без
декоратора; к моменту вызова все поля уже присвоены, включая defaults и
результаты factories. Возвращаемое значение игнорируется: для отказа
поднимите исключение.

Когда вызывается проверка
-------------------------

Метод вызывается в конце ``ProtoModel.__init__`` и поэтому работает также
при ``decode()`` и ``decode_from()``. После чтения байтов создаётся обычный
экземпляр. Например, корректные числа могут нарушать правило диапазона:

.. testcode::

   try:
       Window.decode(bytes.fromhex("00 14 00 0a"))
   except ValueError as error:
       print(error)

.. testoutput::

   start must not exceed end

Исключение validator передаётся как есть: здесь это ``ValueError``,
а не ``DecodeError`` или ``EncodeError``. Выберите тип исключения, который
приложение сможет обработать наравне с ошибками чтения.

Присваивание атрибутов и ``encode()`` **не запускают проверку повторно**:

.. testcode::

   window.start = 30
   print(window.encode().hex(" "))
   try:
       window.__validate__()
   except ValueError as error:
       print(error)

.. testoutput::

   00 1e 00 14
   start must not exceed end

Если меняете объект, вызовите метод явно перед записью или создайте новый
экземпляр. Числовые диапазоны и возможность записи по-прежнему проверяются
codecs при ``encode()``. Полного runtime-контроля типов и автоматического
преобразования значений в модели нет.

Проверка в подклассе
--------------------

Автоматический вызов ищет ``__validate__`` только в самом конкретном классе.
Унаследованный метод доступен в Python, но автоматически не запускается:

.. testcode::

   class UncheckedWindow(Window):
       pass

   unchecked = UncheckedWindow(start=20, end=10)
   assert unchecked.start > unchecked.end

Для повторного использования определите метод в дочернем классе:

.. testcode::

   class CheckedWindow(Window):
       def __validate__(self) -> None:
           super().__validate__()

   try:
       CheckedWindow(start=20, end=10)
   except ValueError as error:
       print(error)

.. testoutput::

   start must not exceed end

Вложенная модель вызывает свою проверку при собственном создании, до
validator внешней модели при decode. Дополнительные правила композиции
и схемы подкласса описаны в :doc:`inheritance`.

Далее — :doc:`errors`: какие исключения обрабатывать при обмене сообщениями.
