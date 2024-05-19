import vk_api
import json
from project_secrets import phone_number, password, owner_id, password_db
from datetime import datetime
import psycopg2

# создание сессии
vk_session = vk_api.VkApi(phone_number, password, app_id=2685278)
vk_session.auth(token_only=True)

vk = vk_session.get_api()
tools = vk_api.VkTools(vk_session)

# FIXME сохраняем текущую дату (в str, к сожалению, потому что json ругается, но лучше исправить в datetime)
now = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

# получаем общее кол-во постов в группе
reply = vk.wall.get(owner_id=owner_id, count=0)
total_count = reply['count']

newDB = True
old_total_count = 0
data = None

# создаем два списка, в posts сохраняем все прошлые посты из data, потом туда добавим новые (или оставляем пустым,
# если newDB = True)
# posts_db оставляем пустым, потом туда добавим также новые посты
posts = []
posts_db = []

# ПЫТАЕМСЯ прочитать файл с данными
try:
  with open('posts.json', 'r', encoding='utf-8') as outfile:
    data = json.load(outfile)
    old_total_count = data['total_count']
    posts = data['items']
    # FIXME: Костыль (возможно)
    newDB = False
except:
    print("Can't find previous parsing data")
finally:
    # По окончанию блока подставляем данные о тотале
    # считаем, сколько постов добавилось, и задаем max_count
    count = total_count - old_total_count
    max_count = count // 25 + 1

# парсим посты и переворачиваем список с ними, потому что нам нужны данные от старых к новым, а парсятся
# от новых к старым
# также обрезаем список до нужного нам кол-ва постов, так как get_all получает кол-во постов, кратное 25

# правильный запрос
reply = tools.get_all(method='wall.get', max_count=9, values={'owner_id': owner_id}, limit=total_count)

# все посты, почему-то (нет limit)
# reply = tools.get_all(method='wall.get', max_count=9, values={'owner_id': owner_id})

# парсит 1125 постов c limit=1000, 450 с limit=300
# reply = tools.get_all(method='wall.get', max_count=9, values={'owner_id': owner_id}, limit=3000)
items = reply['items'][:count:]
items = items[::-1]

# функция, чтобы обернуть комменты просто в список текстов
def get_comments(items):
    comments = []
    for item in items:
        if item['text'] != '':
            comments.append(item['text'])
    return comments

# функция с проверкой для просмотров, потому что их стали считать только в 2017
def get_views(item):
    try:
        return item['views']['count']
    except KeyError:
        return 0

for item in items:
    # создаем пустой пост
    post = {}
    # собираем комменты данного поста (не очень оптимально, но по-другому вряд ли можно)
    comments_reply = vk.wall.get_comments(owner_id=owner_id, post_id=item['id'], count=100, sort='asc',
                                          preview_length=0)
    comments = get_comments(comments_reply['items'])

    # свойства
    if item['marked_as_ads'] == 0:
        post['text'] = item['text']
        post['date'] = str(datetime.fromtimestamp(float(item['date'])))
        post['views'] = get_views(post)
        post['likes'] = item['likes']['count']
        post['reposts'] = item['reposts']['count']
        post['comments'] = {'count': len(comments), 'items': comments}
        post['attachments'] = len(item['attachments'])

        # добавляем пост в posts и posts_db
        posts.append(post)
        posts_db.append(post)

# собираем result, который пойдет в json
result = {'total_count': total_count, 'date_updated': now, 'items': posts}

# result идет в json
with open('posts.json', 'w', encoding='utf-8') as outfile:
    outfile.write(json.dumps(result, ensure_ascii=False, indent=2))

# подключаемся к бд
conn = psycopg2.connect(database="abitmobot", user="postgres", password=password_db, host="localhost", port="5432")

cur = conn.cursor()
res = None

if newDB:
    # очищаем таблицы и сбрасываем PK
    cur.execute('TRUNCATE TABLE comments RESTART IDENTITY CASCADE')
    cur.execute('TRUNCATE TABLE posts RESTART IDENTITY CASCADE')
else:
    # вытаскиваем номер последнего на данный момент времени поста в бд,
    # чтобы потом дать правильные post_id комментам в их таблице
    cur.execute('SELECT post_id FROM posts ORDER BY post_id DESC LIMIT 1')
    res = cur.fetchone()

# задаем корректное i
if res is not None:
    i = res[0] + 1
else:
    i = 1

# записываем посты в бд
for post in posts_db:
    cur.execute('INSERT INTO posts (views, likes, reposts, attachments, text, date) VALUES (%s, %s, %s, %s, %s, %s)',
                (post['views'], post['likes'], post['reposts'], post['attachments'], post['text'], post['date']))

conn.commit()

# записываем комменты постов в бд
for post in posts_db:
    # вытаскиваем комменты из поста
    comments = post['comments']['items']

    for comment in comments:
        cur.execute('INSERT INTO comments (post_id, text) VALUES (%s, %s)',
                    (i, comment))
    i += 1

conn.commit()

cur.close()
conn.close()
