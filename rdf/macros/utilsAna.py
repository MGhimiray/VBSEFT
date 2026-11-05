
import ROOT
import os, json, sys
from utilsCategory import plotCategory
from subprocess import call,check_output
#from correctionlib import _core
import correctionlib
correctionlib.register_pyroot_binding()
#ROOT.gInterpreter.Declare('#include "mysf.h"')
#ROOT.gInterpreter.Load("mysf.so")

useXROOTD = False

def getLumi(year):
    #lumi = [19.5, 16.8, 41.5, 60.0, 8.1, 26.7, 18.1, 9.7, 109.6, 107.5]
#    lumi = [19.5, 16.8, 41.5, 101.5, 8.1, 26.7, 18.1, 9.7, 109.6, 107.5]
    lumi = [19.5, 16.8, 41.5, 60.0, 8.1, 26.9, 18.1, 9.7, 109.6, 133.3, 25.8, 2.1] # 25+26 together
    lumiBit = -999
    if  (year == 20160): lumiBit = 0
    elif(year == 20161): lumiBit = 1
    elif(year == 20170): lumiBit = 2
    elif(year == 20180): lumiBit = 3
    elif(year == 20220): lumiBit = 4
    elif(year == 20221): lumiBit = 5
    elif(year == 20230): lumiBit = 6
    elif(year == 20231): lumiBit = 7
    elif(year == 20240): lumiBit = 8
    elif(year == 20250): lumiBit = 9
    elif(year == 20260): lumiBit = 10
    elif(year == 20261): lumiBit = 11

    print("lumi({0}/{1}) = {2}".format(year,lumiBit,lumi[lumiBit]))

    return lumi[lumiBit]

#if "/functions.so" not in ROOT.gSystem.GetLibraries():
#    ROOT.gSystem.CompileMacro("functions.cc","k")
ROOT.gInterpreter.ProcessLine('#include "functions.h"')

#def loadCorrectionSet(year):
#    ROOT.gInterpreter.Load("mysf.so")
#    ROOT.gInterpreter.Declare('#include "mysf.h"')
#    ROOT.gInterpreter.ProcessLine('auto corr_sf = MyCorrections(%d);' % (year))

def loadJSON(fIn):

    if not os.path.isfile(fIn):
        print("JSON file %s does not exist" % fIn)
        return

    if not hasattr(ROOT, "jsonMap"):
        print("jsonMap not found in ROOT dict")
        return

    info = json.load(open(fIn))
    print("JSON file %s loaded" % fIn)
    for k,v in info.items():

        vec = ROOT.std.vector["std::pair<unsigned int, unsigned int>"]()
        for combo in v:
            pair = ROOT.std.pair["unsigned int", "unsigned int"](*[int(c) for c in combo])
            vec.push_back(pair)
            ROOT.jsonMap[int(k)] = vec

def getTriggerFromJson(overall, type, year):

    if(year > 10000): year = year // 10

    for trigger in overall:
        if(trigger['name'] == type and trigger['year'] == year): return trigger['definition']


def getLeptomSelFromJson(overall, type, year, debug = 0):

    if(year > 10000): year = year // 10
    version = 12
    if(year >= 2024 or year <= 2021): version = 15

    for leptonSel in overall:
        if(leptonSel['name'] == type and leptonSel['version'] == version):
            if(debug == 1):
                print("{0}({1}): {2}".format(leptonSel['name'],leptonSel['version'],leptonSel['definition']))
            return leptonSel['definition']

def getMesonFromJson(overall, type, cat ):

    for meson in overall:
        if meson['name'] == type and meson['type'] == cat: return meson['definition']

def findDataset(name):

    DASclient = "dasgoclient -query '%(query)s'"
    cmd= DASclient%{'query':'file dataset=%s'%name}
    print(cmd)
    check_output(cmd,shell=True)
    fileList=[ 'root://xrootd-cms.infn.it//'+x for x in check_output(cmd,shell=True).split() ]

    files_ROOT = ROOT.vector('string')()
    for f in fileList: files_ROOT.push_back(f)

    return files_ROOT

def findDIR(directory):

    print(directory)

    maxFiles = 1000000000
    if("/1l/" in directory and "NANOAODSIM" in directory and
       "TTto4Q" not in directory and "WWto4Q" not in directory):
        maxFiles = 200

    # HACK!
    #if("/2l/" in directory and "NANOAODSIM" in directory and
    #   ("DY" in directory or "TT" in directory)):
    #    maxFiles = 100

    counter = 0
    rootFiles = ROOT.vector('string')()

    if(useXROOTD == True and "/ceph/submit/data/group/cms" in directory):
        xrd = "root://submit50.mit.edu/"
        xrdpath = directory.replace("/ceph/submit/data/group/cms","")
        f = check_output(['xrdfs', f'{xrd}', 'ls', xrdpath]).decode(sys.stdout.encoding)
        stringFiles = f.split()
        for e in range(len(stringFiles)):
            filePath = xrd + stringFiles[e]
            if "failed/" in filePath: continue
            if "log/" in filePath: continue
            if ".txt" in filePath: continue
            counter+=1
            if(counter > maxFiles): break
            rootFiles.push_back(filePath)

    else:
        for root, directories, filenames in os.walk(directory):
            for f in filenames:

                isBadFile = False
                filePath = os.path.join(os.path.abspath(root), f)
                if "failed/" in filePath: continue
                if "log/" in filePath: continue
                if ".txt" in filePath: continue
                if(("XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX" in filePath) or

                   ("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX" in filePath)
                   ): isBadFile = True

                if(isBadFile == True):
                    print("Bad file: {0}".format(filePath))
                    continue
                counter+=1
                if(counter > maxFiles): break
                rootFiles.push_back(filePath)

    #print(rootFiles)
    return rootFiles

def findMany(basedir, regex):

    if basedir[-1] == "/": basedir = basedir[:-1]
    regex = basedir + "/" + regex

    rootFiles = ROOT.vector('string')()
    for root, directories, filenames in os.walk(basedir):

        for f in filenames:

            filePath = os.path.join(os.path.abspath(root), f)
            if "failed/" in filePath: continue
            if "log/" in filePath: continue
            if fnmatch.fnmatch(filePath, regex): rootFiles.push_back(filePath)

    return rootFiles

# split fIns files in group files
def groupFiles(fIns, group):

    ret =  [fIns[i::group] for i in range(group)]

    return ret

def concatenate(result, tmp1):
    for f in tmp1:
        result.push_back(f)

def getMClist(sampleNOW, skimType):

    files = findDIR("{}".format(SwitchSample(sampleNOW, skimType)[0]))
    return files

def getDATAlist(type, year, skimType):

    if(year > 10000): year = year // 10

    #dirT2 = "/mnt/T2_US_MIT/hadoop/cms/store/user/paus/nanohr/D00/"
    #dirT2 = "/mnt/T3_US_MIT/hadoop/scratch/ceballos/nanoaod/skims_submit/" + skimType
    dirT2 = "/mnt/home/mghimiray/VBSStudies/DATA/DAS"
    dirTest = "/ceph/submit/data/group/cms/store/user/ceballos/test/test/"

    jsnName = ""
    if(year == 2016):
        jsnName = "Cert_271036-284044_13TeV_Legacy2016_Collisions16_JSON.txt"
    elif(year == 2017):
        jsnName = "Cert_294927-306462_13TeV_UL2017_Collisions17_GoldenJSON.txt"
    elif(year == 2018):
        jsnName = "Cert_314472-325175_13TeV_Legacy2018_Collisions18_JSON.txt"
    elif(year == 2022):
        jsnName = "Cert_Collisions2022_355100_362760_Golden.json"
    elif(year == 2023):
        jsnName = "Cert_Collisions2023_366442_370790_Golden.json"
    elif(year == 2024):
        jsnName = "Cert_Collisions2024_378981_386951_Golden.json"
    elif(year == 2025):
        jsnName = "Cert_Collisions2025_391658_398903_Golden.json"
    elif(year == 2026):
        jsnName = "Cert_Collisions2026_401624_403937_golden.json"

    if os.path.exists(os.path.join("jsns",jsnName)):
        loadJSON(os.path.join("jsns",jsnName))
    else:
        loadJSON(jsnName)

    filesL = []
    ##### 2018 ####
    if(year == 2018 and type == 1000):
        filesL = findDIR("{0}/{1}/{2}/SingleMuon+Run2018A-UL2018_MiniAODv2-v2+MINIAOD".format(dirT2, year, skimType))
    elif(year == 2018 and type == 1001):
        filesL = findDIR("{0}/{1}/{2}/SingleMuon+Run2018B-UL2018_MiniAODv2-v2+MINIAOD".format(dirT2, year, skimType))
    elif(year == 2018 and type == 1002):
        filesL = findDIR("{0}/{1}/{2}/SingleMuon+Run2018C-UL2018_MiniAODv2-v2+MINIAOD".format(dirT2, year, skimType))
    elif(year == 2018 and type == 1003):
        filesL = findDIR("{0}/{1}/{2}/SingleMuon+Run2018D-UL2018_MiniAODv2-v3+MINIAOD".format(dirT2, year, skimType))

    elif(year == 2018 and type == 1010):
        filesL = findDIR("{0}/{1}/{2}/DoubleMuon+Run2018A-UL2018_MiniAODv2-v1+MINIAOD".format(dirT2, year, skimType))
    elif(year == 2018 and type == 1011):
        filesL = findDIR("{0}/{1}/{2}/DoubleMuon+Run2018B-UL2018_MiniAODv2-v1+MINIAOD".format(dirT2, year, skimType))
    elif(year == 2018 and type == 1012):
        filesL = findDIR("{0}/{1}/{2}/DoubleMuon+Run2018C-UL2018_MiniAODv2-v1+MINIAOD".format(dirT2, year, skimType))
    elif(year == 2018 and type == 1013):
        filesL = findDIR("{0}/{1}/{2}/DoubleMuon+Run2018D-UL2018_MiniAODv2-v1+MINIAOD".format(dirT2, year, skimType))

    elif(year == 2018 and type == 1020):
        filesL = findDIR("{0}/{1}/{2}/MuonEG+Run2018A-UL2018_MiniAODv2-v1+MINIAOD".format(dirT2, year, skimType))
    elif(year == 2018 and type == 1021):
        filesL = findDIR("{0}/{1}/{2}/MuonEG+Run2018B-UL2018_MiniAODv2-v1+MINIAOD".format(dirT2, year, skimType))
    elif(year == 2018 and type == 1022):
        filesL = findDIR("{0}/{1}/{2}/MuonEG+Run2018C-UL2018_MiniAODv2-v1+MINIAOD".format(dirT2, year, skimType))
    elif(year == 2018 and type == 1023):
        filesL = findDIR("{0}/{1}/{2}/MuonEG+Run2018D-UL2018_MiniAODv2-v1+MINIAOD".format(dirT2, year, skimType))

    elif(year == 2018 and type == 1030):
        filesL = findDIR("{0}/{1}/{2}/EGamma+Run2018A-UL2018_MiniAODv2-v1+MINIAOD".format(dirT2, year, skimType))
    elif(year == 2018 and type == 1031):
        filesL = findDIR("{0}/{1}/{2}/EGamma+Run2018B-UL2018_MiniAODv2-v1+MINIAOD".format(dirT2, year, skimType))
    elif(year == 2018 and type == 1032):
        filesL = findDIR("{0}/{1}/{2}/EGamma+Run2018C-UL2018_MiniAODv2-v1+MINIAOD".format(dirT2, year, skimType))
    elif(year == 2018 and type == 1033):
        filesL = findDIR("{0}/{1}/{2}/EGamma+Run2018D-UL2018_MiniAODv2-v2+MINIAOD".format(dirT2, year, skimType))

    elif(year == 2018 and type == 1050):
        filesL = findDIR("{0}/{1}/{2}/MET+Run2018A-UL2018_MiniAODv2_NanoAODv9-v2+NANOAOD".format(dirT2, year, skimType))
    elif(year == 2018 and type == 1051):
        filesL = findDIR("{0}/{1}/{2}/MET+Run2018B-UL2018_MiniAODv2_NanoAODv9-v2+NANOAOD".format(dirT2, year, skimType))
    elif(year == 2018 and type == 1052):
        filesL = findDIR("{0}/{1}/{2}/MET+Run2018C-UL2018_MiniAODv2_NanoAODv9-v1+NANOAOD".format(dirT2, year, skimType))
    elif(year == 2018 and type == 1053):
        filesL = findDIR("{0}/{1}/{2}/MET+Run2018D-UL2018_MiniAODv2_NanoAODv9-v1+NANOAOD".format(dirT2, year, skimType))

    ##### 2022 ####
    elif(year == 2022 and type == 1001):
        filesL = findDIR("{0}/{1}/{2}/SingleMuon+Run2022B-22Sep2023-v1+NANOAOD".format(dirT2, year, skimType))
    elif(year == 2022 and type == 1002):
        filesL = findDIR("{0}/{1}/{2}/SingleMuon+Run2022C-22Sep2023-v1+NANOAOD".format(dirT2, year, skimType))

    elif(year == 2022 and type == 1011):
        filesL = findDIR("{0}/{1}/{2}/DoubleMuon+Run2022B-22Sep2023-v1+NANOAOD".format(dirT2, year, skimType))
    elif(year == 2022 and type == 1012):
        filesL = findDIR("{0}/{1}/{2}/DoubleMuon+Run2022C-22Sep2023-v1+NANOAOD".format(dirT2, year, skimType))

    elif(year == 2022 and type == 1021):
        filesL = findDIR("{0}/{1}/{2}/MuonEG+Run2022B-22Sep2023-v1+NANOAOD".format(dirT2, year, skimType))
    elif(year == 2022 and type == 1022):
        filesL = findDIR("{0}/{1}/{2}/MuonEG+Run2022C-22Sep2023-v1+NANOAOD".format(dirT2, year, skimType))
    elif(year == 2022 and type == 1023):
        filesL = findDIR("{0}/{1}/{2}/MuonEG+Run2022D-22Sep2023-v1+NANOAOD".format(dirT2, year, skimType))
    elif(year == 2022 and type == 1024):
        filesL = findDIR("{0}/{1}/{2}/MuonEG+Run2022E-22Sep2023-v1+NANOAOD".format(dirT2, year, skimType))
    elif(year == 2022 and type == 1025):
        filesL = findDIR("{0}/{1}/{2}/MuonEG+Run2022F-22Sep2023-v1+NANOAOD".format(dirT2, year, skimType))
    elif(year == 2022 and type == 1026):
        filesL = findDIR("{0}/{1}/{2}/MuonEG+Run2022G-22Sep2023-v1+NANOAOD".format(dirT2, year, skimType))

    elif(year == 2022 and type == 1031):
        filesL = findDIR("{0}/{1}/{2}/EGamma+Run2022B-22Sep2023-v2+NANOAOD".format(dirT2, year, skimType))
    elif(year == 2022 and type == 1032):
        filesL = findDIR("{0}/{1}/{2}/EGamma+Run2022C-22Sep2023-v1+NANOAOD".format(dirT2, year, skimType))
    elif(year == 2022 and type == 1033):
        filesL = findDIR("{0}/{1}/{2}/EGamma+Run2022D-22Sep2023-v1+NANOAOD".format(dirT2, year, skimType))
    elif(year == 2022 and type == 1034):
        filesL = findDIR("{0}/{1}/{2}/EGamma+Run2022E-22Sep2023-v1+NANOAOD".format(dirT2, year, skimType))
    elif(year == 2022 and type == 1035):
        filesL = findDIR("{0}/{1}/{2}/EGamma+Run2022F-22Sep2023-v1+NANOAOD".format(dirT2, year, skimType))
    elif(year == 2022 and type == 1036):
        filesL = findDIR("{0}/{1}/{2}/EGamma+Run2022G-22Sep2023-v2+NANOAOD".format(dirT2, year, skimType))

    elif(year == 2022 and type == 1042):
        filesL = findDIR("{0}/{1}/{2}/Muon+Run2022C-22Sep2023-v1+NANOAOD".format(dirT2, year, skimType))
    elif(year == 2022 and type == 1043):
        filesL = findDIR("{0}/{1}/{2}/Muon+Run2022D-22Sep2023-v1+NANOAOD".format(dirT2, year, skimType))
    elif(year == 2022 and type == 1044):
        filesL = findDIR("{0}/{1}/{2}/Muon+Run2022E-22Sep2023-v1+NANOAOD".format(dirT2, year, skimType))
    elif(year == 2022 and type == 1045):
        filesL = findDIR("{0}/{1}/{2}/Muon+Run2022F-22Sep2023-v2+NANOAOD".format(dirT2, year, skimType))
    elif(year == 2022 and type == 1046):
        filesL = findDIR("{0}/{1}/{2}/Muon+Run2022G-22Sep2023-v1+NANOAOD".format(dirT2, year, skimType))

    elif(year == 2022 and type == 1051):
        filesL = findDIR("{0}/{1}/{2}/MET+Run2022B-22Sep2023-v1+NANOAOD".format(dirT2, year, skimType))
    elif(year == 2022 and type == 1052):
        filesL = findDIR("{0}/{1}/{2}/MET+Run2022C-22Sep2023-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/JetMET+Run2022C-22Sep2023-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2022 and type == 1053):
        filesL = findDIR("{0}/{1}/{2}/JetMET+Run2022D-22Sep2023-v1+NANOAOD".format(dirT2, year, skimType))
    elif(year == 2022 and type == 1054):
        filesL = findDIR("{0}/{1}/{2}/JetMET+Run2022E-22Sep2023-v1+NANOAOD".format(dirT2, year, skimType))
    elif(year == 2022 and type == 1055):
        filesL = findDIR("{0}/{1}/{2}/JetMET+Run2022F-22Sep2023-v2+NANOAOD".format(dirT2, year, skimType))
    elif(year == 2022 and type == 1056):
        filesL = findDIR("{0}/{1}/{2}/JetMET+Run2022G-22Sep2023-v2+NANOAOD".format(dirT2, year, skimType))

##### 2023 ####

    elif(year == 2023 and type == 1022):
        filesL = findDIR("{0}/{1}/{2}/MuonEG+Run2023C-22Sep2023_v1-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/MuonEG+Run2023C-22Sep2023_v2-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/MuonEG+Run2023C-22Sep2023_v3-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/MuonEG+Run2023C-22Sep2023_v4-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2023 and type == 1023):
        filesL = findDIR("{0}/{1}/{2}/MuonEG+Run2023D-22Sep2023_v1-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/MuonEG+Run2023D-22Sep2023_v2-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)

    elif(year == 2023 and type == 1032):
        filesL   = findDIR("{0}/{1}/{2}/EGamma0+Run2023C-22Sep2023_v1-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/EGamma0+Run2023C-22Sep2023_v2-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma0+Run2023C-22Sep2023_v3-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma0+Run2023C-22Sep2023_v4-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma1+Run2023C-22Sep2023_v1-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma1+Run2023C-22Sep2023_v2-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma1+Run2023C-22Sep2023_v3-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma1+Run2023C-22Sep2023_v4-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2023 and type == 1033):
        filesL   = findDIR("{0}/{1}/{2}/EGamma0+Run2023D-22Sep2023_v1-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/EGamma0+Run2023D-22Sep2023_v2-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma1+Run2023D-22Sep2023_v1-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma1+Run2023D-22Sep2023_v2-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)

    elif(year == 2023 and type == 1042):
        filesL   = findDIR("{0}/{1}/{2}/Muon0+Run2023C-22Sep2023_v1-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/Muon0+Run2023C-22Sep2023_v2-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/Muon0+Run2023C-22Sep2023_v3-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/Muon0+Run2023C-22Sep2023_v4-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/Muon1+Run2023C-22Sep2023_v1-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/Muon1+Run2023C-22Sep2023_v2-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/Muon1+Run2023C-22Sep2023_v3-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/Muon1+Run2023C-22Sep2023_v4-v2+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2023 and type == 1043):
        filesL   = findDIR("{0}/{1}/{2}/Muon0+Run2023D-22Sep2023_v1-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/Muon0+Run2023D-22Sep2023_v2-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/Muon1+Run2023D-22Sep2023_v1-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/Muon1+Run2023D-22Sep2023_v2-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)


    elif(year == 2023 and type == 1052):
        filesL   = findDIR("{0}/{1}/{2}/JetMET0+Run2023C-22Sep2023_v1-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/JetMET0+Run2023C-22Sep2023_v2-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/JetMET0+Run2023C-22Sep2023_v3-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/JetMET0+Run2023C-22Sep2023_v4-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/JetMET1+Run2023C-22Sep2023_v1-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/JetMET1+Run2023C-22Sep2023_v2-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/JetMET1+Run2023C-22Sep2023_v3-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/JetMET1+Run2023C-22Sep2023_v4-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2023 and type == 1053):
        filesL   = findDIR("{0}/{1}/{2}/JetMET0+Run2023D-22Sep2023_v1-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/JetMET0+Run2023D-22Sep2023_v2-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/JetMET1+Run2023D-22Sep2023_v1-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/JetMET1+Run2023D-22Sep2023_v2-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)

    ##### 2024 ####
    elif(year == 2024 and type == 1022):
        filesL   = findDIR("{0}/{1}/{2}/MuonEG+Run2024C-MINIv6NANOv15-v1+NANOAOD".format(dirT2, year, skimType))
    elif(year == 2024 and type == 1023):
        filesL   = findDIR("{0}/{1}/{2}/MuonEG+Run2024D-MINIv6NANOv15-v1+NANOAOD".format(dirT2, year, skimType))
    elif(year == 2024 and type == 1024):
        filesL   = findDIR("{0}/{1}/{2}/MuonEG+Run2024E-MINIv6NANOv15-v1+NANOAOD".format(dirT2, year, skimType))
    elif(year == 2024 and type == 1025):
        filesL   = findDIR("{0}/{1}/{2}/MuonEG+Run2024F-MINIv6NANOv15-v2+NANOAOD".format(dirT2, year, skimType))
    elif(year == 2024 and type == 1026):
        filesL   = findDIR("{0}/{1}/{2}/MuonEG+Run2024G-MINIv6NANOv15-v3+NANOAOD".format(dirT2, year, skimType))
    elif(year == 2024 and type == 1027):
        filesL   = findDIR("{0}/{1}/{2}/MuonEG+Run2024H-MINIv6NANOv15-v2+NANOAOD".format(dirT2, year, skimType))
    elif(year == 2024 and type == 1028):
        filesL   = findDIR("{0}/{1}/{2}/MuonEG+Run2024I-MINIv6NANOv15-v2+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/MuonEG+Run2024I-MINIv6NANOv15_v2-v2+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)

    elif(year == 2024 and type == 1032):
        filesL   = findDIR("{0}/{1}/{2}/EGamma0+Run2024C-MINIv6NANOv15-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/EGamma1+Run2024C-MINIv6NANOv15-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2024 and type == 1033):
        filesL   = findDIR("{0}/{1}/{2}/EGamma0+Run2024D-MINIv6NANOv15-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/EGamma1+Run2024D-MINIv6NANOv15-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2024 and type == 1034):
        filesL   = findDIR("{0}/{1}/{2}/EGamma0+Run2024E-MINIv6NANOv15-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/EGamma1+Run2024E-MINIv6NANOv15-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2024 and type == 1035):
        filesL   = findDIR("{0}/{1}/{2}/EGamma0+Run2024F-MINIv6NANOv15-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/EGamma1+Run2024F-MINIv6NANOv15-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2024 and type == 1036):
        filesL   = findDIR("{0}/{1}/{2}/EGamma0+Run2024G-MINIv6NANOv15-v2+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/EGamma1+Run2024G-MINIv6NANOv15-v2+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2024 and type == 1037):
        filesL   = findDIR("{0}/{1}/{2}/EGamma0+Run2024H-MINIv6NANOv15-v2+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/EGamma1+Run2024H-MINIv6NANOv15-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2024 and type == 1038):
        filesL   = findDIR("{0}/{1}/{2}/EGamma0+Run2024I-MINIv6NANOv15-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/EGamma1+Run2024I-MINIv6NANOv15-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma0+Run2024I-MINIv6NANOv15_v2-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma1+Run2024I-MINIv6NANOv15_v2-v2+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)

    elif(year == 2024 and type == 1042):
        filesL   = findDIR("{0}/{1}/{2}/Muon0+Run2024C-MINIv6NANOv15-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/Muon1+Run2024C-MINIv6NANOv15-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2024 and type == 1043):
        filesL   = findDIR("{0}/{1}/{2}/Muon0+Run2024D-MINIv6NANOv15-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/Muon1+Run2024D-MINIv6NANOv15-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2024 and type == 1044):
        filesL   = findDIR("{0}/{1}/{2}/Muon0+Run2024E-MINIv6NANOv15-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/Muon1+Run2024E-MINIv6NANOv15-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2024 and type == 1045):
        filesL   = findDIR("{0}/{1}/{2}/Muon0+Run2024F-MINIv6NANOv15-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/Muon1+Run2024F-MINIv6NANOv15-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2024 and type == 1046):
        filesL   = findDIR("{0}/{1}/{2}/Muon0+Run2024G-MINIv6NANOv15-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/Muon1+Run2024G-MINIv6NANOv15-v2+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2024 and type == 1047):
        filesL   = findDIR("{0}/{1}/{2}/Muon0+Run2024H-MINIv6NANOv15-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/Muon1+Run2024H-MINIv6NANOv15-v2+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2024 and type == 1048):
        filesL   = findDIR("{0}/{1}/{2}/Muon0+Run2024I-MINIv6NANOv15-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/Muon1+Run2024I-MINIv6NANOv15-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/Muon0+Run2024I-MINIv6NANOv15_v2-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/Muon1+Run2024I-MINIv6NANOv15_v2-v2+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)

    elif(year == 2024 and type == 1052):
        filesL   = findDIR("{0}/{1}/{2}/JetMET0+Run2024C-MINIv6NANOv15-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/JetMET1+Run2024C-MINIv6NANOv15-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2024 and type == 1053):
        filesL   = findDIR("{0}/{1}/{2}/JetMET0+Run2024D-MINIv6NANOv15-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/JetMET1+Run2024D-MINIv6NANOv15-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2024 and type == 1054):
        filesL   = findDIR("{0}/{1}/{2}/JetMET0+Run2024E-MINIv6NANOv15-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/JetMET1+Run2024E-MINIv6NANOv15-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2024 and type == 1055):
        filesL   = findDIR("{0}/{1}/{2}/JetMET0+Run2024F-MINIv6NANOv15-v2+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/JetMET1+Run2024F-MINIv6NANOv15-v2+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2024 and type == 1056):
        filesL   = findDIR("{0}/{1}/{2}/JetMET0+Run2024G-MINIv6NANOv15-v2+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/JetMET1+Run2024G-MINIv6NANOv15-v2+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2024 and type == 1057):
        filesL   = findDIR("{0}/{1}/{2}/JetMET0+Run2024H-MINIv6NANOv15-v2+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/JetMET1+Run2024H-MINIv6NANOv15-v2+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2024 and type == 1058):
        filesL   = findDIR("{0}/{1}/{2}/JetMET0+Run2024I-MINIv6NANOv15-v2+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/JetMET1+Run2024I-MINIv6NANOv15-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/JetMET0+Run2024I-MINIv6NANOv15_v2-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/JetMET1+Run2024I-MINIv6NANOv15_v2-v2+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)

##### 2025 ####

    elif(year == 2025 and type == 1021):
        filesL   = findDIR("{0}/{1}/{2}/MuonEG+Run2025B-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
    elif(year == 2025 and type == 1022):
        filesL   = findDIR("{0}/{1}/{2}/MuonEG+Run2025C-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/MuonEG+Run2025C-PromptReco-v2+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2025 and type == 1023):
        filesL   = findDIR("{0}/{1}/{2}/MuonEG+Run2025D-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
    elif(year == 2025 and type == 1024):
        filesL   = findDIR("{0}/{1}/{2}/MuonEG+Run2025E-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
    elif(year == 2025 and type == 1025):
        filesL   = findDIR("{0}/{1}/{2}/MuonEG+Run2025F-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/MuonEG+Run2025F-PromptReco-v2+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2025 and type == 1026):
        filesL   = findDIR("{0}/{1}/{2}/MuonEG+Run2025G-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
    elif(year == 2025 and type == 1031):
        filesL   = findDIR("{0}/{1}/{2}/EGamma0+Run2025B-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/EGamma1+Run2025B-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma2+Run2025B-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma3+Run2025B-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2025 and type == 1032):
        filesL   = findDIR("{0}/{1}/{2}/EGamma0+Run2025C-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/EGamma1+Run2025C-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma2+Run2025C-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma3+Run2025C-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma0+Run2025C-PromptReco-v2+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma1+Run2025C-PromptReco-v2+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma2+Run2025C-PromptReco-v2+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma3+Run2025C-PromptReco-v2+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2025 and type == 1033):
        filesL   = findDIR("{0}/{1}/{2}/EGamma0+Run2025D-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/EGamma1+Run2025D-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma2+Run2025D-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma3+Run2025D-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2025 and type == 1034):
        filesL   = findDIR("{0}/{1}/{2}/EGamma0+Run2025E-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/EGamma1+Run2025E-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma2+Run2025E-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma3+Run2025E-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2025 and type == 1035):
        filesL   = findDIR("{0}/{1}/{2}/EGamma0+Run2025F-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/EGamma1+Run2025F-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma2+Run2025F-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma3+Run2025F-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma0+Run2025F-PromptReco-v2+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma1+Run2025F-PromptReco-v2+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma2+Run2025F-PromptReco-v2+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma3+Run2025F-PromptReco-v2+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2025 and type == 1036):
        filesL   = findDIR("{0}/{1}/{2}/EGamma0+Run2025G-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/EGamma1+Run2025G-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma2+Run2025G-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma3+Run2025G-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)

    elif(year == 2025 and type == 1041):
        filesL   = findDIR("{0}/{1}/{2}/Muon0+Run2025B-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/Muon1+Run2025B-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2025 and type == 1042):
        filesL   = findDIR("{0}/{1}/{2}/Muon0+Run2025C-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/Muon1+Run2025C-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/Muon0+Run2025C-PromptReco-v2+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/Muon1+Run2025C-PromptReco-v2+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2025 and type == 1043):
        filesL   = findDIR("{0}/{1}/{2}/Muon0+Run2025D-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/Muon1+Run2025D-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2025 and type == 1044):
        filesL   = findDIR("{0}/{1}/{2}/Muon0+Run2025E-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/Muon1+Run2025E-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2025 and type == 1045):
        filesL   = findDIR("{0}/{1}/{2}/Muon0+Run2025F-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/Muon1+Run2025F-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/Muon0+Run2025F-PromptReco-v2+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/Muon1+Run2025F-PromptReco-v2+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2025 and type == 1046):
        filesL   = findDIR("{0}/{1}/{2}/Muon0+Run2025G-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/Muon1+Run2025G-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)

    elif(year == 2025 and type == 1051):
        filesL   = findDIR("{0}/{1}/{2}/JetMET0+Run2025B-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/JetMET1+Run2025B-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2025 and type == 1052):
        filesL   = findDIR("{0}/{1}/{2}/JetMET0+Run2025C-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/JetMET1+Run2025C-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/JetMET0+Run2025C-PromptReco-v2+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/JetMET1+Run2025C-PromptReco-v2+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2025 and type == 1053):
        filesL   = findDIR("{0}/{1}/{2}/JetMET0+Run2025D-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/JetMET1+Run2025D-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2025 and type == 1054):
        filesL   = findDIR("{0}/{1}/{2}/JetMET0+Run2025E-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/JetMET1+Run2025E-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2025 and type == 1055):
        filesL   = findDIR("{0}/{1}/{2}/JetMET0+Run2025F-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/JetMET1+Run2025F-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/JetMET0+Run2025F-PromptReco-v2+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/JetMET1+Run2025F-PromptReco-v2+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2025 and type == 1056):
        filesL   = findDIR("{0}/{1}/{2}/JetMET0+Run2025G-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/JetMET1+Run2025G-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)

 #206   
    elif(year == 2026 and type == 1020):
        filesL   = findDIR("{0}/{1}/{2}/MuonEG+Run2026A-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
    elif(year == 2026 and type == 1021):
        filesL   = findDIR("{0}/{1}/{2}/MuonEG+Run2026B-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
    elif(year == 2026 and type == 1022):
        filesL   = findDIR("{0}/{1}/{2}/MuonEG+Run2026C-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
    elif(year == 2026 and type == 1023):
        filesL   = findDIR("{0}/{1}/{2}/MuonEG+Run2026D-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))

    elif(year == 2026 and type == 1030):
        filesL   = findDIR("{0}/{1}/{2}/EGamma0+Run2026A-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/EGamma1+Run2026A-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma2+Run2026A-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma3+Run2026A-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma4+Run2026A-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma5+Run2026A-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2026 and type == 1031):
        filesL   = findDIR("{0}/{1}/{2}/EGamma0+Run2026B-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/EGamma1+Run2026B-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma2+Run2026B-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma3+Run2026B-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma4+Run2026B-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma5+Run2026B-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2026 and type == 1032):
        filesL   = findDIR("{0}/{1}/{2}/EGamma0+Run2026C-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/EGamma1+Run2026C-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma2+Run2026C-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma3+Run2026C-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma4+Run2026C-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma5+Run2026C-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2026 and type == 1033):
        filesL   = findDIR("{0}/{1}/{2}/EGamma0+Run2026D-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/EGamma1+Run2026D-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma2+Run2026D-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma3+Run2026D-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma4+Run2026D-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/EGamma5+Run2026D-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)

    elif(year == 2026 and type == 1040):
        filesL   = findDIR("{0}/{1}/{2}/Muon0+Run2026A-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/Muon1+Run2026A-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/Muon2+Run2026A-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/Muon3+Run2026A-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2026 and type == 1041):
        filesL   = findDIR("{0}/{1}/{2}/Muon0+Run2026B-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/Muon1+Run2026B-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/Muon2+Run2026B-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/Muon3+Run2026B-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2026 and type == 1042):
        filesL   = findDIR("{0}/{1}/{2}/Muon0+Run2026C-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/Muon1+Run2026C-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/Muon2+Run2026C-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/Muon3+Run2026C-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2026 and type == 1043):
        filesL   = findDIR("{0}/{1}/{2}/Muon0+Run2026D-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/Muon1+Run2026D-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/Muon2+Run2026D-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/Muon3+Run2026D-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)

    elif(year == 2026 and type == 1050):
        filesL   = findDIR("{0}/{1}/{2}/JetMET0+Run2026A-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/JetMET1+Run2026A-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2026 and type == 1051):
        filesL   = findDIR("{0}/{1}/{2}/JetMET0+Run2026B-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/JetMET1+Run2026B-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2026 and type == 1052):
        filesL   = findDIR("{0}/{1}/{2}/JetMET0+Run2026C-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/JetMET1+Run2026C-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/JetMET3+Run2026C-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/JetMET4+Run2026C-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/{1}/{2}/JetMET5+Run2026C-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2026 and type == 1053):
        filesL   = findDIR("{0}/{1}/{2}/JetMET0+Run2026D-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        filesAux = findDIR("{0}/{1}/{2}/JetMET1+Run2026D-PromptReco-v1+NANOAOD".format(dirT2, year, skimType))
        for x in filesAux:
            filesL.push_back(x)
            
    elif(year == 2022 and type == 9999):
        filesL = findDIR("{0}".format(dirTest))

    files = ROOT.vector('string')()
    concatenate(files, filesL)

    return files

def SwitchSample(argument, skimType):

    #dirT2 = "/scratch/submit/cms/ceballos/nanoaod/skims_submit/" + skimType
    dirT2 = "/mnt/home/mghimiray/VBSStudies/DATA/Monte_Carlo/"
    dirT3 = "/mnt/home/mghimiray/VBSStudies/DATA/Monte_Carlo/Unskimmed/"
    dirLocal = "/work/submit/mariadlf/Hrare/D01"

    ggWWXS_LO_MCFM = 0.0496265/(0.1086*0.1086)
    ggWWXS_LO_MADGRAPH = 3.51313
    ggWWXS_kFactor = 1.4

    switch = {
       100: (dirT2+"2022/"+skimType+"/DYto2L-2Jets_MLL-10to50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",19982.5*1000,plotCategory("kPlotDY")),
       101: (dirT2+"2022/"+skimType+"/DYto2L-2Jets_MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",6345.99*1000,plotCategory("kPlotDY")),
       102: (dirT2+"2022/"+skimType+"/WWto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",(118.7*1.06-ggWWXS_LO_MCFM)*0.1086*0.1086*9*1000,plotCategory("kPlotqqWW")),
       103: (dirT2+"2022/"+skimType+"/WZto3LNu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",4.924*1.08*1000,plotCategory("kPlotWZ")),
       104: (dirT2+"2022/"+skimType+"/WZto2L2Q_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",7.568*1.08*1000,plotCategory("kPlotWZ")),
       105: (dirT2+"2022/"+skimType+"/ZZto2L2Q_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",6.788*1.19*1000,plotCategory("kPlotZZ")),
       106: (dirT2+"2022/"+skimType+"/ZZto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",1.031*1.16*1000,plotCategory("kPlotZZ")),
       107: (dirT2+"2022/"+skimType+"/ZZto4L_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",1.390*1.19*1000,plotCategory("kPlotZZ")),
       108: (dirT2+"2022/"+skimType+"/TTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.950*923.6*0.1086*0.1086*9*1000,plotCategory("kPlotTT")),
       109: (dirT2+"2022/"+skimType+"/TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.950*923.6*0.1086*3*(1-0.1086*3)*2*1000,plotCategory("kPlotTT")),
       110: (dirT2+"2022/"+skimType+"/TTto4Q_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5_ext1-v2+NANOAODSIM",1000000*0.950*923.6*(1-0.1086*3)*(1-0.1086*3)*1000,plotCategory("kPlotNonPrompt")),
       111: (dirT2+"2022/"+skimType+"/TbarWplusto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",4.67*1000,plotCategory("kPlotTW")),
       112: (dirT2+"2022/"+skimType+"/TWminusto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",4.67*1000,plotCategory("kPlotTW")),
       113: (dirT2+"2022/"+skimType+"/WtoLNu-2Jets_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",64481.58*1000,plotCategory("kPlotOther")),
       114: (dirT2+"2022/"+skimType+"/WWW_4F_TuneCP5_13p6TeV_amcatnlo-madspin-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.23280*1000,plotCategory("kPlotVVV")),
       115: (dirT2+"2022/"+skimType+"/WWZ_4F_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.18510*1000,plotCategory("kPlotVVV")),
       116: (dirT2+"2022/"+skimType+"/WZZ_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.06206*1000,plotCategory("kPlotVVV")),
       117: (dirT2+"2022/"+skimType+"/ZZZ_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.01591*1000,plotCategory("kPlotVVV")),
       118: (dirT2+"2022/"+skimType+"/WZGtoLNuZG_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.08425*1000,plotCategory("kPlotVVV")),
       119: (dirT2+"2022/"+skimType+"/TTWW_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.0081651*1000,plotCategory("kPlotTVX")),
       120: (dirT2+"2022/"+skimType+"/TTZZ_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.0015617*1000,plotCategory("kPlotTVX")),
       121: (dirT2+"2022/"+skimType+"/GluGluHtoZZto4L_M-125_TuneCP5_13p6TeV_powheg2-JHUGenV752-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",52.230*0.02619*0.101*0.101*1000,plotCategory("kPlotHiggs")),
       122: (dirT2+"2022/"+skimType+"/VBFHto2Zto4L_M125_TuneCP5_13p6TeV_powheg-jhugenv752-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",4.0780*0.02619*0.101*0.101*1000,plotCategory("kPlotHiggs")),
       123: (dirT2+"2022/"+skimType+"/TTLL_MLL-4to50_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.03949*1000,plotCategory("kPlotTVX")),
       124: (dirT2+"2022/"+skimType+"/TTLL_MLL-50_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.08646*1000,plotCategory("kPlotTVX")),
       125: (dirT2+"2022/"+skimType+"/ggWWto2L2Nu_OS_PolarizationLL_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.24053*(ggWWXS_LO_MCFM/ggWWXS_LO_MADGRAPH)*1.4*1000,plotCategory("kPlotggWW")),
       126: (dirT2+"2022/"+skimType+"/ggWWto2L2Nu_OS_PolarizationLT_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.08268*(ggWWXS_LO_MCFM/ggWWXS_LO_MADGRAPH)*1.4*1000,plotCategory("kPlotggWW")),
       127: (dirT2+"2022/"+skimType+"/ggWWto2L2Nu_OS_PolarizationTL_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.08268*(ggWWXS_LO_MCFM/ggWWXS_LO_MADGRAPH)*1.4*1000,plotCategory("kPlotggWW")),
       128: (dirT2+"2022/"+skimType+"/ggWWto2L2Nu_OS_PolarizationTT_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",3.10724*(ggWWXS_LO_MCFM/ggWWXS_LO_MADGRAPH)*1.4*1000,plotCategory("kPlotggWW")),
       129: (dirT2+"2022/"+skimType+"/DYGto2LG-1Jets_MLL-50_PTG-10to50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",124.18762*1000,plotCategory("kPlotVG")),
       130: (dirT2+"2022/"+skimType+"/DYGto2LG-1Jets_MLL-50_PTG-50to100_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v3+NANOAODSIM",2.08977*1000,plotCategory("kPlotVG")),
       131: (dirT2+"2022/"+skimType+"/DYGto2LG-1Jets_MLL-50_PTG-100to200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.34767*1000,plotCategory("kPlotVG")),
       132: (dirT2+"2022/"+skimType+"/DYGto2LG-1Jets_MLL-50_PTG-200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.04734*1000,plotCategory("kPlotVG")),
       133: (dirT2+"2022/"+skimType+"/WGtoLNuG-1Jets_PTG-10to100_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",668.91538*1000,plotCategory("kPlotVG")),
       134: (dirT2+"2022/"+skimType+"/WGtoLNuG-1Jets_PTG-100to200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",2.22141*1000,plotCategory("kPlotVG")),
       135: (dirT2+"2022/"+skimType+"/WGtoLNuG-1Jets_PTG-200to400_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v1+NANOAODSIM",0.291367*1000,plotCategory("kPlotVG")),
       136: (dirT2+"2022/"+skimType+"/WWto4Q_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",1000000*(118.7*1.06-ggWWXS_LO_MCFM)*(1-0.1086*3)*(1-0.1086*3)*1000,plotCategory("kPlotNonPrompt")),
       137: (dirT2+"2022/"+skimType+"/GluGluHto2Tau_M-125_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",52.230*0.06272*1000,plotCategory("kPlotHiggs")),
       138: (dirT2+"2022/"+skimType+"/VBFHToTauTau_M125_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",4.0780*0.06272*1000,plotCategory("kPlotHiggs")),
       139: (dirT2+"2022/"+skimType+"/DYGto2LG-1Jets_MLL-4to50_PTG-10to100_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",87.73210*1000,plotCategory("kPlotVG")),
       140: (dirT2+"2022/"+skimType+"/DYGto2LG-1Jets_MLL-4to50_PTG-100to200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.24095*1000,plotCategory("kPlotVG")),
       141: (dirT2+"2022/"+skimType+"/DYGto2LG-1Jets_MLL-4to50_PTG-200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.02228*1000,plotCategory("kPlotVG")),
       142: (dirT2+"2022/"+skimType+"/TbarWplus_DR_AtLeastOneLepton_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",23.97*1000,plotCategory("kPlotTW")),
       143: (dirT2+"2022/"+skimType+"/TWminus_DR_AtLeastOneLepton_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",23.97*1000,plotCategory("kPlotTW")),
       144: (dirT2+"2022/"+skimType+"/VH_HtoNonbb_M-125_TuneCP5_13p6TeV_amcatnloFXFX-madspin-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v1+NANOAODSIM",(0.9439+1.4570)*(1-0.577)*1000,plotCategory("kPlotHiggs")),
       145: (dirT2+"2022/"+skimType+"/DYto2L-2Jets_MLL-50_0J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",5034.65*1000,plotCategory("kPlotDY")),
       146: (dirT2+"2022/"+skimType+"/DYto2L-2Jets_MLL-50_1J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",952.29*1000,plotCategory("kPlotDY")),
       147: (dirT2+"2022/"+skimType+"/DYto2L-2Jets_MLL-50_2J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",359.05*1000,plotCategory("kPlotDY")),
       148: (dirT2+"2022/"+skimType+"/TTLNu-1Jets_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v1+NANOAODSIM",0.2502*1000,plotCategory("kPlotTVX")),
       149: (dirT2+"2022/"+skimType+"/TZQB-Zto2L-4FS_MLL-30_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.07968*1.30* 000,plotCategory("kPlotTVX")),
       150: (dirT2+"2022/"+skimType+"/VBS-SSWW_PolarizationLL_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v1+NANOAODSIM",0.002190*1000,plotCategory("kPlotEWKSSWW")),
       151: (dirT2+"2022/"+skimType+"/VBS-SSWW_PolarizationTL_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v3+NANOAODSIM",0.011700*1000,plotCategory("kPlotEWKSSWW")),
       152: (dirT2+"2022/"+skimType+"/VBS-SSWW_PolarizationTT_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v1+NANOAODSIM",0.017635*1000,plotCategory("kPlotEWKSSWW")),
       153: (dirT2+"2022/"+skimType+"/GluGluHto2Wto2L2Nu_M-125_TuneCP5_13p6TeV_powheg-jhugen752-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",52.230*0.2137*0.1086*0.1086*9*1000,plotCategory("kPlotHiggs")),
       154: (dirT2+"2022/"+skimType+"/VBFHto2Wto2L2Nu_M-125_TuneCP5_13p6TeV_powheg-jhugen752-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",4.0780*0.2137*0.1086*0.1086*9*1000,plotCategory("kPlotHiggs")),
       155: (dirT2+"2022/"+skimType+"/TTHtoNon2B_M-125_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v4+NANOAODSIM",0.5700*(1-0.577)*1000,plotCategory("kPlotHiggs")),
       156: (dirT2+"2022/"+skimType+"/WGtoLNuG-1Jets_PTG-400to600_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v1+NANOAODSIM",0.022322*1000,plotCategory("kPlotVG")),
       157: (dirT2+"2022/"+skimType+"/WGtoLNuG-1Jets_PTG-600_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v3+NANOAODSIM",0.004918*1000,plotCategory("kPlotVG")),
       158: (dirT2+"2022/"+skimType+"/WW_DoubleScattering_TuneCP5_13p6TeV_pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",2.14891*1000,plotCategory("kPlotOther")),
       159: (dirT2+"2022/"+skimType+"/GluGlutoContinto2Zto4E_TuneCP5_13p6TeV_mcfm-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.5*0.0061150*1000,plotCategory("kPlotZZ")),
       160: (dirT2+"2022/"+skimType+"/GluGlutoContinto2Zto4Mu_TuneCP5_13p6TeV_mcfm-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.5*0.0061150*1000,plotCategory("kPlotZZ")),
       161: (dirT2+"2022/"+skimType+"/GluGlutoContinto2Zto4Tau_TuneCP5_13p6TeV_mcfm-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.5*0.0061150*1000,plotCategory("kPlotZZ")),
       162: (dirT2+"2022/"+skimType+"/GluGluToContinto2Zto2E2Tau_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.0061150*1000,plotCategory("kPlotZZ")),
       163: (dirT2+"2022/"+skimType+"/GluGluToContinto2Zto2Mu2Tau_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.0061150*1000,plotCategory("kPlotZZ")),
       164: (dirT2+"2022/"+skimType+"/GluGlutoContinto2Zto2E2Mu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v1+NANOAODSIM",0.0061150*1000,plotCategory("kPlotZZ")),
       165: (dirT2+"2022/"+skimType+"/GluGlutoContintoWWtoENuENu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       166: (dirT2+"2022/"+skimType+"/GluGlutoContintoWWtoENuMuNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       167: (dirT2+"2022/"+skimType+"/GluGlutoContintoWWtoENuTauNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       168: (dirT2+"2022/"+skimType+"/GluGlutoContintoWWtoMuNuENu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       169: (dirT2+"2022/"+skimType+"/GluGlutoContintoWWtoMuNuMuNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       170: (dirT2+"2022/"+skimType+"/GluGlutoContintoWWtoMuNuTauNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       171: (dirT2+"2022/"+skimType+"/GluGlutoContintoWWtoTauNuENu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       172: (dirT2+"2022/"+skimType+"/GluGlutoContintoWWtoTauNuMuNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       173: (dirT2+"2022/"+skimType+"/GluGlutoContintoWWtoTauNuTauNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       174: (dirT2+"2022/"+skimType+"/WWto2L2Nu-2Jets_OS_noTop_EW_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.3301419*1000,plotCategory("kPlotqqWW")),
       175: (dirT2+"2022/"+skimType+"/WWto2L2Nu-2Jets_OS_noTop_QCD_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",2.6758028*1000,plotCategory("kPlotqqWW")),
       176: (dirT2+"2022/"+skimType+"/WWto2L2Nu-2Jets_SS_noTop_EW_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v3+NANOAODSIM",         0.0295255*1000,plotCategory("kPlotEWKSSWW")),
       177: (dirT2+"2022/"+skimType+"/WWto2L2Nu-2Jets_SS_noTop_QCD_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",        0.0279662*1000,plotCategory("kPlotQCDSSWW")),
       178: (dirT2+"2022/"+skimType+"/WZto3LNu-2Jets_EW_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",           0.0429366*1000,plotCategory("kPlotEWKWZ")),
       179: (dirT2+"2022/"+skimType+"/WZto3LNu-2Jets_QCD_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",          0.4958618*1000*0.70,plotCategory("kPlotWZ")),
       180: (dirT2+"2022/"+skimType+"/ZZto2L2Nu-2Jets_EW_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",                  0.0051721*1000,plotCategory("kPlotZZ")),
       181: (dirT2+"2022/"+skimType+"/ZZto2L2Nu-2Jets_QCD_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",                 0.0912313*1000*1.40,plotCategory("kPlotZZ")),
       182: (dirT2+"2022/"+skimType+"/ZZto4L-2Jets_EW_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",                     0.0011422*1000,plotCategory("kPlotZZ")),
       183: (dirT2+"2022/"+skimType+"/ZZto4L-2Jets_QCD_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v3+NANOAODSIM",                    0.0202984*1000*1.40,plotCategory("kPlotZZ")),
       189: (dirT2+"2022/"+skimType+"/SSWWJJ_Interference_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.00341005*1000,plotCategory("kPlotQCDSSWW")),
       190: (dirT2+"2022/"+skimType+"/VBSWZ-Interference_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.04806677*1000,plotCategory("kPlotWZ")),
       192: (dirT3+"2022/SM", 0.0295255*1000,plotCategory("kPlotEWKSSWW")),
       193: (dirT2+"2022/"+skimType+"/VBS_SSWW_M0Int_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.000299*1000,plotCategory("kPlotEFTM0Int")),
       194: (dirT2+"2022/"+skimType+"/VBS_SSWW_M0Quad_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.007332*1000,plotCategory("kPlotEFTM0Quad")),
       195: (dirT3+"Sherpa_Sample/2022", 39.8961,plotCategory("kPlotEWKSSWW")),
       196: (dirT2+"2022/"+skimType+"/VBS_SSWW_M1Int_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", -0.0003746 *1000,plotCategory("kPlotEFTM1Int")),
       197: (dirT2+"2022/"+skimType+"/VBS_SSWW_M1Quad_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.007688*1000,plotCategory("kPlotEFTM1Quad")),
       198: (dirT2+"2022/"+skimType+"/VBS_SSWW_M7Int_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.00002167*1000,plotCategory("kPlotEFTM7Int")),
       199: (dirT2+"2022/"+skimType+"/VBS_SSWW_M7Quad_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.003405*1000,plotCategory("kPlotEFTM7Quad")),
       1990: (dirT2+"2022/"+skimType+"/VBS_SSWW_S0Int_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", -0.0003575*1000,plotCategory("kPlotEFTS0Int")),
       1991: (dirT2+"2022/"+skimType+"/VBS_SSWW_S0Quad_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.008078*1000,plotCategory("kPlotEFTS0Quad")),
       1992: (dirT2+"2022/"+skimType+"/VBS_SSWW_T0Int_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",  -0.0005086*1000,plotCategory("kPlotEFTT0Int")),
       1993: (dirT2+"2022/"+skimType+"/VBS_SSWW_T0Quad_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.02811*1000,plotCategory("kPlotEFTT0Quad")),
       1994: (dirT2+"2022/"+skimType+"/VBS_SSWW_T1Int_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", -0.001284*1000,plotCategory("kPlotEFTT1Int")),
       1995: (dirT2+"2022/"+skimType+"/VBS_SSWW_T1Quad_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.03099*1000,plotCategory("kPlotEFTT1Quad")),
       1996: (dirT2+"2022/"+skimType+"/VBS_SSWW_T2Int_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",  -0.001341*1000,plotCategory("kPlotEFTT2Int")),
       1997: (dirT2+"2022/"+skimType+"/VBS_SSWW_T2Quad_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.01401*1000,plotCategory("kPlotEFTT2Quad")),
       1901: (dirT2+"2022/"+skimType+"/VBS-WZ-M2Quad_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.0002623*1000,plotCategory("kPlotEFTM2QuadWZ")),
       1902: (dirT2+"2022/"+skimType+"/VBS-WZ-M3Quad_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.0001106*1000,plotCategory("kPlotEFTM3QuadWZ")),
       1903: (dirT2+"2022/"+skimType+"/VBS-WZ-M4Quad_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.001995*1000,plotCategory("kPlotEFTM4QuadWZ")),
       1904: (dirT2+"2022/"+skimType+"/VBS-WZ-M5Quad_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.001099*1000,plotCategory("kPlotEFTM5QuadWZ")),
       1905: (dirT2+"2022/"+skimType+"/VBS-WZ-T5Quad_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.001619*1000,plotCategory("kPlotEFTT5QuadWZ")),
       1906: (dirT2+"2022/"+skimType+"/VBS-WZ-T6Quad_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.001873*1000,plotCategory("kPlotEFTT6QuadWZ")),
       1907: (dirT2+"2022/"+skimType+"/VBS-WZ-T7Quad_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.0002992*1000,plotCategory("kPlotEFTT7QuadWZ")),
       1908: (dirT2+"2022/"+skimType+"/VBS-WZto2EMuNu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", -3.893e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       1909: (dirT2+"2022/"+skimType+"/VBS-WZto2EMuNu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.0000005482*1000,plotCategory("kPlotEFTM3IntWZ")),
       1910: (dirT2+"2022/"+skimType+"/VBS-WZto2EMuNu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", -6.032e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       1911: (dirT2+"2022/"+skimType+"/VBS-WZto2EMuNu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.000001213*1000,plotCategory("kPlotEFTM5IntWZ")),
       1912: (dirT2+"2022/"+skimType+"/VBS-WZto2EMuNu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.000006792*1000,plotCategory("kPlotEFTT5IntWZ")),
       1913: (dirT2+"2022/"+skimType+"/VBS-WZto2EMuNu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.00001022*1000,plotCategory("kPlotEFTT6IntWZ")),
       1914: (dirT2+"2022/"+skimType+"/VBS-WZto2EMuNu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.000006764*1000,plotCategory("kPlotEFTT7IntWZ")),
       1915: (dirT2+"2022/"+skimType+"/VBS-WZto2ETauNu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", -4.604e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       1916: (dirT2+"2022/"+skimType+"/VBS-WZto2ETauNu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.0000005346*1000,plotCategory("kPlotEFTM3IntWZ")),
       1917: (dirT2+"2022/"+skimType+"/VBS-WZto2ETauNu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", -5.705e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       1918: (dirT2+"2022/"+skimType+"/VBS-WZto2ETauNu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.000001552*1000,plotCategory("kPlotEFTM5IntWZ")),
       1919: (dirT2+"2022/"+skimType+"/VBS-WZto2ETauNu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.00000669*1000,plotCategory("kPlotEFTT5IntWZ")),
       1920: (dirT2+"2022/"+skimType+"/VBS-WZto2ETauNu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.00001023*1000,plotCategory("kPlotEFTT6IntWZ")),
       1921: (dirT2+"2022/"+skimType+"/VBS-WZto2ETauNu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.000006783*1000,plotCategory("kPlotEFTT7IntWZ")),
       1922: (dirT2+"2022/"+skimType+"/VBS-WZto2MuENu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", -4.819e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       1923: (dirT2+"2022/"+skimType+"/VBS-WZto2MuENu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.0000004808*1000,plotCategory("kPlotEFTM3IntWZ")),
       1924: (dirT2+"2022/"+skimType+"/VBS-WZto2MuENu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", -6.275e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       1925: (dirT2+"2022/"+skimType+"/VBS-WZto2MuENu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.000001302*1000,plotCategory("kPlotEFTM5IntWZ")),
       1926: (dirT2+"2022/"+skimType+"/VBS-WZto2MuENu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.000006689*1000,plotCategory("kPlotEFTT5IntWZ")),
       1927: (dirT2+"2022/"+skimType+"/VBS-WZto2MuENu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.00001045*1000,plotCategory("kPlotEFTT6IntWZ")),
       1928: (dirT2+"2022/"+skimType+"/VBS-WZto2MuENu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.000006781*1000,plotCategory("kPlotEFTT7IntWZ")),
       1929: (dirT2+"2022/"+skimType+"/VBS-WZto2MuTauNu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", -5.153e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       1930: (dirT2+"2022/"+skimType+"/VBS-WZto2MuTauNu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.0000005407*1000,plotCategory("kPlotEFTM3IntWZ")),
       1931: (dirT2+"2022/"+skimType+"/VBS-WZto2MuTauNu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", -6.29e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       1932: (dirT2+"2022/"+skimType+"/VBS-WZto2MuTauNu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.0000009958*1000,plotCategory("kPlotEFTM5IntWZ")),
       1933: (dirT2+"2022/"+skimType+"/VBS-WZto2MuTauNu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.000006643*1000,plotCategory("kPlotEFTT5IntWZ")),
       1934: (dirT2+"2022/"+skimType+"/VBS-WZto2MuTauNu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.00001036*1000,plotCategory("kPlotEFTT6IntWZ")),
       1935: (dirT2+"2022/"+skimType+"/VBS-WZto2MuTauNu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.000006839*1000,plotCategory("kPlotEFTT7IntWZ")),
       1936: (dirT2+"2022/"+skimType+"/VBS-WZto2TauENu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", -4.285e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       1937: (dirT2+"2022/"+skimType+"/VBS-WZto2TauENu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.0000005344*1000,plotCategory("kPlotEFTM3IntWZ")),
       1938: (dirT2+"2022/"+skimType+"/VBS-WZto2TauENu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.0000007902*1000,plotCategory("kPlotEFTM4IntWZ")),
       1939: (dirT2+"2022/"+skimType+"/VBS-WZto2TauENu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", -1.242e-05*1000,plotCategory("kPlotEFTM5IntWZ")),
       1940: (dirT2+"2022/"+skimType+"/VBS-WZto2TauENu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.000006634*1000,plotCategory("kPlotEFTT5IntWZ")),
       1941: (dirT2+"2022/"+skimType+"/VBS-WZto2TauENu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.00001051*1000,plotCategory("kPlotEFTT6IntWZ")),
       1942: (dirT2+"2022/"+skimType+"/VBS-WZto2TauENu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.000006874*1000,plotCategory("kPlotEFTT7IntWZ")),
       1943: (dirT2+"2022/"+skimType+"/VBS-WZto2TauMuNu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", -4.509e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       1944: (dirT2+"2022/"+skimType+"/VBS-WZto2TauMuNu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.0000006144*1000,plotCategory("kPlotEFTM3IntWZ")),
       1945: (dirT2+"2022/"+skimType+"/VBS-WZto2TauMuNu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", -9.821e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       1946: (dirT2+"2022/"+skimType+"/VBS-WZto2TauMuNu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", -1.305e-05*1000,plotCategory("kPlotEFTM5IntWZ")),
       1947: (dirT2+"2022/"+skimType+"/VBS-WZto2TauMuNu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.000006709*1000,plotCategory("kPlotEFTT5IntWZ")),
       1948: (dirT2+"2022/"+skimType+"/VBS-WZto2TauMuNu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.00001045*1000,plotCategory("kPlotEFTT6IntWZ")),
       1949: (dirT2+"2022/"+skimType+"/VBS-WZto2TauMuNu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.000006845*1000,plotCategory("kPlotEFTT7IntWZ")),
       1950: (dirT2+"2022/"+skimType+"/VBS-WZto3ENu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", -4.508e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       1951: (dirT2+"2022/"+skimType+"/VBS-WZto3ENu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.0000005066*1000,plotCategory("kPlotEFTM3IntWZ")),
       1952: (dirT2+"2022/"+skimType+"/VBS-WZto3ENu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", -6.621e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       1953: (dirT2+"2022/"+skimType+"/VBS-WZto3ENu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.000001197*1000,plotCategory("kPlotEFTM5IntWZ")),
       1954: (dirT2+"2022/"+skimType+"/VBS-WZto3ENu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.000006371*1000,plotCategory("kPlotEFTT5IntWZ")),
       1955: (dirT2+"2022/"+skimType+"/VBS-WZto3ENu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.000009477*1000,plotCategory("kPlotEFTT6IntWZ")),
       1956: (dirT2+"2022/"+skimType+"/VBS-WZto3ENu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.00000632*1000,plotCategory("kPlotEFTT7IntWZ")),
       1957: (dirT2+"2022/"+skimType+"/VBS-WZto3MuNu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", -4.468e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       1958: (dirT2+"2022/"+skimType+"/VBS-WZto3MuNu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.0000005005*1000,plotCategory("kPlotEFTM3IntWZ")),
       1959: (dirT2+"2022/"+skimType+"/VBS-WZto3MuNu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", -6.906e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       1960: (dirT2+"2022/"+skimType+"/VBS-WZto3MuNu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.000001524*1000,plotCategory("kPlotEFTM5IntWZ")),
       1961: (dirT2+"2022/"+skimType+"/VBS-WZto3MuNu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.000006547*1000,plotCategory("kPlotEFTT5IntWZ")),
       1962: (dirT2+"2022/"+skimType+"/VBS-WZto3MuNu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.000009484*1000,plotCategory("kPlotEFTT6IntWZ")),
       1963: (dirT2+"2022/"+skimType+"/VBS-WZto3MuNu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.000006383*1000,plotCategory("kPlotEFTT7IntWZ")),
       1964: (dirT2+"2022/"+skimType+"/VBS-WZto3TauNu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", -4.285e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       1965: (dirT2+"2022/"+skimType+"/VBS-WZto3TauNu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.0000005196*1000,plotCategory("kPlotEFTM3IntWZ")),
       1966: (dirT2+"2022/"+skimType+"/VBS-WZto3TauNu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.0000004334*1000,plotCategory("kPlotEFTM4IntWZ")),
       1967: (dirT2+"2022/"+skimType+"/VBS-WZto3TauNu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", -1.149e-05*1000,plotCategory("kPlotEFTM5IntWZ")),
       1968: (dirT2+"2022/"+skimType+"/VBS-WZto3TauNu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.000006569*1000,plotCategory("kPlotEFTT5IntWZ")),
       1969: (dirT2+"2022/"+skimType+"/VBS-WZto3TauNu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.000009913*1000,plotCategory("kPlotEFTT6IntWZ")),
       1970: (dirT2+"2022/"+skimType+"/VBS-WZto3TauNu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.000006535*1000,plotCategory("kPlotEFTT7IntWZ")),


       200: (dirT2+"2022EE/"+skimType+"/DYto2L-2Jets_MLL-10to50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",19982.5*1000,plotCategory("kPlotDY")),
       201: (dirT2+"2022EE/"+skimType+"/DYto2L-2Jets_MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",6345.99*1000,plotCategory("kPlotDY")),
       202: (dirT2+"2022EE/"+skimType+"/WWto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",(118.7*1.06-ggWWXS_LO_MCFM)*0.1086*0.1086*9*1000,plotCategory("kPlotqqWW")),
       203: (dirT2+"2022EE/"+skimType+"/WZto3LNu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",4.924*1.08*1000,plotCategory("kPlotWZ")),
       204: (dirT2+"2022EE/"+skimType+"/WZto2L2Q_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",7.568*1.08*1000,plotCategory("kPlotWZ")),
       205: (dirT2+"2022EE/"+skimType+"/ZZto2L2Q_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",6.788*1.19*1000,plotCategory("kPlotZZ")),
       206: (dirT2+"2022EE/"+skimType+"/ZZto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",1.031*1.16*1000,plotCategory("kPlotZZ")),
       207: (dirT2+"2022EE/"+skimType+"/ZZto4L_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",1.390*1.19*1000,plotCategory("kPlotZZ")),
       208: (dirT2+"2022EE/"+skimType+"/TTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.950*923.6*0.1086*0.1086*9*1000,plotCategory("kPlotTT")),
       209: (dirT2+"2022EE/"+skimType+"/TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.950*923.6*0.1086*3*(1-0.1086*3)*2*1000,plotCategory("kPlotTT")),
       210: (dirT2+"2022EE/"+skimType+"/TTto4Q_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",1000000*0.950*923.6*(1-0.1086*3)*(1-0.1086*3)*1000,plotCategory("kPlotNonPrompt")),
       211: (dirT2+"2022EE/"+skimType+"/TbarWplusto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",4.67*1000,plotCategory("kPlotTW")),
       212: (dirT2+"2022EE/"+skimType+"/TWminusto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",4.67*1000,plotCategory("kPlotTW")),
       213: (dirT2+"2022EE/"+skimType+"/WtoLNu-2Jets_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",64481.58*1000,plotCategory("kPlotOther")),
       214: (dirT2+"2022EE/"+skimType+"/WWW_4F_TuneCP5_13p6TeV_amcatnlo-madspin-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.23280*1000,plotCategory("kPlotVVV")),
       215: (dirT2+"2022EE/"+skimType+"/WWZ_4F_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.18510*1000,plotCategory("kPlotVVV")),
       216: (dirT2+"2022EE/"+skimType+"/WZZ_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.06206*1000,plotCategory("kPlotVVV")),
       217: (dirT2+"2022EE/"+skimType+"/ZZZ_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.01591*1000,plotCategory("kPlotVVV")),
       218: (dirT2+"2022EE/"+skimType+"/WZGtoLNuZG_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.08425*1000,plotCategory("kPlotVVV")),
       219: (dirT2+"2022EE/"+skimType+"/TTWW_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.0081651*1000,plotCategory("kPlotTVX")),
       220: (dirT2+"2022EE/"+skimType+"/TTZZ_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v3+NANOAODSIM",0.0015617*1000,plotCategory("kPlotTVX")),
       221: (dirT2+"2022EE/"+skimType+"/GluGluHtoZZto4L_M-125_TuneCP5_13p6TeV_powheg2-JHUGenV752-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",52.230*0.02619*0.101*0.101*1000,plotCategory("kPlotHiggs")),
       222: (dirT2+"2022EE/"+skimType+"/VBFHto2Zto4L_M125_TuneCP5_13p6TeV_powheg-jhugenv752-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",4.0780*0.02619*0.101*0.101*1000,plotCategory("kPlotHiggs")),
       223: (dirT2+"2022EE/"+skimType+"/TTLL_MLL-4to50_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.03949*1000,plotCategory("kPlotTVX")),
       224: (dirT2+"2022EE/"+skimType+"/TTLL_MLL-50_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.08646*1000,plotCategory("kPlotTVX")),
       225: (dirT2+"2022EE/"+skimType+"/ggWWto2L2Nu_OS_PolarizationLL_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.24053*(ggWWXS_LO_MCFM/ggWWXS_LO_MADGRAPH)*1.4*1000,plotCategory("kPlotggWW")),
       226: (dirT2+"2022EE/"+skimType+"/ggWWto2L2Nu_OS_PolarizationLT_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.08268*(ggWWXS_LO_MCFM/ggWWXS_LO_MADGRAPH)*1.4*1000,plotCategory("kPlotggWW")),
       227: (dirT2+"2022EE/"+skimType+"/ggWWto2L2Nu_OS_PolarizationTL_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.08268*(ggWWXS_LO_MCFM/ggWWXS_LO_MADGRAPH)*1.4*1000,plotCategory("kPlotggWW")),
       228: (dirT2+"2022EE/"+skimType+"/ggWWto2L2Nu_OS_PolarizationTT_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",3.10724*(ggWWXS_LO_MCFM/ggWWXS_LO_MADGRAPH)*1.4*1000,plotCategory("kPlotggWW")),
       229: (dirT2+"2022EE/"+skimType+"/DYGto2LG-1Jets_MLL-50_PTG-10to50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",124.18762*1000,plotCategory("kPlotVG")),
       230: (dirT2+"2022EE/"+skimType+"/DYGto2LG-1Jets_MLL-50_PTG-50to100_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v1+NANOAODSIM",2.08977*1000,plotCategory("kPlotVG")),
       231: (dirT2+"2022EE/"+skimType+"/DYGto2LG-1Jets_MLL-50_PTG-100to200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.34767*1000,plotCategory("kPlotVG")),
       232: (dirT2+"2022EE/"+skimType+"/DYGto2LG-1Jets_MLL-50_PTG-200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v4+NANOAODSIM",0.04734*1000,plotCategory("kPlotVG")),
       233: (dirT2+"2022EE/"+skimType+"/WGtoLNuG-1Jets_PTG-10to100_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",668.91538*1000,plotCategory("kPlotVG")),
       234: (dirT2+"2022EE/"+skimType+"/WGtoLNuG-1Jets_PTG-100to200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",2.22141*1000,plotCategory("kPlotVG")),
       235: (dirT2+"2022EE/"+skimType+"/WGtoLNuG-1Jets_PTG-200to400_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v3+NANOAODSIM",0.291367*1000,plotCategory("kPlotVG")),
       236: (dirT2+"2022EE/"+skimType+"/WWto4Q_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",1000000*(118.7*1.06-ggWWXS_LO_MCFM)*(1-0.1086*3)*(1-0.1086*3)*1000,plotCategory("kPlotNonPrompt")),
       237: (dirT2+"2022EE/"+skimType+"/GluGluHto2Tau_M-125_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",52.230*0.06272*1000,plotCategory("kPlotHiggs")),
       238: (dirT2+"2022EE/"+skimType+"/VBFHToTauTau_M125_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",4.0780*0.06272*1000,plotCategory("kPlotHiggs")),
       239: (dirT2+"2022EE/"+skimType+"/DYGto2LG-1Jets_MLL-4to50_PTG-10to100_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",87.73210*1000,plotCategory("kPlotVG")),
       240: (dirT2+"2022EE/"+skimType+"/DYGto2LG-1Jets_MLL-4to50_PTG-100to200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.24095*1000,plotCategory("kPlotVG")),
       241: (dirT2+"2022EE/"+skimType+"/DYGto2LG-1Jets_MLL-4to50_PTG-200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.02228*1000,plotCategory("kPlotVG")),
       242: (dirT2+"2022EE/"+skimType+"/TbarWplus_DR_AtLeastOneLepton_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",23.97*1000,plotCategory("kPlotTW")),
       243: (dirT2+"2022EE/"+skimType+"/TWminus_DR_AtLeastOneLepton_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",23.97*1000,plotCategory("kPlotTW")),
       244: (dirT2+"2022EE/"+skimType+"/VH_HtoNonbb_M-125_TuneCP5_13p6TeV_amcatnloFXFX-madspin-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v1+NANOAODSIM",(0.9439+1.4570)*(1-0.577)*1000,plotCategory("kPlotHiggs")),
       245: (dirT2+"2022EE/"+skimType+"/DYto2L-2Jets_MLL-50_0J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",5034.65*1000,plotCategory("kPlotDY")),
       246: (dirT2+"2022EE/"+skimType+"/DYto2L-2Jets_MLL-50_1J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",952.29*1000,plotCategory("kPlotDY")),
       247: (dirT2+"2022EE/"+skimType+"/DYto2L-2Jets_MLL-50_2J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",359.05*1000,plotCategory("kPlotDY")),
       248: (dirT2+"2022EE/"+skimType+"/TTLNu-1Jets_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v4+NANOAODSIM",0.2502*1000,plotCategory("kPlotTVX")),
       249: (dirT2+"2022EE/"+skimType+"/TZQB-Zto2L-4FS_MLL-30_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.07968*1.30*1000,plotCategory("kPlotTVX")),
       250: (dirT2+"2022EE/"+skimType+"/VBS-SSWW_PolarizationLL_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v3+NANOAODSIM",0.002190*1000,plotCategory("kPlotEWKSSWW")),
       251: (dirT2+"2022EE/"+skimType+"/VBS-SSWW_PolarizationTL_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v1+NANOAODSIM",0.011700*1000,plotCategory("kPlotEWKSSWW")),
       252: (dirT2+"2022EE/"+skimType+"/VBS-SSWW_PolarizationTT_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v3+NANOAODSIM",0.017635*1000,plotCategory("kPlotEWKSSWW")),
       253: (dirT2+"2022EE/"+skimType+"/GluGluHto2Wto2L2Nu_M-125_TuneCP5_13p6TeV_powheg-jhugen752-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",52.230*0.2137*0.1086*0.1086*9*1000,plotCategory("kPlotHiggs")),
       254: (dirT2+"2022EE/"+skimType+"/VBFHto2Wto2L2Nu_M-125_TuneCP5_13p6TeV_powheg-jhugen752-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",4.0780*0.2137*0.1086*0.1086*9*1000,plotCategory("kPlotHiggs")),
       255: (dirT2+"2022EE/"+skimType+"/TTHtoNon2B_M-125_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.5700*(1-0.577)*1000,plotCategory("kPlotHiggs")),
       256: (dirT2+"2022EE/"+skimType+"/WGtoLNuG-1Jets_PTG-400to600_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v3+NANOAODSIM",0.022322*1000,plotCategory("kPlotVG")),
       257: (dirT2+"2022EE/"+skimType+"/WGtoLNuG-1Jets_PTG-600_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v3+NANOAODSIM",0.004918*1000,plotCategory("kPlotVG")),
       258: (dirT2+"2022EE/"+skimType+"/WW_DoubleScattering_TuneCP5_13p6TeV_pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",2.14891*1000,plotCategory("kPlotOther")),
       259: (dirT2+"2022EE/"+skimType+"/GluGlutoContinto2Zto4E_TuneCP5_13p6TeV_mcfm-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.5*0.0061150*1000,plotCategory("kPlotZZ")),
       260: (dirT2+"2022EE/"+skimType+"/GluGlutoContinto2Zto4Mu_TuneCP5_13p6TeV_mcfm-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.5*0.0061150*1000,plotCategory("kPlotZZ")),
       261: (dirT2+"2022EE/"+skimType+"/GluGlutoContinto2Zto4Tau_TuneCP5_13p6TeV_mcfm-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.5*0.0061150*1000,plotCategory("kPlotZZ")),
       262: (dirT2+"2022EE/"+skimType+"/GluGluToContinto2Zto2E2Tau_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v4+NANOAODSIM",0.0061150*1000,plotCategory("kPlotZZ")),
       263: (dirT2+"2022EE/"+skimType+"/GluGluToContinto2Zto2Mu2Tau_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v4+NANOAODSIM",0.0061150*1000,plotCategory("kPlotZZ")),
       264: (dirT2+"2022EE/"+skimType+"/GluGluToContinto2Zto2E2Mu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.0061150*1000,plotCategory("kPlotZZ")),
       265: (dirT2+"2022EE/"+skimType+"/GluGlutoContintoWWtoENuENu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       266: (dirT2+"2022EE/"+skimType+"/GluGlutoContintoWWtoENuMuNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       267: (dirT2+"2022EE/"+skimType+"/GluGlutoContintoWWtoENuTauNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       268: (dirT2+"2022EE/"+skimType+"/GluGlutoContintoWWtoMuNuENu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       269: (dirT2+"2022EE/"+skimType+"/GluGlutoContintoWWtoMuNuMuNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       270: (dirT2+"2022EE/"+skimType+"/GluGlutoContintoWWtoMuNuTauNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       271: (dirT2+"2022EE/"+skimType+"/GluGlutoContintoWWtoTauNuENu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       272: (dirT2+"2022EE/"+skimType+"/GluGlutoContintoWWtoTauNuMuNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       273: (dirT2+"2022EE/"+skimType+"/GluGlutoContintoWWtoTauNuTauNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       274: (dirT2+"2022EE/"+skimType+"/WWto2L2Nu-2Jets_OS_noTop_EW_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.3301419*1000,plotCategory("kPlotqqWW")),
       275: (dirT2+"2022EE/"+skimType+"/WWto2L2Nu-2Jets_OS_noTop_QCD_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",2.6758028*1000,plotCategory("kPlotqqWW")),
       276: (dirT2+"2022EE/"+skimType+"/WWto2L2Nu-2Jets_SS_noTop_EW_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",         0.0295255*1000,plotCategory("kPlotEWKSSWW")),
       277: (dirT2+"2022EE/"+skimType+"/WWto2L2Nu-2Jets_SS_noTop_QCD_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",        0.0279662*1000,plotCategory("kPlotQCDSSWW")),
       278: (dirT2+"2022EE/"+skimType+"/WZto3LNu-2Jets_EW_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",           0.0429366*1000,plotCategory("kPlotEWKWZ")),
       279: (dirT2+"2022EE/"+skimType+"/WZto3LNu-2Jets_QCD_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",          0.4958618*1000*0.70,plotCategory("kPlotWZ")),
       280: (dirT2+"2022EE/"+skimType+"/ZZto2L2Nu-2Jets_EW_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",                  0.0051721*1000,plotCategory("kPlotZZ")),
       281: (dirT2+"2022EE/"+skimType+"/ZZto2L2Nu-2Jets_QCD_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",                 0.0912313*1000*1.40,plotCategory("kPlotZZ")),
       282: (dirT2+"2022EE/"+skimType+"/ZZto4L-2Jets_EW_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",                     0.0011422*1000,plotCategory("kPlotZZ")),
       283: (dirT2+"2022EE/"+skimType+"/ZZto4L-2Jets_QCD_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v3+NANOAODSIM",                    0.0202984*1000*1.40,plotCategory("kPlotZZ")),
       289: (dirT2+"2022EE/"+skimType+"/SSWWJJ_Interference_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.00341005*1000,plotCategory("kPlotQCDSSWW")),
       290: (dirT2+"2022EE/"+skimType+"/VBSWZ-Interference_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.04806677*1000,plotCategory("kPlotWZ")),
       292: (dirT3+"2022EE/SM", 0.0295255*1000,plotCategory("kPlotEWKSSWW")),
       293: (dirT2+"2022EE/"+skimType+"/VBS_SSWW_M0Int_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.000297*1000,plotCategory("kPlotEFTM0Int")),
       294: (dirT2+"2022EE/"+skimType+"/VBS_SSWW_M0Quad_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.007333*1000,plotCategory("kPlotEFTM0Quad")),
       295: (dirT3+"Sherpa_Sample/2022EE", 39.8961,plotCategory("kPlotEWKSSWW")),
       296: (dirT2+"2022EE/"+skimType+"/VBS_SSWW_M1Int_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", -0.0003746 *1000,plotCategory("kPlotEFTM1Int")),
       297: (dirT2+"2022EE/"+skimType+"/VBS_SSWW_M1Quad_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.007688*1000,plotCategory("kPlotEFTM1Quad")),
       298: (dirT2+"2022EE/"+skimType+"/VBS_SSWW_M7Int_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.00002167*1000,plotCategory("kPlotEFTM7Int")),
       299: (dirT2+"2022EE/"+skimType+"/VBS_SSWW_M7Quad_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.003405*1000,plotCategory("kPlotEFTM7Quad")),
       2990: (dirT2+"2022EE/"+skimType+"/VBS_SSWW_S0Int_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", -0.0003575*1000,plotCategory("kPlotEFTS0Int")),
       2991: (dirT2+"2022EE/"+skimType+"/VBS_SSWW_S0Quad_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.008078*1000,plotCategory("kPlotEFTS0Quad")),
       2992: (dirT2+"2022EE/"+skimType+"/VBS_SSWW_T0Int_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",  -0.0005086*1000,plotCategory("kPlotEFTT0Int")),
       2993: (dirT2+"2022EE/"+skimType+"/VBS_SSWW_T0Quad_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.02811*1000,plotCategory("kPlotEFTT0Quad")),
       2994: (dirT2+"2022EE/"+skimType+"/VBS_SSWW_T1Int_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", -0.001284*1000,plotCategory("kPlotEFTT1Int")),
       2995: (dirT2+"2022EE/"+skimType+"/VBS_SSWW_T1Quad_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.03099*1000,plotCategory("kPlotEFTT1Quad")),
       2996: (dirT2+"2022EE/"+skimType+"/VBS_SSWW_T2Int_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",  -0.001341*1000,plotCategory("kPlotEFTT2Int")),
       2997: (dirT2+"2022EE/"+skimType+"/VBS_SSWW_T2Quad_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.01401*1000,plotCategory("kPlotEFTT2Quad")),
       2901: (dirT2+"2022EE/"+skimType+"/VBS-WZ-M2Quad_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.0002623*1000,plotCategory("kPlotEFTM2QuadWZ")),
       2902: (dirT2+"2022EE/"+skimType+"/VBS-WZ-M3Quad_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.0001106*1000,plotCategory("kPlotEFTM3QuadWZ")),
       2903: (dirT2+"2022EE/"+skimType+"/VBS-WZ-M4Quad_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.001995*1000,plotCategory("kPlotEFTM4QuadWZ")),
       2904: (dirT2+"2022EE/"+skimType+"/VBS-WZ-M5Quad_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.001099*1000,plotCategory("kPlotEFTM5QuadWZ")),
       2905: (dirT2+"2022EE/"+skimType+"/VBS-WZ-T5Quad_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.001619*1000,plotCategory("kPlotEFTT5QuadWZ")),
       2906: (dirT2+"2022EE/"+skimType+"/VBS-WZ-T6Quad_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.001873*1000,plotCategory("kPlotEFTT6QuadWZ")),
       2907: (dirT2+"2022EE/"+skimType+"/VBS-WZ-T7Quad_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.0002992*1000,plotCategory("kPlotEFTT7QuadWZ")),
       2908: (dirT2+"2022EE/"+skimType+"/VBS-WZto2EMuNu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", -3.893e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       2909: (dirT2+"2022EE/"+skimType+"/VBS-WZto2EMuNu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.0000005482*1000,plotCategory("kPlotEFTM3IntWZ")),
       2910: (dirT2+"2022EE/"+skimType+"/VBS-WZto2EMuNu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", -6.032e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       2911: (dirT2+"2022EE/"+skimType+"/VBS-WZto2EMuNu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.000001213*1000,plotCategory("kPlotEFTM5IntWZ")),
       2912: (dirT2+"2022EE/"+skimType+"/VBS-WZto2EMuNu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.000006792*1000,plotCategory("kPlotEFTT5IntWZ")),
       2913: (dirT2+"2022EE/"+skimType+"/VBS-WZto2EMuNu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.00001022*1000,plotCategory("kPlotEFTT6IntWZ")),
       2914: (dirT2+"2022EE/"+skimType+"/VBS-WZto2EMuNu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.000006764*1000,plotCategory("kPlotEFTT7IntWZ")),
       2915: (dirT2+"2022EE/"+skimType+"/VBS-WZto2ETauNu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", -4.604e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       2916: (dirT2+"2022EE/"+skimType+"/VBS-WZto2ETauNu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.0000005346*1000,plotCategory("kPlotEFTM3IntWZ")),
       2917: (dirT2+"2022EE/"+skimType+"/VBS-WZto2ETauNu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", -5.705e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       2918: (dirT2+"2022EE/"+skimType+"/VBS-WZto2ETauNu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.000001552*1000,plotCategory("kPlotEFTM5IntWZ")),
       2919: (dirT2+"2022EE/"+skimType+"/VBS-WZto2ETauNu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.00000669*1000,plotCategory("kPlotEFTT5IntWZ")),
       2920: (dirT2+"2022EE/"+skimType+"/VBS-WZto2ETauNu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.00001023*1000,plotCategory("kPlotEFTT6IntWZ")),
       2921: (dirT2+"2022EE/"+skimType+"/VBS-WZto2ETauNu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.000006783*1000,plotCategory("kPlotEFTT7IntWZ")),
       2922: (dirT2+"2022EE/"+skimType+"/VBS-WZto2MuENu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", -4.819e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       2923: (dirT2+"2022EE/"+skimType+"/VBS-WZto2MuENu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.0000004808*1000,plotCategory("kPlotEFTM3IntWZ")),
       2924: (dirT2+"2022EE/"+skimType+"/VBS-WZto2MuENu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", -6.275e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       2925: (dirT2+"2022EE/"+skimType+"/VBS-WZto2MuENu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.000001302*1000,plotCategory("kPlotEFTM5IntWZ")),
       2926: (dirT2+"2022EE/"+skimType+"/VBS-WZto2MuENu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.000006689*1000,plotCategory("kPlotEFTT5IntWZ")),
       2927: (dirT2+"2022EE/"+skimType+"/VBS-WZto2MuENu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.00001045*1000,plotCategory("kPlotEFTT6IntWZ")),
       2928: (dirT2+"2022EE/"+skimType+"/VBS-WZto2MuENu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.000006781*1000,plotCategory("kPlotEFTT7IntWZ")),
       2929: (dirT2+"2022EE/"+skimType+"/VBS-WZto2MuTauNu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", -5.153e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       2930: (dirT2+"2022EE/"+skimType+"/VBS-WZto2MuTauNu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.0000005407*1000,plotCategory("kPlotEFTM3IntWZ")),
       2931: (dirT2+"2022EE/"+skimType+"/VBS-WZto2MuTauNu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", -6.29e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       2932: (dirT2+"2022EE/"+skimType+"/VBS-WZto2MuTauNu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.0000009958*1000,plotCategory("kPlotEFTM5IntWZ")),
       2933: (dirT2+"2022EE/"+skimType+"/VBS-WZto2MuTauNu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.000006643*1000,plotCategory("kPlotEFTT5IntWZ")),
       2934: (dirT2+"2022EE/"+skimType+"/VBS-WZto2MuTauNu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.00001036*1000,plotCategory("kPlotEFTT6IntWZ")),
       2935: (dirT2+"2022EE/"+skimType+"/VBS-WZto2MuTauNu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.000006839*1000,plotCategory("kPlotEFTT7IntWZ")),
       2936: (dirT2+"2022EE/"+skimType+"/VBS-WZto2TauENu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", -4.285e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       2937: (dirT2+"2022EE/"+skimType+"/VBS-WZto2TauENu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.0000005344*1000,plotCategory("kPlotEFTM3IntWZ")),
       2938: (dirT2+"2022EE/"+skimType+"/VBS-WZto2TauENu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.0000007902*1000,plotCategory("kPlotEFTM4IntWZ")),
       2939: (dirT2+"2022EE/"+skimType+"/VBS-WZto2TauENu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", -1.242e-05*1000,plotCategory("kPlotEFTM5IntWZ")),
       2940: (dirT2+"2022EE/"+skimType+"/VBS-WZto2TauENu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.000006634*1000,plotCategory("kPlotEFTT5IntWZ")),
       2941: (dirT2+"2022EE/"+skimType+"/VBS-WZto2TauENu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.00001051*1000,plotCategory("kPlotEFTT6IntWZ")),
       2942: (dirT2+"2022EE/"+skimType+"/VBS-WZto2TauENu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.000006874*1000,plotCategory("kPlotEFTT7IntWZ")),
       2943: (dirT2+"2022EE/"+skimType+"/VBS-WZto2TauMuNu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", -4.509e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       2944: (dirT2+"2022EE/"+skimType+"/VBS-WZto2TauMuNu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.0000006144*1000,plotCategory("kPlotEFTM3IntWZ")),
       2945: (dirT2+"2022EE/"+skimType+"/VBS-WZto2TauMuNu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", -9.821e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       2946: (dirT2+"2022EE/"+skimType+"/VBS-WZto2TauMuNu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", -1.305e-05*1000,plotCategory("kPlotEFTM5IntWZ")),
       2947: (dirT2+"2022EE/"+skimType+"/VBS-WZto2TauMuNu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.000006709*1000,plotCategory("kPlotEFTT5IntWZ")),
       2948: (dirT2+"2022EE/"+skimType+"/VBS-WZto2TauMuNu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.00001045*1000,plotCategory("kPlotEFTT6IntWZ")),
       2949: (dirT2+"2022EE/"+skimType+"/VBS-WZto2TauMuNu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.000006845*1000,plotCategory("kPlotEFTT7IntWZ")),
       2950: (dirT2+"2022EE/"+skimType+"/VBS-WZto3ENu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", -4.508e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       2951: (dirT2+"2022EE/"+skimType+"/VBS-WZto3ENu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.0000005066*1000,plotCategory("kPlotEFTM3IntWZ")),
       2952: (dirT2+"2022EE/"+skimType+"/VBS-WZto3ENu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", -6.621e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       2953: (dirT2+"2022EE/"+skimType+"/VBS-WZto3ENu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.000001197*1000,plotCategory("kPlotEFTM5IntWZ")),
       2954: (dirT2+"2022EE/"+skimType+"/VBS-WZto3ENu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.000006371*1000,plotCategory("kPlotEFTT5IntWZ")),
       2955: (dirT2+"2022EE/"+skimType+"/VBS-WZto3ENu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.000009477*1000,plotCategory("kPlotEFTT6IntWZ")),
       2956: (dirT2+"2022EE/"+skimType+"/VBS-WZto3ENu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.00000632*1000,plotCategory("kPlotEFTT7IntWZ")),
       2957: (dirT2+"2022EE/"+skimType+"/VBS-WZto3MuNu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", -4.468e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       2958: (dirT2+"2022EE/"+skimType+"/VBS-WZto3MuNu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.0000005005*1000,plotCategory("kPlotEFTM3IntWZ")),
       2959: (dirT2+"2022EE/"+skimType+"/VBS-WZto3MuNu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", -6.906e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       2960: (dirT2+"2022EE/"+skimType+"/VBS-WZto3MuNu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.000001524*1000,plotCategory("kPlotEFTM5IntWZ")),
       2961: (dirT2+"2022EE/"+skimType+"/VBS-WZto3MuNu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.000006547*1000,plotCategory("kPlotEFTT5IntWZ")),
       2962: (dirT2+"2022EE/"+skimType+"/VBS-WZto3MuNu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.000009484*1000,plotCategory("kPlotEFTT6IntWZ")),
       2963: (dirT2+"2022EE/"+skimType+"/VBS-WZto3MuNu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.000006383*1000,plotCategory("kPlotEFTT7IntWZ")),
       2964: (dirT2+"2022EE/"+skimType+"/VBS-WZto3TauNu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", -4.285e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       2965: (dirT2+"2022EE/"+skimType+"/VBS-WZto3TauNu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.0000005196*1000,plotCategory("kPlotEFTM3IntWZ")),
       2966: (dirT2+"2022EE/"+skimType+"/VBS-WZto3TauNu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.0000004334*1000,plotCategory("kPlotEFTM4IntWZ")),
       2967: (dirT2+"2022EE/"+skimType+"/VBS-WZto3TauNu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", -1.149e-05*1000,plotCategory("kPlotEFTM5IntWZ")),
       2968: (dirT2+"2022EE/"+skimType+"/VBS-WZto3TauNu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.000006569*1000,plotCategory("kPlotEFTT5IntWZ")),
       2969: (dirT2+"2022EE/"+skimType+"/VBS-WZto3TauNu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.000009913*1000,plotCategory("kPlotEFTT6IntWZ")),
       2970: (dirT2+"2022EE/"+skimType+"/VBS-WZto3TauNu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.000006535*1000,plotCategory("kPlotEFTT7IntWZ")),


# Era C 2023, 20230
       300: (dirT2+"2023/"+skimType+"/DYto2L-2Jets_MLL-10to50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14_ext1-v3+NANOAODSIM",19982.5*1000,plotCategory("kPlotDY")),
       301: (dirT2+"2023/"+skimType+"/DYto2L-2Jets_MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v1+NANOAODSIM",6345.99*1000,plotCategory("kPlotDY")),
       302: (dirT2+"2023/"+skimType+"/WWto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v4+NANOAODSIM",(118.7*1.06-ggWWXS_LO_MCFM)*0.1086*0.1086*9*1000,plotCategory("kPlotqqWW")),
       303: (dirT2+"2023/"+skimType+"/WZto3LNu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v2+NANOAODSIM",4.924*1.08*1000,plotCategory("kPlotWZ")),
       304: (dirT2+"2023/"+skimType+"/WZto2L2Q_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v3+NANOAODSIM",7.568*1.08*1000,plotCategory("kPlotWZ")),
       305: (dirT2+"2023/"+skimType+"/ZZto2L2Q_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v1+NANOAODSIM",6.788*1.19*1000,plotCategory("kPlotZZ")),
       306: (dirT2+"2023/"+skimType+"/ZZto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v1+NANOAODSIM",1.031*1.16*1000,plotCategory("kPlotZZ")),
       307: (dirT2+"2023/"+skimType+"/ZZto4L_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v3+NANOAODSIM",1.390*1.19*1000,plotCategory("kPlotZZ")),
       308: (dirT2+"2023/"+skimType+"/TTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v2+NANOAODSIM",0.950*923.6*0.1086*0.1086*9*1000,plotCategory("kPlotTT")),
       309: (dirT2+"2023/"+skimType+"/TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v2+NANOAODSIM",0.950*923.6*0.1086*3*(1-0.1086*3)*2*1000,plotCategory("kPlotTT")),
       310: (dirT2+"2023/"+skimType+"/TTto4Q_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23NanoAODv12-JMENano12p5_132X_mcRun3_2023_realistic_v5-v1+NANOAODSIM",1000000*0.950*923.6*(1-0.1086*3)*(1-0.1086*3)*1000,plotCategory("kPlotNonPrompt")),
       311: (dirT2+"2023/"+skimType+"/TbarWplusto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v4+NANOAODSIM",4.67*1000,plotCategory("kPlotTW")),
       312: (dirT2+"2023/"+skimType+"/TWminusto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v2+NANOAODSIM",4.67*1000,plotCategory("kPlotTW")),
       313: (dirT2+"2023/"+skimType+"/WtoLNu-4Jets_TuneCP5_13p6TeV_madgraphMLM-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v3+NANOAODSIM",64481.58*1000,plotCategory("kPlotOther")),
       314: (dirT2+"2023/"+skimType+"/WWW_4F_TuneCP5_13p6TeV_amcatnlo-madspin-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v2+NANOAODSIM",0.23280*1000,plotCategory("kPlotVVV")),
       315: (dirT2+"2023/"+skimType+"/WWZ_4F_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v2+NANOAODSIM",0.18510*1000,plotCategory("kPlotVVV")),
       316: (dirT2+"2023/"+skimType+"/WZZ_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v2+NANOAODSIM",0.06206*1000,plotCategory("kPlotVVV")),
       317: (dirT2+"2023/"+skimType+"/ZZZ_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v2+NANOAODSIM",0.01591*1000,plotCategory("kPlotVVV")),
       318: (dirT2+"2023/"+skimType+"/WZGtoLNuZG_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",0.08425*1000,plotCategory("kPlotVVV")),
       319: (dirT2+"2023/"+skimType+"/TTWW_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",0.0081651*1000,plotCategory("kPlotTVX")),
       320: (dirT2+"2023/"+skimType+"/TTZZ_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v4+NANOAODSIM",0.0015617*1000,plotCategory("kPlotTVX")),
       321: (dirT2+"2023/"+skimType+"/GluGluHtoZZto4L_M-125_TuneCP5_13p6TeV_powheg-jhugen-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v3+NANOAODSIM",52.230*0.02619*0.101*0.101*1000,plotCategory("kPlotHiggs")),
       322: (dirT2+"2023/"+skimType+"/VBFHto2Zto4L_M-125_TuneCP5_13p6TeV_powheg-jhugen-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v3+NANOAODSIM",4.0780*0.02619*0.101*0.101*1000,plotCategory("kPlotHiggs")),
       323: (dirT2+"2023/"+skimType+"/TTLL_MLL-4to50_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",0.03949*1000,plotCategory("kPlotTVX")),
       324: (dirT2+"2023/"+skimType+"/TTLL_MLL-50_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",0.08646*1000,plotCategory("kPlotTVX")),
       325: (dirT2+"2023/"+skimType+"/ggWWto2L2Nu_OS_PolarizationLL_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.24053*(ggWWXS_LO_MCFM/ggWWXS_LO_MADGRAPH)*1.4*1000,plotCategory("kPlotggWW")),
       326: (dirT2+"2023/"+skimType+"/ggWWto2L2Nu_OS_PolarizationLT_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.08268*(ggWWXS_LO_MCFM/ggWWXS_LO_MADGRAPH)*1.4*1000,plotCategory("kPlotggWW")),
       327: (dirT2+"2023/"+skimType+"/ggWWto2L2Nu_OS_PolarizationTL_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.08268*(ggWWXS_LO_MCFM/ggWWXS_LO_MADGRAPH)*1.4*1000,plotCategory("kPlotggWW")),
       328: (dirT2+"2023/"+skimType+"/ggWWto2L2Nu_OS_PolarizationTT_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",3.10724*(ggWWXS_LO_MCFM/ggWWXS_LO_MADGRAPH)*1.4*1000,plotCategory("kPlotggWW")),
       329: (dirT2+"2023/"+skimType+"/DYGto2LG-1Jets_MLL-50_PTG-10to100_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v4+NANOAODSIM",126.469425988806051*1000,plotCategory("kPlotVG")),
       330: (dirT2+"2023/"+skimType+"/DYGto2LG-1Jets_MLL-50_PTG-100to200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v3+NANOAODSIM",0.347454856033058*1000,plotCategory("kPlotVG")),
       331: (dirT2+"2023/"+skimType+"/DYGto2LG-1Jets_MLL-50_PTG-200to400_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v4+NANOAODSIM",0.043623155782532*1000,plotCategory("kPlotVG")),
       332: (dirT2+"2023/"+skimType+"/DYGto2LG-1Jets_MLL-50_PTG-400to600_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v4+NANOAODSIM",0.003152651247494*1000,plotCategory("kPlotVG")),
       333: (dirT2+"2023/"+skimType+"/WGtoLNuG-1Jets_PTG-10to100_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",668.91538*1000,plotCategory("kPlotVG")),
       334: (dirT2+"2023/"+skimType+"/WGtoLNuG-1Jets_PTG-100to200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",2.22141*1000,plotCategory("kPlotVG")),
       335: (dirT2+"2023/"+skimType+"/WGtoLNuG-1Jets_PTG-200to400_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v3+NANOAODSIM",0.291367*1000,plotCategory("kPlotVG")),
       336: (dirT2+"2023/"+skimType+"/WWto4Q_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v4+NANOAODSIM",1000000*(118.7*1.06-ggWWXS_LO_MCFM)*(1-0.1086*3)*(1-0.1086*3)*1000,plotCategory("kPlotNonPrompt")),
       337: (dirT2+"2023/"+skimType+"/GluGluHto2Tau_M-125_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",52.230*0.06272*1000,plotCategory("kPlotHiggs")),
       338: (dirT2+"2023/"+skimType+"/VBFHToTauTau_M125_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",4.0780*0.06272*1000,plotCategory("kPlotHiggs")),
       339: (dirT2+"2023/"+skimType+"/DYGto2LG-1Jets_MLL-4to50_PTG-10to100_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",87.73210*1000,plotCategory("kPlotVG")),
       340: (dirT2+"2023/"+skimType+"/DYGto2LG-1Jets_MLL-4to50_PTG-100to200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.24095*1000,plotCategory("kPlotVG")),
       341: (dirT2+"2023/"+skimType+"/DYGto2LG-1Jets_MLL-4to50_PTG-200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.02228*1000,plotCategory("kPlotVG")),
       342: (dirT2+"2023/"+skimType+"/TbarWplus_DR_AtLeastOneLepton_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",23.97*1000,plotCategory("kPlotTW")),
       343: (dirT2+"2023/"+skimType+"/TWminus_DR_AtLeastOneLepton_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",23.97*1000,plotCategory("kPlotTW")),
       344: (dirT2+"2023/"+skimType+"/VH_HtoNonbb_M-125_TuneCP5_13p6TeV_amcatnloFXFX-madspin-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",(0.9439+1.4570)*(1-0.577)*1000,plotCategory("kPlotHiggs")),
       345: (dirT2+"2023/"+skimType+"/DYto2L-2Jets_MLL-50_0J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v3+NANOAODSIM",5034.65*1000,plotCategory("kPlotDY")),
       346: (dirT2+"2023/"+skimType+"/DYto2L-2Jets_MLL-50_1J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v3+NANOAODSIM",952.29*1000,plotCategory("kPlotDY")),
       347: (dirT2+"2023/"+skimType+"/DYto2L-2Jets_MLL-50_2J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v3+NANOAODSIM",359.05*1000,plotCategory("kPlotDY")),
       348: (dirT2+"2023/"+skimType+"/TTLNu-1Jets_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",0.2502*1000,plotCategory("kPlotTVX")),
       349: (dirT2+"2023/"+skimType+"/TZQB-ZtoLL-TtoL-CPV_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",0.07968*1.00*1000,plotCategory("kPlotTVX")),
       350: (dirT2+"2023/"+skimType+"/VBS-SSWW_PolarizationLL_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v3+NANOAODSIM",0.002190*1000,plotCategory("kPlotEWKSSWW")),
       351: (dirT2+"2023/"+skimType+"/VBS-SSWW_PolarizationTL_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v3+NANOAODSIM",0.011700*1000,plotCategory("kPlotEWKSSWW")),
       352: (dirT2+"2023/"+skimType+"/VBS-SSWW_PolarizationTT_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v3+NANOAODSIM",0.017635*1000,plotCategory("kPlotEWKSSWW")),
       353: (dirT2+"2023/"+skimType+"/GluGluHto2Wto2L2Nu_M-125_TuneCP5_13p6TeV_powheg-jhugen752-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",52.230*0.2137*0.1086*0.1086*9*1000,plotCategory("kPlotHiggs")),
       354: (dirT2+"2023/"+skimType+"/VBFHto2Wto2L2Nu_M-125_TuneCP5_13p6TeV_powheg-jhugen752-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",4.0780*0.2137*0.1086*0.1086*9*1000,plotCategory("kPlotHiggs")),
       355: (dirT2+"2023/"+skimType+"/TTHtoNon2B_M-125_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v2+NANOAODSIM",0.5700*(1-0.577)*1000,plotCategory("kPlotHiggs")),
       356: (dirT2+"2023/"+skimType+"/WGtoLNuG-1Jets_PTG-400to600_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v3+NANOAODSIM",0.022322*1000,plotCategory("kPlotVG")),
       357: (dirT2+"2023/"+skimType+"/WGtoLNuG-1Jets_PTG-600_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v3+NANOAODSIM",0.004918*1000,plotCategory("kPlotVG")),
       358: (dirT2+"2023/"+skimType+"/WW_DoubleScattering_TuneCP5_13p6TeV_pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",2.14891*1000,plotCategory("kPlotOther")),
       359: (dirT2+"2023/"+skimType+"/GluGlutoContinto2Zto4E_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v3+NANOAODSIM",0.5*0.0061150*1000,plotCategory("kPlotZZ")),
       360: (dirT2+"2023/"+skimType+"/GluGlutoContinto2Zto4Mu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v3+NANOAODSIM",0.5*0.0061150*1000,plotCategory("kPlotZZ")),
       361: (dirT2+"2023/"+skimType+"/GluGlutoContinto2Zto4Tau_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v3+NANOAODSIM",0.5*0.0061150*1000,plotCategory("kPlotZZ")),
       362: (dirT2+"2023/"+skimType+"/GluGlutoContinto2Zto2E2Tau_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v3+NANOAODSIM",0.0061150*1000,plotCategory("kPlotZZ")),
       363: (dirT2+"2023/"+skimType+"/GluGlutoContinto2Zto2Mu2Tau_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v3+NANOAODSIM",0.0061150*1000,plotCategory("kPlotZZ")),
       364: (dirT2+"2023/"+skimType+"/GluGluToContinto2Zto2E2Mu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",0.0061150*1000,plotCategory("kPlotZZ")),
       365: (dirT2+"2023/"+skimType+"/GluGlutoContintoWWtoENuENu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       366: (dirT2+"2023/"+skimType+"/GluGlutoContintoWWtoENuMuNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       367: (dirT2+"2023/"+skimType+"/GluGlutoContintoWWtoENuTauNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       368: (dirT2+"2023/"+skimType+"/GluGlutoContintoWWtoMuNuENu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       369: (dirT2+"2023/"+skimType+"/GluGlutoContintoWWtoMuNuMuNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       370: (dirT2+"2023/"+skimType+"/GluGlutoContintoWWtoMuNuTauNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       371: (dirT2+"2023/"+skimType+"/GluGlutoContintoWWtoTauNuENu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       372: (dirT2+"2023/"+skimType+"/GluGlutoContintoWWtoTauNuMuNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       373: (dirT2+"2023/"+skimType+"/GluGlutoContintoWWtoTauNuTauNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       374: (dirT2+"2023/"+skimType+"/WWto2L2Nu-2Jets_OS_noTop_EW_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.3301419*1000,plotCategory("kPlotqqWW")),
       375: (dirT2+"2023/"+skimType+"/WWto2L2Nu-2Jets_OS_noTop_QCD_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",2.6758028*1000,plotCategory("kPlotqqWW")),
       376: (dirT2+"2023/"+skimType+"/WWto2L2Nu-2Jets_SS_noTop_EW_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",         0.0295255*1000,plotCategory("kPlotEWKSSWW")),
       377: (dirT2+"2023/"+skimType+"/WWto2L2Nu-2Jets_SS_noTop_QCD_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",        0.0279662*1000,plotCategory("kPlotQCDSSWW")),
       378: (dirT2+"2023/"+skimType+"/WZto3LNu-2Jets_EW_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",           0.0429366*1000,plotCategory("kPlotEWKWZ")),
       379: (dirT2+"2023/"+skimType+"/WZto3LNu-2Jets_QCD_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v1+NANOAODSIM",          0.4958618*1000*0.70,plotCategory("kPlotWZ")),
       380: (dirT2+"2023/"+skimType+"/ZZto2L2Nu-2Jets_EW_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",                  0.0051721*1000,plotCategory("kPlotZZ")),
       381: (dirT2+"2023/"+skimType+"/ZZto2L2Nu-2Jets_QCD_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",                 0.0912313*1000,plotCategory("kPlotZZ")),
       382: (dirT2+"2023/"+skimType+"/ZZto4L-2Jets_EW_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",                     0.0011422*1000,plotCategory("kPlotZZ")),
       383: (dirT2+"2023/"+skimType+"/ZZto4L-2Jets_QCD_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",                    0.0202984*1000,plotCategory("kPlotZZ")),
       389: (dirT2+"2023/"+skimType+"/SSWWJJ_Interference_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",0.00341005*1000,plotCategory("kPlotQCDSSWW")),
       390: (dirT2+"2023/"+skimType+"/VBSWZ-Interference_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",0.04806677*1000,plotCategory("kPlotWZ")),
       392: (dirT3+"2023/SM", 0.0295255*1000,plotCategory("kPlotEWKSSWW")),
       393: (dirT2+"2023/"+skimType+"/VBS_SSWW_M0Int_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.000297*1000,plotCategory("kPlotEFTM0Int")),
       394: (dirT2+"2023/"+skimType+"/VBS_SSWW_M0Quad_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.007333*1000,plotCategory("kPlotEFTM0Quad")),
       395: (dirT3+"Sherpa_Sample/2023", 39.8961,plotCategory("kPlotEWKSSWW")),
       396: (dirT2+"2023/"+skimType+"/VBS_SSWW_M1Int_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", -0.0003746 *1000,plotCategory("kPlotEFTM1Int")),
       397: (dirT2+"2023/"+skimType+"/VBS_SSWW_M1Quad_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.007688*1000,plotCategory("kPlotEFTM1Quad")),
       398: (dirT2+"2023/"+skimType+"/VBS_SSWW_M7Int_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.00002167*1000,plotCategory("kPlotEFTM7Int")),
       399: (dirT2+"2023/"+skimType+"/VBS_SSWW_M7Quad_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.003405*1000,plotCategory("kPlotEFTM7Quad")),
       3990: (dirT2+"2023/"+skimType+"/VBS_SSWW_S0Int_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", -0.0003575*1000,plotCategory("kPlotEFTS0Int")),
       3991: (dirT2+"2023/"+skimType+"/VBS_SSWW_S0Quad_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.008078*1000,plotCategory("kPlotEFTS0Quad")),
       3992: (dirT2+"2023/"+skimType+"/VBS_SSWW_T0Int_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",  -0.0005086*1000,plotCategory("kPlotEFTT0Int")),
       3993: (dirT2+"2023/"+skimType+"/VBS_SSWW_T0Quad_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.02811*1000,plotCategory("kPlotEFTT0Quad")),
       3994: (dirT2+"2023/"+skimType+"/VBS_SSWW_T1Int_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", -0.001284*1000,plotCategory("kPlotEFTT1Int")),
       3995: (dirT2+"2023/"+skimType+"/VBS_SSWW_T1Quad_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.03099*1000,plotCategory("kPlotEFTT1Quad")),
       3996: (dirT2+"2023/"+skimType+"/VBS_SSWW_T2Int_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",  -0.001341*1000,plotCategory("kPlotEFTT2Int")),
       3997: (dirT2+"2023/"+skimType+"/VBS_SSWW_T2Quad_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.01401*1000,plotCategory("kPlotEFTT2Quad")),

       3901: (dirT2+"2023/"+skimType+"/VBS-WZ-M2Quad_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.0002623*1000,plotCategory("kPlotEFTM2QuadWZ")),
       3902: (dirT2+"2023/"+skimType+"/VBS-WZ-M3Quad_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.0001106*1000,plotCategory("kPlotEFTM3QuadWZ")),
       3903: (dirT2+"2023/"+skimType+"/VBS-WZ-M4Quad_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.001995*1000,plotCategory("kPlotEFTM4QuadWZ")),
       3904: (dirT2+"2023/"+skimType+"/VBS-WZ-M5Quad_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.001099*1000,plotCategory("kPlotEFTM5QuadWZ")),
       3905: (dirT2+"2023/"+skimType+"/VBS-WZ-T5Quad_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.001619*1000,plotCategory("kPlotEFTT5QuadWZ")),
       3906: (dirT2+"2023/"+skimType+"/VBS-WZ-T6Quad_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.001873*1000,plotCategory("kPlotEFTT6QuadWZ")),
       3907: (dirT2+"2023/"+skimType+"/VBS-WZ-T7Quad_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.0002992*1000,plotCategory("kPlotEFTT7QuadWZ")),
       3908: (dirT2+"2023/"+skimType+"/VBS-WZto2EMuNu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", -3.893e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       3909: (dirT2+"2023/"+skimType+"/VBS-WZto2EMuNu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.0000005482*1000,plotCategory("kPlotEFTM3IntWZ")),
       3910: (dirT2+"2023/"+skimType+"/VBS-WZto2EMuNu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", -6.032e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       3911: (dirT2+"2023/"+skimType+"/VBS-WZto2EMuNu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.000001213*1000,plotCategory("kPlotEFTM5IntWZ")),
       3912: (dirT2+"2023/"+skimType+"/VBS-WZto2EMuNu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.000006792*1000,plotCategory("kPlotEFTT5IntWZ")),
       3913: (dirT2+"2023/"+skimType+"/VBS-WZto2EMuNu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.00001022*1000,plotCategory("kPlotEFTT6IntWZ")),
       3914: (dirT2+"2023/"+skimType+"/VBS-WZto2EMuNu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.000006764*1000,plotCategory("kPlotEFTT7IntWZ")),
       3915: (dirT2+"2023/"+skimType+"/VBS-WZto2ETauNu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", -4.604e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       3916: (dirT2+"2023/"+skimType+"/VBS-WZto2ETauNu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.0000005346*1000,plotCategory("kPlotEFTM3IntWZ")),
       3917: (dirT2+"2023/"+skimType+"/VBS-WZto2ETauNu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", -5.705e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       3918: (dirT2+"2023/"+skimType+"/VBS-WZto2ETauNu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.000001552*1000,plotCategory("kPlotEFTM5IntWZ")),
       3919: (dirT2+"2023/"+skimType+"/VBS-WZto2ETauNu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.00000669*1000,plotCategory("kPlotEFTT5IntWZ")),
       3920: (dirT2+"2023/"+skimType+"/VBS-WZto2ETauNu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.00001023*1000,plotCategory("kPlotEFTT6IntWZ")),
       3921: (dirT2+"2023/"+skimType+"/VBS-WZto2ETauNu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.000006783*1000,plotCategory("kPlotEFTT7IntWZ")),
       3922: (dirT2+"2023/"+skimType+"/VBS-WZto2MuENu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", -4.819e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       3923: (dirT2+"2023/"+skimType+"/VBS-WZto2MuENu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.0000004808*1000,plotCategory("kPlotEFTM3IntWZ")),
       3924: (dirT2+"2023/"+skimType+"/VBS-WZto2MuENu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", -6.275e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       3925: (dirT2+"2023/"+skimType+"/VBS-WZto2MuENu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.000001302*1000,plotCategory("kPlotEFTM5IntWZ")),
       3926: (dirT2+"2023/"+skimType+"/VBS-WZto2MuENu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.000006689*1000,plotCategory("kPlotEFTT5IntWZ")),
       3927: (dirT2+"2023/"+skimType+"/VBS-WZto2MuENu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.00001045*1000,plotCategory("kPlotEFTT6IntWZ")),
       3928: (dirT2+"2023/"+skimType+"/VBS-WZto2MuENu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.000006781*1000,plotCategory("kPlotEFTT7IntWZ")),
       3929: (dirT2+"2023/"+skimType+"/VBS-WZto2MuTauNu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", -5.153e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       3930: (dirT2+"2023/"+skimType+"/VBS-WZto2MuTauNu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.0000005407*1000,plotCategory("kPlotEFTM3IntWZ")),
       3931: (dirT2+"2023/"+skimType+"/VBS-WZto2MuTauNu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", -6.29e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       3932: (dirT2+"2023/"+skimType+"/VBS-WZto2MuTauNu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.0000009958*1000,plotCategory("kPlotEFTM5IntWZ")),
       3933: (dirT2+"2023/"+skimType+"/VBS-WZto2MuTauNu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.000006643*1000,plotCategory("kPlotEFTT5IntWZ")),
       3934: (dirT2+"2023/"+skimType+"/VBS-WZto2MuTauNu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.00001036*1000,plotCategory("kPlotEFTT6IntWZ")),
       3935: (dirT2+"2023/"+skimType+"/VBS-WZto2MuTauNu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.000006839*1000,plotCategory("kPlotEFTT7IntWZ")),
       3936: (dirT2+"2023/"+skimType+"/VBS-WZto2TauENu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", -4.285e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       3937: (dirT2+"2023/"+skimType+"/VBS-WZto2TauENu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.0000005344*1000,plotCategory("kPlotEFTM3IntWZ")),
       3938: (dirT2+"2023/"+skimType+"/VBS-WZto2TauENu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.0000007902*1000,plotCategory("kPlotEFTM4IntWZ")),
       3939: (dirT2+"2023/"+skimType+"/VBS-WZto2TauENu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", -1.242e-05*1000,plotCategory("kPlotEFTM5IntWZ")),
       3940: (dirT2+"2023/"+skimType+"/VBS-WZto2TauENu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.000006634*1000,plotCategory("kPlotEFTT5IntWZ")),
       3941: (dirT2+"2023/"+skimType+"/VBS-WZto2TauENu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.00001051*1000,plotCategory("kPlotEFTT6IntWZ")),
       3942: (dirT2+"2023/"+skimType+"/VBS-WZto2TauENu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.000006874*1000,plotCategory("kPlotEFTT7IntWZ")),
       3943: (dirT2+"2023/"+skimType+"/VBS-WZto2TauMuNu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", -4.509e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       3944: (dirT2+"2023/"+skimType+"/VBS-WZto2TauMuNu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.0000006144*1000,plotCategory("kPlotEFTM3IntWZ")),
       3945: (dirT2+"2023/"+skimType+"/VBS-WZto2TauMuNu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", -9.821e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       3946: (dirT2+"2023/"+skimType+"/VBS-WZto2TauMuNu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", -1.305e-05*1000,plotCategory("kPlotEFTM5IntWZ")),
       3947: (dirT2+"2023/"+skimType+"/VBS-WZto2TauMuNu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.000006709*1000,plotCategory("kPlotEFTT5IntWZ")),
       3948: (dirT2+"2023/"+skimType+"/VBS-WZto2TauMuNu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.00001045*1000,plotCategory("kPlotEFTT6IntWZ")),
       3949: (dirT2+"2023/"+skimType+"/VBS-WZto2TauMuNu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.000006845*1000,plotCategory("kPlotEFTT7IntWZ")),
       3950: (dirT2+"2023/"+skimType+"/VBS-WZto3ENu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", -4.508e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       3951: (dirT2+"2023/"+skimType+"/VBS-WZto3ENu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.0000005066*1000,plotCategory("kPlotEFTM3IntWZ")),
       3952: (dirT2+"2023/"+skimType+"/VBS-WZto3ENu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", -6.621e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       3953: (dirT2+"2023/"+skimType+"/VBS-WZto3ENu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.000001197*1000,plotCategory("kPlotEFTM5IntWZ")),
       3954: (dirT2+"2023/"+skimType+"/VBS-WZto3ENu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.000006371*1000,plotCategory("kPlotEFTT5IntWZ")),
       3955: (dirT2+"2023/"+skimType+"/VBS-WZto3ENu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.000009477*1000,plotCategory("kPlotEFTT6IntWZ")),
       3956: (dirT2+"2023/"+skimType+"/VBS-WZto3ENu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.00000632*1000,plotCategory("kPlotEFTT7IntWZ")),
       3957: (dirT2+"2023/"+skimType+"/VBS-WZto3MuNu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", -4.468e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       3958: (dirT2+"2023/"+skimType+"/VBS-WZto3MuNu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.0000005005*1000,plotCategory("kPlotEFTM3IntWZ")),
       3959: (dirT2+"2023/"+skimType+"/VBS-WZto3MuNu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", -6.906e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       3960: (dirT2+"2023/"+skimType+"/VBS-WZto3MuNu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.000001524*1000,plotCategory("kPlotEFTM5IntWZ")),
       3961: (dirT2+"2023/"+skimType+"/VBS-WZto3MuNu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.000006547*1000,plotCategory("kPlotEFTT5IntWZ")),
       3962: (dirT2+"2023/"+skimType+"/VBS-WZto3MuNu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.000009484*1000,plotCategory("kPlotEFTT6IntWZ")),
       3963: (dirT2+"2023/"+skimType+"/VBS-WZto3MuNu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.000006383*1000,plotCategory("kPlotEFTT7IntWZ")),
       3964: (dirT2+"2023/"+skimType+"/VBS-WZto3TauNu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", -4.285e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       3965: (dirT2+"2023/"+skimType+"/VBS-WZto3TauNu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.0000005196*1000,plotCategory("kPlotEFTM3IntWZ")),
       3966: (dirT2+"2023/"+skimType+"/VBS-WZto3TauNu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.0000004334*1000,plotCategory("kPlotEFTM4IntWZ")),
       3967: (dirT2+"2023/"+skimType+"/VBS-WZto3TauNu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", -1.149e-05*1000,plotCategory("kPlotEFTM5IntWZ")),
       3968: (dirT2+"2023/"+skimType+"/VBS-WZto3TauNu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.000006569*1000,plotCategory("kPlotEFTT5IntWZ")),
       3969: (dirT2+"2023/"+skimType+"/VBS-WZto3TauNu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.000009913*1000,plotCategory("kPlotEFTT6IntWZ")),
       3970: (dirT2+"2023/"+skimType+"/VBS-WZto3TauNu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.000006535*1000,plotCategory("kPlotEFTT7IntWZ")),


       400: (dirT2+"2023/"+skimType+"/DYto2L-2Jets_MLL-10to50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2_ext1-v3+NANOAODSIM",19982.5*1000,plotCategory("kPlotDY")),
       401: (dirT2+"2023/"+skimType+"/DYto2L-2Jets_MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",6345.99*1000,plotCategory("kPlotDY")),
       402: (dirT2+"2023/"+skimType+"/WWto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",(118.7*1.06-ggWWXS_LO_MCFM)*0.1086*0.1086*9*1000,plotCategory("kPlotqqWW")),
       403: (dirT2+"2023/"+skimType+"/WZto3LNu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v2+NANOAODSIM",4.924*1.08*1000,plotCategory("kPlotWZ")),
       404: (dirT2+"2023/"+skimType+"/WZto2L2Q_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v2+NANOAODSIM",7.568*1.08*1000,plotCategory("kPlotWZ")),
       405: (dirT2+"2023/"+skimType+"/ZZto2L2Q_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",6.788*1.19*1000,plotCategory("kPlotZZ")),
       406: (dirT2+"2023/"+skimType+"/ZZto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v1+NANOAODSIM",1.031*1.16*1000,plotCategory("kPlotZZ")),
       407: (dirT2+"2023/"+skimType+"/ZZto4L_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",1.390*1.19*1000,plotCategory("kPlotZZ")),
       408: (dirT2+"2023/"+skimType+"/TTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",0.950*923.6*0.1086*0.1086*9*1000,plotCategory("kPlotTT")),
       409: (dirT2+"2023/"+skimType+"/TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",0.950*923.6*0.1086*3*(1-0.1086*3)*2*1000,plotCategory("kPlotTT")),
       410: (dirT2+"2023/"+skimType+"/TTto4Q_TuneCP5Up_13p6TeV_powheg-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",1000000*0.950*923.6*(1-0.1086*3)*(1-0.1086*3)*1000,plotCategory("kPlotNonPrompt")),
       411: (dirT2+"2023/"+skimType+"/TbarWplusto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",4.67*1000,plotCategory("kPlotTW")),
       412: (dirT2+"2023/"+skimType+"/TWminusto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",4.67*1000,plotCategory("kPlotTW")),
       413: (dirT2+"2023/"+skimType+"/WtoLNu-4Jets_TuneCP5_13p6TeV_madgraphMLM-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",64481.58*1000,plotCategory("kPlotOther")),
       414: (dirT2+"2023/"+skimType+"/WWW_4F_TuneCP5_13p6TeV_amcatnlo-madspin-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v2+NANOAODSIM",0.23280*1000,plotCategory("kPlotVVV")),
       415: (dirT2+"2023/"+skimType+"/WWZ_4F_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",0.18510*1000,plotCategory("kPlotVVV")),
       416: (dirT2+"2023/"+skimType+"/WZZ_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v2+NANOAODSIM",0.06206*1000,plotCategory("kPlotVVV")),
       417: (dirT2+"2023/"+skimType+"/ZZZ_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v2+NANOAODSIM",0.01591*1000,plotCategory("kPlotVVV")),
       418: (dirT2+"2023/"+skimType+"/WZGtoLNuZG_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.08425*1000,plotCategory("kPlotVVV")),
       419: (dirT2+"2023/"+skimType+"/TTWW_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.0081651*1000,plotCategory("kPlotTVX")),
       420: (dirT2+"2023/"+skimType+"/TTZZ_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.0015617*1000,plotCategory("kPlotTVX")),
       421: (dirT2+"2023/"+skimType+"/GluGluHtoZZto4L_M-125_TuneCP5_13p6TeV_powheg-jhugen-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",52.230*0.02619*0.101*0.101*1000,plotCategory("kPlotHiggs")),
       422: (dirT2+"2023/"+skimType+"/VBFHto2Zto4L_M-125_TuneCP5_13p6TeV_powheg-jhugen-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",4.0780*0.02619*0.101*0.101*1000,plotCategory("kPlotHiggs")),
       423: (dirT2+"2023/"+skimType+"/TTLL_MLL-4to50_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.03949*1000,plotCategory("kPlotTVX")),
       424: (dirT2+"2023/"+skimType+"/TTLL_MLL-50_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.08646*1000,plotCategory("kPlotTVX")),
       425: (dirT2+"2023/"+skimType+"/ggWWto2L2Nu_OS_PolarizationLL_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.24053*(ggWWXS_LO_MCFM/ggWWXS_LO_MADGRAPH)*1.4*1000,plotCategory("kPlotggWW")),
       426: (dirT2+"2023/"+skimType+"/ggWWto2L2Nu_OS_PolarizationLT_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.08268*(ggWWXS_LO_MCFM/ggWWXS_LO_MADGRAPH)*1.4*1000,plotCategory("kPlotggWW")),
       427: (dirT2+"2023/"+skimType+"/ggWWto2L2Nu_OS_PolarizationTL_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.08268*(ggWWXS_LO_MCFM/ggWWXS_LO_MADGRAPH)*1.4*1000,plotCategory("kPlotggWW")),
       428: (dirT2+"2023/"+skimType+"/ggWWto2L2Nu_OS_PolarizationTT_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",3.10724*(ggWWXS_LO_MCFM/ggWWXS_LO_MADGRAPH)*1.4*1000,plotCategory("kPlotggWW")),
       429: (dirT2+"2023/"+skimType+"/DYGto2LG-1Jets_MLL-50_PTG-10to100_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",126.469425988806051*1000,plotCategory("kPlotVG")),
       430: (dirT2+"2023/"+skimType+"/DYGto2LG-1Jets_MLL-50_PTG-100to200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v3+NANOAODSIM",0.347454856033058*1000,plotCategory("kPlotVG")),
       431: (dirT2+"2023/"+skimType+"/DYGto2LG-1Jets_MLL-50_PTG-200to400_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.043623155782532*1000,plotCategory("kPlotVG")),
       432: (dirT2+"2023/"+skimType+"/DYGto2LG-1Jets_MLL-50_PTG-400to600_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.003152651247494*1000,plotCategory("kPlotVG")),
       433: (dirT2+"2023/"+skimType+"/WGtoLNuG-1Jets_PTG-10to100_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",668.91538*1000,plotCategory("kPlotVG")),
       434: (dirT2+"2023/"+skimType+"/WGtoLNuG-1Jets_PTG-100to200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",2.22141*1000,plotCategory("kPlotVG")),
       435: (dirT2+"2023/"+skimType+"/WGtoLNuG-1Jets_PTG-200to400_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",0.291367*1000,plotCategory("kPlotVG")),
       436: (dirT2+"2023/"+skimType+"/WWto4Q_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",1000000*(118.7*1.06-ggWWXS_LO_MCFM)*(1-0.1086*3)*(1-0.1086*3)*1000,plotCategory("kPlotNonPrompt")),
       437: (dirT2+"2023/"+skimType+"/GluGluHToTauTau_M-125_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v2+NANOAODSIM",52.230*0.06272*1000,plotCategory("kPlotHiggs")),
       438: (dirT2+"2023/"+skimType+"/VBFHToTauTau_M125_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",4.0780*0.06272*1000,plotCategory("kPlotHiggs")),
       439: (dirT2+"2023/"+skimType+"/DYGto2LG-1Jets_MLL-4to50_PTG-10to100_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",87.73210*1000,plotCategory("kPlotVG")),
       440: (dirT2+"2023/"+skimType+"/DYGto2LG-1Jets_MLL-4to50_PTG-100to200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.24095*1000,plotCategory("kPlotVG")),
       441: (dirT2+"2023/"+skimType+"/DYGto2LG-1Jets_MLL-4to50_PTG-200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.02228*1000,plotCategory("kPlotVG")),
       442: (dirT2+"2023/"+skimType+"/TbarWplus_DR_AtLeastOneLepton_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",23.97*1000,plotCategory("kPlotTW")),
       443: (dirT2+"2023/"+skimType+"/TWminus_DR_AtLeastOneLepton_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",23.97*1000,plotCategory("kPlotTW")),
       444: (dirT2+"2023/"+skimType+"/VH_HtoNonbb_M-125_TuneCP5_13p6TeV_amcatnloFXFX-madspin-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",(0.9439+1.4570)*(1-0.577)*1000,plotCategory("kPlotHiggs")),
       445: (dirT2+"2023/"+skimType+"/DYto2L-2Jets_MLL-50_0J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",5034.65*1000,plotCategory("kPlotDY")),
       446: (dirT2+"2023/"+skimType+"/DYto2L-2Jets_MLL-50_1J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",952.29*1000,plotCategory("kPlotDY")),
       447: (dirT2+"2023/"+skimType+"/DYto2L-2Jets_MLL-50_2J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",359.05*1000,plotCategory("kPlotDY")),
       448: (dirT2+"2023/"+skimType+"/TTLNu-1Jets_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.2502*1000,plotCategory("kPlotTVX")),
       449: (dirT2+"2023/"+skimType+"/TZQB-Zto2L-4FS_MLL-30_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v3+NANOAODSIM",0.07968*1.00*1000,plotCategory("kPlotTVX")),
       450: (dirT2+"2023/"+skimType+"/VBS-SSWW_PolarizationLL_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.002190*1000,plotCategory("kPlotEWKSSWW")),
       451: (dirT2+"2023/"+skimType+"/VBS-SSWW_PolarizationTL_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.011700*1000,plotCategory("kPlotEWKSSWW")),
       452: (dirT2+"2023/"+skimType+"/VBS-SSWW_PolarizationTT_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.017635*1000,plotCategory("kPlotEWKSSWW")),
       453: (dirT2+"2023/"+skimType+"/GluGluHto2Wto2L2Nu_M-125_TuneCP5_13p6TeV_powheg-jhugen752-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",52.230*0.2137*0.1086*0.1086*9*1000,plotCategory("kPlotHiggs")),
       454: (dirT2+"2023/"+skimType+"/VBFHto2Wto2L2Nu_M-125_TuneCP5_13p6TeV_powheg-jhugen752-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",4.0780*0.2137*0.1086*0.1086*9*1000,plotCategory("kPlotHiggs")),
       455: (dirT2+"2023/"+skimType+"/TTHtoNon2B_M-125_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v2+NANOAODSIM",0.5700*(1-0.577)*1000,plotCategory("kPlotHiggs")),
       456: (dirT2+"2023/"+skimType+"/WGtoLNuG-1Jets_PTG-400to600_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",0.022322*1000,plotCategory("kPlotVG")),
       457: (dirT2+"2023/"+skimType+"/WGtoLNuG-1Jets_PTG-600_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",0.004918*1000,plotCategory("kPlotVG")),
       458: (dirT2+"2023/"+skimType+"/WW_DoubleScattering_TuneCP5_13p6TeV_pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",2.14891*1000,plotCategory("kPlotOther")),
       459: (dirT2+"2023/"+skimType+"/GluGlutoContinto2Zto4E_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.5*0.0061150*1000,plotCategory("kPlotZZ")),
       460: (dirT2+"2023/"+skimType+"/GluGlutoContinto2Zto4Mu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.5*0.0061150*1000,plotCategory("kPlotZZ")),
       461: (dirT2+"2023/"+skimType+"/GluGlutoContinto2Zto4Tau_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.5*0.0061150*1000,plotCategory("kPlotZZ")),
       462: (dirT2+"2023/"+skimType+"/GluGlutoContinto2Zto2E2Tau_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.0061150*1000,plotCategory("kPlotZZ")),
       463: (dirT2+"2023/"+skimType+"/GluGlutoContinto2Zto2Mu2Tau_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.0061150*1000,plotCategory("kPlotZZ")),
       464: (dirT2+"2023/"+skimType+"/GluGluToContinto2Zto2E2Mu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.0061150*1000,plotCategory("kPlotZZ")),
       465: (dirT2+"2023/"+skimType+"/GluGlutoContintoWWtoENuENu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       466: (dirT2+"2023/"+skimType+"/GluGlutoContintoWWtoENuMuNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       467: (dirT2+"2023/"+skimType+"/GluGlutoContintoWWtoENuTauNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       468: (dirT2+"2023/"+skimType+"/GluGlutoContintoWWtoMuNuENu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       469: (dirT2+"2023/"+skimType+"/GluGlutoContintoWWtoMuNuMuNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       470: (dirT2+"2023/"+skimType+"/GluGlutoContintoWWtoMuNuTauNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       471: (dirT2+"2023/"+skimType+"/GluGlutoContintoWWtoTauNuENu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       472: (dirT2+"2023/"+skimType+"/GluGlutoContintoWWtoTauNuMuNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       473: (dirT2+"2023/"+skimType+"/GluGlutoContintoWWtoTauNuTauNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       474: (dirT2+"2023/"+skimType+"/WWto2L2Nu-2Jets_OS_noTop_EW_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v1+NANOAODSIM", 0.3301419*1000,plotCategory("kPlotqqWW")),
       475: (dirT2+"2023/"+skimType+"/WWto2L2Nu-2Jets_OS_noTop_QCD_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",2.6758028*1000,plotCategory("kPlotqqWW")),
       476: (dirT2+"2023/"+skimType+"/WWto2L2Nu-2Jets_SS_noTop_EW_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",         0.0295255*1000,plotCategory("kPlotEWKSSWW")),
       477: (dirT2+"2023/"+skimType+"/WWto2L2Nu-2Jets_SS_noTop_QCD_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",        0.0279662*1000,plotCategory("kPlotQCDSSWW")),
       478: (dirT2+"2023/"+skimType+"/WZto3LNu-2Jets_EW_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",           0.0429366*1000,plotCategory("kPlotEWKWZ")),
       479: (dirT2+"2023/"+skimType+"/WZto3LNu-2Jets_QCD_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",          0.4958618*1000*0.70,plotCategory("kPlotWZ")),
       480: (dirT2+"2023/"+skimType+"/ZZto2L2Nu-2Jets_EW_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",                  0.0051721*1000,plotCategory("kPlotZZ")),
       481: (dirT2+"2023/"+skimType+"/ZZto2L2Nu-2Jets_QCD_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",                 0.0912313*1000,plotCategory("kPlotZZ")),
       482: (dirT2+"2023/"+skimType+"/ZZto4L-2Jets_EW_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",                     0.0011422*1000,plotCategory("kPlotZZ")),
       483: (dirT2+"2023/"+skimType+"/ZZto4L-2Jets_QCD_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",                    0.0202984*1000,plotCategory("kPlotZZ")),
       489: (dirT2+"2023/"+skimType+"/SSWWJJ_Interference_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.00341005*1000,plotCategory("kPlotQCDSSWW")),
       490: (dirT2+"2023/"+skimType+"/VBSWZ-Interference_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.04806677*1000,plotCategory("kPlotWZ")),
       492: (dirT3+"2023BPix/SM", 0.0295255*1000,plotCategory("kPlotEWKSSWW")),
       493: (dirT2+"2023/"+skimType+"/VBS_SSWW_M0Int_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.000297*1000,plotCategory("kPlotEFTM0Int")),
       494: (dirT2+"2023/"+skimType+"/VBS_SSWW_M0Quad_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.007333*1000,plotCategory("kPlotEFTM0Quad")),
       495: (dirT3+"Sherpa_Sample/2023BPix", 39.8961,plotCategory("kPlotEWKSSWW")),
       496: (dirT2+"2023/"+skimType+"/VBS_SSWW_M1Int_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", -0.0003746 *1000,plotCategory("kPlotEFTM1Int")),
       497: (dirT2+"2023/"+skimType+"/VBS_SSWW_M1Quad_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.007688*1000,plotCategory("kPlotEFTM1Quad")),
       498: (dirT2+"2023/"+skimType+"/VBS_SSWW_M7Int_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.00002167*1000,plotCategory("kPlotEFTM7Int")),
       499: (dirT2+"2023/"+skimType+"/VBS_SSWW_M7Quad_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.003405*1000,plotCategory("kPlotEFTM7Quad")),
       4990: (dirT2+"2023/"+skimType+"/VBS_SSWW_S0Int_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", -0.0003575*1000,plotCategory("kPlotEFTS0Int")),
       4991: (dirT2+"2023/"+skimType+"/VBS_SSWW_S0Quad_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.008078*1000,plotCategory("kPlotEFTS0Quad")),
       4992: (dirT2+"2023/"+skimType+"/VBS_SSWW_T0Int_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",  -0.0005086*1000,plotCategory("kPlotEFTT0Int")),
       4993: (dirT2+"2023/"+skimType+"/VBS_SSWW_T0Quad_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.02811*1000,plotCategory("kPlotEFTT0Quad")),
       4994: (dirT2+"2023/"+skimType+"/VBS_SSWW_T1Int_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", -0.001284*1000,plotCategory("kPlotEFTT1Int")),
       4995: (dirT2+"2023/"+skimType+"/VBS_SSWW_T1Quad_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.03099*1000,plotCategory("kPlotEFTT1Quad")),
       4996: (dirT2+"2023/"+skimType+"/VBS_SSWW_T2Int_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",  -0.001341*1000,plotCategory("kPlotEFTT2Int")),
       4997: (dirT2+"2023/"+skimType+"/VBS_SSWW_T2Quad_TuneCP5_13p6TeV-madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.01401*1000,plotCategory("kPlotEFTT2Quad")),
       4901: (dirT2+"2023/"+skimType+"/VBS-WZ-M2Quad_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.0002623*1000,plotCategory("kPlotEFTM2QuadWZ")),
       4902: (dirT2+"2023/"+skimType+"/VBS-WZ-M3Quad_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.0001106*1000,plotCategory("kPlotEFTM3QuadWZ")),
       4903: (dirT2+"2023/"+skimType+"/VBS-WZ-M4Quad_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.001995*1000,plotCategory("kPlotEFTM4QuadWZ")),
       4904: (dirT2+"2023/"+skimType+"/VBS-WZ-M5Quad_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.001099*1000,plotCategory("kPlotEFTM5QuadWZ")),
       4905: (dirT2+"2023/"+skimType+"/VBS-WZ-T5Quad_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.001619*1000,plotCategory("kPlotEFTT5QuadWZ")),
       4906: (dirT2+"2023/"+skimType+"/VBS-WZ-T6Quad_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.001873*1000,plotCategory("kPlotEFTT6QuadWZ")),
       4907: (dirT2+"2023/"+skimType+"/VBS-WZ-T7Quad_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.0002992*1000,plotCategory("kPlotEFTT7QuadWZ")),
       4908: (dirT2+"2023/"+skimType+"/VBS-WZto2EMuNu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", -3.893e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       4909: (dirT2+"2023/"+skimType+"/VBS-WZto2EMuNu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.0000005482*1000,plotCategory("kPlotEFTM3IntWZ")),
       4910: (dirT2+"2023/"+skimType+"/VBS-WZto2EMuNu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", -6.032e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       4911: (dirT2+"2023/"+skimType+"/VBS-WZto2EMuNu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.000001213*1000,plotCategory("kPlotEFTM5IntWZ")),
       4912: (dirT2+"2023/"+skimType+"/VBS-WZto2EMuNu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.000006792*1000,plotCategory("kPlotEFTT5IntWZ")),
       4913: (dirT2+"2023/"+skimType+"/VBS-WZto2EMuNu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.00001022*1000,plotCategory("kPlotEFTT6IntWZ")),
       4914: (dirT2+"2023/"+skimType+"/VBS-WZto2EMuNu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.000006764*1000,plotCategory("kPlotEFTT7IntWZ")),
       4915: (dirT2+"2023/"+skimType+"/VBS-WZto2ETauNu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", -4.604e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       4916: (dirT2+"2023/"+skimType+"/VBS-WZto2ETauNu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.0000005346*1000,plotCategory("kPlotEFTM3IntWZ")),
       4917: (dirT2+"2023/"+skimType+"/VBS-WZto2ETauNu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", -5.705e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       4918: (dirT2+"2023/"+skimType+"/VBS-WZto2ETauNu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.000001552*1000,plotCategory("kPlotEFTM5IntWZ")),
       4919: (dirT2+"2023/"+skimType+"/VBS-WZto2ETauNu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.00000669*1000,plotCategory("kPlotEFTT5IntWZ")),
       4920: (dirT2+"2023/"+skimType+"/VBS-WZto2ETauNu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.00001023*1000,plotCategory("kPlotEFTT6IntWZ")),
       4921: (dirT2+"2023/"+skimType+"/VBS-WZto2ETauNu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.000006783*1000,plotCategory("kPlotEFTT7IntWZ")),
       4922: (dirT2+"2023/"+skimType+"/VBS-WZto2MuENu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", -4.819e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       4923: (dirT2+"2023/"+skimType+"/VBS-WZto2MuENu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.0000004808*1000,plotCategory("kPlotEFTM3IntWZ")),
       4924: (dirT2+"2023/"+skimType+"/VBS-WZto2MuENu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", -6.275e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       4925: (dirT2+"2023/"+skimType+"/VBS-WZto2MuENu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.000001302*1000,plotCategory("kPlotEFTM5IntWZ")),
       4926: (dirT2+"2023/"+skimType+"/VBS-WZto2MuENu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.000006689*1000,plotCategory("kPlotEFTT5IntWZ")),
       4927: (dirT2+"2023/"+skimType+"/VBS-WZto2MuENu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.00001045*1000,plotCategory("kPlotEFTT6IntWZ")),
       4928: (dirT2+"2023/"+skimType+"/VBS-WZto2MuENu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.000006781*1000,plotCategory("kPlotEFTT7IntWZ")),
       4929: (dirT2+"2023/"+skimType+"/VBS-WZto2MuTauNu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", -5.153e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       4930: (dirT2+"2023/"+skimType+"/VBS-WZto2MuTauNu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.0000005407*1000,plotCategory("kPlotEFTM3IntWZ")),
       4931: (dirT2+"2023/"+skimType+"/VBS-WZto2MuTauNu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", -6.29e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       4932: (dirT2+"2023/"+skimType+"/VBS-WZto2MuTauNu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.0000009958*1000,plotCategory("kPlotEFTM5IntWZ")),
       4933: (dirT2+"2023/"+skimType+"/VBS-WZto2MuTauNu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.000006643*1000,plotCategory("kPlotEFTT5IntWZ")),
       4934: (dirT2+"2023/"+skimType+"/VBS-WZto2MuTauNu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.00001036*1000,plotCategory("kPlotEFTT6IntWZ")),
       4935: (dirT2+"2023/"+skimType+"/VBS-WZto2MuTauNu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.000006839*1000,plotCategory("kPlotEFTT7IntWZ")),
       4936: (dirT2+"2023/"+skimType+"/VBS-WZto2TauENu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", -4.285e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       4937: (dirT2+"2023/"+skimType+"/VBS-WZto2TauENu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.0000005344*1000,plotCategory("kPlotEFTM3IntWZ")),
       4938: (dirT2+"2023/"+skimType+"/VBS-WZto2TauENu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.0000007902*1000,plotCategory("kPlotEFTM4IntWZ")),
       4939: (dirT2+"2023/"+skimType+"/VBS-WZto2TauENu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", -1.242e-05*1000,plotCategory("kPlotEFTM5IntWZ")),
       4940: (dirT2+"2023/"+skimType+"/VBS-WZto2TauENu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.000006634*1000,plotCategory("kPlotEFTT5IntWZ")),
       4941: (dirT2+"2023/"+skimType+"/VBS-WZto2TauENu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.00001051*1000,plotCategory("kPlotEFTT6IntWZ")),
       4942: (dirT2+"2023/"+skimType+"/VBS-WZto2TauENu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.000006874*1000,plotCategory("kPlotEFTT7IntWZ")),
       4943: (dirT2+"2023/"+skimType+"/VBS-WZto2TauMuNu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", -4.509e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       4944: (dirT2+"2023/"+skimType+"/VBS-WZto2TauMuNu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.0000006144*1000,plotCategory("kPlotEFTM3IntWZ")),
       4945: (dirT2+"2023/"+skimType+"/VBS-WZto2TauMuNu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", -9.821e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       4946: (dirT2+"2023/"+skimType+"/VBS-WZto2TauMuNu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", -1.305e-05*1000,plotCategory("kPlotEFTM5IntWZ")),
       4947: (dirT2+"2023/"+skimType+"/VBS-WZto2TauMuNu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.000006709*1000,plotCategory("kPlotEFTT5IntWZ")),
       4948: (dirT2+"2023/"+skimType+"/VBS-WZto2TauMuNu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.00001045*1000,plotCategory("kPlotEFTT6IntWZ")),
       4949: (dirT2+"2023/"+skimType+"/VBS-WZto2TauMuNu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.000006845*1000,plotCategory("kPlotEFTT7IntWZ")),
       4950: (dirT2+"2023/"+skimType+"/VBS-WZto3ENu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", -4.508e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       4951: (dirT2+"2023/"+skimType+"/VBS-WZto3ENu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.0000005066*1000,plotCategory("kPlotEFTM3IntWZ")),
       4952: (dirT2+"2023/"+skimType+"/VBS-WZto3ENu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", -6.621e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       4953: (dirT2+"2023/"+skimType+"/VBS-WZto3ENu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.000001197*1000,plotCategory("kPlotEFTM5IntWZ")),
       4954: (dirT2+"2023/"+skimType+"/VBS-WZto3ENu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.000006371*1000,plotCategory("kPlotEFTT5IntWZ")),
       4955: (dirT2+"2023/"+skimType+"/VBS-WZto3ENu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.000009477*1000,plotCategory("kPlotEFTT6IntWZ")),
       4956: (dirT2+"2023/"+skimType+"/VBS-WZto3ENu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.00000632*1000,plotCategory("kPlotEFTT7IntWZ")),
       4957: (dirT2+"2023/"+skimType+"/VBS-WZto3MuNu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", -4.468e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       4958: (dirT2+"2023/"+skimType+"/VBS-WZto3MuNu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.0000005005*1000,plotCategory("kPlotEFTM3IntWZ")),
       4959: (dirT2+"2023/"+skimType+"/VBS-WZto3MuNu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", -6.906e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       4960: (dirT2+"2023/"+skimType+"/VBS-WZto3MuNu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.000001524*1000,plotCategory("kPlotEFTM5IntWZ")),
       4961: (dirT2+"2023/"+skimType+"/VBS-WZto3MuNu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.000006547*1000,plotCategory("kPlotEFTT5IntWZ")),
       4962: (dirT2+"2023/"+skimType+"/VBS-WZto3MuNu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.000009484*1000,plotCategory("kPlotEFTT6IntWZ")),
       4963: (dirT2+"2023/"+skimType+"/VBS-WZto3MuNu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.000006383*1000,plotCategory("kPlotEFTT7IntWZ")),
       4964: (dirT2+"2023/"+skimType+"/VBS-WZto3TauNu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", -4.285e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       4965: (dirT2+"2023/"+skimType+"/VBS-WZto3TauNu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.0000005196*1000,plotCategory("kPlotEFTM3IntWZ")),
       4966: (dirT2+"2023/"+skimType+"/VBS-WZto3TauNu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.0000004334*1000,plotCategory("kPlotEFTM4IntWZ")),
       4967: (dirT2+"2023/"+skimType+"/VBS-WZto3TauNu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", -1.149e-05*1000,plotCategory("kPlotEFTM5IntWZ")),
       4968: (dirT2+"2023/"+skimType+"/VBS-WZto3TauNu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.000006569*1000,plotCategory("kPlotEFTT5IntWZ")),
       4969: (dirT2+"2023/"+skimType+"/VBS-WZto3TauNu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.000009913*1000,plotCategory("kPlotEFTT6IntWZ")),
       4970: (dirT2+"2023/"+skimType+"/VBS-WZto3TauNu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM", 0.000006535*1000,plotCategory("kPlotEFTT7IntWZ")),


       500: (dirT2+"2024/"+skimType+"/DYto2E_Bin-MLL-10to50_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",19982.5*1000/3.,plotCategory("kPlotDY")),
       501: (dirT2+"2024/"+skimType+"/DYto2E-2Jets_Bin-MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v4+NANOAODSIM",6345.99*1000/3.,plotCategory("kPlotDY")),
       502: (dirT2+"2024/"+skimType+"/WWto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",(118.7*1.06-ggWWXS_LO_MCFM)*0.1086*0.1086*9*1000,plotCategory("kPlotqqWW")),
       503: (dirT2+"2024/"+skimType+"/WZto3LNu_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",4.924*1.08*1000,plotCategory("kPlotWZ")),
       504: (dirT2+"2024/"+skimType+"/WZto2L2Q_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",7.568*1.08*1000,plotCategory("kPlotWZ")),
       505: (dirT2+"2024/"+skimType+"/ZZto2L2Q_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",6.788*1.19*1000,plotCategory("kPlotZZ")),
       506: (dirT2+"2024/"+skimType+"/ZZto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",1.031*1.16*1000,plotCategory("kPlotZZ")),
       507: (dirT2+"2024/"+skimType+"/ZZto4L_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",1.390*1.19*1000,plotCategory("kPlotZZ")),
       508: (dirT2+"2024/"+skimType+"/TTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v3+NANOAODSIM",0.950*923.6*0.1086*0.1086*9*1000,plotCategory("kPlotTT")),
       509: (dirT2+"2024/"+skimType+"/TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.950*923.6*0.1086*3*(1-0.1086*3)*2*1000,plotCategory("kPlotTT")),
       510: (dirT2+"2024/"+skimType+"/TTto4Q_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",1000000*0.950*923.6*(1-0.1086*3)*(1-0.1086*3)*1000,plotCategory("kPlotNonPrompt")),
       511: (dirT2+"2024/"+skimType+"/TbarWplusto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",4.67*1000,plotCategory("kPlotTW")),
       512: (dirT2+"2024/"+skimType+"/TWminusto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",4.67*1000,plotCategory("kPlotTW")),
       513: (dirT2+"2024/"+skimType+"/WtoENu-2Jets_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v3+NANOAODSIM",64481.58*1000/3.,plotCategory("kPlotOther")),
       514: (dirT2+"2024/"+skimType+"/WWW-4F_TuneCP5_13p6TeV_amcatnlo-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.23280*1000,plotCategory("kPlotVVV")),
       515: (dirT2+"2024/"+skimType+"/WWZ-4F_TuneCP5_13p6TeV_amcatnlo-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.18510*1000,plotCategory("kPlotVVV")),
       516: (dirT2+"2024/"+skimType+"/WZZ-5F_TuneCP5_13p6TeV_amcatnlo-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.06206*1000,plotCategory("kPlotVVV")),
       517: (dirT2+"2024/"+skimType+"/ZZZ-5F_TuneCP5_13p6TeV_amcatnlo-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.01591*1000,plotCategory("kPlotVVV")),
       518: (dirT2+"2024/"+skimType+"/WZGtoLNuZG_TuneCP5_13p6TeV_amcatnlo-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.08425*1000,plotCategory("kPlotVVV")),
       519: (dirT2+"2024/"+skimType+"/TTWW_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.0081651*1000,plotCategory("kPlotTVX")),
       520: (dirT2+"2024/"+skimType+"/TTWZ_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.0027199*1000,plotCategory("kPlotTVX")),
       521: (dirT2+"2024/"+skimType+"/GluGluHto2Zto4L_Par-M-125_TuneCP5_13p6TeV_powhegMINNLO-jhugen-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",52.230*0.02619*0.101*0.101*1000,plotCategory("kPlotHiggs")),
       522: (dirT2+"2024/"+skimType+"/VBFH-Hto2Zto4L_Par-M-125_TuneCP5_13p6TeV_powheg-jhugen-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",4.0780*0.02619*0.101*0.101*1000,plotCategory("kPlotHiggs")),
       523: (dirT2+"2024/"+skimType+"/TTLL_Bin-MLL-4to50_TuneCP5_13p6TeV_amcatnlo-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.03949*1000,plotCategory("kPlotTVX")),
       524: (dirT2+"2024/"+skimType+"/TTLL_Bin-MLL-50_TuneCP5_13p6TeV_amcatnlo-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.08646*1000,plotCategory("kPlotTVX")),
       525: (dirT2+"2024/"+skimType+"/DYto2Mu_Bin-MLL-10to50_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",19982.5*1000/3.,plotCategory("kPlotDY")),
       526: (dirT2+"2024/"+skimType+"/DYto2Mu-2Jets_Bin-MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v6+NANOAODSIM",6345.99*1000/3.,plotCategory("kPlotDY")),
       527: (dirT2+"2024/"+skimType+"/DYto2Tau_Bin-MLL-10to50_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",19982.5*1000/3.,plotCategory("kPlotDY")),
       528: (dirT2+"2024/"+skimType+"/DYto2Tau-2Jets_Bin-MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v5+NANOAODSIM",6345.99*1000/3.,plotCategory("kPlotDY")),
       529: (dirT2+"2024/"+skimType+"/DYGto2LG-1Jets_Bin-MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 126.86326*1000,plotCategory("kPlotVG")),
       530: (dirT2+"2024/"+skimType+"/DYGto2LG-1Jets_MLL-50_PTG-100to200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v3+NANOAODSIM",0.347454856033058*1000,plotCategory("kPlotVG")),
       531: (dirT2+"2024/"+skimType+"/DYGto2LG-1Jets_MLL-50_PTG-200to400_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.043623155782532*1000,plotCategory("kPlotVG")),
       532: (dirT2+"2024/"+skimType+"/EWK-ZG2JtoG2L2J_Bin-MLL-50-MJJ-120_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.113109*1000,plotCategory("kPlotVG")),
       533: (dirT2+"2024/"+skimType+"/WGtoLNuG-1Jets_PTG-10to100_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",668.91538*1000,plotCategory("kPlotVG")),
       534: (dirT2+"2024/"+skimType+"/WGtoLNuG-1Jets_PTG-100to200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",2.22141*1000,plotCategory("kPlotVG")),
       535: (dirT2+"2024/"+skimType+"/WGtoLNuG-1Jets_PTG-200to400_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",0.291367*1000,plotCategory("kPlotVG")),
       536: (dirT2+"2024/"+skimType+"/WWto4Q_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",1000000*(118.7*1.06-ggWWXS_LO_MCFM)*(1-0.1086*3)*(1-0.1086*3)*1000,plotCategory("kPlotNonPrompt")),
       537: (dirT2+"2024/"+skimType+"/GluGluH-HTo2Tau_Par-M-125_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",52.230*0.06272*1000,plotCategory("kPlotHiggs")),
       538: (dirT2+"2024/"+skimType+"/VBFH-HTo2Tau_Par-M-125_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",4.0780*0.06272*1000,plotCategory("kPlotHiggs")),
       539: (dirT2+"2024/"+skimType+"/DYGto2LG-1Jets_Bin-MLL-4to50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",88.11067*1000,plotCategory("kPlotVG")),
       540: (dirT2+"2024/"+skimType+"/DYGto2LG-1Jets_MLL-4to50_PTG-100to200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.24095*1000,plotCategory("kPlotVG")),
       541: (dirT2+"2024/"+skimType+"/DYGto2LG-1Jets_MLL-4to50_PTG-200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.02228*1000,plotCategory("kPlotVG")),
       542: (dirT2+"2024/"+skimType+"/WtoMuNu-2Jets_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v3+NANOAODSIM",64481.58*1000/3.,plotCategory("kPlotOther")),
       543: (dirT2+"2024/"+skimType+"/WtoTauNu-2Jets_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v3+NANOAODSIM",64481.58*1000/3.,plotCategory("kPlotOther")),
       544: (dirT2+"2024/"+skimType+"/VH_HtoNonbb_M-125_TuneCP5_13p6TeV_amcatnloFXFX-madspin-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",(0.9439+1.4570)*(1-0.577)*1000,plotCategory("kPlotHiggs")),
       545: (dirT2+"2024/"+skimType+"/DYto2L-2Jets_MLL-50_0J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",5034.65*1000,plotCategory("kPlotDY")),
       546: (dirT2+"2024/"+skimType+"/DYto2L-2Jets_MLL-50_1J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",952.29*1000,plotCategory("kPlotDY")),
       547: (dirT2+"2024/"+skimType+"/DYto2L-2Jets_MLL-50_2J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",359.05*1000,plotCategory("kPlotDY")),
       548: (dirT2+"2024/"+skimType+"/TTLNu-1Jets_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+RunIII2024Summer24NanoAODv15-mg35x_150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.2502*1000,plotCategory("kPlotTVX")),
       549: (dirT2+"2024/"+skimType+"/TZQB-Zto2L-4FS_Bin-MLL-30_TuneCP5_13p6TeV_amcatnlo-pythia8+RunIII2024Summer24NanoAODv15-Madgraph_2_6_5_150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.07968*1.30*1000,plotCategory("kPlotTVX")),
       550: (dirT2+"2024/"+skimType+"/VBS-SSWW_PolarizationLL_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.002190*1000,plotCategory("kPlotEWKSSWW")),
       551: (dirT2+"2024/"+skimType+"/VBS-SSWW_PolarizationTL_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.011700*1000,plotCategory("kPlotEWKSSWW")),
       552: (dirT2+"2024/"+skimType+"/VBS-SSWW_PolarizationTT_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.017635*1000,plotCategory("kPlotEWKSSWW")),
       553: (dirT2+"2024/"+skimType+"/GluGluHto2Wto2L2Nu_Par-M-125_TuneCP5_13p6TeV_powheg-jhugen-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",52.230*0.2137*0.1086*0.1086*9*1000,plotCategory("kPlotHiggs")),
       554: (dirT2+"2024/"+skimType+"/VBFHto2Wto2L2Nu_Par-M-125_TuneCP5_13p6TeV_powheg-jhugen-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",4.0780*0.2137*0.1086*0.1086*9*1000,plotCategory("kPlotHiggs")),
       555: (dirT2+"2024/"+skimType+"/TTH-HtoNon2B_Par-M-125_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.5700*(1-0.577)*1000,plotCategory("kPlotHiggs")),
       556: (dirT2+"2024/"+skimType+"/WGtoLNuG-1Jets_PTG-400to600_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",0.022322*1000,plotCategory("kPlotVG")),
       557: (dirT2+"2024/"+skimType+"/WGtoLNuG-1Jets_PTG-600_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",0.004918*1000,plotCategory("kPlotVG")),
       558: (dirT2+"2024/"+skimType+"/WW-DPS_TuneCP5_13p6TeV_pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",2.14891*1000,plotCategory("kPlotOther")),
       559: (dirT2+"2024/"+skimType+"/GluGlu2Zto4E_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.5*0.0061150*1000,plotCategory("kPlotZZ")),
       560: (dirT2+"2024/"+skimType+"/GluGlu2Zto4Mu_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.5*0.0061150*1000,plotCategory("kPlotZZ")),
       561: (dirT2+"2024/"+skimType+"/GluGlu2Zto4Tau_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.5*0.0061150*1000,plotCategory("kPlotZZ")),
       562: (dirT2+"2024/"+skimType+"/GluGlu2Zto2E2Tau_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.0061150*1000,plotCategory("kPlotZZ")),
       563: (dirT2+"2024/"+skimType+"/GluGlu2Zto2Mu2Tau_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.0061150*1000,plotCategory("kPlotZZ")),
       564: (dirT2+"2024/"+skimType+"/GluGlu2Zto2E2Mu_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.0061150*1000,plotCategory("kPlotZZ")),
       565: (dirT2+"2024/"+skimType+"/GluGluWWto2E2Nu_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       566: (dirT2+"2024/"+skimType+"/GluGluWWtoENuMuNu_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       567: (dirT2+"2024/"+skimType+"/GluGluWWtoENuTauNu_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       568: (dirT2+"2024/"+skimType+"/GluGluWWtoMuNuENu_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       569: (dirT2+"2024/"+skimType+"/GluGluWWto2Mu2Nu_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       570: (dirT2+"2024/"+skimType+"/GluGluWWtoMuNuTauNu_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       571: (dirT2+"2024/"+skimType+"/GluGluWWtoTauNuENu_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       572: (dirT2+"2024/"+skimType+"/GluGluWWtoTauNuMuNu_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       573: (dirT2+"2024/"+skimType+"/GluGluWWto2Tau2Nu_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       574: (dirT2+"2024/"+skimType+"/WWJJto2L2Nu-OS-noTop-EWK_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",                         0.3301419*1000,plotCategory("kPlotqqWW")),
       575: (dirT2+"2024/"+skimType+"/WWJJto2L2Nu-OS-noTop-QCD_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",                         2.6758028*1000,plotCategory("kPlotqqWW")),
       576: (dirT2+"2024/"+skimType+"/WWJJto2L2Nu-SS-noTop-EWK_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",                         0.0295255*1000,plotCategory("kPlotEWKSSWW")),
       577: (dirT2+"2024/"+skimType+"/WWJJto2L2Nu-SS-noTop-QCD_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",                         0.0279662*1000,plotCategory("kPlotQCDSSWW")),
       578: (dirT2+"2024/"+skimType+"/WZJJto3LNu-EWK_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",                                   0.0429366*1000,plotCategory("kPlotEWKWZ")),
       579: (dirT2+"2024/"+skimType+"/WZJJto3LNu-QCD_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",                                   0.4958618*1000*0.70,plotCategory("kPlotWZ")),
       580: (dirT2+"2024/"+skimType+"/ZZJJto2L2Nu-EWK_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",                                  0.0051721*1000,plotCategory("kPlotZZ")),
       581: (dirT2+"2024/"+skimType+"/ZZJJto2L2Nu-QCD_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",                                  0.0912313*1000*1.40,plotCategory("kPlotZZ")),
       582: (dirT2+"2024/"+skimType+"/ZZJJto4L-EWK_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",                                     0.0011422*1000,plotCategory("kPlotZZ")),
       583: (dirT2+"2024/"+skimType+"/ZZJJto4L-QCD_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",                                     0.0202984*1000*1.40,plotCategory("kPlotZZ")),
       584: (dirT2+"2024/"+skimType+"/WpWpJJ-EWK_TuneCP5_13p6TeV-powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.5*0.0295255*1000,plotCategory("kPlotEWKSSWW")),
       585: (dirT2+"2024/"+skimType+"/WmWmJJ-EWK_TuneCP5_13p6TeV-powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.5*0.0295255*1000,plotCategory("kPlotEWKSSWW")),
       586: (dirT2+"2024/"+skimType+"/ZH-HtoNon2B_Par-M-125_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",(0.9439)*(1-0.577)*1000,plotCategory("kPlotHiggs")),
       587: (dirT2+"2024/"+skimType+"/WplusH-HtoNon2B_Par-M-125_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",(1.4570*0.608)*(1-0.577)*1000,plotCategory("kPlotHiggs")),
       588: (dirT2+"2024/"+skimType+"/WminusH-HtoNon2B_Par-M-125_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",(1.4570*0.392)*(1-0.577)*1000,plotCategory("kPlotHiggs")),
       589: (dirT2+"2024/"+skimType+"/SSWWJJ-Interference_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.00341005*1000,plotCategory("kPlotQCDSSWW")),
       590: (dirT2+"2024/"+skimType+"/VBSWZ-Interference_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.04806677*1000,plotCategory("kPlotWZ")),
       591: (dirT2+"2024/"+skimType+"/WGtoLNuG-1Jets_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",671.734705*1000,plotCategory("kPlotVG")),
       592: (dirT3+"2024/SM", 0.0295255*1000,plotCategory("kPlotEWKSSWW")),
       593: (dirT2+"2024/"+skimType+"/VBS-SSWW-M0-Interference_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000297*1000,plotCategory("kPlotEFTM0Int")),
       594: (dirT2+"2024/"+skimType+"/VBS-SSWW-M0-Quadratic_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.007333*1000,plotCategory("kPlotEFTM0Quad")),
       595: (dirT3+"Sherpa_Sample/2024", 39.8961,plotCategory("kPlotEWKSSWW")),
       596: (dirT2+"2024/"+skimType+"/VBS-SSWW-M1-Interference_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -0.0003746 *1000,plotCategory("kPlotEFTM1Int")),
       597: (dirT2+"2024/"+skimType+"/VBS-SSWW-M1-Quadratic_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.007688*1000,plotCategory("kPlotEFTM1Quad")),
       598: (dirT2+"2024/"+skimType+"/VBS-SSWW-M7-Interference_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.00002167*1000,plotCategory("kPlotEFTM7Int")),
       599: (dirT2+"2024/"+skimType+"/VBS-SSWW-M7-Quadratic_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.003405*1000,plotCategory("kPlotEFTM7Quad")),
       5990: (dirT2+"2024/"+skimType+"/VBS-SSWW-S0-Interference_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -0.0003575*1000,plotCategory("kPlotEFTS0Int")),
       5991: (dirT2+"2024/"+skimType+"/VBS-SSWW-S0-Quadratic_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.008078*1000,plotCategory("kPlotEFTS0Quad")),
       5992: (dirT2+"2024/"+skimType+"/VBS-SSWW-T0-Interference_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",  -0.0005086*1000,plotCategory("kPlotEFTT0Int")),
       5993: (dirT2+"2024/"+skimType+"/VBS-SSWW-T0-Quadratic_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.02811*1000,plotCategory("kPlotEFTT0Quad")),
       5994: (dirT2+"2024/"+skimType+"/VBS-SSWW-T1-Interference_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -0.001284*1000,plotCategory("kPlotEFTT1Int")),
       5995: (dirT2+"2024/"+skimType+"/VBS-SSWW-T1-Quadratic_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.03099*1000,plotCategory("kPlotEFTT1Quad")),
       5996: (dirT2+"2024/"+skimType+"/VBS-SSWW-T2-Interference_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",  -0.001341*1000,plotCategory("kPlotEFTT2Int")),
       5997: (dirT2+"2024/"+skimType+"/VBS-SSWW-T2-Quadratic_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.01401*1000,plotCategory("kPlotEFTT2Quad")),
       5901: (dirT2+"2024/"+skimType+"/VBS-WZ-M2Quad_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.0002623*1000,plotCategory("kPlotEFTM2QuadWZ")),
       5902: (dirT2+"2024/"+skimType+"/VBS-WZ-M3Quad_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.0001106*1000,plotCategory("kPlotEFTM3QuadWZ")),
       5903: (dirT2+"2024/"+skimType+"/VBS-WZ-M4Quad_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.001995*1000,plotCategory("kPlotEFTM4QuadWZ")),
       5904: (dirT2+"2024/"+skimType+"/VBS-WZ-M5Quad_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.001099*1000,plotCategory("kPlotEFTM5QuadWZ")),
       5905: (dirT2+"2024/"+skimType+"/VBS-WZ-T5Quad_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.001619*1000,plotCategory("kPlotEFTT5QuadWZ")),
       5906: (dirT2+"2024/"+skimType+"/VBS-WZ-T6Quad_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.001873*1000,plotCategory("kPlotEFTT6QuadWZ")),
       5907: (dirT2+"2024/"+skimType+"/VBS-WZ-T7Quad_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.0002992*1000,plotCategory("kPlotEFTT7QuadWZ")),
       5908: (dirT2+"2024/"+skimType+"/VBS-WZto2EMuNu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -3.893e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       5909: (dirT2+"2024/"+skimType+"/VBS-WZto2EMuNu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.0000005482*1000,plotCategory("kPlotEFTM3IntWZ")),
       5910: (dirT2+"2024/"+skimType+"/VBS-WZto2EMuNu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -6.032e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       5911: (dirT2+"2024/"+skimType+"/VBS-WZto2EMuNu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000001213*1000,plotCategory("kPlotEFTM5IntWZ")),
       5912: (dirT2+"2024/"+skimType+"/VBS-WZto2EMuNu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000006792*1000,plotCategory("kPlotEFTT5IntWZ")),
       5913: (dirT2+"2024/"+skimType+"/VBS-WZto2EMuNu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.00001022*1000,plotCategory("kPlotEFTT6IntWZ")),
       5914: (dirT2+"2024/"+skimType+"/VBS-WZto2EMuNu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000006764*1000,plotCategory("kPlotEFTT7IntWZ")),
       5915: (dirT2+"2024/"+skimType+"/VBS-WZto2ETauNu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -4.604e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       5916: (dirT2+"2024/"+skimType+"/VBS-WZto2ETauNu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.0000005346*1000,plotCategory("kPlotEFTM3IntWZ")),
       5917: (dirT2+"2024/"+skimType+"/VBS-WZto2ETauNu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -5.705e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       5918: (dirT2+"2024/"+skimType+"/VBS-WZto2ETauNu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000001552*1000,plotCategory("kPlotEFTM5IntWZ")),
       5919: (dirT2+"2024/"+skimType+"/VBS-WZto2ETauNu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.00000669*1000,plotCategory("kPlotEFTT5IntWZ")),
       5920: (dirT2+"2024/"+skimType+"/VBS-WZto2ETauNu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.00001023*1000,plotCategory("kPlotEFTT6IntWZ")),
       5921: (dirT2+"2024/"+skimType+"/VBS-WZto2ETauNu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000006783*1000,plotCategory("kPlotEFTT7IntWZ")),
       5922: (dirT2+"2024/"+skimType+"/VBS-WZto2MuENu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -4.819e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       5923: (dirT2+"2024/"+skimType+"/VBS-WZto2MuENu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.0000004808*1000,plotCategory("kPlotEFTM3IntWZ")),
       5924: (dirT2+"2024/"+skimType+"/VBS-WZto2MuENu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -6.275e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       5925: (dirT2+"2024/"+skimType+"/VBS-WZto2MuENu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000001302*1000,plotCategory("kPlotEFTM5IntWZ")),
       5926: (dirT2+"2024/"+skimType+"/VBS-WZto2MuENu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000006689*1000,plotCategory("kPlotEFTT5IntWZ")),
       5927: (dirT2+"2024/"+skimType+"/VBS-WZto2MuENu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.00001045*1000,plotCategory("kPlotEFTT6IntWZ")),
       5928: (dirT2+"2024/"+skimType+"/VBS-WZto2MuENu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000006781*1000,plotCategory("kPlotEFTT7IntWZ")),
       5929: (dirT2+"2024/"+skimType+"/VBS-WZto2MuTauNu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -5.153e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       5930: (dirT2+"2024/"+skimType+"/VBS-WZto2MuTauNu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.0000005407*1000,plotCategory("kPlotEFTM3IntWZ")),
       5931: (dirT2+"2024/"+skimType+"/VBS-WZto2MuTauNu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -6.29e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       5932: (dirT2+"2024/"+skimType+"/VBS-WZto2MuTauNu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.0000009958*1000,plotCategory("kPlotEFTM5IntWZ")),
       5933: (dirT2+"2024/"+skimType+"/VBS-WZto2MuTauNu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000006643*1000,plotCategory("kPlotEFTT5IntWZ")),
       5934: (dirT2+"2024/"+skimType+"/VBS-WZto2MuTauNu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.00001036*1000,plotCategory("kPlotEFTT6IntWZ")),
       5935: (dirT2+"2024/"+skimType+"/VBS-WZto2MuTauNu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000006839*1000,plotCategory("kPlotEFTT7IntWZ")),
       5936: (dirT2+"2024/"+skimType+"/VBS-WZto2TauENu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -4.285e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       5937: (dirT2+"2024/"+skimType+"/VBS-WZto2TauENu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.0000005344*1000,plotCategory("kPlotEFTM3IntWZ")),
       5938: (dirT2+"2024/"+skimType+"/VBS-WZto2TauENu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.0000007902*1000,plotCategory("kPlotEFTM4IntWZ")),
       5939: (dirT2+"2024/"+skimType+"/VBS-WZto2TauENu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -1.242e-05*1000,plotCategory("kPlotEFTM5IntWZ")),
       5940: (dirT2+"2024/"+skimType+"/VBS-WZto2TauENu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000006634*1000,plotCategory("kPlotEFTT5IntWZ")),
       5941: (dirT2+"2024/"+skimType+"/VBS-WZto2TauENu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.00001051*1000,plotCategory("kPlotEFTT6IntWZ")),
       5942: (dirT2+"2024/"+skimType+"/VBS-WZto2TauENu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000006874*1000,plotCategory("kPlotEFTT7IntWZ")),
       5943: (dirT2+"2024/"+skimType+"/VBS-WZto2TauMuNu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -4.509e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       5944: (dirT2+"2024/"+skimType+"/VBS-WZto2TauMuNu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.0000006144*1000,plotCategory("kPlotEFTM3IntWZ")),
       5945: (dirT2+"2024/"+skimType+"/VBS-WZto2TauMuNu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -9.821e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       5946: (dirT2+"2024/"+skimType+"/VBS-WZto2TauMuNu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -1.305e-05*1000,plotCategory("kPlotEFTM5IntWZ")),
       5947: (dirT2+"2024/"+skimType+"/VBS-WZto2TauMuNu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000006709*1000,plotCategory("kPlotEFTT5IntWZ")),
       5948: (dirT2+"2024/"+skimType+"/VBS-WZto2TauMuNu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.00001045*1000,plotCategory("kPlotEFTT6IntWZ")),
       5949: (dirT2+"2024/"+skimType+"/VBS-WZto2TauMuNu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000006845*1000,plotCategory("kPlotEFTT7IntWZ")),
       5950: (dirT2+"2024/"+skimType+"/VBS-WZto3ENu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -4.508e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       5951: (dirT2+"2024/"+skimType+"/VBS-WZto3ENu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.0000005066*1000,plotCategory("kPlotEFTM3IntWZ")),
       5952: (dirT2+"2024/"+skimType+"/VBS-WZto3ENu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -6.621e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       5953: (dirT2+"2024/"+skimType+"/VBS-WZto3ENu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000001197*1000,plotCategory("kPlotEFTM5IntWZ")),
       5954: (dirT2+"2024/"+skimType+"/VBS-WZto3ENu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000006371*1000,plotCategory("kPlotEFTT5IntWZ")),
       5955: (dirT2+"2024/"+skimType+"/VBS-WZto3ENu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000009477*1000,plotCategory("kPlotEFTT6IntWZ")),
       5956: (dirT2+"2024/"+skimType+"/VBS-WZto3ENu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.00000632*1000,plotCategory("kPlotEFTT7IntWZ")),
       5957: (dirT2+"2024/"+skimType+"/VBS-WZto3MuNu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -4.468e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       5958: (dirT2+"2024/"+skimType+"/VBS-WZto3MuNu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.0000005005*1000,plotCategory("kPlotEFTM3IntWZ")),
       5959: (dirT2+"2024/"+skimType+"/VBS-WZto3MuNu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -6.906e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       5960: (dirT2+"2024/"+skimType+"/VBS-WZto3MuNu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000001524*1000,plotCategory("kPlotEFTM5IntWZ")),
       5961: (dirT2+"2024/"+skimType+"/VBS-WZto3MuNu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000006547*1000,plotCategory("kPlotEFTT5IntWZ")),
       5962: (dirT2+"2024/"+skimType+"/VBS-WZto3MuNu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000009484*1000,plotCategory("kPlotEFTT6IntWZ")),
       5963: (dirT2+"2024/"+skimType+"/VBS-WZto3MuNu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000006383*1000,plotCategory("kPlotEFTT7IntWZ")),
       5964: (dirT2+"2024/"+skimType+"/VBS-WZto3TauNu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -4.285e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       5965: (dirT2+"2024/"+skimType+"/VBS-WZto3TauNu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.0000005196*1000,plotCategory("kPlotEFTM3IntWZ")),
       5966: (dirT2+"2024/"+skimType+"/VBS-WZto3TauNu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.0000004334*1000,plotCategory("kPlotEFTM4IntWZ")),
       5967: (dirT2+"2024/"+skimType+"/VBS-WZto3TauNu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -1.149e-05*1000,plotCategory("kPlotEFTM5IntWZ")),
       5968: (dirT2+"2024/"+skimType+"/VBS-WZto3TauNu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000006569*1000,plotCategory("kPlotEFTT5IntWZ")),
       5969: (dirT2+"2024/"+skimType+"/VBS-WZto3TauNu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000009913*1000,plotCategory("kPlotEFTT6IntWZ")),
       5970: (dirT2+"2024/"+skimType+"/VBS-WZto3TauNu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000006535*1000,plotCategory("kPlotEFTT7IntWZ")),


## 2025#####

       600: (dirT2+"2024/"+skimType+"/DYto2E_Bin-MLL-10to50_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",19982.5*1000/3.,plotCategory("kPlotDY")),
       601: (dirT2+"2024/"+skimType+"/DYto2E-2Jets_Bin-MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v4+NANOAODSIM",6345.99*1000/3.,plotCategory("kPlotDY")),
       602: (dirT2+"2024/"+skimType+"/WWto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",(118.7*1.06-ggWWXS_LO_MCFM)*0.1086*0.1086*9*1000,plotCategory("kPlotqqWW")),
       603: (dirT2+"2024/"+skimType+"/WZto3LNu_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",4.924*1.08*1000,plotCategory("kPlotWZ")),
       604: (dirT2+"2024/"+skimType+"/WZto2L2Q_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",7.568*1.08*1000,plotCategory("kPlotWZ")),
       605: (dirT2+"2024/"+skimType+"/ZZto2L2Q_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",6.788*1.19*1000,plotCategory("kPlotZZ")),
       606: (dirT2+"2024/"+skimType+"/ZZto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",1.031*1.16*1000,plotCategory("kPlotZZ")),
       607: (dirT2+"2024/"+skimType+"/ZZto4L_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",1.390*1.19*1000,plotCategory("kPlotZZ")),
       608: (dirT2+"2024/"+skimType+"/TTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v3+NANOAODSIM",0.950*923.6*0.1086*0.1086*9*1000,plotCategory("kPlotTT")),
       609: (dirT2+"2024/"+skimType+"/TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.950*923.6*0.1086*3*(1-0.1086*3)*2*1000,plotCategory("kPlotTT")),
       610: (dirT2+"2024/"+skimType+"/TTto4Q_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",1000000*0.950*923.6*(1-0.1086*3)*(1-0.1086*3)*1000,plotCategory("kPlotNonPrompt")),
       611: (dirT2+"2024/"+skimType+"/TbarWplusto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",4.67*1000,plotCategory("kPlotTW")),
       612: (dirT2+"2024/"+skimType+"/TWminusto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",4.67*1000,plotCategory("kPlotTW")),
       613: (dirT2+"2024/"+skimType+"/WtoENu-2Jets_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v3+NANOAODSIM",64481.58*1000/3.,plotCategory("kPlotOther")),
       614: (dirT2+"2024/"+skimType+"/WWW-4F_TuneCP5_13p6TeV_amcatnlo-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.23280*1000,plotCategory("kPlotVVV")),
       615: (dirT2+"2024/"+skimType+"/WWZ-4F_TuneCP5_13p6TeV_amcatnlo-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.18510*1000,plotCategory("kPlotVVV")),
       616: (dirT2+"2024/"+skimType+"/WZZ-5F_TuneCP5_13p6TeV_amcatnlo-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.06206*1000,plotCategory("kPlotVVV")),
       617: (dirT2+"2024/"+skimType+"/ZZZ-5F_TuneCP5_13p6TeV_amcatnlo-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.01591*1000,plotCategory("kPlotVVV")),
       618: (dirT2+"2024/"+skimType+"/WZGtoLNuZG_TuneCP5_13p6TeV_amcatnlo-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.08425*1000,plotCategory("kPlotVVV")),
       619: (dirT2+"2024/"+skimType+"/TTWW_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.0081651*1000,plotCategory("kPlotTVX")),
       620: (dirT2+"2024/"+skimType+"/TTWZ_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.0027199*1000,plotCategory("kPlotTVX")),
       621: (dirT2+"2024/"+skimType+"/GluGluHto2Zto4L_Par-M-125_TuneCP5_13p6TeV_powhegMINNLO-jhugen-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",52.230*0.02619*0.101*0.101*1000,plotCategory("kPlotHiggs")),
       622: (dirT2+"2024/"+skimType+"/VBFH-Hto2Zto4L_Par-M-125_TuneCP5_13p6TeV_powheg-jhugen-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",4.0780*0.02619*0.101*0.101*1000,plotCategory("kPlotHiggs")),
       623: (dirT2+"2024/"+skimType+"/TTLL_Bin-MLL-4to50_TuneCP5_13p6TeV_amcatnlo-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.03949*1000,plotCategory("kPlotTVX")),
       624: (dirT2+"2024/"+skimType+"/TTLL_Bin-MLL-50_TuneCP5_13p6TeV_amcatnlo-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.08646*1000,plotCategory("kPlotTVX")),
       625: (dirT2+"2024/"+skimType+"/DYto2Mu_Bin-MLL-10to50_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",19982.5*1000/3.,plotCategory("kPlotDY")),
       626: (dirT2+"2024/"+skimType+"/DYto2Mu-2Jets_Bin-MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v6+NANOAODSIM",6345.99*1000/3.,plotCategory("kPlotDY")),
       627: (dirT2+"2024/"+skimType+"/DYto2Tau_Bin-MLL-10to50_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",19982.5*1000/3.,plotCategory("kPlotDY")),
       628: (dirT2+"2024/"+skimType+"/DYto2Tau-2Jets_Bin-MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v5+NANOAODSIM",6345.99*1000/3.,plotCategory("kPlotDY")),
       629: (dirT2+"2024/"+skimType+"/DYGto2LG-1Jets_Bin-MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",126.86326*1000,plotCategory("kPlotVG")),
       630: (dirT2+"2024/"+skimType+"/DYGto2LG-1Jets_MLL-50_PTG-100to200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v3+NANOAODSIM",0.347454856033058*1000,plotCategory("kPlotVG")),
       631: (dirT2+"2024/"+skimType+"/DYGto2LG-1Jets_MLL-50_PTG-200to400_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.043623155782532*1000,plotCategory("kPlotVG")),
       632: (dirT2+"2024/"+skimType+"/EWK-ZG2JtoG2L2J_Bin-MLL-50-MJJ-120_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.113109*1000,plotCategory("kPlotVG")),
       633: (dirT2+"2024/"+skimType+"/WGtoLNuG-1Jets_PTG-10to100_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",668.91538*1000,plotCategory("kPlotVG")),
       634: (dirT2+"2024/"+skimType+"/WGtoLNuG-1Jets_PTG-100to200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",2.22141*1000,plotCategory("kPlotVG")),
       635: (dirT2+"2024/"+skimType+"/WGtoLNuG-1Jets_PTG-200to400_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",0.291367*1000,plotCategory("kPlotVG")),
       636: (dirT2+"2024/"+skimType+"/WWto4Q_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",1000000*(118.7*1.06-ggWWXS_LO_MCFM)*(1-0.1086*3)*(1-0.1086*3)*1000,plotCategory("kPlotNonPrompt")),
       637: (dirT2+"2024/"+skimType+"/GluGluH-HTo2Tau_Par-M-125_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",52.230*0.06272*1000,plotCategory("kPlotHiggs")),
       638: (dirT2+"2024/"+skimType+"/VBFH-HTo2Tau_Par-M-125_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",4.0780*0.06272*1000,plotCategory("kPlotHiggs")),
       639: (dirT2+"2024/"+skimType+"//DYGto2LG-1Jets_Bin-MLL-4to50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",88.11067*1000,plotCategory("kPlotVG")),
       640: (dirT2+"2024/"+skimType+"/DYGto2LG-1Jets_MLL-4to50_PTG-100to200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.24095*1000,plotCategory("kPlotVG")),
       641: (dirT2+"2024/"+skimType+"/DYGto2LG-1Jets_MLL-4to50_PTG-200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.02228*1000,plotCategory("kPlotVG")),
       642: (dirT2+"2024/"+skimType+"/WtoMuNu-2Jets_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v3+NANOAODSIM",64481.58*1000/3.,plotCategory("kPlotOther")),
       643: (dirT2+"2024/"+skimType+"/WtoTauNu-2Jets_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v3+NANOAODSIM",64481.58*1000/3.,plotCategory("kPlotOther")),
       644: (dirT2+"2024/"+skimType+"/VH_HtoNonbb_M-125_TuneCP5_13p6TeV_amcatnloFXFX-madspin-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",(0.9439+1.4570)*(1-0.577)*1000,plotCategory("kPlotHiggs")),
       645: (dirT2+"2024/"+skimType+"/DYto2L-2Jets_MLL-50_0J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",5034.65*1000,plotCategory("kPlotDY")),
       646: (dirT2+"2024/"+skimType+"/DYto2L-2Jets_MLL-50_1J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",952.29*1000,plotCategory("kPlotDY")),
       647: (dirT2+"2024/"+skimType+"/DYto2L-2Jets_MLL-50_2J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",359.05*1000,plotCategory("kPlotDY")),
       648: (dirT2+"2024/"+skimType+"/TTLNu-1Jets_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+RunIII2024Summer24NanoAODv15-mg35x_150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.2502*1000,plotCategory("kPlotTVX")),
       649: (dirT2+"2024/"+skimType+"//TZQB-Zto2L-4FS_Bin-MLL-30_TuneCP5_13p6TeV_amcatnlo-pythia8+RunIII2024Summer24NanoAODv15-Madgraph_2_6_5_150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.07968*1.30*1000,plotCategory("kPlotTVX")),
       650: (dirT2+"2024/"+skimType+"/VBS-SSWW_PolarizationLL_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.002190*1000,plotCategory("kPlotEWKSSWW")),
       651: (dirT2+"2024/"+skimType+"/VBS-SSWW_PolarizationTL_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.011700*1000,plotCategory("kPlotEWKSSWW")),
       652: (dirT2+"2024/"+skimType+"/VBS-SSWW_PolarizationTT_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.017635*1000,plotCategory("kPlotEWKSSWW")),
       653: (dirT2+"2024/"+skimType+"/GluGluHto2Wto2L2Nu_Par-M-125_TuneCP5_13p6TeV_powheg-jhugen-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",52.230*0.2137*0.1086*0.1086*9*1000,plotCategory("kPlotHiggs")),
       654: (dirT2+"2024/"+skimType+"/VBFHto2Wto2L2Nu_Par-M-125_TuneCP5_13p6TeV_powheg-jhugen-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",4.0780*0.2137*0.1086*0.1086*9*1000,plotCategory("kPlotHiggs")),
       655: (dirT2+"2024/"+skimType+"/TTH-HtoNon2B_Par-M-125_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.5700*(1-0.577)*1000,plotCategory("kPlotHiggs")),
       656: (dirT2+"2024/"+skimType+"/WGtoLNuG-1Jets_PTG-400to600_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",0.022322*1000,plotCategory("kPlotVG")),
       657: (dirT2+"2024/"+skimType+"/WGtoLNuG-1Jets_PTG-600_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",0.004918*1000,plotCategory("kPlotVG")),
       658: (dirT2+"2024/"+skimType+"/WW-DPS_TuneCP5_13p6TeV_pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",2.14891*1000,plotCategory("kPlotOther")),
       659: (dirT2+"2024/"+skimType+"/GluGlu2Zto4E_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.5*0.0061150*1000,plotCategory("kPlotZZ")),
       660: (dirT2+"2024/"+skimType+"/GluGlu2Zto4Mu_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.5*0.0061150*1000,plotCategory("kPlotZZ")),
       661: (dirT2+"2024/"+skimType+"/GluGlu2Zto4Tau_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.5*0.0061150*1000,plotCategory("kPlotZZ")),
       662: (dirT2+"2024/"+skimType+"/GluGlu2Zto2E2Tau_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.0061150*1000,plotCategory("kPlotZZ")),
       663: (dirT2+"2024/"+skimType+"/GluGlu2Zto2Mu2Tau_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.0061150*1000,plotCategory("kPlotZZ")),
       664: (dirT2+"2024/"+skimType+"/GluGlu2Zto2E2Mu_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.0061150*1000,plotCategory("kPlotZZ")),
       665: (dirT2+"2024/"+skimType+"/GluGluWWto2E2Nu_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       666: (dirT2+"2024/"+skimType+"/GluGluWWtoENuMuNu_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       667: (dirT2+"2024/"+skimType+"/GluGluWWtoENuTauNu_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       668: (dirT2+"2024/"+skimType+"/GluGluWWtoMuNuENu_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       669: (dirT2+"2024/"+skimType+"/GluGluWWto2Mu2Nu_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       670: (dirT2+"2024/"+skimType+"/GluGluWWtoMuNuTauNu_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       671: (dirT2+"2024/"+skimType+"/GluGluWWtoTauNuENu_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       672: (dirT2+"2024/"+skimType+"/GluGluWWtoTauNuMuNu_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       673: (dirT2+"2024/"+skimType+"/GluGluWWto2Tau2Nu_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       674: (dirT2+"2024/"+skimType+"/WWJJto2L2Nu-OS-noTop-EWK_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",                         0.3301419*1000,plotCategory("kPlotqqWW")),
       675: (dirT2+"2024/"+skimType+"/WWJJto2L2Nu-OS-noTop-QCD_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",                         2.6758028*1000,plotCategory("kPlotqqWW")),
       676: (dirT2+"2024/"+skimType+"/WWJJto2L2Nu-SS-noTop-EWK_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",                         0.0295255*1000,plotCategory("kPlotEWKSSWW")),
       677: (dirT2+"2024/"+skimType+"/WWJJto2L2Nu-SS-noTop-QCD_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",                         0.0279662*1000,plotCategory("kPlotQCDSSWW")),
       678: (dirT2+"2024/"+skimType+"/WZJJto3LNu-EWK_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",                                   0.0429366*1000,plotCategory("kPlotEWKWZ")),
       679: (dirT2+"2024/"+skimType+"/WZJJto3LNu-QCD_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",                                   0.4958618*1000*0.70,plotCategory("kPlotWZ")),
       680: (dirT2+"2024/"+skimType+"/ZZJJto2L2Nu-EWK_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",                                  0.0051721*1000,plotCategory("kPlotZZ")),
       681: (dirT2+"2024/"+skimType+"/ZZJJto2L2Nu-QCD_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",                                  0.0912313*1000*1.40,plotCategory("kPlotZZ")),
       682: (dirT2+"2024/"+skimType+"/ZZJJto4L-EWK_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",                                     0.0011422*1000,plotCategory("kPlotZZ")),
       683: (dirT2+"2024/"+skimType+"/ZZJJto4L-QCD_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",                                     0.0202984*1000*1.40,plotCategory("kPlotZZ")),
       684: (dirT2+"2024/"+skimType+"/WpWpJJ-EWK_TuneCP5_13p6TeV-powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.5*0.0295255*1000,plotCategory("kPlotEWKSSWW")),
       685: (dirT2+"2024/"+skimType+"/WmWmJJ-EWK_TuneCP5_13p6TeV-powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.5*0.0295255*1000,plotCategory("kPlotEWKSSWW")),
       686: (dirT2+"2024/"+skimType+"/ZH-HtoNon2B_Par-M-125_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",(0.9439)*(1-0.577)*1000,plotCategory("kPlotHiggs")),
       687: (dirT2+"2024/"+skimType+"/WplusH-HtoNon2B_Par-M-125_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",(1.4570*0.608)*(1-0.577)*1000,plotCategory("kPlotHiggs")),
       688: (dirT2+"2024/"+skimType+"/WminusH-HtoNon2B_Par-M-125_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",(1.4570*0.392)*(1-0.577)*1000,plotCategory("kPlotHiggs")),
       689: (dirT2+"2024/"+skimType+"/SSWWJJ-Interference_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.00341005*1000,plotCategory("kPlotQCDSSWW")),
       690: (dirT2+"2024/"+skimType+"/VBSWZ-Interference_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.04806677*1000,plotCategory("kPlotWZ")),
       691: (dirT2+"2024/"+skimType+"/WGtoLNuG-1Jets_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",671.734705*1000,plotCategory("kPlotVG")),
       692: (dirT3+"2024/SM", 0.0295255*1000,plotCategory("kPlotEWKSSWW")),
       693: (dirT2+"2024/"+skimType+"/VBS-SSWW-M0-Interference_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000297*1000,plotCategory("kPlotEFTM0Int")),
       694: (dirT2+"2024/"+skimType+"/VBS-SSWW-M0-Quadratic_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.007333*1000,plotCategory("kPlotEFTM0Quad")),
       695: (dirT3+"Sherpa_Sample/2024", 39.8961,plotCategory("kPlotEWKSSWW")),
       696: (dirT2+"2024/"+skimType+"/VBS-SSWW-M1-Interference_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -0.0003746 *1000,plotCategory("kPlotEFTM1Int")),
       697: (dirT2+"2024/"+skimType+"/VBS-SSWW-M1-Quadratic_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.007688*1000,plotCategory("kPlotEFTM1Quad")),
       698: (dirT2+"2024/"+skimType+"/VBS-SSWW-M7-Interference_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.00002167*1000,plotCategory("kPlotEFTM7Int")),
       699: (dirT2+"2024/"+skimType+"/VBS-SSWW-M7-Quadratic_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.003405*1000,plotCategory("kPlotEFTM7Quad")),
       6990: (dirT2+"2024/"+skimType+"/VBS-SSWW-S0-Interference_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -0.0003575*1000,plotCategory("kPlotEFTS0Int")),
       6991: (dirT2+"2024/"+skimType+"/VBS-SSWW-S0-Quadratic_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.008078*1000,plotCategory("kPlotEFTS0Quad")),
       6992: (dirT2+"2024/"+skimType+"/VBS-SSWW-T0-Interference_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",  -0.0005086*1000,plotCategory("kPlotEFTT0Int")),
       6993: (dirT2+"2024/"+skimType+"/VBS-SSWW-T0-Quadratic_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.02811*1000,plotCategory("kPlotEFTT0Quad")),
       6994: (dirT2+"2024/"+skimType+"/VBS-SSWW-T1-Interference_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -0.001284*1000,plotCategory("kPlotEFTT1Int")),
       6995: (dirT2+"2024/"+skimType+"/VBS-SSWW-T1-Quadratic_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.03099*1000,plotCategory("kPlotEFTT1Quad")),
       6996: (dirT2+"2024/"+skimType+"/VBS-SSWW-T2-Interference_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",  -0.001341*1000,plotCategory("kPlotEFTT2Int")),
       6997: (dirT2+"2024/"+skimType+"/VBS-SSWW-T2-Quadratic_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.01401*1000,plotCategory("kPlotEFTT2Quad")),
       6901: (dirT2+"2024/"+skimType+"/VBS-WZ-M2Quad_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.0002623*1000,plotCategory("kPlotEFTM2QuadWZ")),
       6902: (dirT2+"2024/"+skimType+"/VBS-WZ-M3Quad_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.0001106*1000,plotCategory("kPlotEFTM3QuadWZ")),
       6903: (dirT2+"2024/"+skimType+"/VBS-WZ-M4Quad_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.001995*1000,plotCategory("kPlotEFTM4QuadWZ")),
       6904: (dirT2+"2024/"+skimType+"/VBS-WZ-M5Quad_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.001099*1000,plotCategory("kPlotEFTM5QuadWZ")),
       6905: (dirT2+"2024/"+skimType+"/VBS-WZ-T5Quad_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.001619*1000,plotCategory("kPlotEFTT5QuadWZ")),
       6906: (dirT2+"2024/"+skimType+"/VBS-WZ-T6Quad_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.001873*1000,plotCategory("kPlotEFTT6QuadWZ")),
       6907: (dirT2+"2024/"+skimType+"/VBS-WZ-T7Quad_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.0002992*1000,plotCategory("kPlotEFTT7QuadWZ")),
       6908: (dirT2+"2024/"+skimType+"/VBS-WZto2EMuNu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -3.893e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       6909: (dirT2+"2024/"+skimType+"/VBS-WZto2EMuNu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.0000005482*1000,plotCategory("kPlotEFTM3IntWZ")),
       6910: (dirT2+"2024/"+skimType+"/VBS-WZto2EMuNu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -6.032e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       6911: (dirT2+"2024/"+skimType+"/VBS-WZto2EMuNu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000001213*1000,plotCategory("kPlotEFTM5IntWZ")),
       6912: (dirT2+"2024/"+skimType+"/VBS-WZto2EMuNu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000006792*1000,plotCategory("kPlotEFTT5IntWZ")),
       6913: (dirT2+"2024/"+skimType+"/VBS-WZto2EMuNu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.00001022*1000,plotCategory("kPlotEFTT6IntWZ")),
       6914: (dirT2+"2024/"+skimType+"/VBS-WZto2EMuNu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000006764*1000,plotCategory("kPlotEFTT7IntWZ")),
       6915: (dirT2+"2024/"+skimType+"/VBS-WZto2ETauNu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -4.604e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       6916: (dirT2+"2024/"+skimType+"/VBS-WZto2ETauNu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.0000005346*1000,plotCategory("kPlotEFTM3IntWZ")),
       6917: (dirT2+"2024/"+skimType+"/VBS-WZto2ETauNu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -5.705e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       6918: (dirT2+"2024/"+skimType+"/VBS-WZto2ETauNu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000001552*1000,plotCategory("kPlotEFTM5IntWZ")),
       6919: (dirT2+"2024/"+skimType+"/VBS-WZto2ETauNu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.00000669*1000,plotCategory("kPlotEFTT5IntWZ")),
       6920: (dirT2+"2024/"+skimType+"/VBS-WZto2ETauNu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.00001023*1000,plotCategory("kPlotEFTT6IntWZ")),
       6921: (dirT2+"2024/"+skimType+"/VBS-WZto2ETauNu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000006783*1000,plotCategory("kPlotEFTT7IntWZ")),
       6922: (dirT2+"2024/"+skimType+"/VBS-WZto2MuENu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -4.819e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       6923: (dirT2+"2024/"+skimType+"/VBS-WZto2MuENu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.0000004808*1000,plotCategory("kPlotEFTM3IntWZ")),
       6924: (dirT2+"2024/"+skimType+"/VBS-WZto2MuENu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -6.275e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       6925: (dirT2+"2024/"+skimType+"/VBS-WZto2MuENu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000001302*1000,plotCategory("kPlotEFTM5IntWZ")),
       6926: (dirT2+"2024/"+skimType+"/VBS-WZto2MuENu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000006689*1000,plotCategory("kPlotEFTT5IntWZ")),
       6927: (dirT2+"2024/"+skimType+"/VBS-WZto2MuENu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.00001045*1000,plotCategory("kPlotEFTT6IntWZ")),
       6928: (dirT2+"2024/"+skimType+"/VBS-WZto2MuENu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000006781*1000,plotCategory("kPlotEFTT7IntWZ")),
       6929: (dirT2+"2024/"+skimType+"/VBS-WZto2MuTauNu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -5.153e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       6930: (dirT2+"2024/"+skimType+"/VBS-WZto2MuTauNu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.0000005407*1000,plotCategory("kPlotEFTM3IntWZ")),
       6931: (dirT2+"2024/"+skimType+"/VBS-WZto2MuTauNu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -6.29e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       6932: (dirT2+"2024/"+skimType+"/VBS-WZto2MuTauNu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.0000009958*1000,plotCategory("kPlotEFTM5IntWZ")),
       6933: (dirT2+"2024/"+skimType+"/VBS-WZto2MuTauNu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000006643*1000,plotCategory("kPlotEFTT5IntWZ")),
       6934: (dirT2+"2024/"+skimType+"/VBS-WZto2MuTauNu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.00001036*1000,plotCategory("kPlotEFTT6IntWZ")),
       6935: (dirT2+"2024/"+skimType+"/VBS-WZto2MuTauNu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000006839*1000,plotCategory("kPlotEFTT7IntWZ")),
       6936: (dirT2+"2024/"+skimType+"/VBS-WZto2TauENu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -4.285e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       6937: (dirT2+"2024/"+skimType+"/VBS-WZto2TauENu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.0000005344*1000,plotCategory("kPlotEFTM3IntWZ")),
       6938: (dirT2+"2024/"+skimType+"/VBS-WZto2TauENu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.0000007902*1000,plotCategory("kPlotEFTM4IntWZ")),
       6939: (dirT2+"2024/"+skimType+"/VBS-WZto2TauENu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -1.242e-05*1000,plotCategory("kPlotEFTM5IntWZ")),
       6940: (dirT2+"2024/"+skimType+"/VBS-WZto2TauENu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000006634*1000,plotCategory("kPlotEFTT5IntWZ")),
       6941: (dirT2+"2024/"+skimType+"/VBS-WZto2TauENu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.00001051*1000,plotCategory("kPlotEFTT6IntWZ")),
       6942: (dirT2+"2024/"+skimType+"/VBS-WZto2TauENu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000006874*1000,plotCategory("kPlotEFTT7IntWZ")),
       6943: (dirT2+"2024/"+skimType+"/VBS-WZto2TauMuNu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -4.509e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       6944: (dirT2+"2024/"+skimType+"/VBS-WZto2TauMuNu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.0000006144*1000,plotCategory("kPlotEFTM3IntWZ")),
       6945: (dirT2+"2024/"+skimType+"/VBS-WZto2TauMuNu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -9.821e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       6946: (dirT2+"2024/"+skimType+"/VBS-WZto2TauMuNu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -1.305e-05*1000,plotCategory("kPlotEFTM5IntWZ")),
       6947: (dirT2+"2024/"+skimType+"/VBS-WZto2TauMuNu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000006709*1000,plotCategory("kPlotEFTT5IntWZ")),
       6948: (dirT2+"2024/"+skimType+"/VBS-WZto2TauMuNu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.00001045*1000,plotCategory("kPlotEFTT6IntWZ")),
       6949: (dirT2+"2024/"+skimType+"/VBS-WZto2TauMuNu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000006845*1000,plotCategory("kPlotEFTT7IntWZ")),
       6950: (dirT2+"2024/"+skimType+"/VBS-WZto3ENu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -4.508e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       6951: (dirT2+"2024/"+skimType+"/VBS-WZto3ENu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.0000005066*1000,plotCategory("kPlotEFTM3IntWZ")),
       6952: (dirT2+"2024/"+skimType+"/VBS-WZto3ENu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -6.621e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       6953: (dirT2+"2024/"+skimType+"/VBS-WZto3ENu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000001197*1000,plotCategory("kPlotEFTM5IntWZ")),
       6954: (dirT2+"2024/"+skimType+"/VBS-WZto3ENu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000006371*1000,plotCategory("kPlotEFTT5IntWZ")),
       6955: (dirT2+"2024/"+skimType+"/VBS-WZto3ENu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000009477*1000,plotCategory("kPlotEFTT6IntWZ")),
       6956: (dirT2+"2024/"+skimType+"/VBS-WZto3ENu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.00000632*1000,plotCategory("kPlotEFTT7IntWZ")),
       6957: (dirT2+"2024/"+skimType+"/VBS-WZto3MuNu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -4.468e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       6958: (dirT2+"2024/"+skimType+"/VBS-WZto3MuNu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.0000005005*1000,plotCategory("kPlotEFTM3IntWZ")),
       6959: (dirT2+"2024/"+skimType+"/VBS-WZto3MuNu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -6.906e-07*1000,plotCategory("kPlotEFTM4IntWZ")),
       6960: (dirT2+"2024/"+skimType+"/VBS-WZto3MuNu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000001524*1000,plotCategory("kPlotEFTM5IntWZ")),
       6961: (dirT2+"2024/"+skimType+"/VBS-WZto3MuNu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000006547*1000,plotCategory("kPlotEFTT5IntWZ")),
       6962: (dirT2+"2024/"+skimType+"/VBS-WZto3MuNu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000009484*1000,plotCategory("kPlotEFTT6IntWZ")),
       6963: (dirT2+"2024/"+skimType+"/VBS-WZto3MuNu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000006383*1000,plotCategory("kPlotEFTT7IntWZ")),
       6964: (dirT2+"2024/"+skimType+"/VBS-WZto3TauNu-M2Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -4.285e-07*1000,plotCategory("kPlotEFTM2IntWZ")),
       6965: (dirT2+"2024/"+skimType+"/VBS-WZto3TauNu-M3Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.0000005196*1000,plotCategory("kPlotEFTM3IntWZ")),
       6966: (dirT2+"2024/"+skimType+"/VBS-WZto3TauNu-M4Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.0000004334*1000,plotCategory("kPlotEFTM4IntWZ")),
       6967: (dirT2+"2024/"+skimType+"/VBS-WZto3TauNu-M5Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", -1.149e-05*1000,plotCategory("kPlotEFTM5IntWZ")),
       6968: (dirT2+"2024/"+skimType+"/VBS-WZto3TauNu-T5Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000006569*1000,plotCategory("kPlotEFTT5IntWZ")),
       6969: (dirT2+"2024/"+skimType+"/VBS-WZto3TauNu-T6Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000009913*1000,plotCategory("kPlotEFTT6IntWZ")),
       6970: (dirT2+"2024/"+skimType+"/VBS-WZto3TauNu-T7Int_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM", 0.000006535*1000,plotCategory("kPlotEFTT7IntWZ")),
       

       900:(dirLocal+"/2018/vbf-hrhogamma-powheg+NANOAOD_01",1.0*1000,plotCategory("kPlotBSM")),

       901:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/DY_MLM_2022_preEE",6345.99*1000,plotCategory("kPlotDY")),
       902:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/DY_2022_preEE",6345.99*1000,plotCategory("kPlotDY")),
       903:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/DY_2022_postEE",6345.99*1000,plotCategory("kPlotDY")),
       904:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/DY_2023_partA",6345.99*1000,plotCategory("kPlotDY")),
       905:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/DY_2023_partB",6345.99*1000,plotCategory("kPlotDY")),

       906:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/TTto2L2Nu_2022_postEE",0.950*923.6*0.1086*0.1086*9*1000,plotCategory("kPlotTT")),
       907:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/TWminusto2L2Nu_2022_postEE",23.97*1000*2.0,plotCategory("kPlotTW")),

       960:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/qqWW_2018",(118.7-3.974)*0.1086*0.1086*9*1000,plotCategory("kPlotqqWW")),

       961:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/qqWW_2022_postEE",(118.7*1.06-ggWWXS_LO_MCFM)*0.1086*0.1086*9*1000,plotCategory("kPlotqqWW")),

       962:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/GluGlutoContintoWWtoENuENu_postEE"    ,(0.1086*0.1086)*ggWWXS_LO_MCFM*ggWWXS_kFactor*1000,plotCategory("kPlotggWW")),
       963:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/GluGlutoContintoWWtoENuMuNu_postEE"   ,(0.1086*0.1086)*ggWWXS_LO_MCFM*ggWWXS_kFactor*1000,plotCategory("kPlotggWW")),
       964:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/GluGlutoContintoWWtoENuTauNu_postEE"  ,(0.1086*0.1086)*ggWWXS_LO_MCFM*ggWWXS_kFactor*1000,plotCategory("kPlotggWW")),
       965:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/GluGlutoContintoWWtoMuNuENu_postEE"   ,(0.1086*0.1086)*ggWWXS_LO_MCFM*ggWWXS_kFactor*1000,plotCategory("kPlotggWW")),
       966:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/GluGlutoContintoWWtoMuNuMuNu_postEE"  ,(0.1086*0.1086)*ggWWXS_LO_MCFM*ggWWXS_kFactor*1000,plotCategory("kPlotggWW")),
       967:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/GluGlutoContintoWWtoMuNuTauNu_postEE" ,(0.1086*0.1086)*ggWWXS_LO_MCFM*ggWWXS_kFactor*1000,plotCategory("kPlotggWW")),
       968:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/GluGlutoContintoWWtoTauNuENu_postEE"  ,(0.1086*0.1086)*ggWWXS_LO_MCFM*ggWWXS_kFactor*1000,plotCategory("kPlotggWW")),
       969:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/GluGlutoContintoWWtoTauNuMuNu_postEE" ,(0.1086*0.1086)*ggWWXS_LO_MCFM*ggWWXS_kFactor*1000,plotCategory("kPlotggWW")),
       970:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/GluGlutoContintoWWtoTauNuTauNu_postEE",(0.1086*0.1086)*ggWWXS_LO_MCFM*ggWWXS_kFactor*1000,plotCategory("kPlotggWW")),

       971:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/ggWWto2L2Nu_OS_PolarizationLL_postEE",0.24053*(ggWWXS_LO_MCFM/ggWWXS_LO_MADGRAPH)*ggWWXS_kFactor*1000,plotCategory("kPlotggWW")),
       972:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/ggWWto2L2Nu_OS_PolarizationLT_postEE",0.08268*(ggWWXS_LO_MCFM/ggWWXS_LO_MADGRAPH)*ggWWXS_kFactor*1000,plotCategory("kPlotggWW")),
       973:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/ggWWto2L2Nu_OS_PolarizationTL_postEE",0.08268*(ggWWXS_LO_MCFM/ggWWXS_LO_MADGRAPH)*ggWWXS_kFactor*1000,plotCategory("kPlotggWW")),
       974:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/ggWWto2L2Nu_OS_PolarizationTT_postEE",3.10724*(ggWWXS_LO_MCFM/ggWWXS_LO_MADGRAPH)*ggWWXS_kFactor*1000,plotCategory("kPlotggWW")),

       975:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/WW_MINNLO_13p0TeV",(118.7-3.974)*0.1086*0.1086*9*1000,plotCategory("kPlotqqWW")),

       976:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/WW_MINNLO_13p6TeV",12.80173*1000,plotCategory("kPlotqqWW")),

       977:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/WZ3l_2022_postEE",4.924*1.08*1000,plotCategory("kPlotWZ")),

       978:("/ceph/submit/data/user/c/ceballos/test_samples/WpWpJJ-EWK_TuneCP5_13p6TeV-powheg-pythia8",0.5*0.0295255*1000,plotCategory("kPlotEWKSSWW")),
       979:("/ceph/submit/data/user/c/ceballos/test_samples/WmWmJJ-EWK_TuneCP5_13p6TeV-powheg-pythia8",0.5*0.0295255*1000,plotCategory("kPlotEWKSSWW")),

    }
    return switch.get(argument, "BKGdefault, xsecDefault, category")
