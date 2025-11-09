import time
import requests
import schedule
from bs4 import BeautifulSoup
import re
import pickle
import json


def get_book_data(book_url: str) -> dict:
    """
    Получает данные о книге с одной страницы.

    Собирает информацию о книге: название, цену, рейтинг, количество в наличии,
    описание и дополнительные характеристики из таблицы Product Information.

    Args:
        book_url (str): адрес страницы для парсинга с информацией о книге

    Returns:
        dict: Словарь с данными о книге:
            - 'title' (str): название книги
            - 'price' (float): цена
            - 'rating' (str): рейтинг в звездах
            - 'availability' (str): информация о наличии
            - 'description' (str): описание книги
            - 'product_info' (dict): словарь с дополнительной информацией

    Raises:
        requests.RequestException: При ошибках сетевого запроса
    """

    # НАЧАЛО ВАШЕГО РЕШЕНИЯ
    response = requests.get(book_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')
    result = dict()

    # парсим название книги
    result['title'] = soup.find('h1').get_text()

    # переходим к таблице с описанием книги
    table = soup.find('table', class_="table table-striped")

    # нашли цену
    price_raw = (
        table.find("th", string="Price (incl. tax)")
        .find_parent("tr")
        .find("td")
        .get_text()
    )
    result['price'] = float(price_raw[1:])

    # рейтинг в звездах
    result['rating'] = (
        soup.find("article", class_="product_page")
        .find("div", class_="col-sm-6 product_main")
        .find("p", class_=re.compile(r"star-rating.*"))
        .get('class')[1]
    )

    # информация о наличии
    result['availability'] = (
        table.find("th", string="Availability")
        .find_parent("tr")
        .find("td")
        .get_text()
    )

    # описание книги

    try:
        result['description'] = (
            soup.find("article", class_="product_page")
            .find("div", id="product_description")
            .find_next_sibling("p")
            .get_text()
        )
    except AttributeError:
        result['description'] = ""

    # словарь с дополнительной информацией
    ks = [i.get_text() for i in table.find_all("th")]
    vs = [i.get_text() for i in table.find_all("td")]
    result['product_info'] = dict(zip(ks, vs))

    return result
# КОНЕЦ ВАШЕГО РЕШЕНИЯ


def scrape_catalog(debug: bool = False) -> list:
    """
    Функция парсит каталог и возвращает список ссылок на отдельные книги.

    Args
        debug (bool): при отладке читает данные из файла, по умолчанию False

    Returns
        book_urls (list): список URL адресов страниц с книгами
    """
    start_time = time.time()
    n = 1
    pages = []

    # Для удобства отладки добавим опцию писать/читать каталог в файл/из файла
    # Вне режима дебага парсим каталог каждый раз
    if not debug:
        while True:
            try:
                response = requests.get(
                    f"http://books.toscrape.com/catalogue/page-{n}.html",
                    timeout=10
                )

                if not response.ok:
                    break

                pages.append(response.content)
                #print(f"Catalog page {n} scraped")
                n += 1

            except requests.exceptions.RequestException:
                print("Connection error, retrying...")
                time.sleep(5)
                continue

        # with open('catalog_pages.pkl', 'wb') as f:
        #     pickle.dump(pages, f)

    elif debug:

        with open('catalog_pages.pkl', 'rb') as f:
            pages = pickle.load(f)

        print(f"Loaded {len(pages)} pages from file")

    base_url = 'http://books.toscrape.com/catalogue/'
    book_urls = []
    for page in pages:
        soup = BeautifulSoup(page, 'html.parser')

        table = (
            soup.find("div", class_="col-sm-8 col-md-9")
            .find_all("li", class_="col-xs-6 col-sm-4 col-md-3 col-lg-3")
        )

        for book in table:
            # book.find("a", href=True).get("href")
            book_urls.append(base_url + book.find("a", href=True).get("href"))

    end_time = time.time()

    execution_time = end_time - start_time
    print(f"Catalog scraping took {execution_time:.2f} seconds")

    return book_urls


def scrape_books(book_urls: list, is_save: bool = False,
                 debug: bool = False) -> list:
    """
    Парсит предоставленные URL со страницами книг, достает описание этих книг.
    Может записать полученную информацию в файл.

    Args:
        book_urls (list): список URL-адресов книг из каталога
        is_save (bool): сохранение инфо о книгах в файл, по умолчанию false
        debug (bool): режим отладки, парсит первые 10 книг, по умолчанию false
    Return:
        books_data (list): список словарей из scrape_catalog() с книгами
    """

    # Для отладки парсим первые 10 книг для экономии времени
    if debug:
        book_urls = book_urls[0:10]

    books_data = []
    start_time = time.time()

    for i, book_url in enumerate(book_urls, 1):
        for attempt in range(3):  # Retry up to 3 times
            try:
                book = get_book_data(book_url)
                books_data.append(book)
                break  # Success, move to next book
            except requests.exceptions.RequestException:
                if attempt < 2:  # Not the last attempt
                    print(
                        f"Failed to load {book_url}, retry attempt {attempt}")
                    time.sleep(2)
                    continue
                print(f"Failed to load {book_url} after 3 attempts")

        #print(f"Loaded book No {i}: {book_url}")

    # Пишем данные в файл
    # Отладочные данные не надо писать в файл
    if is_save and not debug:
        with open('artifacts/books_data.txt', 'w', encoding='utf-8') as f:
            json.dump(books_data, f, indent=4, ensure_ascii=False)
            print("Scraped books saved to books_data.txt")

    end_time = time.time()

    execution_time = end_time - start_time
    print(f"Catalog scraping took {execution_time:.2f} seconds")

    return books_data


def job():
    print("Запуск сбора данных по таймеру...")
    books = scrape_catalog(debug=False)
    res = scrape_books(is_save=True, book_urls=books, debug=False)
    print("Сбор данных завершен.")


# Запланировать задачу на 19:00 каждый день
schedule.every().day.at("14:19").do(job)

while True:
    schedule.run_pending()  # Проверяет и запускает задачи по расписанию
    time.sleep(30)          # Ждем 30 секунд перед следующей проверкой


# КОНЕЦ ВАШЕГО РЕШЕНИЯ
# books = scrape_catalog(debug=False)
# scrape_books(book_urls=books, debug=False, is_save=True)

