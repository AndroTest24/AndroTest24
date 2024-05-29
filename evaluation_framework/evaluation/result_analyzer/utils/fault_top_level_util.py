# ----------------------
# @Time  : 2024 May
# @Author: Anonymity
# ----------------------
import multiprocessing
import os
from typing import Optional, List, Tuple, Dict

from android_testing_utils.log import my_logger
from constant import PlatformConstant
from evaluation.result_analyzer.utils.fault_util import AbstractItem, BugUtil
from evaluation.result_analyzer.utils.pattern_util import PatternUtil


class BugAnalyzer:
    @staticmethod
    def analyze(
            app_str: Optional[str],
            pattern: Optional[str],
            tag_list: Optional[List[str]],
            detail_level: int,
            show_each: bool = True,
            show_final: bool = True,
            target_time: int = None,
            only_save_one_for_each_file_when_combining : bool = False,
    ) -> Tuple[
        Dict[str, Dict[str, List[AbstractItem]]],
        Dict[str, List[AbstractItem]]
    ]:
        my_logger.hint(my_logger.LogLevel.INFO, "BugUtil", False,
                       f"########## Bug Analyze For App [{app_str}], Pattern [{pattern}] ##########")

        if tag_list is None:
            tag_list = list(sorted(os.listdir(PlatformConstant.LOGCAT_BUG_ROOT_DIR)))

        if pattern is not None:
            tag_list = [item for item in tag_list if PatternUtil.is_match(pattern, item)]

        target_files = []
        for tag in tag_list:
            dir_path = os.path.join(PlatformConstant.LOGCAT_BUG_ROOT_DIR, tag)
            temp_file_list = [item for item in os.listdir(dir_path) if "bug" in item]
            if app_str is not None:
                temp_file_list = [item for item in temp_file_list if item.startswith(app_str)]
            for file in temp_file_list:
                target_files.append(os.path.join(dir_path, file))
        target_files = sorted(target_files)

        all_file_data = {}

        param = [(file_path, target_time) for file_path in target_files]
        with multiprocessing.Pool(12) as pool:
            my_logger.hint(my_logger.LogLevel.INFO, "BugUtil", True, f"Start analyzing bug data with multiprocessing...")
            res = pool.starmap(BugUtil.bug_file_to_abstract_dict, param)
        for i in range(len(target_files)):
            all_file_data[target_files[i]] = res[i]
            if show_each:
                my_logger.hint(my_logger.LogLevel.INFO, "BugUtil", False, f"##### As For File [{target_files[i][target_files[i][:target_files[i].rindex('/')].rindex('/')+1:]}] #####")
                BugUtil.output_bug_data(res[i], detail_level)

        if only_save_one_for_each_file_when_combining:
            for file_name, bug_data in all_file_data.items():
                for bug_key, bug_list in bug_data.items():
                    all_file_data[file_name][bug_key] = bug_list[:1]

        my_logger.hint(my_logger.LogLevel.INFO, "BugUtil", True, f"Start combining bug data ...")
        combined_result = {}
        for item in all_file_data.values():
            combined_result = BugUtil.combine_dict_of_lists(combined_result, item)

        if show_final:
            my_logger.hint(my_logger.LogLevel.INFO, "BugUtil", False, f"##### ALL #####")
            BugUtil.output_bug_data(combined_result, detail_level)

        return all_file_data, combined_result

    @staticmethod
    def analyze_bug_files(
            app_list: List[str] = None,
            prefix: Optional[str] = None,
            tag_list: Optional[List[str]] = None,
            detail_level: int = 0,
            show_each: bool = True,
            show_final: bool = True,
    ):
        if app_list is None:
            res = BugAnalyzer.analyze(
                app_str=None,
                pattern=prefix,
                tag_list=tag_list,
                detail_level=detail_level,
                show_each=show_each,
                show_final=show_final,
            )[1]
        else:
            res = {}
            for app in app_list:
                res[app] = BugAnalyzer.analyze(
                    app_str=app,
                    pattern=prefix,
                    tag_list=tag_list,
                    detail_level=detail_level,
                    show_each=show_each,
                    show_final=show_final,
                )[1]
        return res


class Compare:
    @staticmethod
    def compare_all_bug_type_by_prefixes(prefix_list: List[str]):
        all_data = {}
        for prefix in prefix_list:
            all_data[prefix] = BugAnalyzer.analyze_bug_files(
                app_list=None,
                prefix=prefix,
                tag_list=None,
                detail_level=0,
                show_each=False,
                show_final=False,
            )
        print(BugUtil.bug_type_compare(all_data))

    @staticmethod
    def compare_unique_bug_num_by_prefixes(base_prefix: str, compare_prefix_list: List[str]):
        def get_unique_bug_list(prefix):
            return sorted(list(set(
                BugAnalyzer.analyze_bug_files(
                    app_list=None,
                    prefix=prefix,
                    tag_list=None,
                    detail_level=0,
                    show_each=False,
                    show_final=False,
                ).keys()
            )))

        base_unique_bug_keys = get_unique_bug_list(base_prefix)
        compare_unique_bug_keys_list = [get_unique_bug_list(item) for item in compare_prefix_list]

        all_unique_bug_keys_list = [base_unique_bug_keys]
        all_unique_bug_keys_list.extend(compare_unique_bug_keys_list)
        n = len(all_unique_bug_keys_list)

        # unique count
        for i in range(n):
            print(len(all_unique_bug_keys_list[i]), end=(' 'if i < n-1 else '\n'))

        # characteristic count
        for i in range(n):
            temp_set = set(all_unique_bug_keys_list[i])
            for j in range(n):
                if j != i:
                    temp_set = temp_set.difference(all_unique_bug_keys_list[j])
            print(len(temp_set), end=(' 'if i < n-1 else '\n'))

        # intersection count
        for i in range(n):
            print(len(set(base_unique_bug_keys).intersection(all_unique_bug_keys_list[i])), end=(' 'if i < n-1 else '\n'))

        # union count
        for i in range(n):
            print(len(set(base_unique_bug_keys).union(all_unique_bug_keys_list[i])), end=(' 'if i < n-1 else '\n'))

        # all union count
        res = set()
        for i in range(n):
            res = res.union(all_unique_bug_keys_list[i])
        print(len(res))


# if __name__ == '__main__':
    # Compare.compare_all_bug_type_by_prefixes(["DQT-1125", "APE-1012", "QT-1012", "ARES-1012", "Monkey-1012"])
    # Compare.compare_unique_bug_num_by_prefixes(
    #     "DQT-1125",
    #     ["APE-1012", "QT-1012", "ARES-0622", "Stoat-0609", "DeepGUIT-0616", "Monkey-1012"]
    # )

    # BugAnalyzer.analyze_bug_files(
    #     app_list=None,
    #     tag_list=None,
    #     detail_level=1,
    #     show_each=False,
    #     show_final=True,
    # )