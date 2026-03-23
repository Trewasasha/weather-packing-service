import subprocess
import threading
import time
import signal
import sys

def run_cities_mock():
    """Запуск заглушки Cities API"""
    try:
        subprocess.run([
            "uvicorn",
            "tests.mocks.cities_api_mock:mock_app",
            "--host", "0.0.0.0",
            "--port", "8081",
            "--reload"
        ])
    except KeyboardInterrupt:
        pass

def run_weather_mock():
    """Запуск заглушки Weather API"""
    try:
        subprocess.run([
            "uvicorn",
            "tests.mocks.weather_api_mock:mock_app",
            "--host", "0.0.0.0",
            "--port", "8082",
            "--reload"
        ])
    except KeyboardInterrupt:
        pass

def signal_handler(sig, frame):
    """Обработчик сигнала для корректного завершения"""
    print("\nОстановка заглушек...")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)

    print("Запуск заглушек API для тестирования")

    # Создаем и запускаем потоки
    cities_thread = threading.Thread(target=run_cities_mock, name="CitiesMock")
    weather_thread = threading.Thread(target=run_weather_mock, name="WeatherMock")

    cities_thread.daemon = True
    weather_thread.daemon = True

    cities_thread.start()
    weather_thread.start()

    print("\nЗаглушки запущены:")
    print("  Cities API Mock: http://localhost:8081")
    print("  Weather API Mock: http://localhost:8082")
    print("\nДоступные эндпоинты:")
    print("  • Cities API: http://localhost:8081/cities/api/v3/cities?q=LHR")
    print("  • Weather API: http://localhost:8082/v1/forecast?latitude=51.47&longitude=-0.45&daily=temperature_2m_max&start_date=2026-03-13&end_date=2026-03-13")
    print("\nНажмите Ctrl+C для остановки всех заглушек")
    print("=" * 60)

    try:

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nОстановка заглушек...")
        sys.exit(0)