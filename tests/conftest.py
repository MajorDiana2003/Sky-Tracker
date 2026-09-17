from typing import Any, Dict

import pytest


@pytest.fixture
def sample_aeroplane_data() -> Dict[str, Any]:
    """Фикстура с корректными данными для словаря самолета."""
    return {
        "icao24": "34c21a",
        "callsign": "IBE123",
        "origin_country": "Spain",
        "velocity": 250.5,
        "baro_altitude": 11000.0,
    }


@pytest.fixture
def mock_api_response() -> Dict[str, Any]:
    """Фикстура, имитирующая сырой ответ от OpenSky REST API."""
    return {
        "time": 1700000000,
        "states": [
            ["4b1814", "SWR134J ", "Switzerland", 1700000000, 1700000000, 8.5, 47.4, 9500.0, False, 210.0],
            ["3c66a3", "DLH456  ", "Germany", 1700000000, 1700000000, 9.1, 50.2, 11000.0, False, 240.5],
            ["34c21a", "IBE123   ", "Spain", 1700000000, 1700000000, -3.7, 40.4, 5000.0, False, 180.0],
            ["4b1815", "SWR999  ", "Switzerland", 1700000000, 1700000000, 8.6, 47.5, 9500.0, False, 190.0],
        ],
    }
