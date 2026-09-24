import requests
import json


def get_top_anime():
    url = "https://api.jikan.moe/v4/top/anime"
    answer = requests.get(url)

    # 1. Проверяем статус (ты это сделала отлично!)
    print("Статус запроса:", answer.status_code)

    # 2. Превращаем ответ в словарь и СОХРАНЯЕМ его в переменную
    data_dict = answer.json()

    # 3. Достаем список аниме из ключа 'data'
    anime_list = data_dict['data']

    # 🌟 МАГИЯ ИССЛЕДОВАНИЯ 🌟
    # Распечатаем ПЕРВОЕ аниме целиком, красиво и с поддержкой русского языка
    print("\n--- СМОТРИМ НА СТРУКТУРУ ПЕРВОГО АНИМЕ ---")
    print(json.dumps(anime_list[0], indent=2, ensure_ascii=False))

    # 4. Теперь, когда мы ВИДИМ ключи, делаем красивый вывод для Топ-5
    print("\n--- ТОП 5 АНИМЕ ---")
    for anime in anime_list[:5]:
        title = anime['title']
        score = anime['score']

        # Используем .get(), чтобы если описания нет, код не сломался, а выдал текст
        synopsis = anime.get('synopsis', 'Описание отсутствует')

        print(f"\n🎬 Название: {title}")
        print(f"⭐ Рейтинг: {score}")
        # Берем только первые 150 символов описания, чтобы не засорять экран
        print(f"📝 Описание: {synopsis[:150]}...")

    # Запускаем функцию


get_top_anime()