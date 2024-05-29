# ----------------------
# @Time  : 2024 May
# @Author: Anonymity
# ----------------------
from evalution.result_analyzer.study_analyzer.study_util import Experiments
from evalution.result_analyzer.utils.data_util import DataType


if __name__ == '__main__':
    Experiments.process_all_significance_data(DataType.Coverage)
    Experiments.process_all_significance_data(DataType.Bug)
