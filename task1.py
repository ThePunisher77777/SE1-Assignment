import pydriller as pyd
import datetime
from collections import defaultdict
import matplotlib.pyplot as plt
import re

# regex pattern
pattern = re.compile(r"\b(bug|fix|error|issue)\b", re.IGNORECASE)
defects_per_month = defaultdict(int)
defective_commits = list()

# search commits for regex pattern
for commit in pyd.Repository('../transformers', since=datetime.datetime(2023, 1, 1)).traverse_commits():
    if pattern.search(commit.msg):
        defective_commits.append(commit) 
        year_month = commit.committer_date.strftime("%Y-%m")
        if year_month == "2025-10":
            print(commit.msg)
        defects_per_month[year_month] += 1

for month, count in defects_per_month.items():
    print(month, count)

# count occurences of paths (vs files see below why)
occurences_of_files = defaultdict(int)
for commit in defective_commits:
    for file in commit.modified_files:
        # we use path vs filename otherwise in dict we would count same filename but different path as same
        path = file.new_path or file.old_path
        if path.endswith(".py"):
            occurences_of_files[path] += 1 

# get two most occuging files
two_most_occuring_files = sorted(occurences_of_files.items(), key=lambda item: item[1], reverse=True)[:2]
top_files = [f[0] for f in two_most_occuring_files]
for file in top_files:
    print(file)

# count occurences per month of 2 most occurin
defects_per_month_two_most_occuring = defaultdict(int)
for commit in defective_commits:
    for file in commit.modified_files:
        path = file.new_path or file.old_path
        if path in top_files:
            year_month = commit.committer_date.strftime("%Y-%m")
            defects_per_month_two_most_occuring[year_month] += 1 

fig, axes = plt.subplots(1, 2, figsize=(20, 8))

# defects per month
sorted_months = sorted(defects_per_month.keys())
counts = [defects_per_month[m] for m in sorted_months]
axes[0].bar(sorted_months, counts)
axes[0].set_xlabel("Year and Month")
axes[0].set_ylabel("Number of defects / commits found with keyword")
axes[0].set_xticklabels(sorted_months, rotation=90)
axes[0].set_title("Defects per Month")

# defects per month for two most occurring files
sorted_month_two_most_occuring = sorted(defects_per_month_two_most_occuring.keys())
counts_two_most_occuring = [defects_per_month_two_most_occuring[m] for m in sorted_month_two_most_occuring]
axes[1].bar(sorted_month_two_most_occuring, counts_two_most_occuring)
axes[1].set_xlabel("Year and Month")
axes[1].set_ylabel("Number of defects / commits found with keyword")
axes[1].set_xticklabels(sorted_month_two_most_occuring, rotation=90)
axes[1].set_title("Defects per Month of 2 most occuring files")

plt.tight_layout()
plt.show()