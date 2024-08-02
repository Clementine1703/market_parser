import os
import json
import sys
from pathlib import Path

from django.core.files import File
from slugify import slugify

from src.config import BASE_DIR

sys.path.append(str(Path(__file__).resolve().parent.parent))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promtech.settings')

import django
django.setup()

from documentation.models import Documentation
from product.models import Product, MainCharacteristic, Characteristic


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

        weigth_list = [0]
        if data.get('weigth', False):
            weigth_list = []
            weigth_list.append(data['weigth'].split(' ')[0])
            print(weigth_list, 1)
        elif data.get('options_for_selection'):
            for el in data.get('options_for_selection'):
                if el['title'] == 'Вес':
                    weigth_list = []
                    weigth_list += [value.split(' ')[0] for value in el['values']]
                    print(weigth_list, 2)


        for weigth in weigth_list:
            slug = slugify(f"{data['title']}-{weigth}-asasdfwefgbrtrrfdasdf")

            # Создаем или обновляем продукт
            product, created = Product.objects.get_or_create(title=data['title'], sale=0, slug=slug)

            # Обновляем поля продукта
            product.description = data['application']
            product.weight = weigth
            product.save()

            # Обрабатываем изображения
            for image_path in data['images']:
                with open(f'{BASE_DIR}/{image_path}', 'rb') as f:
                    django_file = File(f)
                    product.image.save(os.path.basename(image_path), django_file, save=True)

            for cert in data['certs']:
                with open(f"{BASE_DIR}/{cert['path']}", 'rb') as f:
                    django_file = File(f)
                    slug = slugify(f"{cert['name']}-{weigth}-asdadfgbtwertsasdrffdf")
                    if Documentation.objects.filter(slug=slug).exists():
                        raise ValueError(f"Slug '{slug}' already exists.")
                    doc, created = Documentation.objects.get_or_create(title=cert['name'], slug=slug)
                    doc.file_download.save(os.path.basename(cert['path']), django_file, save=True)
                    product.documents.add(doc)

            for feature in data['featues']:
                if feature:
                    key, value = feature[0], feature[1]
                    prop, _ = MainCharacteristic.objects.get_or_create(title=key)
                    characteristic, created = Characteristic.objects.get_or_create(product=product, prop=prop, val=value)
                    characteristic.save()
            



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