# Fundamentals of Software Systems - Software Evolution - Part 1 Assignment

# Task 2: Complexity Analysis of the Transformers Repository

## Overview
This part analyzes the complexity of the Hugging Face Transformers repository using the two complexity metrics:

- **Cyclomatic Complexity (CC)** - which measures the number of linearly independent paths through the Python files by measuring the control flow within the program.
- **Lines of Code (LoC)** - which measures the number of lines of executable code excluding blank lines and comments.

The goal of this task was to:

1. Calculate the LoC and CC of all .py files.
2. Identify complexity hotspots.
3. Visualize the complexity distribution across the entire project.
4. Analyze if the selected CC and LoC correlate.
5. Relate complexity with possibility for defects using data from task 1.

---

## 1. Methodology

### 1.1 Repository and File Selection
- In this part only .py files from the Transformers repository where analyzed.
- The template directories in the Transformers repository such as 'templates/adding_a_new_example_script/{{cookiecutter.directory_name}}' were excluded from the cyclomatic complexity analysis because they contain invalid Python placeholders.

### 1.2 Lines of Code (LoC)
For computing the complexity metric LoC we used the Python library cloc, also shown in the examples from the lecture's book, which outputs blank, empty, and code lines. The code lines themselves only count executable code lines and do not count blank lines or comments.

### 1.3 Cyclomatic Complexity (CC)
We used the Python library radon to compute the CC as follows:

from radon.complexity import cc_visit
blocks = cc_visit(code)
total_cc = sum(b.complexity for b in blocks)

Therefore, for each file we summed up the complexity of all functions/classes into a single total CC per file.

### 1.4 Hotspot Definition
The complexity hotspots were defined as files, which are in the top 10% for CC or LoC. The thresholds, which we used for CC and LoC were the following:
- 90th percentile CC: 195.7
- 90th percentile LoC: 864.7

### 1.5 Tools Used
The tools used for the completing the task 2 were:
- Python 3.12 (isolated virtual environment)
- cloc
- radon
- pandas
- mathplotlib
- pathlib / subprocess for automation
All packages needed are exported to requirements.txt.

## 2. Results

### 2.1 Hotspot Visualization
The scatter plot below visualizes the complexity metrics LoC and CC for all the .py files of the Transformer repository.
The complexity hotspots are displayed in red and are more prominent in the upper-right region.

### 2.2 Example Hotspot Files
As displayed above the scatter plot, some of the most complex .py files include:
- src/transformers/modeling_common.py
- src/transformers/modeling_utils.py
- src/transformers/trainer.py
- src/transformers/models/seamless_m4t_v2/modeling_seamless_m4t_v2.py
- src/transformers/models/seamless_m4t/modeling_seamless_m4t.py
These .py files have both a high number of LoC and a high CC.

## 3. Correlation Between LoC and Cyclomatic Complexity
To proof the statement "Files with more lines of code tend to have higher cyclomatic complexity" we computed the Pearson correlation between LoC and CC. The Pearson correlation resulted to 0.9234, which indicates a very strong correlation. Therefore, this statement is supported by the Person correlation and the scatter plot additionally confirms this visually, since the cyclomatic complexity tends to grow approximately linearly with the number of lines of code.

## 4. Relation Between Complexity and Defect-Proneness
To proof the claim that " Files with higher complexity tend to be more defective" we analyzed the Transformer repository as follows.

1. We merged the complexity data with the defect data.

df_merged = df.merge(defects, on="file", how="left")
df_merged["defects"] = df_merged["defects"].fillna(0)

2. We calculated the correlations between CC and the defects and between LoC and the defects.

3. We compared the top 10% CC group with the lower CC groups to see if files with higher complexity exhibit more defects.

4. Using a scatter plot we visualize the relation between CC and the defects. Additionally, we visualize using a boxplot the top 10% CC and the bottom 90%.

## 5. Design Decisions & Limitations

### 5.1 Complexity Metrics CC and LoC
We chose the complexity metrics CC and LoC for this task, because they capture two complementary dimensions of software complexity.

1. Lines of Code: Measuring the size
One the one side LoC measures the size of a file in terms of lines of executable code. The larger the files gets, usually the more complex it gets to maintain the file. Additionally, when a developer has more code to analyze and understand, a higher cognitive load is needed for the developer to understand all the code and LoC also turned out to be one of the strongest individual predictors of quality issues in the code. Therefore, since LoC is a simple metric, which is easy to understand, it provides a first baseline to measure the size of the files.

2. Cyclomatic Complexity: Measuring the logical complexity
On the other side CC measures the number of independent linear paths in the code and captures aspects, which LoC cannot check:
- Branching
- Number of decision points
- While and until loops
CC therefore is logic related and provides a basis to understand how hard a file is to reason about, test, develop, and maintain.

### 5.2 Scatter Plot
We decided to use a scatter plot because it can display two dimensions at the same time. Furthermore, hotspots appear naturally in the upper-right corner and they are easy to detect and understand for users, which are not technical experts.

### 5.3 Limitations
For computing the LoC we used the Python library cloc, which excludes comments and blank lines and there might be different definitions of LoC. The hotspot selection using the 90th percentile was arbitrarly chosen, but is also commonly used in practice.

## 6. Files Produced
When executing the entire analysis file fss_se_assignment.py the following files will be automatically created:
- cloc_output.csv 
The raw cloc output after cloc has computed the LoC of all files, will be stored in the file cloc_output.csv.
- task2_loc_cc.csv
The combined LoC and CC metrics of all files are stored in task2_loc_cc.csv.
- task2_hotspots.csv
All the hotspot files of the repository are stored in task2_hotspots.csv.
- complexity_hotspots.png
The created scatter plot is stored in the file complexity_hotspots.png.
- task2_correlations.csv
The correlation value between LoC and CC is stored in task2_correlations.csv.

## 7. Conclusion
The Transformer repository contains several large and complex Python files, which can be found especially under src/transformers/models and testing utilities. CC and LoC show a very strong correlation (0.92), which indicates that files with more lines of code tend to have higher cyclomatic complexity.
