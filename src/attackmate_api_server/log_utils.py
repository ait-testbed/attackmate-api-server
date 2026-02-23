import datetime
import logging
import os
import sys
from collections import deque
from colorlog import ColoredFormatter
from contextlib import contextmanager
from typing import Any, Generator, List, Optional, Deque, Dict
from attackmate_api_server.config import settings

LOG_DIR = os.path.abspath(settings.log_dir)
TARGET_LOGGER_NAMES = ['playbook', 'output', 'json']
API_CONSOLE_FORMAT = '  %(asctime)s %(log_color)s%(levelname)-8s%(reset)s | API | %(log_color)s%(message)s%(reset)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

api_logger = logging.getLogger('attackmate_api')
    # Console handler for API logs
instance_log_formatter = logging.Formatter(
    '%(asctime)s %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
json_log_formatter = logging.Formatter('%(message)s')

def initialize_api_logger(debug: bool, append_logs: bool) -> logging.Logger:
    api_logger = logging.getLogger('attackmate_api')
    api_logger.setLevel(logging.DEBUG if debug else logging.INFO)

    if not has_stdout_handler(api_logger):
        console_handler = logging.StreamHandler(sys.stdout)
        formatter = ColoredFormatter(API_CONSOLE_FORMAT, datefmt=DATE_FORMAT)
        console_handler.setFormatter(formatter)
        api_logger.addHandler(console_handler)

    api_logger.propagate = False
    return api_logger

def has_stdout_handler(logger: logging.Logger) -> bool:
    return any(
        isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout
        for handler in logger.handlers
    )

class InMemoryLogHandler(logging.Handler):
    """
    Captures log records into a deque for returning to the client.
    """

    def __init__(self, formatter: logging.Formatter):
        super().__init__()
        self.records: Deque[str] = deque()
        self.setFormatter(formatter)

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(self.format(record))

    def get_logs(self) -> List[str]:
        logs = list(self.records)
        return logs


@contextmanager
def instance_logging(
    instance_id: str,
    write_playbook_logs_to_disk: bool,
    log_level: int = logging.INFO
) -> Generator[Dict[str, Any], None, None]:
    """
    Context manager for per-instance logging.
    Always captures logs in-memory to return to the client.
    Only writes to disk if write_playbook_logs_to_disk=True.
    Yields a dict with keys: 'log_files' (List[Optional[str]]) and 'handlers_ref' (InMemoryLogHandler per logger).
    """
    file_handlers: List[logging.FileHandler] = []
    log_files: List[Optional[str]] = [None, None, None]  # [attackmate, output, json]

    # In-memory handlers — always created
    mem_map: Dict[str, InMemoryLogHandler] = {
        'playbook': InMemoryLogHandler(instance_log_formatter),
        'output': InMemoryLogHandler(instance_log_formatter),
        'json': InMemoryLogHandler(json_log_formatter),
    }

    try:
        file_map: Dict[str, logging.FileHandler] = {}
        # if write_playbook_logs_to_disk=True logs will be written to disk
        if write_playbook_logs_to_disk:
            os.makedirs(LOG_DIR, exist_ok=True)
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            paths = {
                'playbook': os.path.join(LOG_DIR, f"{timestamp}_{instance_id}_attackmate.log"),
                'output':   os.path.join(LOG_DIR, f"{timestamp}_{instance_id}_output.log"),
                'json':     os.path.join(LOG_DIR, f"{timestamp}_{instance_id}_attackmate.json"),
            }
            formatters = {
                'playbook': instance_log_formatter,
                'output':   instance_log_formatter,
                'json':     json_log_formatter,
            }
            log_files = [paths['playbook'], paths['output'], paths['json']]

            for name, path in paths.items():
                file_handler = logging.FileHandler(path, mode='a')
                file_handler.setFormatter(formatters[name])
                file_handler.setLevel(log_level)
                file_map[name] = file_handler
                file_handlers.append(file_handler)

        # Attach handlers to target loggers
        for logger_name in TARGET_LOGGER_NAMES:
            logger = logging.getLogger(logger_name)
            logger.setLevel(log_level)
            logger.propagate = False
            if mem_map[logger_name] not in logger.handlers:
                logger.addHandler(mem_map[logger_name])
            if write_playbook_logs_to_disk:
                logger.addHandler(file_map[logger_name])

            api_logger.info(
                f"Instance '{instance_id}': logging set up for '{logger_name}' "
                f"[in-memory=True, file={write_playbook_logs_to_disk}]"
            )

        yield {
            'log_files': log_files,          # paths or None — for response metadata
            'mem_handlers': mem_map,          # access .get_logs() after the block
        }

    except Exception as e:
        api_logger.error(f"Error setting up instance logging for '{instance_id}': {e}", exc_info=True)
        yield {'log_files': [], 'mem_handlers': {}}

    finally:
        for logger_name in TARGET_LOGGER_NAMES:
                logger = logging.getLogger(logger_name)

                mem_h = mem_map.get(logger_name)
                if mem_h:
                    logger.removeHandler(mem_h)

                for handler in list(logger.handlers): 
                    if isinstance(handler, logging.FileHandler):
                        logger.removeHandler(handler)

        for handler in file_handlers:
            try:
                handler.close()
            except Exception as e:
                api_logger.error(
                    f"Error closing file handler for '{instance_id}': {e}", exc_info=True)
        api_logger.info(f"Instance log handlers removed for '{instance_id}'.")