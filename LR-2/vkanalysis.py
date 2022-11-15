import math

import pandas as pd
import json
import numpy
import os
import time
import vk
import matplotlib.pyplot as plt
from collections import Counter
from dateutil.relativedelta import relativedelta
from datetime import datetime
from urllib.request import urlretrieve


def get_token():
    """Возвращает токен из текстового файла"""
    with open('token.txt') as f:
        lines = f.readlines()
    p_token = str(lines[0].replace('\n', ''))
    p_version = str(lines[1].replace('\n', ''))
    p_web_pg1 = str(lines[2].replace('\n', ''))
    p_web_pg2 = str(lines[3].replace('\n', ''))
    p_photo_page = str(lines[4].replace('\n', ''))
    return p_token, p_version, p_web_pg1, p_web_pg2, p_photo_page


def get_api(p_token: str, p_version: str):
    """Возвращает API, по токену и версии API"""
    p_api = vk.API(access_token=p_token, v=p_version)
    return p_api


def get_vk_users(p_api, p_group_id):
    """Возвращает пользователей указанной группы"""
    print('Просматриваю группу: "' + str(p_group_id) + '"')
    users_count = \
        int(p_api.groups.getMembers(group_id=p_group_id, fields='sex,bdate,city', offset=1000, sort='id_desc')['count'])
    users_count = users_count // 1000 + 1
    users = []
    for i in range(users_count):
        users += p_api.groups.getMembers(group_id=p_group_id, fields='sex,bdate,city', offset=i * 1000, sort='id_desc')[
            'items']

    p_df = pd.DataFrame(users)
    print(p_df.head())
    return p_df


def get_cities_to_df(p_df):
    """Возвращает города участников групп"""
    p_cities = []
    for row in p_df:
        if str(row) != 'nan':
            p_cities.append(row['title'])
        else:
            p_cities.append('')
    p_cities = pd.DataFrame(p_cities)
    return p_cities


def get_ages_to_df(p_df):
    """Возвращает возраст участников групп"""
    p_ages = []
    for row in p_df:
        if len(str(row)) < 8:
            p_ages.append(0)
        else:
            p_ages.append(relativedelta(datetime.now(), datetime.strptime(row, '%d.%m.%Y')).years)
    p_ages = pd.DataFrame(p_ages)
    return p_ages


def draw_age(p_df, titles, p_gr: str):
    """Генерирует гистограмму по возросту"""
    ax = p_df.hist('age', by='sex', grid=False, figsize=(8, 10), layout=(2, 1), bins=25,
                   sharex=True, color='#86bf91', zorder=2, rwidth=0.9)
    for i, x in enumerate(ax):

        # Despine
        x.spines['right'].set_visible(False)
        x.spines['top'].set_visible(False)
        x.spines['left'].set_visible(False)

        # Switch off ticks
        x.tick_params(axis="both", which="both", bottom="off", top="off", labelbottom="on", left="off", right="off",
                      labelleft="on")

        # Draw horizontal axis lines
        vals = x.get_yticks()
        for tick in vals:
            x.axhline(y=tick, linestyle='dashed', alpha=0.4, color='#eeeeee', zorder=1)

        x_lbl = "Возраст участников группы" + p_gr
        # Set x-axis label
        x.set_xlabel("Возраст участников группы", labelpad=20, weight='bold', size=12)

        # Set y-axis label
        x.set_ylabel("Количество человек", labelpad=50, weight='bold', size=12)

        x.set(title=titles[i])
        # Format y-axis label
        # x.yaxis.set_major_formatter(StrMethodFormatter('{x:,g}'))

        x.tick_params(axis='x', rotation=0)


def draw_gender(p_df, p_tb_name: str):
    """Генерирует круговую диаграмму по полу"""

    fig, ax = plt.subplots()
    ax = p_df.groupby(['sex'])['id'].count().plot(kind='pie', y='',
                                                  autopct='%1.0f%%', colors=['silver', 'steelblue'])
    name = 'Разделение по полам в ' + p_tb_name
    ax.set(title=name)
    ax.set_ylabel("Участники", labelpad=50, weight='bold', size=12)
    plt.legend()


def draw_cities(p_df, p_tb_name: str):
    """Генерирует круговую диаграмму по городам"""
    p_dict = p_df[p_df['city_name'] != ''].groupby(['city_name'])['id'].count().sort_values().tail(5)
    cnt = 0
    for key in p_dict.keys():
        cnt += p_dict[key]
    other_nm = p_df.shape[0] - cnt
    p_dict['Other'] = other_nm
    fig, ax = plt.subplots()
    ax = p_dict.plot(kind='pie', y='', autopct='%1.0f%%')
    name = 'Разделение по городам в ' + p_tb_name
    ax.set(title=name)
    ax.set_ylabel("Города", labelpad=50, weight='bold', size=12)
    plt.legend(loc='lower left')


def load_photos(p_api, p_url: str):
    """Загружает фотографии"""
    owner_id = p_url.split('/')[-1].split('_')[0].replace('album', '')
    albums = p_api.photos.getAlbums(owner_id=owner_id)
    if not os.path.exists('saved'):
        os.mkdir('saved')

    time_now = time.time()  # время старта

    counter_total = 0
    broken_total = 0

    for album in albums['items']:
        photo_folder = f'saved/album{owner_id}_{album["id"]}'
        if not os.path.exists(photo_folder):
            os.mkdir(photo_folder)
        photos_count = album['size']

        counter = 0  # текущий счетчик
        breaked = 0  # не загружено из-за ошибки
        prog = 0  # процент загруженных

        for j in range(math.ceil(photos_count / 1000)):
            # Получаем список фото
            photos = p_api.photos.get(owner_id=owner_id, album_id=album['id'], count=1000, offset=j * 1000)
            for photo in photos['items']:
                counter += 1
                url = photo['sizes'][-1]['url']  # Получаем адрес изображения
                print(f"Загружаю фото № {counter} из {photos_count} альбома {album['id']}. Прогресс: {prog} %")
                prog = round(100 / photos_count * counter, 2)
                try:
                    # Загружаем и сохраняем файл
                    urlretrieve(url, photo_folder + "/" + os.path.split(url)[1].split('?')[0])
                except Exception:
                    print(url)
                    print('Произошла ошибка, файл пропущен.')
                    breaked += 1

        counter_total += counter
        broken_total += breaked

    time_for_dw = time.time() - time_now
    print(
        f'\nВ очереди было {counter_total} файлов. Из них удачно загружено {counter_total - broken_total} файлов, {broken_total} не удалось загрузить. Затрачено времени: {round(time_for_dw, 1)} сек.')


if __name__ == '__main__':
    """Начальная подготовка"""
    token, version, gr1, gr2, photo_url = get_token()
    api = get_api(token, version)
    print(str(token) + ' ' + str(version))
    df1 = get_vk_users(api, gr1)
    df2 = get_vk_users(api, gr2)
    df = pd.merge(df1, df2, left_on='id', right_on='id', how='inner', suffixes=('', '_y'))
    df.drop(df.filter(regex='_y$').columns, axis=1, inplace=True)
    """Вывод значений характеристик датафреймов"""
    print(gr1 + ' пользователей: ' + str(df1.shape[0]) + '\n' +
          gr2 + ' пользователей: ' + str(df2.shape[0]) +
          '\nПересечение: ' + str(df.shape[0]))

    print(gr1 + '-Количество человек по полу:\nF: ' + str(df1[df1['sex'] == 1].shape[0]) +
          ' ' + str(round(df1[df1['sex'] == 1].shape[0] * 100 / df1.shape[0], 3)) + '%' +
          ' M: '
          + str(abs(df1[df1['sex'] == 1].shape[0] - df1.shape[0]))
          + ' ' + str(round(abs(df1[df1['sex'] == 1].shape[0] - df1.shape[0]) * 100 / df1.shape[0], 3)) + '%')
    print(gr2 + '-Количество человек по полу:\nF: ' + str(df2[df2['sex'] == 1].shape[0]) +
          ' ' + str(round(df2[df2['sex'] == 1].shape[0] * 100 / df2.shape[0], 3)) + '%' +
          ' M: '
          + str(abs(df2[df2['sex'] == 1].shape[0] - df2.shape[0]))
          + ' ' + str(round(abs(df2[df2['sex'] == 1].shape[0] - df2.shape[0]) * 100 / df2.shape[0], 3)) + '%')
    print('Количество человек по полу пересечения:\nF: ' + str(df[df['sex'] == 1].shape[0]) +
          ' ' + str(round(df[df['sex'] == 1].shape[0] * 100 / df.shape[0], 3)) + '%' +
          ' M: '
          + str(abs(df[df['sex'] == 1].shape[0] - df.shape[0]))
          + ' ' + str(round(abs(df[df['sex'] == 1].shape[0] - df.shape[0]) * 100 / df.shape[0], 3)) + '%')

    df1['city_name'] = get_cities_to_df(df1['city'])
    df2['city_name'] = get_cities_to_df(df2['city'])
    df['city_name'] = get_cities_to_df(df['city'])

    df1_city_stats = df1.groupby(['city_name'])['city_name'] \
        .count().reset_index(name='count').sort_values(['count'], ascending=False).head(6)
    df2_city_stats = df2.groupby(['city_name'])['city_name'] \
        .count().reset_index(name='count').sort_values(['count'], ascending=False).head(6)
    df_city_stats = df.groupby(['city_name'])['city_name'] \
        .count().reset_index(name='count').sort_values(['count'], ascending=False).head(6)

    if '' in df1_city_stats.keys():
        df1_city_stats.pop('')
    if '' in df2_city_stats.keys():
        df2_city_stats.pop('')
    if '' in df_city_stats.keys():
        df_city_stats.pop('')

    print('Города в ' + gr1)
    print(df1_city_stats[df1_city_stats['city_name'] != ''])
    print('Города в ' + gr2)
    print(df2_city_stats[df2_city_stats['city_name'] != ''])
    print('Города пересечения')
    print(df_city_stats[df_city_stats['city_name'] != ''])

    df1['age'] = get_ages_to_df(df1['bdate'])
    df2['age'] = get_ages_to_df(df2['bdate'])
    df['age'] = get_ages_to_df(df['bdate'])

    df1_age_stats = df1.groupby(['age'])['age'] \
        .count().reset_index(name='count').sort_values(['count'], ascending=False).head(6)
    df2_age_stats = df2.groupby(['age'])['age'] \
        .count().reset_index(name='count').sort_values(['count'], ascending=False).head(6)
    df_age_stats = df.groupby(['age'])['age'] \
        .count().reset_index(name='count').sort_values(['count'], ascending=False).head(6)

    print('Возраст в ' + gr1)
    print(df1_age_stats[df1_age_stats['age'] != 0])
    print('Возраст в ' + gr2)
    print(df2_age_stats[df2_age_stats['age'] != 0])
    print('Возраст пересечения')
    print(df_age_stats[df_age_stats['age'] != 0])

    draw_age(df1, ['Male', 'Female'], gr1)
    draw_age(df2, ['Male', 'Female'], gr2)
    draw_age(df, ['Male', 'Female'], 'пересечение')

    df1['sex'].replace(1, 'Female', inplace=True)
    df1['sex'].replace(2, 'Male', inplace=True)
    df2['sex'].replace(1, 'Female', inplace=True)
    df2['sex'].replace(2, 'Male', inplace=True)
    df['sex'].replace(1, 'Female', inplace=True)
    df['sex'].replace(2, 'Male', inplace=True)

    draw_gender(df1, gr1)
    draw_gender(df2, gr2)
    draw_gender(df, 'пересечение')

    draw_cities(df1, gr1)
    draw_cities(df2, gr2)
    draw_cities(df, 'пересечение')
    plt.show()

    print('Ожидание ввода пользователя для начала загрузки ...')
    input()
    print('Загрузка изображений ...')
    load_photos(api, photo_url)
    print('Finished process ...')
