import asyncio
import aiohttp
import aiofiles
import certifi
import os
import ssl
import json
from pathlib import Path
from bs4 import BeautifulSoup
import time


from query import fetch, fetch_all, semaphore
from utils import get_exp_by_url
from decorators import print_execution_time
from config import BASE_URL, BASE_DIR


ssl_context = ssl.create_default_context(cafile=certifi.where())
current_directory = os.path.dirname(os.path.abspath(__file__))


@print_execution_time
async def get_category_links(url: str) -> list[str]:
    html = await fetch_all([url])
    html = html[0]

    soup = BeautifulSoup(html, "html5lib")

    catalog_menu = soup.find("div", {"class": "catalog-menu-block"})
    catalog_menu_items = catalog_menu.find_all("div", {"class": "panel-heading"})

    catalog_item_link_tags = [item.find("div", {"class": "accordeon-title"}).find("a") for item in catalog_menu_items]
    catalog_item_links = []

    for item in catalog_item_link_tags:
        try:
            catalog_item_links.append(f"{BASE_URL}{item['href']}")
        except:
            catalog_item_links.append(url)

    return catalog_item_links


@print_execution_time
async def get_product_links(category_links: list[str]) -> list:
    product_html_pages = await fetch_all(category_links)
    soups = [BeautifulSoup(html, "html5lib") for html in product_html_pages]

    product_divs_of_all_categories = [soup.find_all("div", {"class": "main-item-goods"}) for soup in soups]

    all_product_links = []
    for product_divs_of_one_category in product_divs_of_all_categories:
        category_product_links = [BASE_URL + product_div.find("div", {"class": "product-item-title"}).find("a")["href"] for product_div in product_divs_of_one_category]

        if category_product_links:
            all_product_links += category_product_links

    return all_product_links


@print_execution_time
async def get_all_products_information(urls: list[str]) -> list:
    urls = ['https://voronezh.cedrus.market/catalog/dekorativnye-shtukaturki/ekstervell-osl-shuba/', 'https://voronezh.cedrus.market/catalog/dekorativnye-shtukaturki/shtukaturka-dekorativnaya-osnovit-ekstervell-25-kg-shuba-color/']

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        tasks = [asyncio.create_task(get_one_product_information(session, product_id, url)) for product_id, url in enumerate(urls)]
        products_information = []
        for task in tasks:
            time.sleep(3)
            products_information.append(await task)

        with open('data.json', 'w') as f:
            json.dump(products_information, f, indent=4, ensure_ascii=False)

        return products_information


@print_execution_time
async def get_one_product_information(session: aiohttp.ClientSession, product_id: int, url: str) -> dict:
    html = await fetch(session, url)
    soup = BeautifulSoup(html, "html5lib")

    product_info = {
        "title": get_title(soup),
        "images": await download_product_images(session, product_id, soup),
        "certs": await download_product_certs(session, product_id, soup),
        "application": get_product_application(soup),
        "featues": get_product_features(soup),
        "advantages": get_advantages(soup),
        "weigth": get_main_weigth(soup),
        "cost": get_main_cost(soup),
        "options_for_selection": get_options_for_selection(soup)
    }

    return product_info


async def download_product_images(session: aiohttp.ClientSession, product_id: int, soup: BeautifulSoup) -> list[str]:
    gallery_div = soup.find("div", {"id": "gallery"})
    if gallery_div is None:
        print(f"Элемент с id='gallery' не найден для продукта {product_id}")
        return []

    images = gallery_div.find_all("img")
    photo_links = set()  # Используем множество для хранения уникальных URL-адресов
    images_save_path_list = []

    for img in images:
        photo_links.add(f"{BASE_URL}{img['src']}")

    for photo_id, url in enumerate(photo_links):
        relative_save_path = f'files/product/{product_id}/images/{photo_id}{get_exp_by_url(url)}'
        full_save_path = f'{BASE_DIR}/{relative_save_path}'
        await download_file(session, url, full_save_path)
        images_save_path_list.append(relative_save_path)
    
    return images_save_path_list


async def download_product_certs(session: aiohttp.ClientSession, product_id: int, soup: BeautifulSoup) -> list[str]:
    certs_div = soup.find("div", {"id": "panel3"})
    if certs_div is None:
        print(f"Элемент с id='panel3' не найден для продукта {product_id}")
        return []

    certs = certs_div.find_all("a")
    certs_infos = set()  # Используем множество для хранения уникальных URL-адресов

    for c in certs:
        certs_infos.add((c.text, f"{BASE_URL}{c['href']}"))

    certs_info = []
    for cert_id, c_info in enumerate(certs_infos):
        relative_save_path = f'files/product/{product_id}/certs/{cert_id}{get_exp_by_url(c_info[1])}'
        save_path = f'{BASE_DIR}/{relative_save_path}'
        await download_file(session, c_info[1], save_path)
        certs_info.append(
            {
                'name': c_info[0],
                'path': relative_save_path

            }
        )
    
    return certs_info 


@print_execution_time
async def download_file(session: aiohttp.ClientSession, url: str, save_path: str) -> str:
    if os.path.exists(save_path):
        print(f"Файл уже существует: {save_path}")
        return save_path

    Path(os.path.dirname(save_path)).mkdir(parents=True, exist_ok=True)

    async with session.get(url, ssl=ssl_context) as response:
        if response.status == 200:
            async with aiofiles.open(save_path, 'wb+') as f:
                await f.write(await response.read())
            print(f"Скачивание {url} в {save_path}")
        else:
            print(f"Ошибка скачивания {url}, статус кода: {response.status}")

    return save_path


def get_product_application(soup: BeautifulSoup) -> str:
    product_application = soup.find("div", {"id": "panel1"}).prettify()

    return product_application


def get_product_features(soup: BeautifulSoup) -> list:
    product_features_container = soup.find("div", {"id": "panel2"})
    product_features = []

    table_rows = product_features_container.find_all("tr")
    for tr in table_rows:
        tds = tr.find_all("td")

        feature_element = []
        for td in tds:
            feature_element.append(td.text.replace('\n', '').replace('\t', '').strip())

        product_features.append(feature_element)
    
    return product_features


def get_advantages(soup: BeautifulSoup) -> list:
    advantages_detail = soup.find_all("div", {"class": "advantages-detail-descript"})
    if advantages_detail:
        advantages_detail = [detail.text for detail in advantages_detail]
    return advantages_detail


def get_main_weigth(soup: BeautifulSoup) -> str:
    weigth_container = soup.find("div", {"class": "main-block-weight"})
    if weigth_container:
        weigth = weigth_container.text.replace('\n', '').replace('\t', '')
        return weigth
    return None


def get_main_cost(soup: BeautifulSoup) -> str:
    cost_container = soup.find("div", {"class": "product-item-detail-price-current"})
    if cost_container:
        cost = cost_container.text.replace('\n', '').replace('\t', '')
        return cost
    return None

def get_title(soup: BeautifulSoup) -> str:
    title_container = soup.find("h1", {"class": "detail-title"})
    if title_container:
        title = title_container.text.replace('\n', '').replace('\t', '')
        return title
    return None


def get_options_for_selection(soup):
    options_containers = soup.find_all("div", {"data-entity": "sku-line-block"})
    result = []
    for o_container in options_containers:
        title = o_container.find("div", {"class": "product-item-detail-info-container-title"}).text
        have_color = bool(o_container.find("div", {"class": "product-item-scu-item-color"}))

        values = []
        if not have_color:
            values = [item.text for item in o_container.find_all("div", {"class": "product-item-scu-item-text"})]
        if have_color:
            values = [item.text for item in soup.find_all("div", {"class": "color-pict-detail-description"})]
        item = {
           'title': title,
           'values': values
        }
        result.append(item)
    return result
