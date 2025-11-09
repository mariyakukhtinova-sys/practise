import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper import get_book_data, scrape_books, scrape_catalog
# по PEP-8 этот импорт должен быть вверху, но он требует смены директории,
# иначе его не запустить из ноутбука
# а для смены директории в свою очередь нужны другие импорты и строчка кода


def test_get_book_data(
    url: str = (
        "http://books.toscrape.com/catalogue/"
        "batman-the-dark-knight-returns-batman_792/index.html"
    )
) -> None:
    """
    Тестирует get_book_data на корректность структуры возвращаемых данных.

    Проверяет, что функция возвращает словарь с ожидаемыми ключами и
    правильными типами данных.

    Args:
        url (str): URL страницы книги для тестирования. По умолчанию
            используется конкретная книга для обеспечения стабильности теста.

    Returns:
        None: Тест не возвращает значений, использует assert для проверок.

    Raises:
        AssertionError: Если структура данных не соответствует ожиданиям.
    """

    result = get_book_data(url)
    # Проверяем наличие всех ожидаемых ключей
    expected_keys = ['title', 'price', 'rating', 'availability',
                     'description', 'product_info']
    assert all(key in result for key in expected_keys)

    # Проверяем типы данных результата
    assert isinstance(result, dict)
    assert isinstance(result['title'], str)
    assert isinstance(result['price'], float)
    assert isinstance(result['rating'], str)
    assert isinstance(result['availability'], str)
    assert isinstance(result['description'], str)
    assert isinstance(result['product_info'], dict)


def test_get_book_data_field_values() -> None:
    """
    Тестирует get_book_data на корректность возвращаемых данных.
    Использует URL с известной книгой для обеспечения воспроизводимости.
    Работает с полями title, price, rating, availability

    Args:
        None

    Returns:
        None

    Raises:
        AssertionError: Если значения полей не соответствуют ожидаемым:
                       - Неправильное название книги
                       - Неправильная цена
                       - Рейтинг не входит в допустимый диапазон (One-Five)
                       - Отсутствует информация о наличии в описании
    """
    test_url = (
        "http://books.toscrape.com/catalogue/"
        "batman-the-dark-knight-returns-batman_792/index.html"
    )

    result = get_book_data(test_url)

    # Проверяем конкретные значения полей
    assert result['title'] == "Batman: The Dark Knight Returns (Batman)"
    assert result['price'] == 15.38
    assert result['rating'].lower() in ["one", "two", "three", "four", "five"]
    assert "available" in result['availability'].lower()


def test_scrape_catalog() -> None:
    """
    Тестирует scrape_catalog на корректность возвращаемых данных.

    Проверяет, что функция возвращает 1000 книг и что все элементы
    в возвращаемом списке являются валидными URL-адресами.

    Args:
        None

    Returns:
        None

    Raises:
        AssertionError: Если количество возвращенных книг не равно 1000
                        если какие-либо элементы списка не являются строками
                       или не являются валидными URL-адресами книг.
    """
    books = scrape_catalog(debug=False)

    assert len(books) == 1000

    # Проверяем, что все элементы являются строками и валидными URL
    for book_url in books:
        assert isinstance(book_url, str)
        assert book_url.startswith("http://books.toscrape.com/catalogue/")
        assert book_url.endswith("/index.html")
