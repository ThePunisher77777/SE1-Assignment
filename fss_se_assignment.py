from pathlib import Path
import pandas as pd
import subprocess
import csv
import matplotlib.pyplot as plot
from radon.complexity import cc_visit
import pydriller as pyd
from collections import defaultdict
import matplotlib.pyplot as plt
import re
import os
from datetime import datetime
from itertools import combinations
from collections import Counter
from pydriller import Repository
import ast
import sys
from typing import Dict, Set

"""
RUN THIS FILE OUTSIDE transformers REPOSITORY (on the same height).
"""


# regex pattern
pattern = re.compile(r"\b(bug|fix|error|issue)\b", re.IGNORECASE)

def task1():
    defects_per_month, defective_commits = defects_month_commits()
    occurences_of_files = occ_of_files(defective_commits)
    with open("defects_per_file.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["file", "defects"])
        for key, value in occurences_of_files.items():
            w.writerow([key, value])
    two_most_occuring_files = create_two_most_occuring(occurences_of_files)
    defect_per_month_of_two_most = defect_per_month_of_two_most_occ(defective_commits, two_most_occuring_files)
    plot_task_1(defects_per_month=defects_per_month, defects_per_month_two_most_occuring=defect_per_month_of_two_most)

def defects_month_commits():
    # search commits for regex pattern
    defects_per_month = defaultdict(int)
    defective_commits = list()
    for commit in pyd.Repository('./transformers', since=datetime(2023, 1, 1)).traverse_commits():
        if pattern.search(commit.msg):
            defective_commits.append(commit) 
            year_month = commit.committer_date.strftime("%Y-%m")
            defects_per_month[year_month] += 1
    return defects_per_month, defective_commits

# count occurences of paths (vs files see below why)
def occ_of_files(defective_commits):
    occurences_of_files = defaultdict(int)
    for commit in defective_commits:
        for file in commit.modified_files:
            # we use path vs filename otherwise in dict we would count same filename but different path as same
            path = file.new_path or file.old_path
            if path.endswith(".py"):
                occurences_of_files[path] += 1 
    return occurences_of_files

def create_two_most_occuring(occ_files):
    # get two most occuging files
    two_most_occuring_files = sorted(occ_files.items(), key=lambda item: item[1], reverse=True)[:2]
    top_files = [f[0] for f in two_most_occuring_files]
    return top_files

# count occurences per month of 2 most occurin
def defect_per_month_of_two_most_occ(defective_commits, top_files):
    defects_per_month_two_most_occuring = defaultdict(int)
    for commit in defective_commits:
        for file in commit.modified_files:
            path = file.new_path or file.old_path
            if path in top_files:
                year_month = commit.committer_date.strftime("%Y-%m")
                defects_per_month_two_most_occuring[year_month] += 1 
    return defects_per_month_two_most_occuring

def plot_task_1(defects_per_month, defects_per_month_two_most_occuring):
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
    plt.savefig("Task1Plot.png", dpi=300)

def run_cloc(repo_root="transformers", out_file="cloc_output.csv"):
    repo_root = Path(repo_root).resolve()

    cmd = [
        "cloc",
        str(repo_root),
        "--unix",
        "--by-file",
        "--csv",
        "--quiet",
        f"--report-file={out_file}",
    ]

    subprocess.run(cmd, check=True)

def load_cloc_results(csv_path="cloc_output.csv", repo_root="transformers"):
    repo_root = Path(repo_root).resolve()
    files_data = []

    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["language"] != "Python":
                continue

            abs_path = Path(row["filename"])
            rel_path = abs_path.relative_to(repo_root)

            files_data.append({
                "file": str(rel_path),
                "loc": int(row["code"]),
                "blank": int(row["blank"]),
                "comment": int(row["comment"]),
            })

    return pd.DataFrame(files_data)

def compute_cc_per_file(file_path, repo_root="transformers"):
    full_path = Path(repo_root) / file_path

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            code = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

    try:
        blocks = cc_visit(code)
        total_cc = sum(b.complexity for b in blocks)
        return total_cc
    except Exception as e:
        print(f"Radon failed on {file_path}: {e}")
        return None


def compute_cc_for_all_files(repo_root="transformers"):
    repo_root = Path(repo_root).resolve()
    py_files = list(repo_root.rglob("*.py"))

    files_data = []
    for abs_path in py_files:
        if "templates" in abs_path.parts:
            continue

        rel_path = abs_path.relative_to(repo_root)
        cc = compute_cc_per_file(rel_path, repo_root)
        files_data.append({"file": str(rel_path), "cc": cc})

    return pd.DataFrame(files_data)

def identify_hotspots(all_results):
    cc_threshold = all_results["cc"].quantile(0.90)
    loc_threshold = all_results["loc"].quantile(0.90)

    all_results["cc_rank"] = all_results["cc"].rank(ascending=False)
    all_results["loc_rank"] = all_results["loc"].rank(ascending=False)

    hotspots = all_results[(all_results["cc"] >= cc_threshold) | (all_results["loc"] >= loc_threshold)]
    hotspots_sorted = hotspots.sort_values(by="cc", ascending=False)

    hotspots_sorted.to_csv("task2_hotspots.csv", index=False)

    return hotspots_sorted

def plot_hotspots(all_results, hotspots):
    plot.figure(figsize=(14, 9))

    plot.scatter(all_results["loc"], all_results["cc"], alpha=0.3, label="All files")
    plot.scatter(hotspots["loc"], hotspots["cc"], alpha=0.9, color="red", label="Hotspots")

    top5 = all_results.nlargest(5, "cc")
    for _, row in top5.iterrows():
        plot.text(row["loc"], row["cc"], row["file"], fontsize=7)

    plot.xlabel("Lines of Code (LoC)")
    plot.ylabel("Cyclomatic Complexity (CC)")
    plot.title("Complexity Hotspots in the Transformers Repository")
    plot.legend()
    plot.grid(True)

    plot.savefig("complexity_hotspots.png", dpi=300)

def compute_correlation(all_results):
    corr = all_results["loc"].corr(all_results["cc"])
    pd.DataFrame({"correlation_loc_cc": [corr]}).to_csv("task2_correlation.csv", index=False)
    return corr

def analyse_defects(all_results, defects_path="defects_per_file.csv"):
    defects = pd.read_csv(defects_path)

    all_results_merged = all_results.merge(defects, on="file", how="left")
    all_results_merged["defects"] = all_results_merged["defects"].fillna(0)

    all_results_merged.to_csv("task2_loc_cc_defects.csv", index=False)

    corr_cc_defects = all_results_merged["cc"].corr(all_results_merged["defects"])
    corr_loc_defects = all_results_merged["loc"].corr(all_results_merged["defects"])

    print(f"Correlation CC vs defects:  {corr_cc_defects}")
    print(f"Correlation LoC vs defects: {corr_loc_defects}")

    cc_threshold = all_results_merged["cc"].quantile(0.90)
    high_cc = all_results_merged["cc"] >= cc_threshold

    avg_defects_high = all_results_merged[high_cc]["defects"].mean()
    avg_defects_low = all_results_merged[~high_cc]["defects"].mean()

    print(f"Avg defects (high CC files): {avg_defects_high}")
    print(f"Avg defects (low CC files):  {avg_defects_low}")

    plot.figure(figsize=(12, 8))
    plot.scatter(all_results_merged["cc"], all_results_merged["defects"], alpha=0.5)
    plot.xlabel("Cyclomatic Complexity (CC)")
    plot.ylabel("# Defect-related commits")
    plot.title("Defects vs Cyclomatic Complexity")
    plot.grid(True)
    plot.savefig("defects_vs_cc.png", dpi=300)

    plot.figure(figsize=(10, 6))
    plot.boxplot(
        [all_results_merged[high_cc]["defects"], all_results_merged[~high_cc]["defects"]],
        labels=["High CC (top 10%)", "Lower 90%"],
    )
    plot.ylabel("# Defect-related commits")
    plot.title("Defect Distribution by CC Group")
    plot.savefig("defect_boxplot_cc_groups.png", dpi=300)

    return {
        "corr_cc_defects": corr_cc_defects,
        "corr_loc_defects": corr_loc_defects,
        "avg_defects_high": avg_defects_high,
        "avg_defects_low": avg_defects_low,
        "all_results_merged": all_results_merged,
    }

def task2_2():
    run_cloc("transformers", "cloc_output.csv")
    loc_results = load_cloc_results("cloc_output.csv")
    cc_results = compute_cc_for_all_files("transformers")

    all_results = loc_results.merge(cc_results, on="file", how="inner")
    all_results.to_csv("task2_loc_cc.csv", index=False)

    return all_results


def task2_3(all_results):
    hotspots = identify_hotspots(all_results)
    plot_hotspots(all_results, hotspots)
    return hotspots


def task2_4(all_results):
    return compute_correlation(all_results)


def task2_5(all_results):
    return analyse_defects(all_results)

def task3_1():
    REPO_PATH = os.path.dirname(os.path.abspath(__file__))
    SINCE_DATE = datetime(2023, 1, 1)
    MIN_COMMITS_PAIR = 2  # threshold to filter noise

    def extract_commit_data():
        file_count = Counter()
        pair_count = Counter()

        for i, commit in enumerate(Repository(REPO_PATH, since=SINCE_DATE).traverse_commits(), start=1):
            if i % 50 == 0:
                print(f"Processed {i} commits...")

            changed = set()
            for m in commit.modified_files:
                path = m.new_path or m.old_path
                if path and path.endswith('.py'):
                    changed.add(path)

            if not changed:
                continue

            for f in changed:
                file_count[f] += 1

            if len(changed) > 1:
                for f1, f2 in combinations(sorted(changed), 2):
                    pair_count[(f1, f2)] += 1

        print("Finished extracting commits.")
        print(f"Unique files touched: {len(file_count)}")
        print(f"File pairs detected: {len(pair_count)}")

        return file_count, pair_count

    def compute_logical_coupling(file_count, pair_count):
        results = []
        for (f1, f2), cij in pair_count.items():
            if cij < MIN_COMMITS_PAIR:
                continue
            ci, cj = file_count[f1], file_count[f2]
            lc = cij / min(ci, cj)  # normalization
            results.append((f1, f2, cij, ci, cj, lc))

        results.sort(key=lambda x: x[-1], reverse=True)
        return results

    def main():
        file_count, pair_count = extract_commit_data()
        lc_results = compute_logical_coupling(file_count, pair_count)

        df = pd.DataFrame(lc_results, columns=[
            "file1", "file2",
            "commits_together",
            "commits_file1",
            "commits_file2",
            "logical_coupling"
        ])

        # Write CSV
        out_path = "task3_code_pairs.csv"
        df.to_csv(out_path, index=False)

        print(f"\nSaved CSV to: {out_path}")
        print("Top 20 rows:")
        print(df.head(20))

    main()


def task3_2():
    REPO_PATH = os.path.dirname(os.path.abspath(__file__))
    SINCE_DATE = datetime(2023, 1, 1)
    MIN_COMMITS_PAIR = 2  # threshold to filter noise

    def is_test_file(path: str) -> bool:
        base = os.path.basename(path)

        if base.startswith("test_"):
            return True
        return False

    def extract_commit_data():
        file_count = Counter()
        pair_count = Counter()

        for i, commit in enumerate(Repository(REPO_PATH, since=SINCE_DATE).traverse_commits(), start=1):
            if i % 50 == 0:
                print(f"Processed {i} commits...")

            changed = set()
            for m in commit.modified_files:
                path = m.new_path or m.old_path
                if path and path.endswith(".py"):
                    changed.add(path)

            if not changed:
                continue

            for f in changed:
                file_count[f] += 1

            # update pair counts
            if len(changed) > 1:
                for f1, f2 in combinations(sorted(changed), 2):
                    pair_count[(f1, f2)] += 1

        print("Finished extracting commits.")
        print(f"Unique files touched: {len(file_count)}")
        print(f"File pairs detected (all): {len(pair_count)}")

        return file_count, pair_count

    def compute_test_code_coupling(file_count, pair_count):
        results = []

        for (f1, f2), cij in pair_count.items():
            if cij < MIN_COMMITS_PAIR:
                continue

            is_test1 = is_test_file(f1)
            is_test2 = is_test_file(f2)

            # skip pairs that are test–test or non-test–non-test
            if is_test1 == is_test2:
                continue

            ci, cj = file_count[f1], file_count[f2]
            lc = cij / min(ci, cj)  # same normalization as before

            results.append((f1, f2, cij, ci, cj, lc))

        results.sort(key=lambda x: x[-1], reverse=True)
        return results

    def main():
        file_count, pair_count = extract_commit_data()
        print("Computing logical coupling for TEST–CODE pairs only...")
        lc_results = compute_test_code_coupling(file_count, pair_count)

        df = pd.DataFrame(lc_results, columns=[
            "file1", "file2",
            "commits_together",
            "commits_file1",
            "commits_file2",
            "logical_coupling"
        ])

        # Write CSV
        out_path = "task3_test_code_pairs.csv"
        df.to_csv(out_path, index=False)

        print(f"\nSaved CSV to: {out_path}")
        print("Top 20 rows:")
        print(df.head(20))

    main()


def task3_4_1(file_path):
    def mirror_structure(rel_src: Path) -> Path:
        """
        Mirror the structure exactly:
        src/.../name.py  ->  tests/.../test_name.py
        """
        parts = list(rel_src.parts)

        if not parts or parts[0] != "src":
            raise ValueError(f"Expected path starting with 'src/', got: {rel_src}")

        parts[0] = "tests"
        filename = parts[-1]
        stem = Path(filename).stem
        new_filename = f"test_{stem}.py"
        parts[-1] = new_filename

        return Path(*parts)

    def to_repo_relative(path: Path) -> Path:
        return Path(path)

    def find_test_structural_mirror(src_file: Path) -> Path:
        """Return the strict mirrored test path."""
        rel_src = to_repo_relative(src_file)
        return mirror_structure(rel_src)

    def main():
        test_path = find_test_structural_mirror(Path(file_path))
        print(test_path)

    main()


def task3_4_2(file_path):
    def find_repo_root(start: Path) -> Path:
        current = start.resolve()
        for parent in [current] + list(current.parents):
            if (parent / ".git").is_dir():
                return parent
        raise RuntimeError(f"Could not find .git directory above {start}")

    def to_repo_relative(path: Path, repo_root: Path) -> Path:
        try:
            return path.resolve().relative_to(repo_root)
        except ValueError:
            raise RuntimeError(f"{path} is not inside repo root {repo_root}")

    def compute_module_name(rel_src: Path) -> str:
        """
        Compute a Python module name from a repo-relative source path.
        Example: src/transformers/data/processors/squad.py -> transformers.data.processors.squad
        """
        parts = list(rel_src.parts)

        if not parts or parts[0] != "src":
            raise ValueError(f"Source file must be under src/, got: {rel_src}")

        # drop "src"
        parts = parts[1:]

        # remove .py
        if parts[-1].endswith(".py"):
            parts[-1] = parts[-1][:-3]

        if not parts:
            raise ValueError(f"Cannot compute module name from path: {rel_src}")

        return ".".join(parts)

    def build_import_index(repo_root: Path) -> Dict[str, Set[Path]]:
        tests_root = repo_root / "tests"
        mapping: Dict[str, Set[Path]] = defaultdict(set)

        if not tests_root.is_dir():
            print(f"[WARN] No tests/ directory found under {repo_root}", file=sys.stderr)
            return mapping

        for test_path in tests_root.rglob("test*.py"):
            rel_test = test_path.relative_to(repo_root)
            imports_for_this_test: Set[str] = set()

            try:
                text = test_path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError) as e:
                print(f"[WARN] Could not read {rel_test}: {e}", file=sys.stderr)
                continue

            try:
                tree = ast.parse(text, filename=str(test_path))
            except SyntaxError as e:
                print(f"[WARN] Syntax error in {rel_test}: {e}", file=sys.stderr)
                continue

            # go through files and collect imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    # e.g. "import transformers.data.processors.squad as squad_mod"
                    for alias in node.names:
                        name = alias.name  # "transformers.data.processors.squad"
                        mapping[name].add(rel_test)
                        imports_for_this_test.add(name)

                elif isinstance(node, ast.ImportFrom):
                    # e.g. "from transformers.data.processors.squad import SquadExample"
                    mod = node.module  # "transformers.data.processors.squad"
                    if mod is None:
                        continue

                    mapping[mod].add(rel_test)
                    imports_for_this_test.add(mod)

                    # Also index full name including imported symbol
                    for alias in node.names:
                        full_name = f"{mod}.{alias.name}"  # "transformers.data.processors.squad.SquadExample"
                        mapping[full_name].add(rel_test)
                        imports_for_this_test.add(full_name)

            if imports_for_this_test:
                imports_sorted = sorted(imports_for_this_test)
            else:
                imports_sorted = []
            # print(f"[IMPORTS] {rel_test}: {imports_sorted}")

        return mapping

    def find_test_by_imports(src_file: Path) -> Path:
        """
        Input: a non-test source file, find the most related test file
        """
        if not src_file.is_file():
            raise FileNotFoundError(f"Source file does not exist: {src_file}")

        repo_root = find_repo_root(src_file)
        rel_src = to_repo_relative(src_file, repo_root)

        module_name = compute_module_name(rel_src)
        print(f"[INPUT] Source file: {rel_src}")
        # print(f"[INFO] Module name: {module_name}")

        import_index = build_import_index(repo_root)
        direct_tests = import_index.get(module_name, set())

        if not direct_tests:
            # check entries where module_name is a prefix:
            # e.g. module_name = transformers.data.processors.squad
            # and index key = transformers.data.processors.squad.SquadExample
            prefix = module_name + "."
            candidates = {t for mod, tests in import_index.items() if mod.startswith(prefix) for t in tests}

            if not candidates:
                raise RuntimeError(f"No test file imports module '{module_name}' (or its symbols).")

            direct_tests = candidates

        best = sorted(
            direct_tests,
            key=lambda p: (len(p.parts), str(p))
        )[0]

        return best

    def main():
        src_path = Path(file_path)
        try:
            test_rel = find_test_by_imports(src_path)
        except Exception as e:
            print(f"[ERROR] {e}", file=sys.stderr)
            sys.exit(1)

        print(f"[RESULT] {test_rel}")

    main()


def plot_task3(csv_path: str, out_path: str = "top10_bar.png"):
    def plot_top10(csv_path: str, out_path: str = "top10_bar.png"):
        if not os.path.isfile(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        df = pd.read_csv(csv_path)

        # Sort and select top 10
        df_sorted = df.sort_values(
            ["logical_coupling", "commits_together"],
            ascending=[False, False]
        )
        top10 = df_sorted.head(10)

        labels = []
        for _, row in top10.iterrows():
            left = os.path.basename(row["file1"])
            right = os.path.basename(row["file2"])
            labels.append(f"{left} & {right}")

        # Plot
        plt.figure(figsize=(12, 6))
        plt.barh(labels, top10["logical_coupling"])
        plt.gca().invert_yaxis()  # highest score at top
        plt.xlabel("Logical Coupling (C(i,j) / min(C(i), C(j)))")
        plt.title("Top 10 Most Logically Coupled File Pairs")
        plt.tight_layout()
        plt.savefig(out_path, dpi=200)
        plt.close()

        print(f"Saved bar chart to: {out_path}")

    plot_top10(csv_path, out_path)


if __name__ == "__main__":
    print("Running Task 1...")
    task1()
    print("Finished Task 1.")
    print("\nRunning Task 2...")
    all_results = task2_2()
    hotspots = task2_3(all_results)
    correlation = task2_4(all_results)
    defect_results = task2_5(all_results)
    print("Finished Task 2.")
    print("\nRunning Task 3...")
    task3_1()
    task3_2()
    task3_4_1("src/transformers/generation/utils.py")
    task3_4_2("transformers/src/transformers/generation/utils.py")
    print("Finished Task 3.")
    print("Finished all tasks successfully.")