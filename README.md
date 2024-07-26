# Statistical Android Metrics Evaluation (pre-released)
## Overview
A pre-released version of our study data and evaluation framework, as well as the AndroTest24 benchmark apps.

<br/>

## Part-1  AndroidTest24 App Benchamrk
As the file is large for GitHub, please download it from [GoogleDrive](https://drive.google.com/drive/folders/1Oi2FtP13uIldCiGaeHJ01Qj0YX-Py_wj?usp=sharing).<br />The app version information is also provided by file names with the app files.

<br/>

## Part-2 Study Data (/study_data)
The study data of our study.<br />They are organized according to our RQs and have been renamed for better understandability.

### Selected Testing Approaches
#### 1. Random-Based
Monkey

- Tool: https://developer.android.com/studio/test/other-testing-tools/monkey
#### 2. Model-Based
Stoat

- Paper: [ESEC/FSE’17] Guided, stochastic model-based GUI testing of Android apps
- Tool: https://github.com/tingsu/Stoat

APE

- Paper: [ICSE’19] Practical GUI Testing of Android Applications via Model Abstraction and Refinement
- Tool: https://github.com/tianxiaogu/ape
#### 3. Systematic
ComboDroid

- Paper: [ICSE’20] ComboDroid: Generating High-Quality Test Inputs for Android Apps via Use Case Combinations
- Tool: https://github.com/skull591/ComboDroid-Artifact
#### 4. Machine-Learning-Based
**4.1 Supervised-Learning-Based**<br />Humanoid

- Paper: [ASE’19] Humanoid: A Deep Learning-based Approach to Automated Black-box Android App Testing
- Tool: https://github.com/yzygitzh/Humanoid

**4.2 Tabular-RL-Based**<br />Q-testing

- Paper: [ISSTA’20] Reinforcement Learning Based Curiosity-Driven Testing of Android Applications
- Tool: https://github.com/anlalalu/Q-testing

**4.3 Deep-RL-Based**<br />ARES

- Paper: [TOSEM’22] Deep Reinforcement Learning for Black-box Testing of Android Apps
- Tool: https://github.com/H2SO4T/ARES

DQT

- Paper: [ICSE’24] Deeply Reinforcing Android GUI Testing with Deep Reinforcement Learning
- Tool: https://github.com/Yuanhong-Lan/DQT

### Emulator Settings
**Basic Settings**

- Hardware: Google Pixel 2
- Resolution: 1080*1920
- Android Version: Android 9.0 (API Level 28)
- Google Sevice: Google APIs

**Storage**

- RAM: 4GB
- VM Heap: 2GB
- Internal Storage: 8GB
- SD Card: 1GB

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
│       ├── study_analyzer  Analyzers that are customized for our study
│       └── utils  Some utils
└── runtime_collection  Some dependent test configs

```

#### Environment

- Python: Tested on **Python 3.7**, recommended to build the Python project and environment under `/evaluation_framework/` to avoid import problems.
- Requirements: `pip install -r ./requirements.txt`

#### Run
Some raw exported data has been provided under `/evaluation_framework/evaluation/result_analyzer/excel/`.<br />Uncommented code in the main fields of our study analyzers under `/evaluation_framework/evaluation/result_analyzer/study_analyzer/` could be run directly.<br />Since there are some dependencies between data, it's recommended to run them in the following order:

1. granularities_analyzer.py
2. metrics_relation_analyzer.py
3. randomness_analyzer.py
4. convergence_analyzer.py

Note: A test shell (`/evaluation_framework/test.sh`) which rely on the `python` cmd is also provided for a quick test. Run it inside the Python environment.

