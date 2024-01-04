import datetime
import json
import re

import pandas as pd
from tqdm import tqdm



class Ptt:

    def __init__(self, json_path: str) -> None:

        self.json_path = json_path

        self.post = self.__from_json(json_path)

    def __from_json(self, json_path: str) -> str:

        with open(json_path, mode='r') as file:

            post_json = json.load(file)
            return post_json

    def __to_json(self) -> None:

        # datetime to str
        result_json = json.dumps(self.post, indent=4, ensure_ascii=False, default=str)

        with open(self.json_path, encoding="utf-8", mode="w") as file:
            file.write(result_json)

    def get_post(self) -> dict:
        return self.post

    def all_content(self) -> tuple[str, str]:

        def __filter_news(post_content):

            remove_str = ["1.媒體來源:", "2.記者署名:", "3.完整新聞標題:", "4.完整新聞內文:",
                          "5.完整新聞連結 (或短網址)不可用YAHOO、LINE、MSN等轉載媒體:", "6.備註:"]

            for val in remove_str:
                post_content = post_content.replace(val, "")

            return post_content

        post_content = __filter_news(self.post["post_content"]).replace('\n', "")

        comment_content_list = []
        for comment in self.post["comments"]:
            comment_content_list.append(comment["comment_content"])

        comment_content = "".join(comment_content_list)

        # remove url
        # https://stackoverflow.com/questions/3809401/what-is-a-good-regular-expression-to-match-a-url
        patt = re.compile(R"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)")
        post_content = patt.sub("", post_content)
        comment_content = patt.sub("", comment_content)

        return post_content, comment_content

    def save(self, to_save, key: str) -> None:

        print(f"save - {self.post["post_id"]} , {self.post["post_title"]} ------")

        self.post[key] = to_save

        self.__to_json()


class Analysis:

    def __init__(self) -> None:
        pass

    def __load_drop_dict(self, dict_path) -> list:

        loaded = []
        with open(dict_path, mode='r', encoding="utf-8") as file:

            for line in file:

                tmp = line.rstrip('\n')
                if tmp != "":
                    loaded.append(tmp)

        return loaded

    def get_themes(self, string: str) -> list:

        print(f"get_themes ......")

        import jieba
        jieba.set_dictionary(R'_tests/data/other/dict.txt.big')  # 支持繁体分词更好的词典文件 https://github.com/fxsjy/jieba/raw/master/extra_dict/dict.txt.big
        jieba.load_userdict(R"_tests/data/other/dict_t1.txt")

        # 精确模式
        seg_list = jieba.cut(string)

        result_list = list(seg_list)
        # print("|".join(result_list))

        return result_list

    def count_themes(self, themes: list) -> dict:
        """ sum count by same theme """

        print(f"count_themes ......")

        df = pd.DataFrame(themes)
        df.columns = ["themes"]

        # group by same theme and sort by count
        df_groupby = df.groupby(by=["themes"], as_index=False).size()
        df_groupby = df_groupby.sort_values(by=["size"], ascending=False)
        df_groupby = df_groupby.set_index("themes")

        # ignore words
        to_drop = self.__load_drop_dict(R"data\parsed\drop_dict.txt")
        df_ignored = df_groupby.drop(to_drop, errors='ignore')

        # to dict
        result = df_ignored.to_dict('dict')["size"]

        return result

    def sum_themes_count_all(self, posts_themes_count: list) -> dict:

        print(f"sum_themes_count_all ......")

        df = pd.DataFrame(posts_themes_count).T
        df.index.name = "themes"

        df_sum = pd.DataFrame(df.sum(axis="columns"), columns=['count'])

        # --?
        to_drop = self.__load_drop_dict(R"data\parsed\drop_dict.txt")
        df_sum = df_sum.drop(to_drop, axis="index", errors="ignore")

        df_sum['count'] = df_sum['count'].astype(int)
        df_sum = df_sum.sort_values(by=["count"], ascending=False)

        # to dict
        result = df_sum.to_dict()["count"]

        return result

    def sum_themes_count_by_period(self, posts_themes_count: list, posts_time: list, period: datetime.timedelta) -> list:
        """ sum count by same theme with period """

        print(f"sum_themes_count_by_period ......")

        # init
        df = pd.DataFrame(posts_themes_count).transpose()
        df.columns = posts_time

        # utc str to datetime
        df = df.transpose()
        df.insert(0, "datetime", pd.to_datetime(df.index))

        # sum by period
        df_sum = df.groupby(pd.Grouper(key="datetime", freq=period)).sum()

        # order by descending with all sum count
        df_ordered = df_sum.T

        df_ordered.insert(0, "sum_count", df_ordered.sum(axis="columns"))
        df_ordered = df_ordered.sort_values(by=["sum_count"], ascending=False)

        # --?
        to_drop = self.__load_drop_dict(R"data\parsed\drop_dict.txt")
        df_ordered = df_ordered.drop(to_drop, axis="index", errors="ignore")

        #
        df_ordered = df_ordered.drop("sum_count", axis="columns")
        df_ordered = df_ordered.head(50).T.astype(int)

        # to dict
        result_dict = df_ordered.to_dict("index")

        results = []
        for key, value in result_dict.items():

            count_by_period = {}
            count_by_period["post_time"] = key.isoformat()
            count_by_period["themes_count"] = value

            results.append(count_by_period)

        return results
