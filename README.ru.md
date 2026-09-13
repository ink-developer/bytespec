# bytespec

[English](README.md) · Русский

[Документация](https://bytespec.pymax.org) · [PyPI](https://pypi.org/project/bytespec/) · [Telegram](https://t.me/bytespec)

Типизированные Python-модели для последовательных бинарных форматов.
Вы явно задаёте расположение полей в байтах и работаете с обычными
Python-объектами; bytespec читает и записывает поля, считает длины и смещения.

```python
from bytespec import ProtoModel


class User(ProtoModel):
    name: str
    active: bool


user = User(name="Anna", active=True)
encoded = user.encode()
decoded = User.decode(encoded)

assert decoded == user
```

Стандартный header используется автоматически. Задавать `__header__`
нужно только тогда, когда вашему формату требуется другое расположение
служебных элементов.

## Существующие бинарные форматы

Для существующего протокола выберите элементы header и представление полей:

```python
from bytespec import Constructor, Flags, PayloadLength, ProtoModel, field
from bytespec.types import UInt32


class Packet(ProtoModel):
    __constructor__ = 0x1234
    __header__ = (Constructor(2), Flags(1), PayloadLength(2))

    user_id: UInt32
    name: str | None = field(flag=0, prefix_length=1)


packet = Packet(user_id=42, name="Anna")
assert Packet.decode(packet.encode()) == packet
```

`Constructor` задаёт идентификатор сообщения, `Flags` отмечает присутствующие
необязательные поля, а `PayloadLength` хранит общую длину полей в байтах.
bytespec вычисляет флаги и длины; `UInt32` и `field()` задают представление полей.

## Когда использовать bytespec

bytespec подходит для собственных или существующих последовательных бинарных
форматов, когда нужны типизированные модели без отдельного языка схем
и генерации кода. Поддерживаются списки, вложенные модели, необязательные поля,
`IntEnum`, UUID, datetime, числовые представления и собственные кодеки.

Другие инструменты решают другие задачи:

- [Construct](https://construct.readthedocs.io/en/latest/intro.html) — мощный DSL для разбора и построения бинарных данных.
- [msgspec](https://msgspec.dev/) — стандартные форматы, такие как JSON и MessagePack.
- [Protobuf](https://protobuf.dev/overview/) — экосистема схем и компиляторов с собственным бинарным форматом.
- [struct](https://docs.python.org/3/library/struct.html) — небольшие фиксированные структуры.

**[Зачем bytespec?](https://bytespec.pymax.org/ru/why-bytespec.html)** объясняет
границы применимости и показывает один пакет в struct, Construct и bytespec.

## Установка

Python 3.10+:

```bash
pip install bytespec
```

Или `uv add bytespec`.

## Документация

Полное руководство и справочник API доступны на [bytespec.pymax.org](https://bytespec.pymax.org) на русском и английском языках.

Возьмите известный пакет своего протокола, опишите несколько полей и сравните
повторную запись с исходными байтами — это хороший первый способ проверить,
подходит ли библиотека вашему формату.

## Сообщество

Вопросы, идеи и обратную связь можно оставить в
[Telegram-чате](https://t.me/bytespec).

[Лицензия MIT](LICENSE).
