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
