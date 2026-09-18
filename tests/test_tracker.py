from typing import Any, Dict, List

import pytest


from main import filter_aeroplanes, get_aeroplanes_by_altitude, get_top_aeroplanes, sort_aeroplanes
from src.aeroplane import Aeroplane
from src.api import AeroplanesAPI
from src.saver import JSONSaver

# ==========================================
# ТЕСТЫ ДЛЯ КЛАССА AEROPLANE
# ==========================================


def test_aeroplane_creation_and_validation(sample_aeroplane_data: Dict[str, Any]) -> None:
    plane = Aeroplane(
        icao24=sample_aeroplane_data["icao24"],
        origin_country=sample_aeroplane_data["origin_country"],
        velocity=sample_aeroplane_data["velocity"],
        baro_altitude=sample_aeroplane_data["baro_altitude"],
        callsign=sample_aeroplane_data["callsign"],
    )
    assert plane.icao24 == "34c21a"
    assert plane.callsign == "IBE123"
    assert plane.velocity == 250.5


def test_aeroplane_validation_none_values() -> None:
    plane = Aeroplane(icao24="12345", origin_country="Unknown", velocity=None, baro_altitude=None, callsign=None)
    assert plane.callsign == "UNKNOWN"
    assert plane.velocity == 0.0
    assert plane.baro_altitude == 0.0


def test_aeroplane_validation_type_error() -> None:
    with pytest.raises(TypeError):
        Aeroplane(icao24="1", origin_country="X", velocity="fast", baro_altitude=1000.0)  # type: ignore


def test_aeroplane_serialization(sample_aeroplane_data: Dict[str, Any]) -> None:
    plane = Aeroplane.from_dict(sample_aeroplane_data)
    assert plane.icao24 == "34c21a"

    serialized = plane.to_dict()
    assert serialized["velocity"] == 250.5


def test_aeroplane_comparison() -> None:
    plane_low = Aeroplane("1", "Country", velocity=200.0, baro_altitude=5000.0)
    plane_high = Aeroplane("2", "Country", velocity=200.0, baro_altitude=10000.0)
    plane_equal = Aeroplane("3", "Country", velocity=200.0, baro_altitude=5000.0)

    assert plane_low < plane_high
    assert plane_high > plane_low
    assert plane_low == plane_equal


def test_cast_to_object_list(mock_api_response: Dict[str, Any]) -> None:
    planes = Aeroplane.cast_to_object_list(mock_api_response)
    assert len(planes) == 4
    assert planes[0].icao24 == "4b1814"


def test_cast_to_object_list_empty() -> None:
    assert Aeroplane.cast_to_object_list(None) == []
    assert Aeroplane.cast_to_object_list({}) == []
    assert Aeroplane.cast_to_object_list({"states": None}) == []


# ==========================================
# ТЕСТЫ ДЛЯ СЕРВИСА API И СОХРАНЕНИЯ (ПОВЫШЕНИЕ ПОКРЫТИЯ)
# ==========================================


def test_api_fallback_mechanism() -> None:
    """Проверка, что при ошибке сети API переключается на резервные координаты."""
    api = AeroplanesAPI()
    # Передаем заведомо несуществующую страну, чтобы вызвать ошибку, или проверяем перехват
    with pytest.raises(ConnectionError):
        api._get_country_bbox("NonExistentCountry")

    # Проверяем работу fallback для Франции (метод должен вернуть координаты из словаря при ошибке)
    bbox = api._get_country_bbox("France")
    assert isinstance(bbox, list)
    assert len(bbox) == 4


def test_json_saver_operations(tmp_path: Any, sample_aeroplane_data: Dict[str, Any]) -> None:
    """Тестирование сохранения и удаления файлов в изолированной временной папке."""
    test_file = tmp_path / "test_airplanes.json"
    saver = JSONSaver(filepath=str(test_file))

    plane = Aeroplane.from_dict(sample_aeroplane_data)

    # Тест добавления
    saver.add_aeroplane(plane)
    assert len(saver._read()) == 1

    # Тест удаления
    saver.delete_aeroplane(plane)
    assert len(saver._read()) == 0


# ==========================================
# ТЕСТЫ ДЛЯ ФУНКЦИЙ ОБРАБОТКИ ДАННЫХ (MAIN)
# ==========================================


def test_filter_aeroplanes(mock_api_response: Dict[str, Any]) -> None:
    planes = Aeroplane.cast_to_object_list(mock_api_response)
    filtered = filter_aeroplanes(planes, "Germany")
    assert len(filtered) == 1

    filtered_multi = filter_aeroplanes(planes, "Spain, Switzerland")
    assert len(filtered_multi) == 3


def test_get_aeroplanes_by_altitude(mock_api_response: Dict[str, Any]) -> None:
    planes = Aeroplane.cast_to_object_list(mock_api_response)
    ranged = get_aeroplanes_by_altitude(planes, "4000 - 6000")
    assert len(ranged) == 1

    bad_ranged = get_aeroplanes_by_altitude(planes, "сломанный_диапазон")
    assert len(bad_ranged) == len(planes)


def test_sort_and_top_aeroplanes(mock_api_response: Dict[str, Any]) -> None:
    planes = Aeroplane.cast_to_object_list(mock_api_response)
    sorted_planes = sort_aeroplanes(planes)
    assert sorted_planes[0].baro_altitude == 11000.0

    top_2 = get_top_aeroplanes(sorted_planes, 2)
    assert len(top_2) == 2


# ==========================================
# ТЕСТЫ ДЛЯ CLI ИНТЕРФЕЙСА (ДЛЯ ПОДНЯТИЯ COVERAGE)
# ==========================================


def test_main_print_aeroplanes_empty() -> None:
    """Проверка вывода, если список самолетов пуст."""
    from main import print_aeroplanes


    print_aeroplanes([])


def test_user_interaction_empty_country(monkeypatch: Any) -> None:
    """Тестирование выхода из CLI, если пользователь ввел пустую строку."""
    import main

    # Симулируем, что пользователь нажал Enter (ввел пустую строку)
    monkeypatch.setattr("builtins.input", lambda _: "")

    # Перехватываем системный выход sys.exit(0)
    with pytest.raises(SystemExit) as sample_exit:
        main.user_interaction()

    assert sample_exit.value.code == 0


def test_main_helpers_coverage(mock_api_response: Dict[str, Any]) -> None:
    """Дополнительный тест функций main для гарантированного покрытия >70%."""
    from main import Aeroplane, filter_aeroplanes, get_aeroplanes_by_altitude

    planes = Aeroplane.cast_to_object_list(mock_api_response)

    # Тестируем передачу пустых строк в фильтры
    assert len(filter_aeroplanes(planes, "")) == len(planes)
    assert len(get_aeroplanes_by_altitude(planes, "")) == len(planes)
