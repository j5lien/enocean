import json
import logging
import logging.handlers

import pytest

from enocean.consolelogger import init_logging


@pytest.fixture
def enocean_logger():
    logger = logging.getLogger('enocean')
    handlers, level = logger.handlers[:], logger.level
    yield logger
    for handler in logger.handlers[len(handlers) :]:
        handler.close()
    logger.handlers[:], logger.level = handlers, level


def test_logs_to_console(enocean_logger, capsys):
    init_logging(level=logging.INFO)

    logging.getLogger('enocean.test').info('hello')

    assert enocean_logger.level == logging.INFO
    assert 'enocean.test - INFO - hello' in capsys.readouterr().err


def test_logs_to_rotating_file(enocean_logger, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    init_logging(level=logging.WARNING, log_to_file=True)

    logging.getLogger('enocean.test').warning('to file')
    logging.getLogger('enocean.test').info('filtered out')

    assert any(isinstance(h, logging.handlers.RotatingFileHandler) for h in enocean_logger.handlers)
    content = (tmp_path / 'enocean.log').read_text()
    assert 'to file' in content and 'filtered out' not in content


def test_json_format_includes_structured_fields(enocean_logger, capsys):
    init_logging(level=logging.INFO, json_format=True)

    logging.getLogger('enocean.test').info('received %s', 'x', extra={'sender': '01:02:03:04', 'rorg': 0xA5})
    try:
        raise ValueError('boom')
    except ValueError:
        logging.getLogger('enocean.test').exception('failed')

    first, second = (json.loads(line) for line in capsys.readouterr().err.splitlines())
    assert first['message'] == 'received x'
    assert first['level'] == 'INFO'
    assert first['logger'] == 'enocean.test'
    assert first['sender'] == '01:02:03:04' and first['rorg'] == 0xA5
    assert 'time' in first and 'args' not in first
    assert 'ValueError: boom' in second['exception']
