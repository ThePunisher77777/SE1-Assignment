import pydriller as pyd
import datetime

for commit in pyd.Repository('../transformers', since=datetime.datetime(2023, 1, 1)).traverse_commits():
    print(commit.msg)