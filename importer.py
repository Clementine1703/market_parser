import os
import json
import sys
from pathlib import Path
import shortuuid


from django.core.files import File
from slugify import slugify

from parser.src.config import BASE_DIR

sys.path.append(str(Path(__file__).resolve().parent.parent))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promtech.settings')

import django
django.setup()

from documentation.models import Documentation
from product.models import Product, MainCharacteristic, Characteristic, CurrentProduct, Packing, Color, Unit
from category.models import Category

def generate_vendor_code():
    return shortuuid.uuid()[:20].upper()

category_matching_table = {
    'smesi-dlya-ustroystva-pola': 'smesi-dlya-pola',
    'shtukaturki': 'shtukaturki',
    'shpaklevki': 'shpaklevki',
    'plitochnye-klei': 'plitochnyj-klej',
    'zatirki-i-rasshivki': 'zatirki-i-rasshivki',
    'dekorativnye-shtukaturki': 'dekorativnye-shtukaturki',
    'smesi-dlya-teploizolyatsii': 'smesi-dlya-teploizolyacii',
    'kladochnye-rastvory': 'kladochnye-rastvory',
    'montazhnye-klei': 'montazhnye-klei',
    'gidroizolyatsiya': 'gidroizolyaciya',
    'spetsialnye-rastvory': 'specialnye-rastvory',
    'gruntovki': 'gruntovki',
    'smesi-dlya-bruschatki': 'smesi-dlya-bruschatki',
    # 'podlivochnye-sostavy': '',
    # 'promyshlennye-poly': '',
    # 'remont-i-zashchita-betona': '',
    'dobavki-v-rastvory': 'dobavki-v-rastvory',
    'smesi-dlya-pechey-i-kaminov': 'smesi-dlya-pechej-i-kaminov',
    'osnovit-home': 'uhod',
    'kraski': 'interernye-kraski',
}



# Читаем данные из файла
with open(f'{BASE_DIR}/data.json', 'r') as f:
    items = json.load(f)
    for data in items:

        weigth = 0
        if data.get('weigth', False):
            weigth = data['weigth'].split(' ')[1]
            

        # for weigth in weigth_list:
        slug = slugify(f"{data['title']}-asacsdffweffgbrtaasffdevffgffsffffkffjhdff-ras-dfass-fsgfff-drd-fg-fasdfdasdf")

        category_slug = data['category_slug']
        if category_slug in category_matching_table:
            category = Category.objects.get(slug=category_matching_table[category_slug])
            
            product, created = Product.objects.get_or_create(title=data['title'], sale=0, slug=slug, isPublic=True)
            product.save()

            # Убедитесь, что поле category инициализировано
            if product.category is None:
                product.category = category
                product.save()
        else:
            continue
        
        # Обновляем поля продукта
        product.description = data['application']
        product.weight = float(str(weigth).replace(',', '.').replace('л', '').replace('кг', ''))
        product.save()

        category = Category.objects.filter(slug=category_matching_table[data['category_slug']]).first()

        # Обрабатываем изображения
        for image_path in data['images']:
            with open(f'{BASE_DIR}/{image_path}', 'rb') as f:
                django_file = File(f)
                product.image.save(os.path.basename(image_path), django_file, save=True)

        for id, cert in enumerate(data['certs']):
            with open(f"{BASE_DIR}/{cert['path']}", 'rb') as f:
                django_file = File(f)
                slug = slugify(f"product-{product.id}-{cert['name']}-fdfavfffgfffgfffefffffffffrg-sdk-fs-df-a-s-vv-{id}")
                if Documentation.objects.filter(slug=slug).exists():
                    raise ValueError(f"Slug '{slug}' already exists.")
                doc, created = Documentation.objects.get_or_create(title=cert['name'], slug=slug)
                doc.file_download.save(os.path.basename(cert['path']), django_file, save=True)
                product.documents.add(doc)

        for feature in data['featues']:
            if feature:
                try:
                    key, value = feature[0], feature[1]
                except:
                    continue
                prop, _ = MainCharacteristic.objects.get_or_create(title=key)
                characteristic, created = Characteristic.objects.get_or_create(product=product, prop=prop, val=value)
                characteristic.save()


        packings = []
        if data.get('options_for_selection'):
            for el in data.get('options_for_selection'):
                if el['title'] == 'Вес':
                    for value in el['values']:
                        unit = Unit(unit=value.split(' ')[1])
                        unit.save()
                        packing = Packing(size=float(str(value.split(' ')[0]).replace(',', '.')), unit=unit)
                        packing.save()
                        packings.append(packing)

        colors = []
        if data.get('options_for_selection'):
            for el in data.get('options_for_selection'):
                if el['title'] == 'Цвет':
                    for value in el['values']:
                        if value != '-':
                            color = Color(prop=value)
                            color.save()
                            colors.append(color)

        current_products = []
        if packings and colors:
            for packing in packings:
                for color in colors:
                    current_products.append(CurrentProduct(color=color, packing=packing))
        elif packings:
            for packing in packings:
                current_products.append(CurrentProduct(packing=packing))
        elif colors:
            for color in colors:
                current_products.append(CurrentProduct(color=color))

        for cur_product in current_products:
            cur_product.vendorCode = generate_vendor_code()
            cur_product.product = product
            cur_product.save()

        if not data.get('options_for_selection'):
            cur_product = CurrentProduct(vendorСode=f'no_current_{product.id}')
            cur_product.product = product
            cur_product.save()

        



        



        # Обрабатываем преимущества
        # for advantage in data['advantages']:
            # ...
            # Здесь можно создать модель для преимуществ и связать её с продуктом
            # Например: Advantage.objects.get_or_create(product=product, text=advantage)

        # Обрабатываем опции выбора
        # for option in data['options_for_selection']:
        #     title = option['title']
        #     values = option['values']
            # Здесь можно создать модель для опций выбора и связать её с продуктом
            # Например: Option.objects.get_or_create(product=product, title=title, values=values)

        print(f"Product {product.title} has been {'created' if created else 'updated'}.")

