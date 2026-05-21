import ROOT
import glob
import os

ROOT.ROOT.DisableImplicitMT()

print("Current directory:")
print(os.getcwd())

patterns = [
    "../../../../DATA/Monte_Carlo/2022/2l/VBS_SSWW_T1Int_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM/output_2l*.root",
    "../../../../DATA/Monte_Carlo/2022/2l/VBS_SSWW_T1Quad_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM/output_2l*.root",
]

files = []

for p in patterns:
    matched = glob.glob(p)
    print("\nPattern:")
    print(p)
    print("Matched files:", len(matched))
    for f in matched:
        print("  ", f)
    files += matched

print("\nTotal files found:", len(files))

if len(files) == 0:
    print("\nNo files found. Your relative path is wrong from this directory.")
    exit()

for f in files:
    print("\n==============================")
    print("FILE:", f)

    tf = ROOT.TFile.Open(f)
    if not tf or tf.IsZombie():
        print("BAD FILE / cannot open")
        continue

    t = tf.Get("Events")
    if not t:
        print("NO Events tree")
        tf.ls()
        continue

    print("Entries:", t.GetEntries())

    branches = [b.GetName() for b in t.GetListOfBranches()]

    needed = [
        "GenDressedLepton_pt",
        "GenDressedLepton_eta",
        "GenDressedLepton_phi",
        "GenDressedLepton_mass",
        "GenMET_pt",
        "GenMET_phi",
    ]

    print("Branch check:")
    for br in needed:
        print(f"  {br:30s} {'YES' if br in branches else 'NO'}")

    if "GenDressedLepton_pt" not in branches:
        print("Skipping RDataFrame check because GenDressedLepton_pt is missing")
        continue

    df = ROOT.RDataFrame("Events", f)

    df2 = df.Define("nGenDress", "GenDressedLepton_pt.size()")

    n_total = df2.Count().GetValue()
    n_0     = df2.Filter("nGenDress == 0").Count().GetValue()
    n_1     = df2.Filter("nGenDress == 1").Count().GetValue()
    n_ge2   = df2.Filter("nGenDress >= 2").Count().GetValue()

    print("nTotal     =", n_total)
    print("nGen == 0  =", n_0)
    print("nGen == 1  =", n_1)
    print("nGen >= 2  =", n_ge2)