# bytespec

English · [Русский](README.ru.md)

[Documentation](https://bytespec.pymax.org) · [PyPI](https://pypi.org/project/bytespec/) · [Telegram](https://t.me/bytespec)

Typed Python models for sequential binary formats. Keep the wire layout
explicit while working with ordinary Python objects; bytespec reads and
writes the fields and tracks lengths and offsets.

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

The default header is used automatically. You only need to set `__header__`
when your format requires a different layout.

## Existing wire formats

For an existing protocol, choose the header elements and field representations:

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

`Constructor` identifies the message, `Flags` marks present optional fields,
and `PayloadLength` records the total byte length of all fields. bytespec computes the
flags and lengths; `UInt32` and `field()` define the field representation.

## When to use bytespec

bytespec fits custom or existing sequential binary formats when you want
typed models without a separate schema language or code generation.
It supports lists, nested models, optional fields, `IntEnum`, UUID, datetime,
numeric representations, and custom codecs.

Other tools serve different needs:

- [Construct](https://construct.readthedocs.io/en/latest/intro.html) — a powerful binary parser/builder DSL.
- [msgspec](https://msgspec.dev/) — standard formats such as JSON and MessagePack.
- [Protobuf](https://protobuf.dev/overview/) — a schema/compiler ecosystem with its own wire format.
- [struct](https://docs.python.org/3/library/struct.html) — small, fixed structures.

**[Why bytespec?](https://bytespec.pymax.org/en/why-bytespec.html)** explains
the tradeoffs and shows the same packet in struct, Construct, and bytespec.

## Installation

Python 3.10+:

```bash
pip install bytespec
```

Or `uv add bytespec`.

## Documentation

The full guide and API reference are available at [bytespec.pymax.org](https://bytespec.pymax.org) in Russian and English.

Take a known packet from your protocol, describe a few fields, and compare
the re-encoded result with the original bytes. That is a useful first check
of whether the library fits your format.

## Community

Questions, ideas and feedback are welcome in the
[Telegram community](https://t.me/bytespec).

[MIT license](LICENSE).
