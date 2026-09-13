Первая модель
=============

Установите ``bytespec`` в окружение с Python 3.10+:

.. code-block:: console

   python -m pip install bytespec

Этот пример можно сохранить в ``user.py`` и выполнить целиком:

.. testcode::

   from bytespec import ProtoModel

   class User(ProtoModel):
       name: str
       active: bool

   user = User(name="Anna", active=True)
   encoded = user.encode()
   decoded = User.decode(encoded)

   print(decoded.name)    # Anna
   print(decoded.active)  # True

.. testoutput::
   :hide:

   Anna
   True

Теперь разберём три действия из примера.

Описать и создать модель
------------------------

``User`` наследует ``ProtoModel``. Аннотации ``name: str`` и ``active: bool``
описывают два поля сообщения. Для строк и логических значений дополнительная
настройка не нужна.

Значения передаются по именам и доступны как атрибуты:

.. testcode::

   user = User(name="Boris", active=False)
   print(user.name)  # Boris

.. testoutput::
   :hide:

   Boris

Пока оба поля обязательны: их нужно передать при создании ``User``.
На следующей странице добавим значение по умолчанию.

Записать в bytes
----------------

.. testcode::

   encoded = user.encode()
   print(type(encoded).__name__)  # bytes

.. testoutput::
   :hide:

   bytes

``encode()`` возвращает законченное бинарное сообщение. Его можно сохранить
в файл или отправить по сети без преобразования в текст. После стандартного
header записываются ``name`` и ``active`` в порядке объявления полей.
Длину текста и всего body библиотека вычисляет сама; вручную двигать offset
или поддерживать отдельную функцию записи не нужно.

Прочитать обратно
-----------------

.. testcode::

   decoded = User.decode(encoded)
   print(decoded.name)    # Boris
   print(decoded.active)  # False

.. testoutput::
   :hide:

   Boris
   False

``decode()`` вызывается у класса и создаёт новый ``User``. Передайте ему байты
одного сообщения. Получатель должен знать его модель: библиотека не выбирает
класс автоматически по содержимому.

Это весь цикл обычного использования: **класс → экземпляр → bytes → экземпляр**.
Меняя поля или их настройки, согласуйте модель у отправителя и получателя.

Посмотреть на байты
-------------------

У первой модели ``User(name="Anna", active=True)`` содержимое полей такое:

.. testcode::

   encoded = User(name="Anna", active=True).encode()
   print(encoded[14:].hex(" "))

.. testoutput::

   00 00 00 04 41 6e 6e 61 01

Четыре байта длины строки, UTF-8 ``Anna``, затем ``01`` для ``True``.
Срез пропускает 14 байт стандартного header. Для другого протокола можно
выбрать размер числа, префикс строки и само framing; это постепенно
разбирается в :doc:`types`, :doc:`field-configuration` и :doc:`headers`.

Далее — :doc:`fields`: сделаем ``active`` полем со значением по умолчанию.
