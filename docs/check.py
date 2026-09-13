"""Check both languages, translation coverage, links, API, and README examples."""

from __future__ import annotations

import contextlib
import io
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from types import ModuleType
from typing import get_origin
from urllib.parse import unquote, urlsplit

from babel.messages.pofile import read_po

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import bytespec
from bytespec import codecs, types


class Links(HTMLParser):
    def __init__(self, text: str) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.targets: list[str] = []
        self.language: str | None = None
        self.feed(text)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "html":
            self.language = values.get("lang")
        if values.get("id"):
            self.ids.add(values["id"])
        for name in ("href", "src"):
            if values.get(name):
                self.targets.append(values[name])


def main() -> None:
    html_root = ROOT / "docs/_build/html"
    pages = {p.resolve(): Links(p.read_text()) for p in html_root.rglob("*.html")}
    if not pages:
        raise SystemExit("Build Sphinx HTML first")

    errors = []
    catalogs = ROOT / "docs/_build/gettext"
    templates = sorted(catalogs.rglob("*.pot"))
    if not templates:
        errors.append("Build Sphinx gettext catalogs first")
    translations = 0
    for template in templates:
        relative = template.relative_to(catalogs)
        translated = ROOT / "docs/locale/en/LC_MESSAGES" / relative.with_suffix(".po")
        if not translated.is_file():
            errors.append(f"Missing translation catalog: {translated.relative_to(ROOT)}")
            continue
        with template.open("rb") as source, translated.open("rb") as target:
            original = read_po(source)
            english = read_po(target, locale="en", abort_invalid=True)
        for message in original:
            if not message.id:
                continue
            translation = english.get(message.id)
            if translation is None or not translation.string or translation.fuzzy:
                errors.append(f"{relative}: missing or fuzzy translation: {message.id[:100]}")
            else:
                translations += 1
        for message, problems in english.check():
            errors.append(f"{relative}: {message.id[:100]}: {problems}")
        if relative.parts[0] == "api":
            translated = ROOT / "docs/locale/ru/LC_MESSAGES" / relative.with_suffix(".po")
            if not translated.is_file():
                errors.append(f"Missing translation catalog: {translated.relative_to(ROOT)}")
            else:
                with translated.open("rb") as target:
                    russian = read_po(target, locale="ru", abort_invalid=True)
                for message in original:
                    if not message.id or re.search("[А-Яа-яЁё]", message.id):  # noqa: RUF001
                        continue
                    translation = russian.get(message.id)
                    if translation is None or not translation.string or translation.fuzzy:
                        errors.append(
                            f"{relative}: missing or fuzzy Russian translation: {message.id[:100]}"
                        )
                    else:
                        translations += 1
                for message, problems in russian.check():
                    errors.append(f"{relative}: {message.id[:100]}: {problems}")
        for language in ("ru", "en"):
            page = (html_root / language / relative.with_suffix(".html")).resolve()
            if page not in pages:
                errors.append(f"Missing {language} page: {relative.with_suffix('.html')}")
            elif pages[page].language != language:
                errors.append(f"Incorrect HTML language: {page.relative_to(ROOT)}")

    entry = (html_root / "index.html").resolve()
    if entry not in pages:
        errors.append("Missing language entry page: docs/_build/html/index.html")

    local_links = 0
    for page, parsed in pages.items():
        for target in parsed.targets:
            url = urlsplit(target)
            if url.scheme or url.netloc:
                continue
            local_links += 1
            path = (page.parent / unquote(url.path)).resolve() if url.path else page
            if not path.is_file():
                errors.append(f"{page.relative_to(ROOT)}: missing {target}")
            elif url.fragment and path in pages and unquote(url.fragment) not in pages[path].ids:
                errors.append(f"{page.relative_to(ROOT)}: missing anchor {target}")

    # Check each intended export, not just references already used by the text.
    api_names = {f"bytespec.{name}" for name in bytespec.__all__}
    api_names |= {f"bytespec.codecs.{name}" for name in codecs.__all__}
    api_names |= {
        f"bytespec.types.{name}"
        for name, value in vars(types).items()
        if not name.startswith("_")
        and (
            get_origin(value) is not None
            or getattr(value, "__module__", None) == "bytespec.types.spec"
        )
    }
    api_names |= {
        f"bytespec.ProtoModel.{name}"
        for name in (
            "encode",
            "decode",
            "decode_from",
            "configure_codecs",
            "__validate__",
            "__constructor__",
            "__header__",
            "__byte_order__",
        )
    }
    api_names.add("bytespec.__version__")
    for language in ("ru", "en"):
        language_root = html_root / language
        ids = set().union(
            *(page.ids for path, page in pages.items() if path.is_relative_to(language_root))
        )
        errors.extend(f"Missing {language} API target: {name}" for name in sorted(api_names - ids))

    example_count = 0
    for readme_name in ("README.md", "README.ru.md"):
        readme = (ROOT / readme_name).read_text()
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", readme):
            url = urlsplit(target)
            if not url.scheme and not url.netloc and not (ROOT / unquote(url.path)).is_file():
                errors.append(f"{readme_name}: missing {target}")

        snippets = re.findall(r"```python\n(.*?)\n```", readme, re.DOTALL)
        if not snippets:
            errors.append(f"{readme_name}: no Python example found")
        example_count += len(snippets)
        for number, snippet in enumerate(snippets, 1):
            output = io.StringIO()
            module = ModuleType("_bytespec_readme_example")
            sys.modules[module.__name__] = module
            try:
                with contextlib.redirect_stdout(output):
                    code = compile(
                        snippet, f"{readme_name}:example-{number}", "exec", dont_inherit=True
                    )
                    exec(code, module.__dict__)  # noqa: S102 - Execute repository documentation.
            finally:
                del sys.modules[module.__name__]
            expected = re.findall(r"^\s*print\(.*\)\s+# (.*)$", snippet, re.MULTILINE)
            if output.getvalue().splitlines() != expected:
                errors.append(
                    f"{readme_name} example {number}: output differs from print comments"
                )

    if errors:
        raise SystemExit("\n".join(errors))
    print(
        f"{local_links} local HTML links, {len(api_names)} API targets, "
        f"{translations} translations, {example_count} README examples: OK (ru, en)"
    )


if __name__ == "__main__":
    main()
