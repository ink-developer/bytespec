bytespec
========

Опишите данные Python-классом, сохраните их в байты и прочитайте обратно.
``bytespec`` сам определяет, где заканчивается одно поле и начинается следующее.

.. testcode::

   from bytespec import ProtoModel

   class User(ProtoModel):
       name: str
       active: bool

   user = User(name="Anna", active=True)
   encoded = user.encode()
   decoded = User.decode(encoded)

   print(decoded.name, decoded.active)
   assert decoded == user

.. testoutput::

   Anna True

Это новый ``User`` с теми же значениями. В байты можно записывать и списки,
и вложенные модели. Для существующего бинарного формата вы явно задаёте
размеры и порядок полей — без отдельного языка схем и генерации кода.

.. code-block:: console

   pip install bytespec

или

.. code-block:: console

   uv add bytespec

Python 3.10+. Начните с первой модели или выберите нужную задачу:

.. grid:: 1 2 2 2
   :gutter: 2

   .. grid-item-card:: Первая модель
      :link: getting-started
      :link-type: doc

      От Python-класса до разбора полученных байтов. Знание протоколов не нужно.

   .. grid-item-card:: Зачем bytespec?
      :link: why-bytespec
      :link-type: doc

      Один пакет в bytespec, struct и Construct. Когда подходит каждый инструмент.

   .. grid-item-card:: Практические задачи
      :link: examples
      :link-type: doc

      Прочитать TCP-пакет, разобрать несколько сообщений, настроить порядок байтов.

   .. grid-item-card:: Справочник API
      :link: api/index
      :link-type: doc

      Сигнатуры, параметры и точные правила чтения и записи.

.. toctree::
   :maxdepth: 1
   :hidden:
   :caption: Начало работы

   getting-started
   fields
   types
   optional-defaults
   collections

.. toctree::
   :maxdepth: 1
   :hidden:
   :caption: Устройство и понятия

   concepts
   why-bytespec
   wire-format

.. toctree::
   :maxdepth: 1
   :hidden:
   :caption: Практические задачи

   examples
   field-configuration
   headers
   codecs
   inheritance
   validation
   errors
   models

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Справочник API

   api/index
   building
