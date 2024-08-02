import os
import json
import sys
from pathlib import Path


from django.core.files import File

from src.config import BASE_DIR

sys.path.append(Path(__file__).resolve().parent.parent)

from documentation.models import Documentation
from product.models import Product


category_matching_table = {
    'smesi-dlya-ustroystva-pola': '',
    'shtukaturki': '',
    'shpaklevki': '',
    'plitochnye-klei': '',
    'zatirki-i-rasshivki': '',
    'dekorativnye-shtukaturki': '',
    'smesi-dlya-teploizolyatsii': '',
    'kladochnye-rastvory': '',
    'montazhnye-klei': '',
    'gidroizolyatsiya': '',
    'spetsialnye-rastvory': '',
    'gruntovki': '',
    'smesi-dlya-bruschatki': '',
    # 'podlivochnye-sostavy': '',
    # 'promyshlennye-poly': '',
    # 'remont-i-zashchita-betona': '',
    'dobavki-v-rastvory': '',
    'smesi-dlya-pechey-i-kaminov': '',
    'osnovit-home': '',
    'kraski': '',
}






# Читаем данные из файла
with open(f'{BASE_DIR}/data.json', 'r') as f:
    data = json.load(f)

    # Создаем или обновляем продукт
    product, created = Product.objects.get_or_create(title=data['title'])

    # Обновляем поля продукта
    product.description = data['application']
    product.weight = data['weigth'] if data['weigth'] is not None else 0
    product.save()

    # Обрабатываем изображения
    for image_path in data['images']:
        with open(f'{BASE_DIR}/{image_path}', 'rb') as f:
            django_file = File(f)
            product.image.save(os.path.basename(image_path), django_file, save=True)

    # Обрабатываем сертификаты
    for cert in data['certs']:
        with open(f"{BASE_DIR}/{cert['path']}", 'rb') as f:
            django_file = File(f)
            doc, created = Documentation.objects.get_or_create(name=cert['name'])
            doc.document.save(os.path.basename(cert['path']), django_file, save=True)
            product.documents.add(doc)

    # Обрабатываем характеристики
    for feature in data['featues']:
        if feature:
            key, value = feature[0], feature[1]
            # Здесь можно создать модель для характеристик и связать её с продуктом
            # Например: Feature.objects.get_or_create(product=product, key=key, value=value)

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