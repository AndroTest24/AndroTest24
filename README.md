# Statistical Android Metrics Evaluation (pre-released)
## Overview
A pre-released version of our study data and evaluation framework, as well as the AndroTest24 benchmark apps.

<br/>

## Part-1  AndroidTest24 App Benchamrk
As the file is large for GitHub, please download it from [GoogleDrive](https://drive.google.com/drive/folders/1Oi2FtP13uIldCiGaeHJ01Qj0YX-Py_wj?usp=sharing).

<br/>

## Part-2 Study Data (/study_data)
The raw statistical data tables of our study.<br />They are organized according to different statistical methods and further divided by different objects.

<br/>

## Part-3 Evaluation Framework (/evaluation_framework)
The source code of our evaluation framework.

#### File Structure
```
evaluation_framework
├── android_testing_utils/log  Log helper.
├── constant  Some constant loaded from config.yaml.
├── evaluation  The main code logic for our framework.
│   ├── data_manager  Raw experimental data processing.
│   └── result_analyzer  Analyzation for further statistical data.
│       ├── analysis  Statistical analysis methods.
│       ├── excel  Data.
│       ├── study_analyzer  Analysis corresponds to our study.
│       └── utils  Some utils.
└── runtime_collection  Some dependent test configs.

```

#### Environment

- Python: Tested on Python 3.7
- Requirements: `pip install -r ./requirements.txt`

#### Run
Some raw exported data has been provided under `/evaluation_framework/evaluation/result_analyzer/excel/`.<br />Code (uncommented) under the main fields of `/evaluation_framework/evaluation/result_analyzer/study_analyzer/` could be run directly.<br />Since there are some dependencies between the data, it's recommended to run them in the following order:

1. submetrics_analyzer.py
2. randomness_analyzer.py
3. convergence_analyzer.py
4. metrics_relation_analyzer.py

