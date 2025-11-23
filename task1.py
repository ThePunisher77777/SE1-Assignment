import pydriller as pyd
import datetime
from collections import defaultdict
import matplotlib.pyplot as plt
import re

# regex pattern
pattern = re.compile(r"\b(bug|fix|error|issue)\b", re.IGNORECASE)

def defects_month_commits():
    # search commits for regex pattern
    defects_per_month = defaultdict(int)
    defective_commits = list()
    for commit in pyd.Repository('../transformers', since=datetime.datetime(2023, 1, 1)).traverse_commits():
        if pattern.search(commit.msg):
            defective_commits.append(commit) 
            year_month = commit.committer_date.strftime("%Y-%m")
            if year_month == "2025-10":
                print(commit.msg)
            defects_per_month[year_month] += 1
    return defects_per_month, defective_commits

# count occurences of paths (vs files see below why)
def occurences_of_files():
    occurences_of_files = defaultdict(int)
    _, defective_commits = defects_month_commits()
    for commit in defective_commits:
        for file in commit.modified_files:
            # we use path vs filename otherwise in dict we would count same filename but different path as same
            path = file.new_path or file.old_path
            if path.endswith(".py"):
                occurences_of_files[path] += 1 
    return occurences_of_files

def create_two_most_occuring():
    # get two most occuging files
    two_most_occuring_files = sorted(occurences_of_files.items(), key=lambda item: item[1], reverse=True)[:2]
    top_files = [f[0] for f in two_most_occuring_files]
    return top_files

# count occurences per month of 2 most occurin
def defect_per_month_of_two_most_occuring():
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