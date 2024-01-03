import datetime
import json
import pathlib
import re
import time

import requests
from bs4 import BeautifulSoup



class Ptt:

    def __init__(self) -> None:
        pass

    def __fetch(self, url: str) -> requests.Response:

        cookies = {"over18": "1"}
        response = requests.get(url, cookies=cookies)

        # prevent API Rate Limiting
        # time.sleep(0.1)

        return response

    def __get_post_datetime(self, url: str) -> str:

        response = self.__fetch(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        founds_time = soup.select(' #main-content .article-metaline .article-meta-tag:-soup-contains("時間") ')

        return founds_time[0].next_sibling.get_text()

    def __get_board(self, url: str) -> str | None:

        match = re.search(R"bbs\/(.*)\/", url)
        if match:
            board = match.group(1)
        else:
            return None

        return board

    def __get_post_id(self, url: str) -> str | None:

        board = self.__get_board(url)
        if board is None:
            return None

        # split url by board name
        tmp = url.partition(board)[2]
        post_id = tmp.lstrip("/").rstrip(".html")

        return post_id

    def __get_post_list_url_id(self, url: str) -> int | None:

        match = re.search(R"index(\d+)\.html", url)
        if match:
            url_id = match.group(1)
        else:
            return None

        return int(url_id)

    def __get_previous_url_id(self, url: str) -> int | None:

        response = self.__fetch(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # <a class="btn wide" href="/bbs/Gossiping/index39020.html">‹ 上頁</a>
        href_str = soup.find_all("a", string="‹ 上頁")[0]['href']

        match = re.search(R"index(\d+)\.html", href_str)
        if match:
            url_id = match.group(1)
        else:
            return None

        return int(url_id)

    def __page_post_list(self, url: str, year: int) -> tuple[list, int, bool]:
        """ get single page post list """

        print(f"page_post_list - {url} ")

        year_ = year

        response = self.__fetch(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        def __get_post_list_for_index(soup):

            posts = []

            found_posts = soup.select(' #main-container .r-list-container > div ')
            found_stop = soup.select(' #main-container .r-list-container .r-list-sep ')

            for element in found_posts:

                if element == found_stop[0]:
                    break

                if "r-ent" in element['class']:
                    posts.append(element)

            #
            return posts

        # check if page is index.html
        if url.endswith("index.html"):
            page_id = -1
            found_posts = __get_post_list_for_index(soup)
        else:
            page_id = self.__get_post_list_url_id(url)
            found_posts = soup.select(' #main-container .r-list-container .r-ent ')

        def __extract_post_item(element):

            meta_author = element.select(' .meta .author ')[0].get_text()
            if meta_author == "-":
                # 本文已被刪除
                return None

            title = element.select(' .title ')[0].get_text().lstrip('\n').rstrip('\n')
            url = element.select(' .title ')[0].a['href']
            meta_date = element.select(' .meta .date ')[0].get_text().lstrip()
            vote_balance = element.select(' .nrec ')[0].get_text()

            # result dict
            result = {}
            result["vote_balance"] = vote_balance
            result["title"] = title

            url = "https://www.ptt.cc" + url
            result["url"] = url

            meta_date = datetime.datetime.strptime(meta_date, "%m/%d")
            result["meta_date"] = meta_date

            result["meta_author"] = meta_author

            return result

        def __check_year_change(posts):
            """ check if year change in post list """

            meta_date_first = posts[0].select(' .meta .date ')[0].get_text()
            meta_date_last = posts[-1].select(' .meta .date ')[0].get_text()

            if meta_date_first == "12/31" and meta_date_last == " 1/01":
                return True
            else:
                return False

        is_year_change = __check_year_change(found_posts)

        posts = []
        for element in found_posts:

            post = __extract_post_item(element)

            if post is None:
                continue

            if is_year_change and post["meta_date"].day == 31:
                post["meta_date"] = post["meta_date"].replace(year=year_ - 1)
            else:
                post["meta_date"] = post["meta_date"].replace(year=year_)

            posts.append(post)

        return posts, page_id, is_year_change

    def __create_folder(self, board: str, file_path, datetime_: datetime.datetime):

        folder_path = pathlib.Path(file_path) / board / datetime_.strftime("%Y-%m-%d")
        folder_path.mkdir(parents=True, exist_ok=True)

        return folder_path

    def save_post_list(self, board: str, period_start: str, period_end: str, file_path) -> None:
        """  """

        url = "https://www.ptt.cc/bbs/" + board + "/index.html"

        start_datetime = datetime.datetime.fromisoformat(period_start)
        end_datetime = datetime.datetime.fromisoformat(period_end)
        year_ = start_datetime.year

        second_url_id = self.__get_previous_url_id(url)

        def __to_json(posts, page_id, file_path):

            page_id_ = page_id

            #
            result = {}

            if page_id == -1:
                page_id_ = "index"
                result['page_id'] = page_id_
            else:
                result['page_id'] = page_id

            result['articles'] = posts

            # datetime to str
            result_json = json.dumps(result, indent=4, ensure_ascii=False, default=str)

            file_name = str(page_id_) + ".json"
            with open(pathlib.Path(file_path) / file_name, mode='w', encoding='utf8') as file:
                file.write(result_json)

        def __get_period_article(article_list):

            index_from = 0
            for index, article in enumerate(reversed(article_list)):

                if article['meta_date'] < start_datetime:
                    index_from = len(article_list) - index
                    break

            return article_list[index_from:]

        previous_url = url
        end_flag = True
        while True:

            posts, page_id, is_year_change = self.__page_post_list(previous_url, year_)
            print(f"save_post_list - {posts[0]["meta_date"]}")

            second_url_id -= 1
            previous_url = "https://www.ptt.cc/bbs/" + board + "/index" + str(second_url_id) + ".html"

            if is_year_change:
                year_ -= 1

            if not posts:
                raise RuntimeError()

            # use "first" in ptt web post list , (old to new)
            if posts[0]["meta_date"] < start_datetime and posts[-1]["meta_date"] < start_datetime:
                break

            if posts[0]["meta_date"] < end_datetime and posts[-1]["meta_date"] < end_datetime and end_flag:
                continue
            else:
                end_flag = False

                path_ = self.__create_folder(board, file_path, posts[-1]["meta_date"])
                __to_json(posts, page_id, path_)

    def to_html(self,  url: str, file_path, file_name: str) -> None:
        """ save post to html """

        print(f"to_html - {url} ")

        response = self.__fetch(url)

        path = pathlib.Path(file_path) / (file_name + ".html")
        with open(path, encoding="utf-8", mode="w") as file:
            file.write(response.text)

    def to_html_from_post_list(self,  json_path, file_path) -> None:
        """ save post to html from post_list """

        def __read_posts(json_path):

            with open(json_path, mode='r') as file:

                post_list = json.load(file)
                return post_list

        post_list = __read_posts(json_path)

        print(f"to_html_from_posts_list - page_id: {post_list["page_id"]} ")

        for post in post_list["articles"]:

            folder_path = self.__create_folder(self.__get_board(post["url"]), file_path, datetime.datetime.fromisoformat(post["meta_date"]))
            self.to_html(post["url"], folder_path, self.__get_post_id(post["url"]))
