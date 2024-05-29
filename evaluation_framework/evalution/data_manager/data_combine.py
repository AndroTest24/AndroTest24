# ----------------------
# @Time  : 2024 May
# @Author: Anonymity
# ----------------------
import os
import shutil
import time
from typing import List, Dict, Optional, Tuple

import numpy as np

from android_testing_utils.log import my_logger
from constant import PlatformConstant
from evalution.result_analyzer.utils.coverage_util import CoverageTimeUtil, CoverageDataUtil
from evalution.result_analyzer.utils.pattern_util import PatternUtil
from runtime_collection import unified_testing_config
from runtime_collection.collector_util.util_coverage import CoverageItem, CoverageDetail, CoverageDetailWithStd, \
    get_readable_final_coverage_info_string


class CoverageCombine:
    @staticmethod
    def __combine_coverage_raw_data_lists(
            raw_data_lists: List[List[CoverageItem]],
            need_std: bool = False,
            recalculate_std: bool = True,
            recalculate_rate: bool = True,
            same_package: bool = True,
    ):
        """Raw data combination for data lists."""
        full_time_list = []
        for raw_data in raw_data_lists:
            full_time_list.extend([i.time for i in raw_data])
        full_time_list = sorted(list(set(full_time_list)))

        for i in range(len(raw_data_lists)):
            raw_data_lists[i] = CoverageTimeUtil.padding_data(raw_data_lists[i], full_time_list)

        combined_coverage_data = []
        for i in range(len(full_time_list)):
            covered_list: List[float] = []
            total_list: List[float] = []
            rate_list: List[float] = []

            if not recalculate_std:
                std_list: List[float] = []
                std_upper_list: List[float] = []
                std_lower_list: List[float] = []

            for raw_data in raw_data_lists:
                assert raw_data[i].time == full_time_list[i]
                covered_list.append(raw_data[i].detail.covered)
                total_list.append(raw_data[i].detail.total)
                rate_list.append(raw_data[i].detail.rate)
                if not recalculate_std:
                    std_list.append(raw_data[i].detail.std)
                    std_upper_list.append(raw_data[i].detail.std_upper)
                    std_lower_list.append(raw_data[i].detail.std_lower)

            covered_avg = round(float(np.mean(covered_list)), 2)
            total = round(float(np.mean(total_list)), 2)
            if recalculate_rate:
                rate_avg = round(covered_avg / total, 4)
            else:
                rate_avg = round(float(np.mean(rate_list)), 4)
            if same_package:
                assert (np.array(total_list) == total).all()

            if not need_std:
                detail = CoverageDetail(
                    covered=covered_avg,
                    total=total,
                    rate=rate_avg
                )
            else:
                if not recalculate_std:
                    std = round(float(np.mean(std_list)), 4)
                    std_lower = round(float(np.mean(std_lower_list)), 4)
                    std_upper = round(float(np.mean(std_upper_list)), 4)
                else:
                    std = round(np.std(np.array(covered_list) / total), 4)
                    std_lower = round(rate_avg - std, 4)
                    std_upper = round(rate_avg + std, 4)
                detail = CoverageDetailWithStd(
                    covered=covered_avg,
                    total=total,
                    rate=rate_avg,
                    std=std,
                    std_lower=std_lower,
                    std_upper=std_upper
                )

            combined_coverage_data.append(
                CoverageItem(
                    full_time_list[i],
                    detail
                )
            )

        return CoverageDataUtil.extend_coverage_data_list_with_standard_time_series(
            combined_coverage_data, PlatformConstant.TIME_LENGTH, PlatformConstant.TIME_INTERVAL, need_std
        )

    @staticmethod
    def __combine_coverage_raw_data_dicts(
            raw_data_dicts: List[Dict[str, List[CoverageItem]]],
            need_std: bool,
            recalculate_std: bool,
            recalculate_rate: bool,
            same_package: bool,
    ):
        """Raw data combination for data dicts (with different types)."""
        res: Dict[str, List[CoverageItem]] = {}
        for data_type in raw_data_dicts[0].keys():
            raw_data_list = [data[data_type] for data in raw_data_dicts]
            res[data_type] = CoverageCombine.__combine_coverage_raw_data_lists(
                raw_data_lists=raw_data_list,
                need_std=need_std,
                recalculate_std=recalculate_std,
                recalculate_rate=recalculate_rate,
                same_package=same_package,
            )
        return res

    @staticmethod
    def __combine_packages_with_tag_pattern(
            tag_pattern: str,
            need_std: bool = False,
            target_apps: Optional[List[unified_testing_config.Apps]] = None,
    ):
        for package in os.listdir(PlatformConstant.COVERAGE_DATA_ROOT_DIR):
            if (target_apps is not None) and (unified_testing_config.get_app_by_package_name(package) not in target_apps):
                continue
            package_dir = os.path.join(PlatformConstant.COVERAGE_DATA_ROOT_DIR, package)

            data_to_combine: List[Dict[str, List[CoverageItem]]] = []
            tag_to_combine = []
            for tag in os.listdir(package_dir):
                if PatternUtil.is_match(tag_pattern, tag):
                    tag_to_combine.append(tag)
                    tag_dir = os.path.join(package_dir, tag)

                    temp = {}
                    if len(os.listdir(tag_dir)) != 4:
                        my_logger.hint(my_logger.LogLevel.WARNING, "DataUtil", False, f"Not 4 items, Continue! {tag_dir}")
                        continue
                    for file in os.listdir(tag_dir):
                        if file.endswith(".npy"):
                            data: Dict[str, List[CoverageItem]] = np.load(os.path.join(tag_dir, file), allow_pickle=True).item()
                            temp.update(data)
                    data_to_combine.append(temp)

            if len(tag_to_combine) == 0:
                my_logger.hint(my_logger.LogLevel.WARNING, "DataUtil", False, f"Nothing to combine for {package}")
                continue

            combine_tag = tag_pattern.replace('**', '') if '**' in tag_pattern else tag_pattern[:-1]
            save_dir = os.path.join(package_dir, f"{combine_tag}@{len(data_to_combine)}")
            if os.path.exists(save_dir):
                s = input(f"Path {save_dir} exists, remove?(y/n)")
                if s == 'y':
                    shutil.rmtree(save_dir)
                else:
                    print("Don't remove, continue!")
                    continue

            os.makedirs(save_dir)

            file_name_prefix = f"{package}_Coverage_{time.strftime('%Y-%m-%d-%H:%M:%S', time.localtime())}"
            raw_file_path = os.path.join(save_dir, f"{file_name_prefix}.npy")
            log_file_path = os.path.join(save_dir, f"{file_name_prefix}.txt")

            res = CoverageCombine.__combine_coverage_raw_data_dicts(
                raw_data_dicts=data_to_combine,
                need_std=need_std,
                recalculate_std=True,
                recalculate_rate=True,
                same_package=True,
            )

            np.save(raw_file_path, res)

            res_string = get_readable_final_coverage_info_string(res)
            with open(log_file_path, 'w') as f:
                f.write(res_string)
                my_logger.hint(my_logger.LogLevel.INFO, "DataUtil", False,
                               f"Combined Coverage Result save to {log_file_path}")
            my_logger.hint(my_logger.LogLevel.INFO, "DataUtil", False, f"{package}  {tag_to_combine}:{len(tag_to_combine)}")

    @staticmethod
    def __combine_to_one_with_tag_list(
            tag_list: List[str],
            combined_tag: str,
            need_std: bool,
    ):

        expected_file_num = 2 if '@' in tag_list[0] else 4

        data_to_combine: List[Dict[str, List[CoverageItem]]] = []
        target_to_combine: List[Tuple[str, str]] = []

        for package in os.listdir(PlatformConstant.COVERAGE_DATA_ROOT_DIR):
            package_dir = os.path.join(PlatformConstant.COVERAGE_DATA_ROOT_DIR, package)

            for tag in os.listdir(package_dir):
                if tag in tag_list:
                    tag_dir = os.path.join(package_dir, tag)
                    temp = {}
                    if len(os.listdir(tag_dir)) != expected_file_num:
                        my_logger.hint(my_logger.LogLevel.WARNING, "DataUtil", False, f"Not {expected_file_num} items, Continue! {tag_dir}")
                        continue
                    for file in os.listdir(tag_dir):
                        if file.endswith(".npy"):
                            data: Dict[str, List[CoverageItem]] = np.load(os.path.join(tag_dir, file), allow_pickle=True).item()
                            temp.update(data)

                    target_to_combine.append((package, tag))
                    temp = CoverageTimeUtil.normalize_time_for_data_dict(temp, PlatformConstant.TIME_LENGTH)
                    temp = CoverageDataUtil.extend_coverage_data_dict_with_standard_time_series(temp, PlatformConstant.TIME_LENGTH, PlatformConstant.TIME_INTERVAL, need_std)
                    temp = CoverageDataUtil.filter_coverage_data_dict_with_standard_time_series(temp, PlatformConstant.TIME_LENGTH, PlatformConstant.TIME_INTERVAL)
                    data_to_combine.append(temp)

        if len(target_to_combine) == 0:
            my_logger.hint(my_logger.LogLevel.WARNING, "DataUtil", False, f"Nothing to combine for {tag_list}, exit!")
            return
        else:
            print(f"The following [{len(data_to_combine)}] targets will be combined!")
            for target in target_to_combine:
                print(f"\t{target}")
            s = input("Continue?(y/n)")
            if s != 'y':
                print("Exit!")
                return

        save_dir = os.path.join(PlatformConstant.STATISTICS_DATA_ROOT_DIR, f"{combined_tag}@{len(data_to_combine)}")
        if os.path.exists(save_dir):
            s = input(f"Path {save_dir} exists, remove?(y/n)")
            if s == 'y':
                shutil.rmtree(save_dir)
            else:
                print("Don't remove, exit!")
                return

        os.makedirs(save_dir)

        file_name_prefix = f"{combined_tag}_Coverage_{time.strftime('%Y-%m-%d-%H:%M:%S', time.localtime())}"
        raw_file_path = os.path.join(save_dir, f"{file_name_prefix}.npy")
        log_file_path = os.path.join(save_dir, f"{file_name_prefix}.txt")

        res = CoverageCombine.__combine_coverage_raw_data_dicts(
            raw_data_dicts=data_to_combine,
            need_std=need_std,
            recalculate_std=False,
            recalculate_rate=False,
            same_package=False,
        )

        np.save(raw_file_path, res)

        res_string = get_readable_final_coverage_info_string(res)
        with open(log_file_path, 'w') as f:
            f.write(res_string)
            my_logger.hint(my_logger.LogLevel.INFO, "DataUtil", False,
                           f"Combined Coverage Result save to {log_file_path}")

    @staticmethod
    def combine_packages_with_pattern(pattern, need_std=True, target_apps: Optional[List[unified_testing_config.Apps]] = None):
        """CoverageCombine data with the same prefix by packages, e.g., ARES-0622-uni~"""
        CoverageCombine.__combine_packages_with_tag_pattern(tag_pattern=pattern, need_std=need_std, target_apps=target_apps)

    @staticmethod
    def combine_to_one_with_prefix(prefix, combined_tag):
        """CoverageCombine data with the listed tags across packages, e.g., ARES-0622-uni@5"""
        CoverageCombine.__combine_to_one_with_tag_list(
            tag_list=[f"{prefix}@5"],
            combined_tag=combined_tag,
            need_std=True,
        )


if __name__ == '__main__':
    from evalution.result_analyzer.study_analyzer.study_util import Experiments
    for current_pattern, current_target_apps in Experiments.EXPERIMENTAL_APP_DICT.items():
        CoverageCombine.combine_packages_with_pattern(
            pattern=current_pattern,
            need_std=True,
            target_apps=current_target_apps,
        )

    # CoverageCombine.combine_to_one_with_prefix("DQT-1125-uni", "DQT0807")
