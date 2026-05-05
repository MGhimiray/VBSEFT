import getopt
import glob
import os
import re
import sys

import ROOT


def parse_sample_id(path):
    match = re.search(r"_sample(\d+)_year", os.path.basename(path))
    if match:
        return int(match.group(1))
    return -1


if __name__ == "__main__":
    ROOT.PyConfig.DisableRootLogon = True

    dir_tag = "1000" #vscode
    path = "fillhisto_sswwAnalysis" #vscode
    year = 20250 #vscode
    output = f"/mnt/home/mghimiray/VBSStudies/Outputs_EFT/matrix_method/{dir_tag}/histo/fillhisto_sswwAnalysis/" #vscode
    histo = 18 #vscode
    category = 11 #vscode

    valid = ["dir=", "path=", "year=", "output=", "histo=", "category=", "help"] #vscode
    usage  = f"Usage: {os.path.basename(sys.argv[0])} --path=<{path}>\\n" #vscode
    usage += f"       --year=<{year}>\\n" #vscode
    usage += f"       --output=<{output}>\\n" #vscode
    usage += f"       --dir=<{dir_tag}>\\n" #vscode
    usage += f"       --histo=<{histo}>\\n" #vscode
    usage += f"       --category=<{category}>" #vscode

    try:
        opts, args = getopt.getopt(sys.argv[1:], "", valid)
    except getopt.GetoptError as ex:
        print(usage)
        print(str(ex))
        sys.exit(1)

    for opt, arg in opts:
        if opt == "--help":
            print(usage)
            sys.exit(0)
        if opt == "--dir":
            dir_tag = str(arg) #vscode
        if opt == "--path":
            path = str(arg)
        if opt == "--year":
            year = int(arg)
        if opt == "--output":
            output = str(arg)
        if opt == "--histo":
            histo = int(arg)
        if opt == "--category":
            category = int(arg)

    file_pattern = os.path.join(output, f"{path}1001_sample*_year{year}1_job*.root") #vscode
    input_files = sorted(glob.glob(file_pattern))

    print(f"Looking for files: {file_pattern}") #vscode
    print(f"Found files: {len(input_files)}") #vscode

    if len(input_files) == 0:
        print("No files found")
        sys.exit(1)

    contributions = [] #vscode
    hist_name = f"histo_{histo}_{category}" #vscode

    for input_file_name in input_files:
        input_file = ROOT.TFile.Open(input_file_name, "READ")
        if not input_file or input_file.IsZombie():
            print(f"Could not open: {input_file_name}") #vscode
            continue

        hist_obj = input_file.Get(hist_name)
        if not hist_obj:
            input_file.Close()
            continue

        integral = hist_obj.Integral()
        entries = hist_obj.GetEntries()
        sample_id = parse_sample_id(input_file_name)
        contributions.append((integral, sample_id, entries, input_file_name)) #vscode
        input_file.Close()

    contributions.sort(reverse=True) #vscode

    total = 0.0 #vscode
    print(f"Per-sample contributions for {hist_name}") #vscode
    for integral, sample_id, entries, input_file_name in contributions:
        total += integral
        print(f"sample={sample_id:4d} integral={integral:12.6f} entries={entries:12.1f} file={os.path.basename(input_file_name)}") #vscode

    print(f"Total integral from unmerged files: {total:.6f}") #vscode
