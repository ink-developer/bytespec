# bytespec

English · [Русский](README.ru.md)

[Documentation](https://bytespec.pymax.org) · [PyPI](https://pypi.org/project/bytespec/) · [Telegram](https://t.me/bytespec)

Typed Python models over an explicit sequential binary representation.
One model reads and writes numbers, strings, lists, and nested objects;
you choose their representation, and the library tracks lengths and offsets.

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

`12` identifies the message; `09` is the computed length of its fields.
Next come the four-byte `id` and a UTF-8 name with a one-byte length prefix.
In your application, these are ordinary `int` and `str` values. Your first
models can use the default framing without setting `__header__`; for an
existing format, you can customize or remove it.

bytespec fits custom or existing sequential binary protocols when you want
to work with classes without a separate schema language or code generation.
It supports optional fields through flags, `IntEnum`, UUID, datetime, numeric
encodings, and custom codecs. This is a small 0.1.0 library: for a flexible
binary parser DSL, consider Construct; for standard JSON/MessagePack, msgspec;
for a schema ecosystem with its own wire format, protobuf.

## Installation

Python 3.10+:

```bash
pip install bytespec
```

Or `uv add bytespec`.

## Documentation

The full guide and API reference are available at [bytespec.pymax.org](https://bytespec.pymax.org) in Russian and English.

To build the documentation locally:

```bash
uv sync --locked --group docs
uv run --no-sync python -m sphinx -E -a -n -W --keep-going -b html -D language=ru docs docs/_build/html/ru
uv run --no-sync python -m sphinx -E -a -n -W --keep-going -b html -D language=en docs docs/_build/html/en
```

Open `docs/_build/html/en/index.html`. The language switcher keeps you on
the same page. Start with **Getting started**, **Why bytespec?**, or
**Headers and framing**, then consult the **API reference**.
The [documentation sources](docs/index.rst) and
[build instructions](docs/building.rst) are in Russian; Sphinx applies
the [English translation catalogs](docs/locale/en/LC_MESSAGES/index.po)
when building the English version.

Take a known packet from your protocol, describe a few fields, and compare
the re-encoded result with the original bytes. That is a useful first check
of whether the library fits your format.

## Community

Questions, ideas and feedback are welcome in the
[Telegram community](https://t.me/bytespec).

[MIT license](LICENSE).
