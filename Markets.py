# Тест библиотеки "Драматург" (смешной перевод)

from playwright.sync_api import sync_playwright
import time
import json

# Основна функция, принимает инпут пользователя
def parse_wildberries(search_query):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # headless=False для визуализации
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
        page = context.new_page()

        # Формируем URL поиска
        url = f"https://www.wildberries.ru/catalog/0/search.aspx?search={search_query}"
        page.goto(url)

        # Ждем появления карточек товаров
        page.wait_for_selector("a.product-card__link.j-card-link.j-open-full-product-card", timeout=10000)

        products = []

        # Функция для парсинга товаров на текущей странице

        def parse_page():
            # Можно было бы выбрать не "самый" родительский класс карточки, но тогда возникали сложности с рейтингом и ценой
            # Но очевидный фрейм карточки это как бы ссылка, с нее можно прочитать название и саму ссылку, но все остальное нет
            # Поэтому пришлось взять родителя и "прогуляться вниз" через дополнительные переменные
            cards = page.query_selector_all("div.product-card__wrapper")
            for card in cards:
                link = card.query_selector("a.product-card__link.j-card-link.j-open-full-product-card")
                href = link.get_attribute("href")
                aria_label = link.get_attribute("aria-label").lower().strip()
                price_el = card.query_selector("ins.price__lower-price.wallet-price")
                if price_el:
                    price = price_el.text_content().strip()
                else:
                    price = None
                rating_el = card.query_selector("span.address-rate-mini")
                if rating_el:
                    rating = rating_el.text_content().strip()
                else:
                    rating = None

                products.append({"price": price, "rating": rating, "title": aria_label,  "url": href})

        # Парсим первую страницу
        parse_page()

        # Пробуем пройти по страницам пагинации, если есть
        max_pages = 10
        current_page = 1
        while True:
            # Проверяем кнопку "Следующая страница" и доступность
            next_button = page.query_selector("a.pagination-next,j-next-page")
            if next_button and not next_button.is_disabled() and current_page < max_pages:
                next_button.click()
                # Ждем загрузки новых товаров
                page.wait_for_selector("div.product-card__wrapper", timeout=10000)
                time.sleep(1)  # небольшая пауза для стабильности
                parse_page()
                current_page += 1
            else:
                break

        browser.close()
        return products

if __name__ == "__main__":
    search = input("Что будешь искать? в одну строку или через _ : ")
    items = parse_wildberries(search)
    print(f"Найдено товаров: {len(items)}")
    for i, item in enumerate(items, 1): # Перебираем элементы Items(индекс начиная с 1)
        print(f"{i}. {item["price"]} - {item["rating"]} - {item['title']} - {item['url']}")

    with open(f"search{search}.json", "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=4)
