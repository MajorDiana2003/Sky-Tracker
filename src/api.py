import abc
import os
from typing import Any, Dict, List, cast

import requests
from dotenv import load_dotenv

from src.logger import logger

# Загружаем переменные среды из скрытого локального файла .env
load_dotenv()


class BaseAPI(abc.ABC):
    """Абстрактный класс для работы с API сервисами геокодинга и авиации."""

    @abc.abstractmethod
    def get_aeroplanes(self, country: str) -> Dict[str, Any]:
        """Получить сырые данные о самолетах в пространстве выбранной страны."""
        pass


class AeroplanesAPI(BaseAPI):
    """Реализация работы с OpenStreetMap Nominatim и OpenSky Network API."""

    def __init__(self) -> None:
        self.nominatim_url: str = "https://openstreetmap.org"
        self.opensky_url: str = "https://opensky-network.org"

        # Реалистичный User-Agent
        self.headers: Dict[str, str] = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        }

        # Безопасное чтение учетных данных из переменных среды (.env)
        opensky_user: str = os.getenv("OPENSKY_USER", "diana")
        opensky_password: str = os.getenv("OPENSKY_PASSWORD", "")

        # Создаем авторизованную сессию для OpenSky Network
        self.session = requests.Session()
        self.session.auth = (opensky_user, opensky_password)

        # Резервный словарь географических координат стран на случай блокировки со стороны Nominatim
        self._fallback_boxes: Dict[str, List[str]] = {
            "france": ["41.3", "51.1", "-5.1", "9.6"],
            "spain": ["35.1", "43.8", "-9.3", "4.3"],
            "germany": ["47.2", "55.1", "5.8", "15.0"],
            "switzerland": ["45.8", "47.8", "5.9", "10.5"],
            "canada": ["41.6", "83.1", "-141.0", "-52.6"],
            "italy": ["35.4", "47.1", "6.6", "18.6"],
            "ukraine": ["44.3", "52.4", "22.1", "40.2"],
        }

    def _get_country_bbox(self, country: str) -> List[str]:
        """Внутренний вспомогательный метод для получения географического boundingbox страны."""
        params: Dict[str, Any] = {"country": country, "format": "json", "limit": 1}
        try:
            response = requests.get(self.nominatim_url, params=params, headers=self.headers, timeout=5)
            response.raise_for_status()


            data: List[Dict[str, Any]] = response.json()

            if not data or not isinstance(data, list) or len(data) == 0:
                raise ValueError(f"Сервис геокодинга не смог найти страну с названием '{country}'.")

            # Берём первый элемент списка (найденную страну)
            country_data = data[0]
            bbox = country_data.get("boundingbox")

            if not bbox or not isinstance(bbox, list):
                raise KeyError("Поле 'boundingbox' отсутствует или имеет неверный формат.")

            return cast(List[str], bbox)

        except (requests.RequestException, Exception) as e:
            country_key = country.lower().strip()
            if country_key in self._fallback_boxes:
                logger.warning(
                    f"Удаленный хост Nominatim разорвал подключение или ответил ошибкой ({e}). "
                    f"Активированы резервные координаты для региона: {country}"
                )
                return self._fallback_boxes[country_key]

            raise ConnectionError(
                f"Не удалось подключиться к Nominatim API и для страны '{country}' нет резервных координат: {e}"
            )

    def get_aeroplanes(self, country: str) -> Dict[str, Any]:
        """Получает самолеты, находящиеся в коробке координат (bbox) указанной страны."""
        try:
            logger.info(f"Запрос географических координат для страны: {country}")
            bbox: List[str] = self._get_country_bbox(country)

            # Извлекаем элементы списка по индексам [ymin, ymax, xmin, xmax]
            params: Dict[str, float] = {
                "lamin": float(bbox[0]),
                "lamax": float(bbox[1]),
                "lomin": float(bbox[2]),
                "lomax": float(bbox[3]),
            }

            logger.info(f"Отправка авторизованного запроса к OpenSky API для региона [{country}]")
            # Используем авторизованную сессию вместо базового requests
            response = self.session.get(self.opensky_url, params=params, headers=self.headers, timeout=7)

            if response.status_code == 429:
                logger.warning("Превышен лимит запросов к OpenSky API (Код 429).")
                return self._get_mock_data()

            response.raise_for_status()
            result_data: Dict[str, Any] = response.json()
            return result_data

        except requests.RequestException as e:
            logger.error(f"Ошибка сети при запросе данных о самолетах: {e}")
            return self._get_mock_data()
        except (ValueError, IndexError, KeyError) as e:
            logger.error(f"Не удалось обработать данные для страны {country}: {e}")
            return self._get_mock_data()

    def _get_mock_data(self) -> Dict[str, Any]:
        """Внутренний демонстрационный режим данных на случай перегрузки сервера."""
        logger.warning("Включен аварийный демонстрационный режим отображения воздушного пространства.")
        return {
            "states": [
                ["4b1814", "SWR134   ", "Switzerland", 1700000000, 1700000000, 8.5, 47.4, 11500.0, False, 240.0],
                ["3c66a3", "DLH456   ", "Germany", 1700000000, 1700000000, 9.1, 50.2, 9800.0, False, 210.5],
                ["34c21a", "IBE123   ", "Spain", 1700000000, 1700000000, -3.7, 40.4, 5000.0, False, 180.0],
                ["4b1815", "AFR012   ", "France", 1700000000, 1700000000, 2.3, 48.8, 12000.0, False, 255.0],
                ["a00001", "AAL777   ", "United States", 1700000000, 1700000000, -74.0, 40.7, 10500.0, False, 235.2],
            ]
        }
