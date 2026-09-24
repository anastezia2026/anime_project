import sqlite3


def setup_database():
    conn = sqlite3.connect('anime.db')
    cursor = conn.cursor()

    # Создаем таблицу users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # ИСПРАВЛЕНО: таблица называется user_anime_lists (с s на конце)
    cursor.execute(''' 
    CREATE TABLE IF NOT EXISTS user_anime_lists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        anime_title TEXT NOT NULL,
        status TEXT NOT NULL
    )''')

    conn.commit()
    conn.close()
    print("✅ База данных успешно создана!")


def register_user(username, password):
    conn = sqlite3.connect('anime.db')
    cursor = conn.cursor()
    try:
        # ИСПРАВЛЕНО: добавлен кортеж (username, password) и исправлено password
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        print(f"✅ Пользователь {username} зарегистрирован!")
    except sqlite3.IntegrityError:  # ИСПРАВЛЕНО: правильное исключение
        print(f'❌ Пользователь {username} уже существует')
    finally:
        conn.commit()
        conn.close()


def add_anime_to_list(user_id, anime_title, status):
    conn = sqlite3.connect('anime.db')
    cursor = conn.cursor()
    # ИСПРАВЛЕНО: INSERT INTO (не TO) + добавлен кортеж со значениями
    cursor.execute('INSERT INTO user_anime_lists (user_id, anime_title, status) VALUES (?, ?, ?)',
                   (user_id, anime_title, status))
    conn.commit()
    conn.close()


def get_user_anime_list(user_id, status):
    conn = sqlite3.connect('anime.db')
    cursor = conn.cursor()
    # ИСПРАВЛЕНО: добавлен кортеж со значениями + результат сохранен в переменную
    cursor.execute('SELECT anime_title FROM user_anime_lists WHERE user_id = ? AND status = ?',
                   (user_id, status))
    results = cursor.fetchall()  # ИСПРАВЛЕНО: сохраняем результат
    conn.close()
    return results


# --- ТЕСТОВЫЙ БЛОК ---
if __name__ == "__main__":
    # Удаляем старую базу, если она есть (чтобы начать с чистого листа)
    import os

    if os.path.exists('anime.db'):
        os.remove('anime.db')

    # Создаем базу
    setup_database()

    # Регистрируем тестового пользователя
    register_user("test_user", "password123")

    # Добавляем аниме в разные списки
    add_anime_to_list(1, "Наруто", "watched")
    add_anime_to_list(1, "Атака Титанов", "watching")
    add_anime_to_list(1, "Ван-Пис", "want_to_watch")

    # Получаем список просмотренных аниме
    watched = get_user_anime_list(1, "watched")
    print("\n📺 Просмотренные аниме:")
    for anime in watched:
        print(f"  - {anime[0]}")

    # Получаем список того, что смотрим сейчас
    watching = get_user_anime_list(1, "watching")
    print("\n🎬 Сейчас смотрю:")
    for anime in watching:
        print(f"  - {anime[0]}")