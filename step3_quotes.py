import json
import pandas as pd


def search_anime_quotes():
    # 1. Открываем файл quotes.json для чтения
    with open('quotes.json', 'r', encoding='utf-8') as file:
        quotes_data= json.load(file)
    df = pd.DataFrame(quotes_data)

    # 3. Спрашиваем у пользователя, какое аниме он ищет
    search_word = input("Введите название аниме для поиска цитат: ")
    filtered_df = df[df['anime'].str.contains(search_word, case=False, na=False)]
    # 5. Выводим результат
    print("\n--- НАЙДЕННЫЕ ЦИТАТЫ ---")
    if len(filtered_df) > 0:
        # Пройдемся циклом по найденным строкам
        for index, row in filtered_df.iterrows():
            print(f"🎬 {row['anime']}")
            print(f"👤 {row['character']}: «{row['quote']}»\n")
    else:
        print("По вашему запросу ничего не найдено 😔")


# Запускаем функцию
search_anime_quotes()