"""
The documentation's code: the examples under docs/examples run (they need no hardware), and every Python block of the
pages and the README parses and imports names that exist, so API changes can't silently leave the docs behind.
"""

import ast
import importlib
import re
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = sorted((ROOT / 'docs' / 'examples').glob('*.py'))
PAGES = sorted((ROOT / 'docs').rglob('*.md')) + [ROOT / 'README.md']
BLOCK = re.compile(r'```python\n(.*?)```', re.DOTALL)


def python_blocks():
    for page in PAGES:
        for number, block in enumerate(BLOCK.findall(page.read_text()), 1):
            if '--8<--' not in block:  # snippet includes are the examples, run below
                yield pytest.param(block, id='%s-%d' % (page.relative_to(ROOT), number))


@pytest.mark.parametrize('example', EXAMPLES, ids=[example.name for example in EXAMPLES])
def test_example_runs(example, capsys):
    runpy.run_path(str(example), run_name='__main__')


@pytest.mark.parametrize('block', python_blocks())
def test_code_block_is_valid(block):
    tree = ast.parse(block)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.split('.')[0] == 'enocean':
            if node.module == 'enocean.prometheus':
                pytest.importorskip('prometheus_client')
            module = importlib.import_module(node.module)
            for alias in node.names:
                assert hasattr(module, alias.name), 'from %s import %s: no such name' % (node.module, alias.name)


def test_snippets_exist():
    for page in PAGES:
        # A formatter rewriting --8<-- "x" as Python (--8 < --'x') would silently drop the example
        assert not re.search(r'--8\s+<', page.read_text()), '%s: mangled snippet marker' % page
        for name in re.findall(r'--8<-- "([^"]+)"', page.read_text()):
            assert (ROOT / 'docs' / 'examples' / name).exists() or (ROOT / name).exists(), name
