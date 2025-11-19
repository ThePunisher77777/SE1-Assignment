from pathlib import Path
import pandas as pd
import subprocess
import csv
import matplotlib.pyplot as plot
from radon.complexity import cc_visit

RUN_DEFECT_ANALYSIS = False

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

def run_task2_complexity_pipeline():
    print("\nSTEP 1: Running cloc")
    run_cloc("transformers", "cloc_output.csv")

    print("\nSTEP 2: Reading LoC results")
    loc_results = load_cloc_results("cloc_output.csv")

    print("\nSTEP 3: Computing Cyclomatic Complexity")
    cc_results = compute_cc_for_all_files("transformers")

    print("\nSTEP 4: Merging metrics")
    all_results = loc_results.merge(cc_results, on="file", how="inner")
    all_results.to_csv("task2_loc_cc.csv", index=False)

    print("\nSTEP 5: Identifying hotspots")
    hotspots = identify_hotspots(all_results)

    print("\nSTEP 6: Plotting hotspots")
    plot_hotspots(all_results, hotspots)

    print("\nSTEP 7: Correlation between LoC and CC")
    compute_correlation(all_results)

    if RUN_DEFECT_ANALYSIS:
        print("\nSTEP 8: Analysing defects")
        defect_results = analyse_defects(all_results)
    else:
        print("\nSTEP 8: Skipping defect analysis (Task 1 not ready yet)")
        defect_results = None

    return all_results, hotspots, defect_results

if __name__ == "__main__":
    all_results, hotspots, defect_results = run_task2_complexity_pipeline()
