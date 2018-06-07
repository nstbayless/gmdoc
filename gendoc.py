#!/usr/bin/python3

import sys
import os
import glob

# local includes
import docmodel

def printUsage():
    print("Usage: " + sys.argv[0] + " path-to-project [path-to-doc-output]")

def isValidProjectDirectory(path):
    if os.path.isfile(path):
        return False
    if os.path.exists(path):
        paths = glob.glob(os.path.join(path, "*.project.gmx")
        if len(paths) == 1:
            return os.path.split(paths[0])[1]
        print("Error: expected one .project.gmx file in given directory")
    return False

def main():
    if len(sys.argv) == 0:
        print_usage()
        return -1
        
    # input project
    path = os.path(sys.argv[1])
    projectpath = isValidProjectDirectory(path)
    
    if project == False:
        print("Error: invalid project directory")
        return -1
    
    # output directory
    buildpath = path.join(projectpath, "docs/build/")
    if len(sys.argv > 2):
        os.path(sys.argv[2]
    
    # create output directory
    if not os.path.isdir(buildpath):
        os.makedirs(buildpath)
        
    docmodel = docmodel.generateDocModel(projectpath)
    print(docmodel)
    return 0
    
errcode = main()
sys.exit(errcode)