"""
Скрипт проверяет качество передачи данных и позволяет найти ошибку в расхождении исходных и переданных данных
"""

import hashlib
import os
import sys
from pathlib import Path


def verify_files_by_content(file_paths):
    """
    Проверяет, что все файлы имеют идентичное содержимое
    """
    print('\n🔍 Проверка совпадения содержимого файлов...')

    if len(file_paths) < 2:
        print('❌ Нужно как минимум 2 файла для сравнения')
        return False

    file_contents = []
    for file_path in file_paths:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                file_contents.append((file_path, content))
                print(f'📁 {os.path.basename(file_path)}: {len(content)} символов')
        except Exception as e:
            print(f'❌ Ошибка чтения файла {file_path}: {e}')
            return False

    first_content = file_contents[0][1]
    all_match = True

    for file_path, content in file_contents[1:]:
        if content == first_content:
            print(f'✅ {os.path.basename(file_path)} совпадает с {os.path.basename(file_paths[0])}')
        else:
            print(f'❌ {os.path.basename(file_path)} НЕ совпадает с {os.path.basename(file_paths[0])}')
            all_match = False

    return all_match


def verify_files_by_hash(file_paths):
    """
    Проверяет совпадение файлов по хеш-суммам
    """
    print('\n🔐 Проверка по MD5 хеш-суммам...')

    hashes = {}
    for file_path in file_paths:
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5()
                while chunk := f.read(8192):
                    file_hash.update(chunk)
                hashes[file_path] = file_hash.hexdigest()
                print(f'📁 {os.path.basename(file_path)}: {hashes[file_path]}')
        except Exception as e:
            print(f'❌ Ошибка вычисления хеша для {file_path}: {e}')
            return False

    first_hash = list(hashes.values())[0]
    all_match = all(h == first_hash for h in hashes.values())

    if all_match:
        print('✅ Все файлы имеют одинаковую хеш-сумму')
    else:
        print('❌ Файлы имеют разные хеш-суммы')

    return all_match


def verify_file_sizes(file_paths):
    """
    Проверяет совпадение размеров файлов
    """
    print('\n📊 Проверка размеров файлов...')

    sizes = {}
    for file_path in file_paths:
        try:
            size = os.path.getsize(file_path)
            sizes[file_path] = size
            print(f'📁 {os.path.basename(file_path)}: {size} байт')
        except Exception as e:
            print(f'❌ Ошибка получения размера для {file_path}: {e}')
            return False

    first_size = list(sizes.values())[0]
    all_match = all(s == first_size for s in sizes.values())

    if all_match:
        print('✅ Все файлы имеют одинаковый размер')
    else:
        print('❌ Файлы имеют разные размеры')

    return all_match


def find_test_files(directory=None):
    """
    Находит тестовые файлы в указанной директории
    """
    if directory is None:
        directory = Path(__file__).parent

    test_files = list(directory.glob('test*.txt'))
    test_files.sort()

    return test_files


def main():
    print('=' * 50)
    print('🔍 ПРОВЕРКА ТЕСТОВЫХ ФАЙЛОВ')
    print('=' * 50)

    test_files = find_test_files()

    if not test_files:
        print('❌ Не найдены тестовые файлы (test*.txt) в текущей директории')
        print('Доступные файлы:')
        for file in Path(__file__).parent.iterdir():
            if file.is_file():
                print(f'  - {file.name}')
        sys.exit(1)

    print(f'📁 Найдено файлов: {len(test_files)}')
    for file in test_files:
        print(f'   • {file.name}')

    file_paths = [str(f) for f in test_files]

    size_ok = verify_file_sizes(file_paths)
    hash_ok = verify_files_by_hash(file_paths)
    content_ok = verify_files_by_content(file_paths)

    print('\n' + '=' * 50)
    print('📊 ИТОГИ ПРОВЕРКИ:')
    print('=' * 50)
    print(f'✅ Размеры файлов: {"СОВПАДАЮТ" if size_ok else "НЕ СОВПАДАЮТ"}')
    print(f'✅ Хеш-суммы: {"СОВПАДАЮТ" if hash_ok else "НЕ СОВПАДАЮТ"}')
    print(f'✅ Содержимое: {"СОВПАДАЕТ" if content_ok else "НЕ СОВПАДАЕТ"}')

    if size_ok and hash_ok and content_ok:
        print('\n🎉 ВСЕ ФАЙЛЫ ИДЕНТИЧНЫ! Передача прошла успешно!')
        sys.exit(0)
    else:
        print('\n💥 Обнаружены различия в файлах!')
        sys.exit(1)


if __name__ == '__main__':
    main()
