#!/usr/bin/env python3
import os
import sys
import subprocess
import time
from pathlib import Path


def run_command(command, cwd=None, shell=True):
    """Запускает команду и возвращает процесс"""
    print(f"Запускаем: {command}")
    return subprocess.Popen(command, cwd=cwd, shell=shell)


def main():
    # Получаем текущую директорию скрипта (backend/src)
    script_dir = Path(__file__).parent

    # Поднимаемся на два уровня вверх к корню проекта
    base_dir = script_dir.parent.parent

    # Правильные пути
    frontend_dir = base_dir / "frontend"
    backend_dir = script_dir  # backend/src где находится manage.py

    print(f"Корень проекта: {base_dir}")
    print(f"Frontend: {frontend_dir}")
    print(f"Backend: {backend_dir}")

    # Проверяем существование папок
    if not frontend_dir.exists():
        print(f"Папка frontend не найдена: {frontend_dir}")
        return

    if not backend_dir.exists():
        print(f"Папка backend не найдена: {backend_dir}")
        return

    # Проверяем существование manage.py
    manage_py = backend_dir / "manage.py"
    if not manage_py.exists():
        print(f"manage.py не найден: {manage_py}")
        return

    print("✅ Все пути проверены успешно!")

    # Запускаем Django
    print("\n🐍 Запускаем Django сервер...")
    django_process = run_command("python manage.py runserver", cwd=str(backend_dir))

    # Даем Django время на запуск
    print("⏳ Ждем запуска Django...")
    time.sleep(5)

    # Запускаем React
    print("\n⚛️  Запускаем React сервер...")
    react_process = run_command("npm start", cwd=str(frontend_dir))

    print("\n🎉 Оба сервера запущены!")
    print("📱 React: http://localhost:3000")
    print("🐍 Django: http://localhost:8000")
    print("⏹️  Нажмите Ctrl+C для остановки")

    try:
        # Ждем завершения процессов
        django_process.wait()
        react_process.wait()
    except KeyboardInterrupt:
        print("\nОстанавливаем серверы...")
        django_process.terminate()
        react_process.terminate()
        print("✅ Серверы остановлены")


if __name__ == "__main__":
    main()