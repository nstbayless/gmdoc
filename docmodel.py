# document model

import xml.etree.ElementTree as ET
import glob
import os
import re
import markdown
from constants import *

reLines = re.compile("//.*?$|/\*.*?\*/|^\s*([a-zA-Z_0-9]+)\s*=((.*)?(//(.*))?$)", re.MULTILINE)

class VarModel:
    def __init__(self):
        self.name = ""
        self.docText = ""
        self.createValue = ""
        self.baseObject = self
    
    def __repr__(self):
        return self.name + ": " + self.docText

class ObjectModel:
    def __init__(self, dm):
        self.name = "<undefined>"
        self.spriteName = ""
        self.parentName = ""
        self.parent = None
        self.docText = ""
        self.vars = [] # variables
        self.children = []
        self._varnames = []
        self._docmodel = dm
        self._linked = False
    
    def __reprvars__(self):
        tr = ""
        for var in self.vars:
            tr += "\n  " + var.__repr__()
        if len(self.parentName) > 0:
            for obj in self._docmodel.objects:
                if obj.name == self.parentName:
                    tr += "\n\n -- inherited from " + obj.name + " --"
                    tr += obj.__reprvars__()
        return tr
    
    def __repr__(self):
        tr =  self.name + ": " + \
            "\n  sprite: " + self.spriteName + \
            (("\n  parent: " + self.parentName) if len(self.parentName) > 0 else "")
        if len(self.docText) > 0:
            tr += "\n\n" + self.docText + "\n\n"
        tr += "\n\n -- members --"
        tr += self.__reprvars__()
        return tr

    def linkParent(self):
        if not self._linked:
            self.parent = self._docmodel.getObject(self.parentName)
            if self.parent != None:
                self.parent.linkParent()
                for var in self.parent.vars:
                    for myVar in vars:
                        if var.name == myVar.name:
                            myVar.baseObject = var.baseObject
                            if var.docText != "":
                                myVar.docText = var.docText + "</p><p>Notes for " + self.name + ":</p><p>\n" + myVar.docText
            

    def getVariable(self, varName):
        for var in vars:
            if var.name == varName:
                return var
        if self.parentName == ""
            return None
        parent = self._docmodel.getObject(self.parentName)
        if parent != None:
            return parent.getVariable(varName)

class DocModel:
    def __init__(self):
        self.objects = []
        self.scripts = []
        
        # style
        self.footerMessage = ""
        self.assetsDir = ""
        
    def __repr__(self):
        tr = "objects: "
        for obj in self.objects:
            tr += "\n  " + obj.__repr__()
        return tr
        
    def getObject(self, objectName):
        if objectName == "":
            return None
        for object in self.objects:
            if object.name == objectName:
                return object
        return None
    
    def parseDocText(self, lines):
        text = ""
        for l in lines:
            text += l[1] + "\n"
        return markdown.markdown(text.strip())
    
    def parseObject(self, objectFile):
        tree = ET.parse(objectFile)
        root = tree.getroot()
        if root.tag != "object":
            root = root[0]
        assert(root.tag == "object")
        obj = ObjectModel(self)
        obj.name = os.path.splitext(os.path.splitext(os.path.basename(objectFile))[0])[0]
        eltSpriteName = root.find("spriteName")
        obj.spriteName = eltSpriteName.text
        eltParentName = root.find("parentName")
        obj.parentName = eltParentName.text
        # event parse
        eltEvents = root.find("events")
        lines = []
        for eltEvent in eltEvents:
            if "eventtype" in eltEvent.attrib and "enumb" in eltEvent.attrib:
                if eltEvent.attrib["eventtype"] == "0" and eltEvent.attrib["enumb"] == "0":
                    # collect list of comments, blank lines, and variable declarations
                    lines = self._collectLines(eltEvent)
        
        docTextParsed = False # has the doctext for the object been read?
        for i in range(len(lines)):
            l = lines[i]
            lType = l[0]
            lText = l[1]
            
            if lType == LT_VAR or lType == LT_JUNK or lType == LT_SEP:
                proposedDocIDX = i # index of last line of doctext
                if lType == LT_VAR:
                    var = lText
                    if i > 0:
                        if lines[i-1][0] == LT_COMMENT:
                            proposedDocIDX = i-1
                            var.docText = self.parseDocText([lines[i-1]])
                    if len(lines) > i + 1:
                        if lines[i+1][0] == LT_POSTCOMMENT:
                            proposedDocIDX = i
                            var.docText = self.parseDocText([lines[i+1]])
                    if var.name not in obj._varnames:
                        obj._varnames.append(var.name)
                        obj.vars.append(var)
                if not docTextParsed:
                    docTextParsed = True
                    obj.docText = self.parseDocText(lines[0:proposedDocIDX])
        
        self.objects.append(obj)
    
    def parseProject(self, projectpath):
        objectFiles = glob.glob(os.path.join(projectpath, "objects/*.object.gmx"))
        scriptFiles = glob.glob(os.path.join(projectpath, "scripts/*.gml"))
        
        # parse objects
        for objectFile in objectFiles:
            self.parseObject(objectFile)
        for object in self.objects:
            object.linkParent()
            if object.parent != None:
                object.parent.children.append(object)
        
        self.assetsDir = os.path.join(projectpath, "docs", "assets")
        if not os.path.exists(self.assetsDir):
            self.assetsDir = ""
        

    def _collectLines(self, eltEvent):
        lines = []
        for action in eltEvent.findall("action"):
            actID = -1
            actKind = -1
            for id in action.findall("id"):
                actID = id.text
            for kind in action.findall("kind"):
                actKind = kind.text
            if actID == "603" and actKind == "7": # code block
                argumentElt = action.find("arguments")
                for argument in argumentElt:
                    stringElt = argument.find("string")
                    text = stringElt.text
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
                            while line.startswith('/'):
                                line = line[1:]
                            lines.append((LT_COMMENT, line))
                        elif line[0:2] == "/*":
                            while line.startswith("*"):
                                line = line[1:]
                            lines.append((LT_COMMENT, line[0:-2]))
                        else:
                            var = VarModel()
                            var.name = m.group(1)
                            lines.append((LT_VAR, (var)))
                            var.createValue = m.group(2).strip()
                            if m.group(5) != None:
                                lines.append((LT_POSTCOMMENT, m.group(5)))
                        prev = m.end()
            lines.append((LT_SEP, "---- action separator ----"))
        return lines
