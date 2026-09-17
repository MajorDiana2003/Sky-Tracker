from typing import Any, Dict, List, Optional


class Aeroplane:
    """Класс, представляющий самолет (с валидацией и методами сравнения)."""

    def __init__(
        self,
        icao24: str,
        origin_country: str,
        velocity: Optional[float],
        baro_altitude: Optional[float],
        callsign: Optional[str] = "UNKNOWN",
    ) -> None:
        self.icao24: str = icao24.strip() if icao24 else "UNKNOWN"
        self.callsign: str = callsign.strip() if callsign else "UNKNOWN"
        self.origin_country: str = origin_country.strip() if origin_country else "UNKNOWN"

        self.velocity: float = self._validate_numeric(velocity)
        self.baro_altitude: float = self._validate_numeric(baro_altitude)

    @staticmethod
    def _validate_numeric(value: Optional[float]) -> float:
        """Внутренний метод валидации. Если API вернул None, ставит 0.0."""
        if value is None:
            return 0.0
        if not isinstance(value, (int, float)):
            raise TypeError("Скорость и высота полета должны быть числовыми значениями.")
        return float(value)

    def __lt__(self, other: Any) -> bool:
        """Магический метод сравнения 'меньше чем' (<) по высоте, затем по скорости."""
        if not isinstance(other, Aeroplane):
            return NotImplemented
        if self.baro_altitude == other.baro_altitude:
            return self.velocity < other.velocity
        return self.baro_altitude < other.baro_altitude

    def __eq__(self, other: Any) -> bool:
        """Магический метод сравнения 'равно' (==)."""
        if not isinstance(other, Aeroplane):
            return NotImplemented
        return self.baro_altitude == other.baro_altitude and self.velocity == other.velocity

    @classmethod
    def cast_to_object_list(cls, api_response: Optional[Dict[str, Any]]) -> List["Aeroplane"]:
        """Преобразование сырого ответа OpenSky REST API в список объектов класса Aeroplane."""
        objects: List[Aeroplane] = []
        if not api_response or "states" not in api_response or api_response["states"] is None:
            return objects

        raw_states = api_response["states"]
        if not isinstance(raw_states, list):
            return objects

        for state in raw_states:
            try:
                if not isinstance(state, list) or len(state) < 10:
                    continue

                # Извлекаем значения по индексам OpenSky API с явным приведением типов для mypy
                icao = str(state[0]) if state[0] is not None else ""
                callsign = str(state[1]).strip() if state[1] is not None else "UNKNOWN"
                origin_country = str(state[2]) if state[2] is not None else "UNKNOWN"
                altitude = float(state[7]) if state[7] is not None else None
                velocity = float(state[9]) if state[9] is not None else None

                obj = cls(
                    icao24=icao,
                    callsign=callsign,
                    origin_country=origin_country,
                    baro_altitude=altitude,
                    velocity=velocity,
                )
                objects.append(obj)
            except (IndexError, TypeError, ValueError):
                continue
        return objects

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование объекта в словарь для сохранения в JSON."""
        return {
            "icao24": self.icao24,
            "callsign": self.callsign,
            "origin_country": self.origin_country,
            "velocity": self.velocity,
            "baro_altitude": self.baro_altitude,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Aeroplane":
        """Восстановление объекта Aeroplane из словаря."""
        return cls(
            icao24=str(data.get("icao24", "")),
            origin_country=str(data.get("origin_country", "")),
            velocity=data.get("velocity") if data.get("velocity") is not None else None,
            baro_altitude=data.get("baro_altitude") if data.get("baro_altitude") is not None else None,
            callsign=str(data.get("callsign", "UNKNOWN")),
        )

    def __str__(self) -> str:
        """Пользовательское строковое представление для вывода на экран."""
        return (
            f"Рейс: {self.callsign:8} | ICAO: {self.icao24} | "
            f"Рег: {self.origin_country:15} | "
            f"Высота: {self.baro_altitude:7.1f}м | Скорость: {self.velocity:5.1f} м/с"
        )
