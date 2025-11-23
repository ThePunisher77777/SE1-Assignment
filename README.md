# Fundamentals of Software Systems - Software Evolution - Part 1 Assignment
Daniel Maksimovic, Cedric Egon von Rauscher, Mika Schoch

# Task 1: Defect Analysis
## Question: Calculate and plot the total number of defects per month. Why do you think the number of defects dropped sharply in October 2025?
Commit 2ccc6ca contains many commit messages in one. Multiple of these have the word fix in them. But since we only count if the keyword is in the commit and not how often it is in the commit, we will get a 1 for the month October in 2025. https://github.com/huggingface/transformers/commit/2ccc6cae21faaf11631efa5fb9054687ae5dc931

## Question 2: Calculate and plot the number of defects per month for the two files with the highest number of defects. In which month were the most defects introduced? How would you explain it? Manually examine the repository for that month (e.g., change logs, releases, commit messages) and come up with a hypothesis.
March 2025. We can see that there was a large change 'Gemma3' with many commits. This seems like a large introduction of a new model/module which can cause many issues.
![Plot Task 1](Task1Plot.png)

## Question 3: What are the limitations of this method for finding defective hotspots?
### 1. Keyword restriction
We restrict ourselves to certain keywords. We don't know how commit messages are handled, it could be that sometimes none of the keywords provided in this code is ever used for a fix. (we make assumptions about the commit message handling)

### 2. Defective files having side effects on other files
Further we consider whole commits and then look at the files within one commit containing one of the keywords. This can lead to noisy data in the sense that we consider files to be "defective" since they were changed in one of those commits containing a certain keyword even if they did not have a defect. A scenario for this could be when a file references a defective file or need to acces some of its methods and maybe the signature of the method (params or return values) changed with the fix. 

# Task 2: Complexity Analysis
## Question 1: Select two complexity metrics of your choice.
We selected for task 2 the complexity metrics Cyclomatic Complexity (CC) and Lines of Code (LoC), because they capture two complementary dimensions of software complexity. One the one side LoC measures the size of a file in terms of lines of executable code. The larger the files gets, usually the more complex it gets to maintain the file. Additionally, when a developer has more code to analyze and understand, a higher cognitive load is needed for the developer to understand all the code and LoC also turned out to be one of the strongest individual predictors of quality issues in the code. Therefore, since LoC is a simple metric, which is easy to understand, it provides a first baseline to measure the size of the files. On the other side CC measures the number of independent linear paths in the code and captures aspects, which LoC cannot check such as, branching, number of decision points and while and until loops. CC therefore is logic related and provides a basis to understand how hard a file is to reason about, test, develop, and maintain.

## Question 2: Calculate the complexity of all .py files in the repository using the selected metrics.
For computing the complexity metric LoC we used the Python library cloc, also shown in the examples from the lecture's book, which outputs blank, empty, and code lines. The Python library cloc excludes comments and blank lines and there might be different definitions of LoC. The code lines themselves only count executable code lines and do not count blank lines or comments. We used the Python library radon to compute the CC and for each file we summed up the complexity of all functions/classes into a single total CC per file. The two complexity metrics of all .py files were calculated except the template directories in the Transformers repository such as 'templates/adding_a_new_example_script/{{cookiecutter.directory_name}}' were excluded from the cyclomatic complexity analysis because they contain invalid Python placeholders. The calculated complexity metrics CC and LoC can be found in the files cloc_output.csv (for LoC) and task2_loc_cc.csv (for both LoC and CC), which are automatically generated when executing the code.

## Question 3: Visualize the complexity hotspots. The visualization should effectively convey which parts of the code are more complex or change more frequently. Feel free to use any visualization of your choice and explain the rationale behind your decision.
The complexity hotspots were defined as files, which are in the top 10% for CC or LoC. The thresholds, which we used for CC and LoC were the 90th percentile of CC (195.7) and the 90th percentile of LoC (864.7). We decided to use a scatter plot because it can display two dimensions at the same time. Furthermore, hotspots appear naturally in the upper-right corner and they are easy to detect and understand for users, which are not technical experts. The scatter plot below visualizes the complexity metrics LoC and CC for all the .py files of the Transformer repository. The complexity hotspots are displayed in red and are more prominent in the upper-right region.

<img width="4200" height="2700" alt="complexity_hotspots" src="https://github.com/user-attachments/assets/7b887eaf-dc60-4233-9ca7-15cd869cbf4f" />

As displayed above the scatter plot, some of the most complex .py files include:
- src/transformers/modeling_common.py
- src/transformers/modeling_utils.py
- src/transformers/trainer.py
- src/transformers/models/seamless_m4t_v2/modeling_seamless_m4t_v2.py
- src/transformers/models/seamless_m4t/modeling_seamless_m4t.py
These .py files have both a high number of LoC and a high CC. The exact hotspot files detected by our analysis can be found in the file task2_hotspots.csv.

## Question 4: What can you say about the correlation between the two complexity measures in this repository? For example, if you selected CC and LoC, what can you say for the statement “Files with more lines of code tend to have higher cyclomatic complexity”?
To proof the statement "Files with more lines of code tend to have higher cyclomatic complexity" we computed the Pearson correlation between LoC and CC. The Pearson correlation resulted to 0.9234, which indicates a very strong positive relationship. Therefore, this statement is supported by the Pearson correlation and the scatter plot above additionally confirms this visually, since the cyclomatic complexity tends to grow approximately linearly with the number of lines of code. The file task2_correlation.csv contains the actual Pearson correlation value.

## Question 5: A colleague of yours claims that “Files with higher complexity tend to be more defective”. What evidence can you present to support or reject this claim for the selected complexity measures in this repository?
To proof the claim that " Files with higher complexity tend to be more defective" we merged the complexity metrics (LoC and CC) from Task 2 with the defect counts from Task 1 (defects_per_file.csv) into the file task2_loc_cc_defects.csv. We then calculated the correlations between CC and the number of defect-related commits and between LoC and the number of defect-related commits. The statistical analysis shows moderate positive correlation between CC and defects (r = 0.555) and a similar correlation between LoC and defects (r = 0.567). This shows, that generally more complex files tend to have more defect-related commits. Using a scatter plot we visualized the relation between CC and the defect-related commits in the image defects_vs_cc as shown below.

<img width="3600" height="2400" alt="defects_vs_cc" src="https://github.com/user-attachments/assets/4854cea5-217b-4cf4-980d-3da9a06a42e4" />

We compared the top 10% most complex CC group with the lower 90% CC groups to see if files with higher complexity exhibit more defects. The hotspot selection using the 90th percentile was arbitrarly chosen, but is also commonly used in practice. Files in the top complexity group have 31 defects on average, whereas the remaining 90% CC groups only about 8 defects on average. Therefore, this comparison also supports the claim. Even though both correlations are not extremely strong, they both point in the same direction. Additionally, we visualized this using a boxplot the top 10% CC and the bottom 90% as displayed in defect_boxplot_cc_groups.png or also below.

<img width="3000" height="1800" alt="defect_boxplot_cc_groups" src="https://github.com/user-attachments/assets/e8a4c802-71ed-48e6-9776-45c8568c8b77" />

Therefore, these results provide enough evidence that files with higher complexity tend to be more defective.

# Task 3: Coupling Analysis
## 10 Most Coupled File Pairs
![Plot Task 3.1](Task3_1Plot.png)

The following formula was used to calculate logical coupling LC:

LC = C(F, T) / ( min( C(F), C(T)) )

- C(F, T) = commits touching the file and the test file
- C(F) = commits touching the file
- C(T) = commits touching the test file

The files setup.py and dependency_versions_table.py have a high logical coupling, because setup.py defines the requirements for packages and dependency_versions_table.py contains the supported versions of the packages. Whenever a dependency is updated, the versions are changed in both files.

## 10 Most Coupled File Pairs (with test files)
![Plot Task 3.2](Task3_2Plot.png)

The files backbone_utils.py and test_backbone_utils.py are highly coupled. When a test file and a non-test file change together in the same commits very often (high logical coupling), it means that the test is tightly focused on that specific piece of production code. Whenever developers modify the code, they also have to adjust the test for it to pass, which means the test is sensitive to changes of the specific code.
Therefore, the high coupling does not indicate that the code should be refactored. It rather shows how closely the tests track changes in the code.

## Methods For Selecting the Most "Related" Test File
1.	**Version-control based logical coupling**: 
We can use the Git history to find the test file that most often changes together with the target input .py file. It finds the test file which is the most associated with a given source file based on the commits.
However, finding these files e.g. computing coupling can take several minutes, depending on how many commits are being searched for and how big the repository is.

2.	**Matching structural and naming conventions**:
Usually, the test files and folder structure in the /test folder mirrors the one in the /src folder. With that, the associated file can easily be located by getting the path of the target input .py file. This solution is fast and doesn’t require Git history.
However, it may not find additional integration tests that are stored elsewhere, or test files that cover multiple modules. It only works in a repository with exact same /src and /test structure.

4.	**Coverage-based mapping**:
We could use test coverage to see which test files execute the lines in the target .py file. The test file with tests that hit and cover the most parts of the target .py file is the most related.
However, if coverage is too low, this metric may not be useful. Also, the quality of the tests play a role. Furthermore, the entire test suite has to be run, which could take long. This doesn’t require the test files to have a correct naming convention.

6.	**Test file import analysis**:
Analyse the imports of all test files and take the test files that import the target .py file. This doesn’t require Git history or tests to run and also doesn’t need correct naming conventions and file/folder structures.


## Implementation of Structural Naming Method and Import-Analysis Method
**Structural Naming Method**

First, it maps the generation subfolder under src/transformers to tests/generation, and then it creates the test file with the naming convention of adding “test_” to the target .py file, e.g. for utils.py it creates test_utils.py.
However, this is wrong, as the structure in /test is not identical to the one in /src. The corresponding test file is at tests\generation\test_utils.py.

-> task3_4_1() in fss_se_assignment.py

**Import-Analysis Method**

It analysis the import statements of all the files in the fest folders. It outputs the filepath of the test file that imported the input .py file.
For src/transformers/generation/utils.py, it outputs the path tests\generation\test_utils.py which is correct (the file already exists there and imports the utils.py target file.

-> task3_4_2() in fss_se_assignment.py
