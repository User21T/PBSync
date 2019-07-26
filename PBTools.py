import xml.etree.ElementTree as ET
import os.path
import os
import psutil
import shutil
import subprocess

# PBSync Imports
import PBParser

def run_pbget():
    os.chdir("PBGet")
    subprocess.call(["PBGet.exe", "resetcache"])
    status = subprocess.call(["PBGet.exe", "pull"])
    os.chdir("..")
    return status

def check_running_process(process_name):
    if process_name in (p.name() for p in psutil.process_iter()):
        return True
    return False

def check_git_installation():
    return subprocess.getoutput(["git", "--version"])

def check_lfs_installation():
    return subprocess.getoutput(["git-lfs", "--version"])

def run_ue4versionator():
    if PBParser.is_versionator_symbols_enabled():
        return subprocess.call(["ue4versionator.exe", "--with-symbols"])
    else:
        return subprocess.call(["ue4versionator.exe"])