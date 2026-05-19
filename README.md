```
   ▄████████  ▄██████▄   ▄█        ▄█        ▄████████  ▄████████     ███
  ███    ███ ███    ███ ███       ███       ███    ███ ███    ███ ▀█████████▄
  ███    █▀  ███    ███ ███       ███       ███    █▀  ███    █▀     ▀███▀▀██
  ███        ███    ███ ███       ███      ▄███▄▄▄     ███            ███   ▀
▀███████████ ███    ███ ███       ███     ▀▀███▀▀▀     ███            ███
         ███ ███    ███ ███       ███       ███    █▄  ███    █▄      ███
   ▄█    ███ ███    ███ ███▌    ▄ ███▌    ▄ ███    ███ ███    ███     ███
 ▄████████▀   ▀██████▀  █████▄▄██ █████▄▄██ ██████████ ████████▀     ▄████▀
                        ▀         ▀
```

<div align="center">

**Bundle source files into a single artifact — for LLM context, code reviews, sharing, or archiving.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

</div>

---

## Why

Pasting a whole project into an LLM is the #1 use case for tools like this, and it drove every design decision in v2.

```
                                  ┌──────────────────┐
   ┌─────────┐                    │  collected.md    │
   │  src/   │ ─┐                 │  ────────────    │
   ├─────────┤  │   ┌─────────┐   │  ## main.py      │
   │  *.py   │  └──▶│ collect │──▶│  ```python       │
   │  *.ts   │  ┌──▶│         │   │  def hello()...  │
   ├─────────┤  │   └─────────┘   │  ```             │
   │ tests/  │ ─┘                 │  ## utils.ts     │
   └─────────┘                    │  ...             │
                                  └──────────────────┘
```

- ✅ Markdown / XML / JSON / TXT output with proper language fences
- ✅ Respects `.gitignore` — no more shipping `node_modules` by accident
- ✅ Token counting (with `tiktoken` if installed)
- ✅ Binary detection — won't crash on `.png` or `.zip`
- ✅ UTF-8 by default, with safe fallbacks
- ✅ Glob include / exclude patterns
- ✅ Pretty terminal output via `rich`

---

## Install

```bash
pipx install git+https://github.com/4tocall/File-Collector-Script.git
```

For token counting:

```bash
pipx install "file-collector[tokens] @ git+https://github.com/4tocall/File-Collector-Script.git"
```

> 💡 No alias setup, no `chmod +x`, no `.zshrc` editing. The `collect` command lands on your PATH automatically.

---

## Quick usage

```bash
# Interactive: prompts for extensions, shows a table, asks which to include
collect

# Bundle all .py and .ts files into Markdown, copy to clipboard
collect py ts --all --copy

# Everything (gitignored excluded) as XML, written to ctx.xml, opened
collect --all --format xml --output ctx.xml --open

# All .py files outside tests/, with token count
collect py --exclude 'tests/**' --all --copy --tokens

# Run without installing
python -m collector py --all --copy
```

### Range selection in the interactive picker

```
   0 3 5       ─►  pick those
   0-4         ─►  pick 0 through 4
   0,2,5-7     ─►  combine
   (blank)     ─►  pick all
```

---

## All options

```text
ARGUMENTS
  EXTENSIONS...      Extensions to collect (e.g. py ts md). Omit to be prompted.

OPTIONS
  -r, --root PATH        Directory to scan (default: cwd)
  -a, --all              Select every matching file, skip the picker
  -o, --output PATH      Output file (default: ./collected.<ext>)
  -f, --format FMT       md | txt | xml | json (default: md)
  -c, --copy             Copy to clipboard instead of writing a file
      --open             Open the output in your default app afterwards
  -x, --exclude GLOB     Exclude glob (repeatable): -x 'tests/**' -x '*.snap'
  -i, --include GLOB     Require glob (repeatable)
      --max-size BYTES   Skip files larger than this (default: 1_000_000)
      --no-gitignore     Ignore .gitignore rules
      --no-tree          Skip the file tree header
      --tokens           Estimate token count
  -q, --quiet            Suppress non-essential output
  -v, --version          Print version
```

---

## Output formats

### Markdown (default)
Best for human-readable bundles and LLM prompts:

````markdown
## `src/auth.py`

```python
def login(): ...
```
````

### XML
Recommended for Claude and other LLMs that parse multi-file context cleanly:

```xml
<files>
  <file path="src/auth.py" size="42">
def login(): ...
  </file>
</files>
```

### JSON
For piping into other tools.

### Text
Legacy plain-text format with `// path:` separators.

---

## Project structure

```
file-collector/
├── pyproject.toml          ← modern packaging (hatchling)
├── README.md
├── LICENSE
├── src/collector/
│   ├── __init__.py
│   ├── __main__.py         ← enables `python -m collector`
│   ├── cli.py              ← Typer-based CLI with Rich output
│   ├── config.py           ← dataclass config + language map
│   ├── discovery.py        ← file walking + .gitignore + binary skip
│   ├── formatters.py       ← md / txt / xml / json renderers
│   ├── platform_utils.py   ← clipboard + open helpers
│   └── tokens.py           ← optional tiktoken counting
└── tests/
    └── test_collector.py   ← 25 tests
```

---

## Development

```bash
git clone git@github.com:4tocall/File-Collector-Script.git
cd File-Collector-Script
pip install -e ".[dev,tokens]"
pytest
ruff check .
```

---

## Changelog

### v0.2.0 — full refactor
- Restructure into a proper Python package under `src/`
- Replace argparse with Typer, plain prints with Rich
- Auto-skip binary files (no more crashes on `.png`)
- Respect `.gitignore` by default
- Add Markdown / XML / JSON output formats with language fences
- Add token counting via `tiktoken` (optional dependency)
- Add glob include / exclude patterns (`--exclude 'tests/**'`)
- Replace alias setup with `pyproject.toml` entry point
- Add test suite (25 tests)
- UTF-8 everywhere with safe fallbacks

### v0.1.0
Original single-file script — still available at `git checkout v0.1.0`.

---

<div align="center">

**MIT License** — see [LICENSE](LICENSE)

Made with ☕ by [4tocall](https://github.com/4tocall)

</div>
