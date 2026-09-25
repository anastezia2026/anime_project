from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import requests
import pandas as pd
import json
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Нужно для работы сессий


# ==========================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С ДАННЫМИ
# ==========================================

def get_top_anime_pandas():
    """Получает топ аниме через API и обрабатывает через Pandas"""
    url = "https://api.jikan.moe/v4/top/anime"
    response = requests.get(url)
    data_dict = response.json()
    anime_list = data_dict['data']

    df = pd.DataFrame(anime_list)

    # Добавляем колонку с картинкой (извлекаем из вложенной структуры)
    df['image_url'] = df['images'].apply(lambda x: x['jpg']['large_image_url'])

    df = df[['title', 'score', 'synopsis', 'url', 'image_url']]
    df = df[df['score'] >= 8.0]
    df = df.sort_values(by='score', ascending=False)

    return df.head(20).to_dict(orient='records')


def search_anime_in_api(query):
    """Ищет аниме в стабильном API Kitsu по названию"""
    query = query.strip()
    url = f"https://kitsu.io/api/edge/anime?filter[text]={query}&page[limit]=15"
    response = requests.get(url)

    print(f"🔍 Поиск: '{query}' | Статус ответа: {response.status_code}")

    if response.status_code != 200:
        print("⚠️ Ошибка соединения с API")
        return []

    data_dict = response.json()
    if 'data' not in data_dict or not data_dict['data']:
        print("⚠️ Ничего не найдено")
        return []

    # Превращаем сложные данные Kitsu в плоский список для Pandas
    flat_data = []
    for item in data_dict['data']:
        attr = item.get('attributes', {})
        flat_data.append({
            'title': attr.get('canonicalTitle') or attr.get('titles', {}).get('en', 'Без названия'),
            'score': attr.get('averageRating'),
            'synopsis': attr.get('synopsis', 'Описание отсутствует'),
            'url': f"https://kitsu.io/anime/{item.get('id')}",
            'image_url': attr.get('posterImage', {}).get('original', '')
        })

    df = pd.DataFrame(flat_data)

    # Kitsu дает рейтинг от 0 до 100. Делим на 10, чтобы получить привычные 8.5, 9.0 и т.д.
    df['score'] = pd.to_numeric(df['score'], errors='coerce').fillna(0) / 10

    # Оставляем только аниме с рейтингом 7.0 и выше
    df = df[df['score'] >= 7.0]

    print(f"✅ Найдено и отфильтровано: {len(df)} аниме")
    return df.to_dict(orient='records')


def get_anime_by_genres(genres):
    """Подбирает аниме по жанрам через поиск Kitsu"""
    # Словарь для перевода ID наших жанров в английские ключевые слова
    genre_keywords = {
        '1': 'action', '2': 'adventure', '4': 'comedy', '8': 'drama',
        '10': 'fantasy', '14': 'horror', '7': 'mystery', '22': 'romance',
        '24': 'sci-fi', '36': 'slice of life', '30': 'sports', '37': 'supernatural'
    }

    # Собираем ключевые слова для выбранных жанров
    keywords = [genre_keywords.get(g, '') for g in genres if g in genre_keywords]
    if not keywords:
        return []

    query = " ".join(keywords)
    # sort=-averageRating сортирует по рейтингу (от большего к меньшему)
    url = f"https://kitsu.io/api/edge/anime?filter[text]={query}&page[limit]=15&sort=-averageRating"
    response = requests.get(url)

    print(f"🎯 Подбор по жанрам (слова: '{query}') | Статус: {response.status_code}")

    if response.status_code != 200 or 'data' not in response.json():
        return []

    data_dict = response.json()['data']
    flat_data = []

    for item in data_dict:
        attr = item.get('attributes', {})
        try:
            score = float(attr.get('averageRating', 0)) / 10
        except (ValueError, TypeError):
            score = 0

        flat_data.append({
            'title': attr.get('canonicalTitle') or attr.get('titles', {}).get('en', 'Без названия'),
            'score': score,
            'synopsis': attr.get('synopsis', 'Описание отсутствует'),
            'url': f"https://kitsu.io/anime/{item.get('id')}",
            'image_url': attr.get('posterImage', {}).get('original', '')
        })

    df = pd.DataFrame(flat_data)
    df = df[df['score'] >= 7.0]

    print(f"✅ Найдено и отфильтровано: {len(df)} аниме")
    return df.to_dict(orient='records')

def search_quotes_in_json(anime_name):
    """Ищет цитаты в локальном JSON файле через Pandas"""
    with open('quotes.json', 'r', encoding='utf-8') as file:
        quotes_data = json.load(file)

    df = pd.DataFrame(quotes_data)
    filtered_df = df[df['anime'].str.contains(anime_name, case=False, na=False)]

    return filtered_df.to_dict(orient='records')


def setup_database():
    """Создает базу данных и таблицы"""
    conn = sqlite3.connect('anime.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_anime_lists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            anime_title TEXT NOT NULL,
            status TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()


def register_user_db(username, password):
    """Регистрирует нового пользователя"""
    conn = sqlite3.connect('anime.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return True, "Регистрация успешна!"
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Пользователь с таким логином уже существует"


def login_user_db(username, password):
    """Проверяет логин и пароль"""
    conn = sqlite3.connect('anime.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
    result = cursor.fetchone()
    conn.close()

    if result:
        return True, result[0]
    return False, None


def add_anime_to_list_db(user_id, anime_title, status):
    """Добавляет аниме в список пользователя"""
    conn = sqlite3.connect('anime.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO user_anime_lists (user_id, anime_title, status) VALUES (?, ?, ?)',
                   (user_id, anime_title, status))
    conn.commit()
    conn.close()


def remove_anime_from_list_db(user_id, anime_title):
    """Удаляет аниме из списка пользователя"""
    conn = sqlite3.connect('anime.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM user_anime_lists WHERE user_id = ? AND anime_title = ?',
                   (user_id, anime_title))
    conn.commit()
    conn.close()


def get_user_anime_list_db(user_id, status):
    """Получает список аниме пользователя с определенным статусом"""
    conn = sqlite3.connect('anime.db')
    cursor = conn.cursor()
    cursor.execute('SELECT anime_title FROM user_anime_lists WHERE user_id = ? AND status = ?',
                   (user_id, status))
    results = [row[0] for row in cursor.fetchall()]
    conn.close()
    return results


def get_username_db(user_id):
    """Получает имя пользователя по ID"""
    conn = sqlite3.connect('anime.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else "Пользователь"


# ==========================================
# РОУТЫ FLASK
# ==========================================

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/top')
def top_anime():
    animes = get_top_anime_pandas()
    return render_template('top.html', animes=animes)
@app.route('/search')
def search_anime():
    query = request.args.get('q', '')
    results = []

    if query:
        results = search_anime_in_api(query)

    return render_template('search.html', results=results, search_query=query)

@app.route('/quotes')
def search_quotes():
    anime_name = request.args.get('anime', '')
    quotes = []

    if anime_name:
        quotes = search_quotes_in_json(anime_name)

    return render_template('quotes.html', quotes=quotes, search_query=anime_name)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        success, message = register_user_db(username, password)

        if success:
            return redirect(url_for('login'))
        else:
            return render_template('register.html', error=message)

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        success, user_id = login_user_db(username, password)

        if success:
            session['user_id'] = user_id
            session['username'] = username
            return redirect(url_for('profile'))
        else:
            return render_template('login.html', error="Неверный логин или пароль")

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    username = get_username_db(user_id)

    want_to_watch = get_user_anime_list_db(user_id, 'want_to_watch')
    watching = get_user_anime_list_db(user_id, 'watching')
    watched = get_user_anime_list_db(user_id, 'watched')

    return render_template('profile.html',
                           username=username,
                           want_to_watch=want_to_watch,
                           watching=watching,
                           watched=watched)


@app.route('/add_to_list', methods=['POST'])
def add_to_list():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    anime_title = request.form.get('anime_title')
    status = request.form.get('status')

    add_anime_to_list_db(session['user_id'], anime_title, status)
    return redirect(request.referrer or url_for('top_anime'))


@app.route('/remove_from_list', methods=['POST'])
def remove_from_list():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    anime_title = request.form.get('anime_title')
    remove_anime_from_list_db(session['user_id'], anime_title)
    return redirect(url_for('profile'))


@app.route('/recommend')
def recommend_anime():
    """Страница подбора аниме по жанрам"""
    genres = request.args.getlist('genres')
    results = []

    if genres:
        results = get_anime_by_genres(genres)

    # Список популярных жанров для выбора
    all_genres = [
        {'id': '1', 'name': 'Экшен'},
        {'id': '2', 'name': 'Приключения'},
        {'id': '4', 'name': 'Комедия'},
        {'id': '8', 'name': 'Драма'},
        {'id': '10', 'name': 'Фэнтези'},
        {'id': '14', 'name': 'Ужасы'},
        {'id': '7', 'name': 'Мистика'},
        {'id': '22', 'name': 'Романтика'},
        {'id': '24', 'name': 'Фантастика'},
        {'id': '36', 'name': 'Повседневность'},
        {'id': '30', 'name': 'Спорт'},
        {'id': '37', 'name': 'Сверхъестественное'}
    ]

    return render_template('recommend.html',
                           results=results,
                           selected_genres=genres,
                           all_genres=all_genres)

# ==========================================
# ЗАПУСК СЕРВЕРА
# ==========================================

if __name__ == '__main__':
    setup_database()  # Создаем базу при запуске
    app.run(debug=True, port=5000)