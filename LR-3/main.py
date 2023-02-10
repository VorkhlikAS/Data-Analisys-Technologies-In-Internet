"""
## Ворхлик Александр, ПИ19-1
### Требования к ЛР №3

 * (4-6 баллов) Разработать программу (Python, C# или др.) для оценки тональности отзывов о 5 фильмах, оставленных
 пользователями на сайтах [IMDB](https://www.imdb.com/) или [Кинопоиск](https://www.kinopoisk.ru/lists/movies/top250/).
 Выбрать и обосновать инструментальное средство (библиотеку).
 * (+2 балла) Текст отзывов получен с помощью технологии web-скрапинга или Web API.
 * (+1-2 балла) Выполнить анализ полученных результатов. Оценить зависимость указанного пользователем рейтинга от
 тональности отзыва. Рассчитать статистики, построить иллюстрирующие графики.

 Установка необходиых библиотек

 Для работы с веб-скрепингом потребуется установить библиотеки для работы с веб страницами, такие как selenium и
 webdriver_manager. Torch - блблиотека для глубокого обучения, и transformers - библиотека с обученными моделями
 для работы с натуральными языками.

 Импортирование библиотек

* regex - для работы с html документами страниц
* mathplotlib и seaborn - для создания графиков
* numpy и pandas - для работы с большим количеством данных
* selenium, beautifulSoup и webdriver_manager - для работы с веб-страницами и браузером
* tqdm - для определения времени операции
* transformers и torch - для работы с библиотеками машинного обучения по естественным языкам
"""
import re
import matplotlib.pyplot as plt
import nltk
import numpy as np
import pandas as pd
import seaborn as sns
import torch
from time import sleep
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from tqdm.autonotebook import tqdm
from transformers import AutoModelForSequenceClassification, BertTokenizerFast  #
from webdriver_manager.firefox import GeckoDriverManager

nltk.download('punkt')
nltk_tokenizer = nltk.data.load("tokenizers/punkt/russian.pickle")
sns.set_theme()

urls = [("Американский психопат", "https://www.kinopoisk.ru/film/588/reviews/ord/date/status/all/perpage/200/"),
        ("Джокер", "https://www.kinopoisk.ru/film/1048334/reviews/ord/date/status/all/perpage/200/"),
        ("Бегущий по лезвию 2049", "https://www.kinopoisk.ru/film/589290/reviews/ord/date/status/all/perpage/200/"),
        ("Таксист", "https://www.kinopoisk.ru/film/358/reviews/ord/date/status/all/perpage/200/"),
        ("Гадкий я", "https://www.kinopoisk.ru/film/432724/reviews/ord/date/status/all/perpage/200/")]


def get_page(browser, url: str, page: int = None):
    """ Возвращает код указанной страницы """
    browser.get(url + f"page/{page}/")
    sleep(5)
    p_page = BeautifulSoup(browser.page_source, "html.parser")
    return p_page


def get_mark(review):
    """ Выдает значение оценки пользователя  """
    if "style" in review.find("li", {"id": re.compile("li_good_.*_a")}).attrs:
        p_mark = 1
    elif "style" in review.find("li", {"id": re.compile("li_bad.*_a")}).attrs:
        p_mark = -1
    else:
        p_mark = 0
    return p_mark


def analayze_review(review: str) -> tuple[float, float, float]:
    """ Выдает тройку значений по эмоциональной окраске предложения """
    sentences = [sentence.strip() for sentence in nltk_tokenizer.tokenize(review)]
    positive = []
    neutral = []
    negative = []
    for sentence in sentences:
        positive_score, neutral_score, negative_score = predict(sentence)
        positive.append(positive_score)
        neutral.append(neutral_score)
        negative.append(negative_score)
    return np.median(positive), np.median(neutral), np.median(negative)


@torch.no_grad()
def predict(text: str) -> tuple[float, float, float]:
    """ Выдает тройку значений по предсказаниям модели """
    inputs = tokenizer(text, max_length=512, padding=True, truncation=True, return_tensors="pt").to(device)
    outputs = model(**inputs)
    predictions = torch.nn.functional.softmax(outputs.logits, dim=1)
    positive = []
    neutral = []
    negative = []
    for prediction in predictions:
        positive.append(prediction[0].cpu().item())
        neutral.append(prediction[1].cpu().item())
        negative.append(prediction[2].cpu().item())
    return positive, neutral, negative


if __name__ == "__main__":
    status = True
    invalid = False
    while (status):
        if invalid:
            invalid = False
            print('Некорректный ввод')
        print('1. Загрузить и подготовить данные\n2. Загрузить графики\n3. Описать данные\n4. Выход')
        usr_choice = input()
        if usr_choice == '1':
            gecko_service = Service(GeckoDriverManager().install())
            browser = webdriver.Firefox(service=gecko_service)  # type: ignore
            reviews = []
            for film_title, url in tqdm(urls):
                page = get_page(browser, url, 1)
                total_reviews = int(page.find("li", class_="all").text.split(":")[1])
                for i in range(total_reviews // 200 + 1):
                    page = get_page(browser, url, i + 1)
                    for review in page.find_all("div", class_="reviewItem"):
                        title = review.find("p", class_="sub_title").text
                        text = re.sub("[\xa0\n\t]", " ", review.find("table").text)
                        mark = get_mark(review)
                        reviews.append({"film": film_title, "title": title, "text": text, "mark": mark})

            df = pd.DataFrame(reviews)
            print(df.describe())

            tokenizer = BertTokenizerFast.from_pretrained("blanchefort/rubert-base-cased-sentiment-rusentiment")
            model = AutoModelForSequenceClassification.from_pretrained(
                "blanchefort/rubert-base-cased-sentiment-rusentiment", return_dict=True
            )
            device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
            model.to(device);

            positive = []
            neutral = []
            negative = []
            for review in tqdm(df["text"]):
                positive_score, neutral_score, negative_score = analayze_review(review)
                positive.append(positive_score)
                neutral.append(neutral_score)
                negative.append(negative_score)

            df["positive"] = positive
            df["neutral"] = neutral
            df["negative"] = negative
            df["result"] = 0
            for i in df.index:
                df.loc[i, "result"] = df.loc[i, ["positive", "neutral", "negative"]].values.argmax() * -1 + 1
            print(df.head())
            df.to_csv("data.csv", index=False)

        elif usr_choice == '2':
            df = pd.read_csv("data.csv")
            cormat = df[["mark", "positive", "neutral", "negative", "result"]].corr()
            fig, ax = plt.subplots(figsize=(11, 7))
            sns.heatmap(cormat, annot=True, cmap="BuPu", vmin=0.1, vmax=0.9)
            ax.set_title('Корреляция переменных окраски текста')

            fig, ax = plt.subplots(figsize=(20, 10), sharey=True)
            graph_mark = sns.countplot(data=df, x="film", hue="mark")
            graph_mark.set(title='Оценка пользователей')
            for p in graph_mark.patches:
                height = p.get_height()
                graph_mark.text(p.get_x() + p.get_width() / 2., height + 0.1, height, ha="center")

            fig, ax = plt.subplots(figsize=(20, 10), sharey=True)
            graph_res = sns.countplot(data=df, x="film", hue="result")
            graph_res.set(title='Результат по оттенку отзыва')
            for p in graph_res.patches:
                height = p.get_height()
                graph_res.text(p.get_x() + p.get_width() / 2., height + 0.1, height, ha="center")
            plt.show()
        elif usr_choice == '3':
            df = pd.read_csv("data.csv")
            print(df.describe())
        elif usr_choice == '4':
            break
        else:
            invalid = True
    print('Finished running')
