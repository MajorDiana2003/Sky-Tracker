import abc
import json
import os
from typing import Any, Dict, List

from src.aeroplane import Aeroplane
from src.logger import logger


class BaseSaver(abc.ABC):
    """Абстрактный класс для работы с файлами (хранилищами данных)."""

    @abc.abstractmethod
    def add_aeroplane(self, aeroplane: Aeroplane) -> None:
        pass

    @abc.abstractmethod
    def delete_aeroplane(self, aeroplane: Aeroplane) -> None:
        pass


class JSONSaver(BaseSaver):
    """Класс для сохранения, удаления и чтения данных в формате JSON."""

    def __init__(self, filepath: str = "data/airplanes.json") -> None:
        self.filepath: str = filepath
        dir_name = os.path.dirname(self.filepath)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        if not os.path.exists(self.filepath):
            self._write([])
            logger.info(f"Создан новый файл базы данных: {self.filepath}")

    def _read(self) -> List[Dict[str, Any]]:
        """Внутренний метод для чтения сырых данных из JSON файла."""
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                return []
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"Ошибка при чтении JSON-файла {self.filepath}: {e}. База будет перезаписана.")
            return []

    def _write(self, data: List[Dict[str, Any]]) -> None:
        """Внутренний метод для записи данных в JSON файл."""
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except IOError as e:
            logger.error(f"Критическая ошибка записи в файл {self.filepath}: {e}")

    def add_aeroplane(self, aeroplane: Aeroplane) -> None:
        """Добавляет самолет в локальную базу данных, избегая дубликатов по ICAO24."""
        data = self._read()
        data = [item for item in data if item.get("icao24") != aeroplane.icao24]
        data.append(aeroplane.to_dict())
        self._write(data)

    def delete_aeroplane(self, aeroplane: Aeroplane) -> None:
        """Удаляет самолет из базы данных по его объекту."""
        data = self._read()
        initial_count = len(data)
        data = [item for item in data if item.get("icao24") != aeroplane.icao24]

        if len(data) < initial_count:
            self._write(data)
            logger.info(f"Самолет с кодом ICAO {aeroplane.icao24} успешно удален из базы.")
        else:
            logger.warning(f"Самолет с кодом ICAO {aeroplane.icao24} не найден в базе данных.")
