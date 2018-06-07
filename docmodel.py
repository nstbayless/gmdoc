# document model

import xml.etree.ElementTree as ET
import glob
import os
import re

reLines = re.compile("//.*?$|/\*.*?\*|^\s*([a-zA-Z_0-9])+\s*=([^\n]*//([^\n]*))?\n", re.MULTILINE)

class VarModel:
    name = ""
    docText = ""

class ObjectModel:
    name = "<undefined>"
    spriteName = ""
    parentName = ""
    docText = ""
    ccv = [] # creation code variables.
    v = [] # non-creation code variables

class DocModel:
    objects = []
    scripts = []
    
    def parseObject(self, objectFile):
        tree = ET.parse(objectFile)
        root = tree.getroot()
        if (root.tag != "object")
            root = root[0]
        assert(root.tag == "object")
        obj = ObjectModel()
        obj.name = os.path.splitext(os.path.basename(objectFile))[0]
        eltSpriteName = root.find("spriteName")
        obj.spriteName = eltSpriteName.text
        eltParentName = root.find("parentName")
        obj.parentName = eltParentName.text
        
        # event parse
        eltEvents = root.find("events")
        for eltEvent in eltEvents:
            if "eventtype" in eltEvent.attrib and "enumb" in eltEvent.attrib:
                if eltEvent.attrib["eventtype"] == "0" and eltEvent.attrib["enumb"] == 0:
                    # collect list of comments, blank lines, and variable declarations
                    lines = []
                    LT_COMMENT = 0
                    LT_POSTCOMMENT = 1
                    LT_VAR = 2
                    LT_JUNK = 3
                    LT_BLANK = 4
                    LT_SEP = 5
                    for action in eltEvent.findall("action"):
                        actID = -1
                        actKind = -1
                        for id in eltEvent.findall("id"):
                            actID = id
                        for kind in eltEvent.findall("kind"):
                            actKind = kind
                        if actID == 603 and actKind == 7: # code block
                            argumentElt = eltEvents.find("arguments")
                            for argument in argumentElt:
                                text = argument.text
                                prev = 0
                                for m in reLines.finditer(text):
                                    start = m.start()
                                    
                                    # check for junk in between matches
                                    prevLine = text[prev:start]
                                    if prevLine.strip() != "":
                                        lines.append((LT_JUNK, prevLine))
                                    elif prevLine.count("\n") > 1:
                                        lines.append((LT_BLANK, prevLine))
                                    
                                    # determine line type
                                    line = m.group()
                                    if line[0:2] == "//":
                                        lines.append(LT_COMMENT, line[2:])
                                    elif line[0:2] == "/*":
                                        lines.append(LT_COMMENT, line[2:-2])
                                    else:
                                        lines.append((LT_VAR, line.group(1)))
                                        if len(line.group(3)) != "":
                                            lines.append((LT_POSTCOMMENT, line.group(3)))
                                    prev = start
                        lines.append(LT_SEP, "---- action separator ----")
                        print(lines)
                            
        self.objects.append(obj)
    
    def parseDocModel(self, projectpath):
        objectFiles = glob(os.path.join(projectpath, "objects/*.object.gmx"))
        scriptFiles = glob(os.path.join(projectpath, "scripts/*.gml"))
        
        # parse objects
        for objectFile in objectFiles:
            parseObject(objectFile)
        