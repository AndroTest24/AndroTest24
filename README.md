# Statistical Android Metrics Evaluation (pre-released)
## Overview
A pre-released version of our study data and evaluation framework, as well as the AndroTest24 benchmark apps.

<br/>

## Part-1  AndroidTest24 App Benchamrk
As the file is large for GitHub, please download it from [GoogleDrive](https://drive.google.com/drive/folders/1Oi2FtP13uIldCiGaeHJ01Qj0YX-Py_wj?usp=sharing).

<br/>

## Part-2 Study Data (/study_data)
The study data of our study.<br />They are organized according to our RQs and have been renamed for better understandability.

<br/>

## Part-3 Evaluation Framework (/evaluation_framework)
The source code of our evaluation framework.

#### File Structure
```
evaluation_framework
├── android_testing_utils/log  Log helper
├── constant  Some constants loaded from config.yaml
├── evaluation  The main part of our framework
│   ├── data_manager  Data managing and scheduling
│   └── result_analyzer  Main analyzation
│       ├── analysis  Statistical analysis methods
│       ├── excel  Data
│       ├── study_analyzer  Analyzers that are customized for our study.
│       └── utils  Some utils.
└── runtime_collection  Some dependent test configs.

```

#### Environment

- Python: Tested on **Python 3.7**, recomended to build the python environment under `/evaluation_framework/` to avoid import problem.
- Requirements: `pip install -r ./requirements.txt`

#### Run
Some raw exported data has been provided under `/evaluation_framework/evaluation/result_analyzer/excel/`.<br />Uncommented code under the main fields of our study analyzers under `/evaluation_framework/evaluation/result_analyzer/study_analyzer/` could be run directly.<br />Since there are some dependencies between data, it's recommended to run them in the following order:

1. granularities_analyzer
2. metrics_relation_analyzer
3. randomness_analyzer.py
4. convergence_analyzer.py
