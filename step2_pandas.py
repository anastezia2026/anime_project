import requests
import pandas as pd  # Подключаем нашего главного героя


def process_anime_with_pandas():
    # 1. Получаем данные из интернета (как в Шаге 1)
    url = "https://api.jikan.moe/v4/top/anime"
    response = requests.get(url)
    data_dict = response.json()
    anime_list = data_dict['data']

    # 2. Превращаем список словарей в таблицу Pandas
    df = pd.DataFrame(anime_list)
    df = df[['title','score','synopsis','url']]
    df = df['score'] >= 8.0
    df = df.sort_values(by = 'score', ascending = False)
    print("\n--- ТОП АНИМЕ ПОСЛЕ ОБРАБОТКИ PANDAS ---")
    print(df.head(5))
process_anime_with_pandas()