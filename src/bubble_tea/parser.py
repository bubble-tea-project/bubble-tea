import datetime
import json
import pathlib
import re

import bs4
from bs4 import BeautifulSoup
from tqdm import tqdm

from . import scraping



class Ptt:

    def __init__(self, html_path: str) -> None:
        """ Constructing parser from a html_file """

        self.html_path = html_path

        html_str = self.__from_html(html_path)
        self.soup = BeautifulSoup(html_str, 'html.parser')

    def __from_html(self, html_path: str) -> str:

        with open(html_path, mode='r') as file:

            html_str = file.read()
            return html_str

    def __post_url(self) -> str:

        found = self.soup.select(' head [rel="canonical"]  ')
        post_url = found[0]["href"]

        return post_url

    def __post_id(self) -> str:

        scraping_ptt = scraping.Ptt()

        return scraping_ptt.__get_post_id(self.__post_url())

    def __post_title(self) -> str:

        found = self.soup.select(' head [property="og:title"]  ')
        post_title = found[0]["content"]

        return post_title

    def __post_author(self) -> str:

        found = self.soup.select(' #main-content .article-metaline :-soup-contains("作者") ')
        post_author = found[0].next_sibling.get_text()

        return post_author

    def __post_time(self) -> str:

        found = self.soup.select(' #main-content .article-metaline .article-meta-tag:-soup-contains("時間") ')
        post_time = found[0].next_sibling.get_text()

        post_time_isoformat = datetime.datetime.strptime(post_time, "%a %b %d %H:%M:%S %Y").isoformat()

        return post_time_isoformat

    def __post_ip(self) -> str:

        # --?
        # https://www.ptt.cc/bbs/Gossiping/M.1703323721.A.65C.html

        found = self.soup.select(' #main-content :-soup-contains("發信站: 批踢踢實業坊(ptt.cc)") ')
        if not found:
            return None
        else:
            post_ip = found[0].get_text().partition("來自: ")[2].rstrip('\n')

            return post_ip

    def __post_content(self) -> str:

        # 時間Thu Dec 21 16:14:43 2023
        found_start = self.soup.select(' #main-content .article-metaline .article-meta-tag:-soup-contains("時間") ')
        start_element = found_start[0].parent

        # <span class="f2">※ 編輯: angellll (111.249.63.175 臺灣), 12/21/2023 01:11:07 </span>
        def __find_end_element(soup):

            # found = self.soup.select(' .push ')
            # if found:
            #     found = self.soup.select(' .push ')[0]
            # else:
            #     found = self.soup.select(' #main-content .f2:-soup-contains("※ 文章網址:") ')[0]

            # ---?
            # https://www.ptt.cc/bbs/Gossiping/M.1703356436.A.F47.html
            found = self.soup.select(' #main-content .f2:-soup-contains("※ 文章網址:") ')[0]

            previous_element = None
            for element in found.previous_siblings:

                if isinstance(element, bs4.NavigableString):
                    return previous_element

                previous_element = element

        end_element = __find_end_element(self.soup)

        post_content = ""
        for element in start_element.next_siblings:

            if element == end_element:
                break
            else:
                post_content += element.get_text()

        return post_content

    def __comments(self) -> list:

        # skip richcontent
        # comments = self.soup.select(' .push  ')

        # ---?
        # https://www.ptt.cc/bbs/Gossiping/M.1703391450.A.7E7.html , 檔案過大！部分文章無法顯示
        found = self.soup.select(' #main-content .f2:-soup-contains("※ 文章網址:") ')[0]

        comments = []
        for element in found.next_siblings:

            if (isinstance(element, bs4.element.Tag)
                and element.has_attr('class')
                and "push" in element['class']
                    and "warning-box" not in element['class']):

                comments.append(element)

        return comments

    def __comment_vote(self, comment_element) -> str | None:

        found = comment_element.select(' .push-tag ')
        comment_vote = found[0].get_text()

        match comment_vote:
            case "→ ":
                return "arrow"
            case "推 ":
                return "up"
            case "噓 ":
                return "up"
            case _:
                return None

    def __comment_author(self, comment_element) -> str:

        found = comment_element.select(' .push-userid ')
        comment_author = found[0].get_text()

        return comment_author

    def __comment_content(self, comment_element) -> str:

        found = comment_element.select(' .push-content ')
        comment_content = found[0].get_text().lstrip(": ")

        return comment_content

    def __comment_ipdatetime(self, comment_element) -> str:

        found = comment_element.select(' .push-ipdatetime ')
        ipdatetime = found[0].get_text()

        return ipdatetime

    def __comment_ip(self, comment_element) -> str | None:

        match = re.search(R" (.*) \d{2}/\d{2}", self.__comment_ipdatetime(comment_element))
        if match:
            return match.group(1)
        else:
            return None

    def __comment_time(self, comment_element) -> str | None:

        match = re.search(R"\d{2}/\d{2}.*\d", self.__comment_ipdatetime(comment_element))
        if match:
            comment_time = match.group()
        else:
            return None

        # --?
        try:
            comment_time = datetime.datetime.strptime(comment_time, "%m/%d %H:%M")
        except ValueError:
            print("ValueError -------------------------------------------------")
            return None

        # use post time year
        post_time_year = datetime.datetime.fromisoformat(self.__post_time()).year
        comment_time = comment_time.replace(year=post_time_year)

        return comment_time.isoformat()

    def to_dict(self) -> dict:

        print(f"parser - to_dict , {self.html_path}")

        # result dict
        result = {}
        result["url"] = self.__post_url()
        result["post_id"] = self.__post_id()
        result["post_title"] = self.__post_title()
        result["post_author"] = self.__post_author()
        result["post_time"] = self.__post_time()

        if self.__post_ip() is None:
            print(f"skip - {result["url"]}")
            return None
        else:
            result["post_ip"] = self.__post_ip()

        result["post_content"] = self.__post_content()

        print(f"parser - to_dict , {result["post_title"]} , {result["post_id"]}")

        print(f"parser - parse comments")
        comments_raw = self.__comments()

        comments = []
        for comment_raw in tqdm(comments_raw):

            comment = {}
            comment["comment_vote"] = self.__comment_vote(comment_raw)
            comment["comment_author"] = self.__comment_author(comment_raw)
            comment["comment_content"] = self.__comment_content(comment_raw)
            comment["comment_ip"] = self.__comment_ip(comment_raw)
            comment["comment_time"] = self.__comment_time(comment_raw)

            comments.append(comment)

        #
        result["comments"] = comments

        return result

    def to_json(self, file_path) -> None:

        post_dict = self.to_dict()

        if post_dict is None:
            return None

        print(f"parser - to_json , {post_dict["post_id"]}")

        # datetime to str
        result_json = json.dumps(post_dict, indent=4, ensure_ascii=False, default=str)

        path = pathlib.Path(file_path) / (post_dict["post_id"] + ".json")
        with open(path, encoding="utf-8", mode="w") as file:
            file.write(result_json)
