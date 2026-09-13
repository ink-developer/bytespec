bytespec
========

``bytespec`` описывает последовательный бинарный формат типизированным
Python-классом. Вы задаёте представление полей; библиотека записывает и читает
их, считает длины и перемещает offset. Это удобно для собственных протоколов
и существующих форматов, которые укладываются в такую модель.

Установите пакет (Python 3.10+):

.. code-block:: console

   python -m pip install bytespec

.. testcode::

   from bytespec import ProtoModel

   class User(ProtoModel):
       name: str
       active: bool

   user = User(name="Anna", active=True)
   encoded = user.encode()           # bytes для хранения или передачи
   decoded = User.decode(encoded)   # снова User

   print(decoded.name)  # Anna

.. testoutput::
   :hide:

   Anna

Для чтения нужен тот же класс модели. Бинарное представление определяется
типами полей и их настройками; при необходимости можно выбрать размер числа,
кодировку строки или собственное правило сериализации.

:doc:`why-bytespec` сравнивает один пакет в struct, Construct и bytespec
и объясняет границы применимости. :doc:`getting-started` проведёт от этого
примера к модели с другими типами,
необязательными полями и списками. Если уже знаете, что ищете, откройте
:doc:`api/index` или :doc:`wire-format`.

.. toctree::
   :maxdepth: 1
   :hidden:
   :caption: Начало работы

   why-bytespec
   getting-started
   fields
   types
   optional-defaults
   collections
   field-configuration
   examples

.. toctree::
   :maxdepth: 1
   :hidden:
   :caption: Управление форматом

   headers
   codecs
   inheritance
   validation
   errors
   models
   wire-format

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Справочник

   api/index
   building
