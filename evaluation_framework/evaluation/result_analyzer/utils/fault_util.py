import datetime
import os
import random
import re
import traceback
from enum import Enum
from typing import List, Tuple, Optional, Dict, Iterable, Set, NamedTuple

import pandas as pd

from android_testing_utils.log import my_logger
from constant import PlatformConstant
from evaluation.result_analyzer.utils.path_util import PathUtil


class AbstractItem(NamedTuple):
    abstract: str
    occur_time: str
    relative_time: float


class FaultDomain(Enum):
    Fatal = "F"
    Vital = "V"
    E_plus = "E+"
    E_all = "E"


class LogcatUtil:
    @staticmethod
    def get_real_code_package_identifier(raw_package):
        parts = raw_package.split('.')

        common_android_words = ["java", "android", "androidx", "com", "org", "kotlin", "kotlinx"]
        postfix_words = ['debug', 'release', 'test', 'alpha', 'beta', 'dev', 'edition', "free"]

        for postfix in postfix_words:
            if postfix in parts[-1]:
                parts = parts[:-1]
                for postfix2 in postfix_words:
                    if postfix2 in parts[-1]:
                        parts = parts[:-1]
                        break
                break

        for i in range(len(parts)):
            if parts[i] in common_android_words:
                continue
            else:
                return '.'.join(parts[i:])

        return '.'.join(parts)

    @staticmethod
    def get_domain_of_logcat_line(logcat_line):
        if ' E ' in logcat_line:
            return logcat_line[logcat_line.index(' E ') + 2:logcat_line[19:].index(':') + 19].strip()
        elif ' F ' in logcat_line:
            return logcat_line[logcat_line.index(' F ') + 2:logcat_line[19:].index(':') + 19].strip()
        else:
            my_logger.hint(my_logger.LogLevel.WARNING, "LogcatUtil", False, f"Wrong with line [{logcat_line}]")

    @staticmethod
    def collect_stack_trace(
            logcat_lines: List[str],
            start_line_index: int,
            content_start_pos: int,
            content_domain: str,
            code_package_identifier: str
    ) -> Tuple[List[str], Optional[str]]:
        res = []
        i = start_line_index
        j = 0
        first_code_position_line = None
        while (
                (i + j < len(logcat_lines)) and
                (not logcat_lines[i+j].startswith('-')) and
                (not logcat_lines[i+j][content_start_pos:].strip() == '') and
                (LogcatUtil.get_domain_of_logcat_line(logcat_lines[i+j]) == content_domain)
        ):
            current_line = logcat_lines[i+j][content_start_pos:]
            res.append(current_line)
            if (
                    (first_code_position_line is None) and
                    (current_line.strip().startswith("at")) and
                    (code_package_identifier in current_line)
            ):
                first_code_position_line = current_line
            j += 1
        return res, first_code_position_line

    @classmethod
    def function_info_filter(cls, function_info: str):
        function_info = re.sub(r'\{.*}', '{_}', function_info)
        function_info = re.sub(r'@.*\[', '@_[', function_info)
        function_info = re.sub(r'@.* ', '@_ ', function_info)
        function_info = re.sub(r'/\S+/(\S/?)+', '/.../...', function_info)
        return function_info

    E_PLUS_LIST = ["AndroidRuntime", "CrashAnrDetector", "ActivityManager", "SQLiteDatabase", "WindowManager", "ActivityThread", "Parcel"]

    @classmethod
    def get_num_of_different_bugs(cls, abstract_keys: Iterable[str]) -> Dict[FaultDomain, int]:
        bug_domain_list = [item.split('|')[1].strip() for item in abstract_keys]
        fatal_count = bug_domain_list.count("FATAL")
        anr_count = bug_domain_list.count("ANR")
        e_plus_count = 0
        for bug_domain in bug_domain_list:
            if bug_domain.startswith("E:") and bug_domain[2:] in cls.E_PLUS_LIST:
                e_plus_count += 1
        return {
            FaultDomain.Fatal: fatal_count,
            FaultDomain.Vital: fatal_count + anr_count,
            FaultDomain.E_plus: fatal_count + anr_count + e_plus_count,
            FaultDomain.E_all: len(bug_domain_list),
        }

    @classmethod
    def get_type_of_bug_key(cls, bug_key: str) -> FaultDomain:
        bug_domain = bug_key.split('|')[1].strip()
        if bug_domain == "FATAL":
            return FaultDomain.Fatal
        elif bug_domain == "ANR":
            return FaultDomain.Vital
        elif bug_domain.startswith("E:") and bug_domain[2:] in cls.E_PLUS_LIST:
            return FaultDomain.E_plus
        else:
            return FaultDomain.E_all


class FaultResUtil:
    @staticmethod
    def remove_duplicate_bugs(bug_abstract_dict: Dict[str, List]):
        raw_keys = list(bug_abstract_dict.keys())
        raw_keys.sort(key=lambda x: 1 if "| FATAL |" in x else 2 if "| ANR |" in x else 3)
        res = {}
        for raw_key in raw_keys:
            if '|'.join(raw_key.split('|')[-2:]) in ['|'.join(item.split('|')[-2:]) for item in res.keys()]:
                # print("Duplicate:", raw_key)
                continue
            else:
                res[raw_key] = bug_abstract_dict[raw_key]
        return res

    @classmethod
    def get_unique_bugs(cls, raw_group: List[Tuple[str, Set]]) -> List[Tuple[str, Set]]:
        n = len(raw_group)
        res_group = []
        for i in range(n):
            current_i_res: Set = raw_group[i][1]
            for j in range(n):
                if j != i:
                    current_i_res = current_i_res.difference(raw_group[j][1])
            res_group.append((raw_group[i][0], current_i_res))
        return res_group

    @classmethod
    def get_combine_faults(cls, raw_group: List[Tuple[str, Set]], k: int) -> List[Tuple[str, Set]]:
        n = len(raw_group)
        res_group = []
        for i in range(n):
            current_i_res: Set = set()
            for j in random.choices(range(n), k=k):
                current_i_res = current_i_res.union(raw_group[j][1])
            res_group.append((raw_group[i][0], current_i_res))
        return res_group


class BugUtil:
    @staticmethod
    def bug_type_compare(all_data: Dict[str, Dict[str, List]]):
        items = all_data.keys()

        bug_keys = set()
        for item, data in all_data.items():
            bug_keys = bug_keys.union(set(data.keys()))

        res = pd.DataFrame(columns=items, index=bug_keys)

        for item, data in all_data.items():
            for bug_key, detail_list in data.items():
                res.at[bug_key, item] = len(detail_list)

        res = res.sort_index(axis=0)
        return res

    @staticmethod
    def combine_dict_of_lists(raw_dict: Dict, new_dict: Dict):
        for key, value in new_dict.items():
            if key in raw_dict:
                raw_dict[key].extend(value)
            else:
                raw_dict[key] = value
        return raw_dict

    @staticmethod
    def output_bug_data(data: Dict[str, List[AbstractItem]], detail_level=2):
        my_logger.hint(my_logger.LogLevel.INFO, "BugUtil", False, f"Unique bug count: {len(data.keys())}")
        if detail_level >= 1:
            sorted_data: List[Tuple[str, List[AbstractItem]]] = sorted(data.items(), key=lambda x: len(x[1]), reverse=True)
            for i in range(len(sorted_data)):
                bug_key = sorted_data[i][0]
                bug_occurrence_list = sorted_data[i][1]
                print(f"No.{i + 1:<2} [KEY] {bug_key}")
                if detail_level >= 2:
                    for j in range(min(3, len(bug_occurrence_list))):
                        print(f"---------- Example {j+1} ---------- {bug_occurrence_list[j].occur_time}({bug_occurrence_list[j].relative_time:.2f}s)")
                        print(bug_occurrence_list[j].abstract)
                    if len(bug_occurrence_list) > 3:
                        print(f"... Total {len(bug_occurrence_list)}")
                    print()
                else:
                    print(f"Occur time: {len(bug_occurrence_list)}")
        print()
        print()

    @staticmethod
    def bug_file_to_abstract_dict(absolute_file_path: str, target_time: int = None, print_error: bool = False) -> Dict[str, List[AbstractItem]]:
        res: Dict[str, List[AbstractItem]] = {}

        target_package = PathUtil.get_package_from_logcat_file_path(absolute_file_path)
        code_package_identifier = LogcatUtil.get_real_code_package_identifier(target_package)
        # print(f"{target_package} -> {code_package_identifier}")
        app_name = PathUtil.get_app_name_from_logcat_file_path(absolute_file_path)

        start_time_str = absolute_file_path.split('/')[-1].split('_')[1]
        start_time = datetime.datetime.strptime(start_time_str, "%Y-%m-%d-%H:%M:%S")

        try:
            logcat_info = open(absolute_file_path, 'r').read()
        except UnicodeDecodeError as e:
            if print_error:
                traceback.print_exc()
                print("UnicodeDecodeError:", absolute_file_path)
            logcat_info = open(absolute_file_path, 'r', errors='ignore').read()

        lines = logcat_info.split('\n')

        i = 0
        while i < len(lines):
            occur_time = lines[i][:18]
            relative_time = None
            try:
                current_time_year = start_time_str.split('-')[0]
                if occur_time.startswith("01") and start_time_str.split('-')[1] == "12":
                    current_time_year = str(int(current_time_year) + 1)
                current_time = datetime.datetime.strptime(f"{current_time_year}-{occur_time}", "%Y-%m-%d %H:%M:%S.%f")
                relative_time = abs((current_time - start_time).total_seconds())
                if target_time is not None and relative_time > target_time:
                    break
            except Exception as e:
                pass

            key = None
            abstract = None

            try:
                if ("FATAL EXCEPTION" in lines[i]) and (i+1 < len(lines) and target_package in lines[i+1]):
                    content_start_pos = lines[i].index("FATAL EXCEPTION")
                    content_domain = LogcatUtil.get_domain_of_logcat_line(lines[i])

                    current_bug_info, first_code_position_line = LogcatUtil.collect_stack_trace(
                        logcat_lines=lines,
                        start_line_index=i,
                        content_start_pos=content_start_pos,
                        content_domain=content_domain,
                        code_package_identifier=code_package_identifier,
                    )

                    exception_name = None
                    for line in current_bug_info:
                        if "Exception:" in line:
                            exception_name = line.split(":")[0]
                            break
                    if exception_name is None:
                        exception_name = current_bug_info[2]

                    function_info = first_code_position_line if first_code_position_line is not None \
                        else current_bug_info[3] if len(current_bug_info) >= 4 else current_bug_info[-1]
                    function_info = LogcatUtil.function_info_filter(function_info)
                    function_info = function_info.strip()

                    key = f"{app_name} | FATAL | {exception_name} | {function_info}"
                    abstract = '\n'.join(current_bug_info)

                    i += len(current_bug_info) - 1
                elif ("ANR" in lines[i]) and (target_package in lines[i]):
                    content_start_pos = lines[i].index("ANR")

                    current_bug_info = []
                    for offset in range(3):
                        current_bug_info.append(lines[i+offset][content_start_pos:])

                    module_info = ""
                    if '(' in current_bug_info[0]:
                        module_info = current_bug_info[0].split('(')[1].split(')')[0]

                    reason_info = re.sub(r'[0-9]+', '_', current_bug_info[2])

                    key = f"{app_name} | ANR | {module_info} | {reason_info}"
                    abstract = '\n'.join(current_bug_info)

                    i += len(current_bug_info) - 1

                    if "act=com.example.pkg.END_EMMA" in abstract:
                        continue
                else:
                    # if (
                    #         lines[i].startswith('-') or
                    #         (i + 1 < len(lines) and lines[i + 1].startswith('-')) or
                    #         lines[i].strip() == '' or
                    #         (i + 1 < len(lines) and lines[i + 1].strip() == '')
                    # ):
                    if (
                        (lines[i] == '' or (not lines[i][0].isdigit())) or
                        (i + 1 < len(lines) and (lines[i+1] == '' or (not lines[i + 1][0].isdigit())))
                    ):
                        i += 1
                        continue

                    content_start_pos = lines[i][19:].index(':') + 19 + 1
                    content_domain = LogcatUtil.get_domain_of_logcat_line(lines[i])

                    if (
                            (not lines[i][content_start_pos:].strip() == "") and
                            (not lines[i][content_start_pos:].strip().startswith("at ")) and
                            (not lines[i][content_start_pos:].strip().startswith("Caused by: ")) and
                            (
                                    i+1 < len(lines) and
                                    LogcatUtil.get_domain_of_logcat_line(lines[i+1]) == content_domain and
                                    lines[i+1][content_start_pos:].strip().startswith("at ")
                            )
                    ):
                        current_bug_info, first_code_position_line = LogcatUtil.collect_stack_trace(
                            logcat_lines=lines,
                            start_line_index=i,
                            content_start_pos=content_start_pos,
                            content_domain=content_domain,
                            code_package_identifier=code_package_identifier,
                        )

                        exception_name = current_bug_info[0].strip().split(':')[0] if ':' in current_bug_info[0] else current_bug_info[0].strip()

                        function_info = first_code_position_line if first_code_position_line is not None else current_bug_info[0].strip()[len(exception_name)+2:]
                        function_info = LogcatUtil.function_info_filter(function_info)
                        function_info = function_info.strip()

                        key = f"{app_name} | E:{content_domain} | {exception_name} | {function_info}"
                        abstract = '\n'.join(current_bug_info)

                        i += len(current_bug_info) - 1

                        if code_package_identifier not in abstract:
                            key = None
                            abstract = None
                if key is not None:
                    current_abstract_item = AbstractItem(abstract, occur_time, relative_time)
                    if key not in res:
                        res[key] = []
                    res[key].append(current_abstract_item)
            except Exception as e:
                print(absolute_file_path)
                print(i, lines[i])
                raise e
            i += 1
        res = FaultResUtil.remove_duplicate_bugs(res)
        return res


class ANRAnalyzer:
    @staticmethod
    def search_for_non_empty_dirs():
        anr_root_path = PlatformConstant.ANR_BUG_ROOT_DIR
        for tag in os.listdir(anr_root_path):
            tag_path = os.path.join(anr_root_path, tag)
            for app_package in os.listdir(tag_path):
                package_path = os.path.join(tag_path, app_package)
                anr_path = os.path.join(package_path, "anr")
                anr_files = os.listdir(anr_path)
                if len(anr_files) > 0:
                    if "dumptrace_dqyNui" in anr_files:
                        anr_files.remove("dumptrace_dqyNui")
                    if len(anr_files) > 0:
                        print(f"{anr_path}: {len(anr_files)}")


def get_bug_statistic_data(bug_file_path):
    res = {}

    abstract_dict = BugUtil.bug_file_to_abstract_dict(bug_file_path)
    res["total_unique_bugs"] = len(abstract_dict.keys())

    total_count = 0
    for key, value in abstract_dict.items():
        total_count += len(value)
    res["total_bugs"] = total_count
    res["bug_details"] = abstract_dict
    return res


# if __name__ == '__main__':
    # ANRAnalyzer.search_for_non_empty_dirs()

    # p = "/DATA/experimental_results/logcat_bug/empirical-08162-dqt-1/Apps.AntennaPod_2024-01-11-16:13:47_empirical-08162-dqt-1_bug.txt"
    # res = BugUtil.bug_file_to_abstract_dict(p)
    # BugUtil.output_bug_data(res, detail_level=2)
