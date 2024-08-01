import os
from urllib.parse import urlparse


def get_exp_by_url(url):
    # Извлекаем расширение из URL
    parsed_url = urlparse(url)
    path = parsed_url.path
    ext = os.path.splitext(path)[1]

    return ext

