import os
import json
import csv
import tkinter as tk
from tkinter import filedialog

# Load version.json or versioninfo.json
def load_version_json(path):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading {path}: {e}")
        return None

# Format bytes into human-readable string
def format_size(size_bytes):
    for unit in ['B','KB','MB','GB','TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"

# Convert bytes to GB
def bytes_to_gb(size_bytes):
    return size_bytes / (1024 ** 3)

# Collect all .usdc files in a folder and subfolders
# Collect all .usdc/.usd/.usda/.vdb files in a folder and subfolders
def find_usdc_files_in_tree(root_dir):
    usdc_files = []
    for root, _, files in os.walk(root_dir):
        for f in files:
            if f.lower().endswith((".usdc", ".usd", ".usda", ".vdb")):
                usdc_files.append(os.path.join(root, f))
    return usdc_files


# Main recursive collector
def collect_all_usdc_data(version_path, visited_versions=None, collected_usdc=None):
    if visited_versions is None:
        visited_versions = set()
    if collected_usdc is None:
        collected_usdc = {}

    version_path = os.path.abspath(version_path)
    if version_path in visited_versions:
        return collected_usdc
    visited_versions.add(version_path)

    data = load_version_json(version_path)
    if not data:
        return collected_usdc

    dependencies = data.get("dependencies", [])

    for dep in dependencies:
        if not dep.lower().endswith((".usdc", ".usd", ".usda")):
            continue

        abs_dep = os.path.abspath(dep) #absolute path of dependency
        parent_dir = os.path.dirname(abs_dep) #dependency directory

        #get all .usdc in this folder + subfolders
        all_usdc_in_tree = find_usdc_files_in_tree(parent_dir)

        for usdc_file in all_usdc_in_tree:
            if usdc_file not in collected_usdc:
                try:
                    #get file size of all collected usd
                    size_bytes = os.path.getsize(usdc_file)
                    collected_usdc[usdc_file] = {
                        "size_bytes": size_bytes,
                        "size_gb": bytes_to_gb(size_bytes),
                        "from_version": version_path
                    }
                except FileNotFoundError:
                    pass  # Ignore missing files

        #Check for version.json/info in folder + subfolders
        for root, _, files in os.walk(parent_dir):
            for name in files:
                if name in ["version.json", "versioninfo.json"]:
                    version_candidate = os.path.join(root, name)
                    version_candidate = os.path.abspath(version_candidate)
                    if version_candidate not in visited_versions:
                        collect_all_usdc_data(version_candidate, visited_versions, collected_usdc)

    return collected_usdc

# ui to select versioninfo.json
def main():
    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(
        title="Select version.json or versioninfo.json",
        filetypes=[("JSON Files", "version*.json"), ("All Files", "*.*")]
    )

    if not file_path:
        print("No file selected.")
        return

    print(f"\n🔍 Scanning all .usdc from dependencies, siblings, and children of: {file_path}\n")

    #launch the scapper
    usdc_data = collect_all_usdc_data(file_path)

    total_size = 0
    for path, info in usdc_data.items():
        print(f"- {path}")

        print(f"    Linked to: {info['from_version']}")
        total_size += info["size_bytes"]

    print(f"\n Total size of all .usd files: {format_size(total_size)}")

    # Export to CSV
    csv_path = os.path.splitext(file_path)[0] + "_usd_sizes.csv"

    with open(csv_path, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file, delimiter=';')  # Use ; as separator
        writer.writerow(["usdc_filename", "size_gb"])
        for path, info in usdc_data.items():
            writer.writerow([
                os.path.basename(path),                              # only the filename
                f"{info['size_gb']:.3f}".replace('.', ',')           # GB with comma decimal
            ])

    print(f"\n CSV exported to: {csv_path}")


if __name__ == "__main__":
    main()
