import datetime
import json
import pathlib
from multiprocessing import Pool

from tqdm import tqdm
from wordcloud import WordCloud

from bubble_tea import analysis, parser, scraping



def __to_json(path, obj) -> None:

    # datetime to str
    result_json = json.dumps(obj, indent=4, ensure_ascii=False)

    with open(path, encoding="utf-8", mode="w") as file:
        file.write(result_json)

def __load_json(path):

    with open(path, mode='r') as file:

        obj = json.load(file)
        return obj



if __name__ == '__main__':

    # region # scraping -----

    scraping_ptt = scraping.Ptt()

    # scraping_ptt.save_post_list( "Gossiping" , period_start="2023-12-22" , period_end="2023-12-24" , file_path="_tests/data/post_list"  )

    def __to_html_period(file_path, board, period_start, period_end):

        start_datetime = datetime.datetime.fromisoformat(period_start)
        end_datetime = datetime.datetime.fromisoformat(period_end)

        day = datetime.timedelta(days=1)
        while end_datetime >= start_datetime:

            path = pathlib.Path(file_path) / board / end_datetime.strftime("%Y-%m-%d")
            print()
            print(f"iter - path: {path} ")

            for file in path.iterdir():
                scraping_ptt.to_html_from_post_list(file, "_tests/data/html")

            end_datetime -= day

    # __to_html_period( "_tests/data/post_list" , "Gossiping" , period_start="2023-12-22" , period_end="2023-12-24" )

    # endregion


    # region parse -----

    # test
    # parser_ptt = parser.Ptt(R"data\html\Gossiping\2023-12-23\M.1703323721.A.65C.html")
    # parser_ptt.to_dict()

    # single version
    def __parse_period(file_path, board, period_start, period_end):

        start_datetime = datetime.datetime.fromisoformat(period_start)
        end_datetime = datetime.datetime.fromisoformat(period_end)

        day = datetime.timedelta(days=1)
        while end_datetime >= start_datetime:

            path = pathlib.Path(file_path) / board / end_datetime.strftime("%Y-%m-%d")

            print()
            print(f"iter - path: {path} ")

            path_out = pathlib.Path(R"_tests/data/parsed") / board / end_datetime.strftime("%Y-%m-%d")
            path_out.mkdir(parents=True, exist_ok=True)

            for index, file in enumerate(path.iterdir()):
                print(f"__parse_period - {index} / {len(list(path.iterdir()))}")

                parser_ptt = parser.Ptt(file)
                parser_ptt.to_json(path_out)

            end_datetime -= day

    # __parse_period( "_tests/data/html" , "Gossiping" , period_start="2023-12-23" , period_end="2023-12-23" )


    # multiprocessing version
    def __task_parse_period(file_, path_out_):
        print(f"start- {file_}")
        parser_ptt = parser.Ptt(file_)
        parser_ptt.to_json(path_out_)
        print(f"end- {file_}")

    def __parse_period_mt(file_path, board, period_start, period_end):

        start_datetime = datetime.datetime.fromisoformat(period_start)
        end_datetime = datetime.datetime.fromisoformat(period_end)

        day = datetime.timedelta(days=1)
        while end_datetime >= start_datetime:

            path = pathlib.Path(file_path) / board / end_datetime.strftime("%Y-%m-%d")

            print()
            print(f"iter - path: {path} ")

            path_out = pathlib.Path(R"_tests/data/parsed") / board / end_datetime.strftime("%Y-%m-%d")
            path_out.mkdir(parents=True, exist_ok=True)

            # ----
            n = len(list(path.iterdir()))
            with Pool(processes=4) as pool, tqdm(total=n) as pbar:

                for index, file in enumerate(path.iterdir()):
                    print(f"__parse_period - {index} / {len(list(path.iterdir()))}")

                    pool.apply_async(__task_parse_period, args=(file, path_out), callback=lambda _: pbar.update(1))

                #
                pool.close()
                pool.join()

            end_datetime -= day

    # __parse_period_mt( "_tests/data/html" , "Gossiping" , period_start="2023-12-22" , period_end="2023-12-22" )

    # endregion


    # region analysis -----

    # test
    def __analysis_test0():

        analysis_ptt = analysis.Ptt(R"data\parsed\Gossiping\M.1703347205.A.34D.json")
        post_content, comment_content = analysis_ptt.all_content()

        analysis_cls = analysis.Analysis()
        tmp_themes = analysis_cls.get_themes(post_content)
        tmp_themes += analysis_cls.get_themes(comment_content)

        analysis_ptt.save(tmp_themes, "themes")

    def __analysis_test1():

        analysis_ptt = analysis.Ptt(R"data\parsed\Gossiping\M.1703394244.A.414.json")
        post = analysis_ptt.get_post()

        analysis_cls = analysis.Analysis()
        themes_count = analysis_cls.count_themes(post["themes"])

        analysis_ptt.save(themes_count, "themes_count")

    # __analysis_test1()


    # single version

    def __analysis_period(file_path, board, period_start, period_end):

        start_datetime = datetime.datetime.fromisoformat(period_start)
        end_datetime = datetime.datetime.fromisoformat(period_end)

        day = datetime.timedelta(days=1)
        while end_datetime >= start_datetime:

            path = pathlib.Path(file_path) / board / end_datetime.strftime("%Y-%m-%d")

            print()
            print(f"iter - path: {path} ")

            for index, file in enumerate(path.iterdir()):
                print(f"__analysis_period - {index}")

                analysis_ptt = analysis.Ptt(file)
                post_content, comment_content = analysis_ptt.all_content()

                analysis_cls = analysis.Analysis()
                tmp_themes = analysis_cls.get_themes(post_content)
                tmp_themes += analysis_cls.get_themes(comment_content)

                analysis_ptt.save(tmp_themes, "themes")

            #
            end_datetime -= day

    def __count_themes_period(file_path, board, period_start, period_end):

        start_datetime = datetime.datetime.fromisoformat(period_start)
        end_datetime = datetime.datetime.fromisoformat(period_end)

        day = datetime.timedelta(days=1)
        while end_datetime >= start_datetime:

            path = pathlib.Path(file_path) / board / end_datetime.strftime("%Y-%m-%d")

            print()
            print(f"iter - path: {path} ")

            for index, file in enumerate(path.iterdir()):
                print(f"__count_themes_period - {index}")

                analysis_ptt = analysis.Ptt(file)
                post = analysis_ptt.get_post()

                analysis_cls = analysis.Analysis()
                themes_count = analysis_cls.count_themes(post["themes"])

                analysis_ptt.save(themes_count, "themes_count")

            #
            end_datetime -= day

    def __sum_themes_all_period(file_path, board, period_start, period_end):

        start_datetime = datetime.datetime.fromisoformat(period_start)
        end_datetime = datetime.datetime.fromisoformat(period_end)

        analysis_cls = analysis.Analysis()

        posts_themes_count = []
        day = datetime.timedelta(days=1)
        while end_datetime >= start_datetime:

            path = pathlib.Path(file_path) / board / end_datetime.strftime("%Y-%m-%d")

            print()
            print(f"iter - path: {path} ")

            for index, file in enumerate(path.iterdir()):

                print(f"__sum_themes_all_period - {index}")

                analysis_ptt = analysis.Ptt(file)
                post = analysis_ptt.get_post()

                posts_themes_count.append(post["themes_count"])

                # !
                # if index == 5:
                #     break

            #
            end_datetime -= day

        #
        themes_count_all = analysis_cls.sum_themes_count_all(posts_themes_count)
        __to_json(R"data\parsed\all.json", themes_count_all)

    def __sum_themes_period(file_path, board, period, period_start, period_end):

        start_datetime = datetime.datetime.fromisoformat(period_start)
        end_datetime = datetime.datetime.fromisoformat(period_end)

        analysis_cls = analysis.Analysis()

        posts_themes_count = []
        posts_time = []

        day = datetime.timedelta(days=1)
        while end_datetime >= start_datetime:

            path = pathlib.Path(file_path) / board / end_datetime.strftime("%Y-%m-%d")

            print()
            print(f"iter - path: {path} ")

            for index, file in enumerate(path.iterdir()):

                print(f"__sum_themes_period - {index}")

                analysis_ptt = analysis.Ptt(file)
                post = analysis_ptt.get_post()

                #
                posts_themes_count.append(post["themes_count"])
                posts_time.append(post["post_time"])

                # tmp = {}
                # tmp["themes_count"] =
                # tmp["post_time"] =

                # posts_themes_count.append(tmp)

                # !
                # if index == 3:
                #     break

            #
            end_datetime -= day

        #
        themes_count_period = analysis_cls.sum_themes_count_by_period(posts_themes_count, posts_time, period)
        __to_json(R"data\parsed\period.json", themes_count_period)

    # __analysis_period( "_tests/data/parsed" , "Gossiping" , period_start="2023-12-24" , period_end="2023-12-24" )
    # __count_themes_period( "_tests/data/parsed" , "Gossiping" , period_start="2023-12-24" , period_end="2023-12-24" )
    # __sum_themes_all_period( "_tests/data/parsed" , "Gossiping" , period_start="2023-12-24" , period_end="2023-12-24" )
    # __sum_themes_period( "_tests/data/parsed" , "Gossiping", datetime.timedelta(hours=1) , period_start="2023-12-24" , period_end="2023-12-24" )


    # multiprocessing version
    def __task_get_themes(file_):

        analysis_ptt = analysis.Ptt(file_)
        post_content, comment_content = analysis_ptt.all_content()

        analysis_cls = analysis.Analysis()
        tmp_themes = analysis_cls.get_themes(post_content)
        tmp_themes += analysis_cls.get_themes(comment_content)

        analysis_ptt.save(tmp_themes, "themes")

        print(f"end- {file_}")

    def __analysis_period_mt(file_path, board, period_start, period_end):

        start_datetime = datetime.datetime.fromisoformat(period_start)
        end_datetime = datetime.datetime.fromisoformat(period_end)

        day = datetime.timedelta(days=1)
        while end_datetime >= start_datetime:

            path = pathlib.Path(file_path) / board / end_datetime.strftime("%Y-%m-%d")

            print()
            print(f"iter - path: {path} ")

            # ----
            n = len(list(path.iterdir()))
            with Pool(processes=7) as pool, tqdm(total=n) as pbar:

                for index, file in enumerate(path.iterdir()):
                    print(f"__analysis_period - {index} / {len(list(path.iterdir()))}")

                    pool.apply_async(__task_get_themes, args=(file,), callback=lambda _: pbar.update(1))

                    # if index == 3:
                    #     break

                #
                pool.close()
                pool.join()

            #
            end_datetime -= day

    __analysis_period_mt("_tests/data/parsed", "Gossiping", period_start="2023-12-22", period_end="2023-12-22")

    # endregion


    # region plot -----

    def __get_word_cloud(themes_dict, name="out"):

        # Generate a word cloud image
        wordcloud = WordCloud(font_path=R"data\other\SourceHanSansTC-VF.otf", width=1920, height=1080)
        wordcloud.generate_from_frequencies(themes_dict)

        # Display the generated image:
        # the matplotlib way:
        import matplotlib.pyplot as plt
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis("off")

        # plt.show()
        path = R"_tests/data/parsed/" + name + ".jpg"
        plt.savefig(path, dpi=500)

    def __get_word_cloud_period(period_list):

        for index, period in enumerate(period_list):
            print(f"__get_word_cloud_period - {index} ")

            __get_word_cloud(period["themes_count"], str(index))

    # test
    # __get_word_cloud(__load_json(R"data\parsed\Gossiping\2023-12-24\M.1703394244.A.414.json")["themes_count"])

    #
    # __get_word_cloud(__load_json(R"data\parsed\all.json"))
    # __get_word_cloud_period(__load_json(R"data\parsed\period.json"))

    # endregion


    print()
