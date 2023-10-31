import vk_api
import json
from secrets import phone_number, password, owner_id, password_db
from datetime import datetime
import psycopg2

# создание сессии
vk_session = vk_api.VkApi(phone_number, password, app_id=2685278)
vk_session.auth(token_only=True)

vk = vk_session.get_api()
tools = vk_api.VkTools(vk_session)

# сохраняем текущую дату (в str, к сожалению, потому что json ругается, но лучше исправить в дату, чтобы
# в бд тоже дата закидывалась)
now = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

# получаем общее кол-во постов в группе
reply = vk.wall.get(owner_id=owner_id, count=0)
total_count = reply['count']

# парсим посты и переворачиваем список с ними, потому что нам нужны данные от старых к новым, а парсятся
# от новых к старым
reply = tools.get_all(method='wall.get', max_count=1, values={'owner_id': owner_id}, limit=1)
items = reply['items'][::-1]

# создаем список, куда запихнем посты
posts = []

# функция, чтобы обернуть комменты просто в список текстов
def get_comments(items):
    comments = []
    for item in items:
        if item['text'] != '':
            comments.append(item['text'])
    return comments

# мерзкий цикл
for item in items:
    # создаем пустой пост, куда потом всего напихаем
    post = {}
    # собираем комменты данного поста (не очень оптимально, но по-другому вряд ли можно)
    comments_reply = vk.wall.get_comments(owner_id=owner_id, post_id=item['id'], count=100, sort='asc',
                                          preview_length=0)
    comments = get_comments(comments_reply['items'])

    # прикалываемся со свойствами
    if item['marked_as_ads'] == 0:
        post['text'] = item['text']
        post['date'] = str(datetime.fromtimestamp(float(item['date'])))
        post['views'] = item['views']['count']
        post['likes'] = item['likes']['count']
        post['reposts'] = item['reposts']['count']
        post['comments'] = {'count': len(comments), 'items': comments}
        post['attachments'] = len(item['attachments'])

        # добавляем пост в posts
        posts.append(post)

# собираем result, который пойдет в json
result = {'total_count': total_count, 'date_updated': now, 'items': posts}

# result идет в json
with open('posts.json', 'w', encoding='utf-8') as outfile:
    outfile.write(json.dumps(result, ensure_ascii=False, indent=2))

# подключаемся к бд (мне лень убрать пароли в другой файл)
conn = psycopg2.connect(database="parsed_posts", user="postgres", password=password_db, host="localhost", port="5432")

cur = conn.cursor()

# очищаем таблицы и сбрасываем PK
cur.execute('TRUNCATE TABLE comments RESTART IDENTITY CASCADE')
cur.execute('TRUNCATE TABLE posts RESTART IDENTITY CASCADE')

# тут без проверки говна, просто i
i = 1

# просто записываем новые посты в бд
# юзаем posts
for post in posts:
    cur.execute('INSERT INTO posts (views, likes, reposts, attachments, text, date) VALUES (%s, %s, %s, %s, %s, %s)',
                (post['views'], post['likes'], post['reposts'], post['attachments'], post['text'], post['date']))

conn.commit()

# записываем комменты новых постов в бд
# опять же юзаем posts
for post in posts:
    # вытаскиваем комменты из поста
    comments = post['comments']['items']

    for comment in comments:
        cur.execute('INSERT INTO comments (post_id, text) VALUES (%s, %s)',
                    (i, comment))
    i += 1

conn.commit()

cur.close()
conn.close()