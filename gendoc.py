#!/usr/bin/python3

import sys
import os
import glob

# local includes
import docmodel
import builddoc

def printUsage():
    print("Usage: " + sys.argv[0] + " path-to-project [path-to-doc-output]")

def isValidProjectDirectory(path):
    if os.path.isfile(path):
        return False
    if os.path.exists(path):
        paths = glob.glob(os.path.join(path, "*.project.gmx"))
        if len(paths) == 1:
            return os.path.split(paths[0])[0]
        print("Error: expected one .project.gmx file in given directory")
    return False

def main():
    if len(sys.argv) <= 1:
        printUsage()
        return -1
        
    # input project
    path = sys.argv[1]
    projectpath = isValidProjectDirectory(path)
    docpath = os.path.join(projectpath, "docs")
    
    if projectpath == False:
        print("Error: invalid project directory")
        return -1
    
    # output directory
    buildpath = os.path.join(projectpath, "docs/build/")
    if len(sys.argv) > 2:
        sys.argv[2]
    
    # create output directory
    if not os.path.isdir(buildpath):
        os.makedirs(buildpath)
        
    dcm = docmodel.DocModel()
    dcm.parseProject(projectpath, docpath)
    builddoc.build(dcm, buildpath)
    print("Done.")
    return 0
    
errcode = main()
sys.exit(errcode)