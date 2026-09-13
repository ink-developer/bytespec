# bytespec

[English](README.md) · Русский

[Документация](https://bytespec.pymax.org) · [PyPI](https://pypi.org/project/bytespec/)

Типизированные Python-модели для бинарных форматов с явным расположением полей.
Одна модель читает и записывает числа, строки, списки и вложенные объекты;
вы выбираете их представление, библиотека считает длины и offsets.

```python
from bytespec import Constructor, PayloadLength, ProtoModel, field
from bytespec.types import UInt32


class User(ProtoModel):
    __constructor__ = 0x12
    __header__ = (Constructor(1), PayloadLength(1))
    id: UInt32
    name: str = field(prefix_length=1)


user = User(id=42, name="Anna")
data = user.encode()
restored = User.decode(data)

print(data.hex(" "))  # 12 09 00 00 00 2a 04 41 6e 6e 61
print(restored.name)  # Anna
assert restored == user
```

`12` — идентификатор сообщения, `09` — вычисленная длина его полей.
Дальше идут четырёхбайтовый `id` и UTF-8 имя с однобайтовым префиксом длины.
В приложении это обычные `int` и `str`. Для первых моделей можно не задавать
`__header__`: есть стандартное framing; для существующего формата его можно
настроить или убрать.

bytespec подходит для собственного или существующего последовательного
бинарного протокола, когда хочется работать с классами без отдельного языка
схем и генерации кода. Есть optional flags, `IntEnum`, UUID, datetime,
числовые encodings и custom codecs. Это небольшая библиотека 0.1.0:
сложный parser DSL остаётся задачей Construct, стандартный JSON/MessagePack —
msgspec, а экосистема схем с собственным wire format — protobuf.

## Установка

Python 3.10+:

```bash
pip install bytespec
```

Или `uv add bytespec`.

## Документация

Полное руководство и справочник API: [bytespec.pymax.org](https://bytespec.pymax.org).

- [Первая модель](docs/getting-started.rst) — объявить, записать и прочитать.
- [Зачем bytespec?](docs/why-bytespec.rst) — ниша и один пакет в struct, Construct и bytespec.
- [Header и framing](docs/headers.rst) — согласовать модель с существующим протоколом.
- [Справочник API](docs/api/index.rst) · [Сборка и проверка примеров](docs/building.rst).

Возьмите известный пакет своего протокола, опишите несколько полей и сравните
повторную запись с исходными байтами — это хороший первый способ проверить,
подходит ли библиотека вашему формату.

[Лицензия MIT](LICENSE).
