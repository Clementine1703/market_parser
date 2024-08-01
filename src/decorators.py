import asyncio
import functools

# Декоратор для асинхронной функции
def print_execution_time(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = asyncio.get_running_loop().time()
        print(f'Начало выполнения функции: {func.__name__}')
        try:
            result = await func(*args, **kwargs)
        finally:
            end_time = asyncio.get_running_loop().time()
            elapsed_time = end_time - start_time
            print(f"{func.__name__} выполнялась {elapsed_time:.2f} секунд")
        return result
    return wrapper