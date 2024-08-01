import asyncio

from service import get_product_links, get_category_links, get_all_products_information
from decorators import print_execution_time
from config import START_PAGE_URL


@print_execution_time
async def main():
    category_links = await get_category_links(START_PAGE_URL)
    product_links = await get_product_links(category_links)
    await get_all_products_information(product_links)

if __name__ == '__main__':
    asyncio.run(main())