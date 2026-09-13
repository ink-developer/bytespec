from __future__ import annotations

import sys
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version
from pathlib import Path
from shutil import copyfile
from typing import Any, get_origin

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

project = "bytespec"
author = "ink-developer"
copyright = "2026, ink-developer"

# Use distribution metadata; an uninstalled source checkout gets its
# version from the same project file.
try:
    release = package_version("bytespec")
except PackageNotFoundError:
    import tomllib

    with (ROOT / "pyproject.toml").open("rb") as project_file:
        release = tomllib.load(project_file)["project"]["version"]
version = release

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.doctest",
    "sphinx_copybutton",
]

language = "ru"
locale_dirs = ["locale"]
gettext_compact = False
gettext_additional_targets = ["literal-block"]
gettext_location = False
gettext_uuid = False
root_doc = "index"
exclude_patterns = ["_build", "superpowers", "locale", "Thumbs.db", ".DS_Store"]
autosummary_generate = True

# Reference pages explicitly select their public members. Do not expose
# resolver internals or every attribute inherited by a model/codec.
autodoc_member_order = "bysource"
autodoc_typehints = "signature"
autodoc_typehints_format = "short"
autodoc_class_signature = "mixed"
autodoc_inherit_docstrings = False
autodoc_type_aliases = {
    "PrefixLength": "bytespec.models.PrefixLength",
    "UIntEncoding": "bytespec.models.UIntEncoding",
    "DefaultFactory": "bytespec.models.DefaultFactory",
    "CodecFactory": "bytespec.resolvers.CodecFactory",
    "ResolveCallback": "bytespec.resolvers.ResolveCallback",
}

# These implementation-only types appear in imported signatures. Keep their
# spelling, but do not publish private API pages just to create link targets.
nitpick_ignore = [
    ("py:class", "bytespec.codecs.base.T"),
    ("py:class", "bytespec.missing._MissingType"),
    ("py:class", "bytespec.models.ResolvedType"),
    ("py:class", "NoneType"),
]

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = False
napoleon_use_param = True
napoleon_use_rtype = True

intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}

html_theme = "furo"
html_title = "bytespec"
templates_path = ["_templates"]
html_static_path = ["_static"]
html_css_files = ["languages.css"]
html_sidebars = {
    "**": [
        "sidebar/brand.html",
        "sidebar/languages.html",
        "sidebar/search.html",
        "sidebar/scroll-start.html",
        "sidebar/navigation.html",
        "sidebar/ethical-ads.html",
        "sidebar/scroll-end.html",
        "sidebar/variant-selector.html",
    ]
}
html_theme_options = {"sidebar_hide_name": False, "navigation_with_keys": True}
pygments_style = "friendly"
pygments_dark_style = "monokai"


def skip_typing_docstrings(
    app: Any, what: str, name: str, obj: Any, options: Any, lines: list[str]
) -> None:
    if what in {"data", "attribute"} and get_origin(obj) is not None:
        lines.clear()


def render_alias_signature(
    app: Any,
    what: str,
    name: str,
    obj: Any,
    options: Any,
    signature: str | None,
    return_annotation: str | None,
) -> tuple[str | None, str | None]:
    if signature and name == "bytespec.types.CodecSpec":
        signature = signature.replace(
            "TypeAliasForwardRef('bytespec.models.PrefixLength')",
            "bytespec.models.PrefixLength",
        )
    return signature, return_annotation


def write_language_redirect(app: Any, exception: Exception | None) -> None:
    output = Path(app.outdir)
    if (
        exception is None
        and app.builder.name == "html"
        and app.config.language in {"ru", "en"}
        and output.name == app.config.language
    ):
        copyfile(Path(app.srcdir) / "_templates/redirect.html", output.parent / "index.html")


def setup(app: Any) -> None:
    app.connect("autodoc-process-docstring", skip_typing_docstrings)
    app.connect("autodoc-process-signature", render_alias_signature)
    app.connect("build-finished", write_language_redirect)
