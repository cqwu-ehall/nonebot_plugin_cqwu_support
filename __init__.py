import pkgutil
from pathlib import Path

from .data import cqwu_data

__all__ = ["cqwu_data"]

FILE_PATH = Path(__file__).parent.absolute()

for _, file, _ in pkgutil.iter_modules([str(FILE_PATH)]):
    __import__(file, globals(), level=1)
