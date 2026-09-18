import sys
from typing import List

from src.aeroplane import Aeroplane
from src.api import AeroplanesAPI
from src.logger import logger
from src.saver import JSONSaver


def filter_aeroplanes(aeroplanes: List[Aeroplane], filter_words: str) -> List[Aeroplane]:
    """Фильтрация списка самолетов по стране их регистрации (регистронезависимо)."""
    if not filter_words.strip():
        return aeroplanes

    countries: List[str] = [c.strip().lower() for c in filter_words.replace(",", " ").split() if c.strip()]

    result = [plane for plane in aeroplanes if plane.origin_country.lower() in countries]
    logger.info(f"После фильтрации по странам регистрации осталось: {len(result)}")
    return result


def get_aeroplanes_by_altitude(aeroplanes: List[Aeroplane], altitude_range: str) -> List[Aeroplane]:
    """Фильтрация списка по диапазону высот полета (например, '1000 - 5000')."""
    if not altitude_range.strip():
        return aeroplanes

    try:
        parts: List[str] = altitude_range.split("-")
        if len(parts) != 2:
            raise ValueError("Диапазон должен содержать дефис")

        min_alt: float = float(parts[0].strip())
        max_alt: float = float(parts[1].strip())

        result = [plane for plane in aeroplanes if min_alt <= plane.baro_altitude <= max_alt]
        logger.info(f"После фильтрации по высоте ({altitude_range} м) осталось: {len(result)}")
        return result

    except (ValueError, IndexError):
        logger.warning("Некорректный формат диапазона высот. Фильтрация по высоте пропущена.")
        return aeroplanes


def sort_aeroplanes(aeroplanes: List[Aeroplane]) -> List[Aeroplane]:
    """Сортировка самолетов по убыванию характеристик (DESC)."""
    return sorted(aeroplanes, reverse=True)


def get_top_aeroplanes(aeroplanes: List[Aeroplane], top_n: int) -> List[Aeroplane]:
    """Получение первых N элементов списка."""
    return aeroplanes[:top_n]


def print_aeroplanes(aeroplanes: List[Aeroplane]) -> None:
    """Человекочитаемый вывод списка самолетов в консоль."""
    if not aeroplanes:
        logger.info("Список самолетов пуст.")
        return

    for index, plane in enumerate(aeroplanes, start=1):
        print(f"{index}. {plane}")


def user_interaction() -> None:
    """Основной сценарий взаимодействия с пользователем (CLI интерфейс)."""
    logger.info("Инициализация сервисов авиатрекера...")
    api: AeroplanesAPI = AeroplanesAPI()
    json_saver: JSONSaver = JSONSaver()

    print("\n=== Добро пожаловать в Систему Мониторинга Самолетов ===")

    country: str = input("Введите название страны на английском (например, France): ").strip()
    if not country:
        logger.warning("Название страны не может быть пустым.")
        sys.exit(0)

    raw_data = api.get_aeroplanes(country)
    aeroplanes: List[Aeroplane] = Aeroplane.cast_to_object_list(raw_data)
    logger.info(f"Успешно обработано объектов в небе: {len(aeroplanes)}")

    if not aeroplanes:
        logger.warning(f"В настоящее время в небе над {country} нет активных бортов.")
        return

    # Сохраняем лаконично (без спама сотен строк)
    logger.info(f"Синхронизация {len(aeroplanes)} бортов с локальной базой данных JSON...")
    for plane in aeroplanes:
        json_saver.add_aeroplane(plane)
    logger.info("Данные успешно сохранены.")

    print("\n--- Настройка параметров отображения результатов ---")
    try:
        top_n_input = input("Введите количество самолетов для вывода в ТОП (по умолчанию 10): ").strip()
        top_n: int = int(top_n_input) if top_n_input else 10
    except ValueError:
        top_n = 10
        logger.warning("Некорректный ввод. Установлено значение: 10")

    filter_words: str = input("Фильтр по странам регистрации судна (через запятую или пусто): ").strip()
    altitude_range: str = input("Диапазон высот полета в метрах (Пример: 5000 - 12000 или пусто): ").strip()

    filtered: List[Aeroplane] = filter_aeroplanes(aeroplanes, filter_words)
    ranged: List[Aeroplane] = get_aeroplanes_by_altitude(filtered, altitude_range)
    sorted_list: List[Aeroplane] = sort_aeroplanes(ranged)
    top_results: List[Aeroplane] = get_top_aeroplanes(sorted_list, top_n)

    print(f"\n=== ТОП {len(top_results)} САМОЛЕТОВ В НЕБЕ НАД РЕГИОНОМ {country.upper()} ===")
    print_aeroplanes(top_results)


if __name__ == "__main__":
    try:
        user_interaction()
    except KeyboardInterrupt:
        print("\n")
        logger.info("Программа завершена пользователем.")
