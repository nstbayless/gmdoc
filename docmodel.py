# document model

import xml.etree.ElementTree as ET
import glob
import os
import re
import copy
import markdown
import markdown.extensions.extra
from constants import *
import json
from datetime import datetime

buildDate = datetime.utcnow().strftime("%Y-%m-%d %H:%M")

builtIn = {}

with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "gms2_map.json"), "r") as gms2Map:
    builtIn = json.load(gms2Map)

reLines = re.compile("//.*?$|/\*.*?\*/|^\s*([a-zA-Z_0-9]+)\s*=((.*?)(//(.*))?$)", re.MULTILINE)
reFlag = re.compile("^\s*@(.+?)\\b")

class PageModel:
    def __init__(self):
        content = ""
        path = ""

class VarModel:
    def __init__(self):
        self.name = ""
        self.docText = ""
        self.createValue = ""
        self.baseObject = None
        self.flags = []
    
    def __repr__(self):
        flagstr = ""
        if len(self.flags) > 0:
           flagstr = " [@" + ",@".join(self.flags) + "]"
        return self.name + flagstr + " = " + self.createValue + ": " + self.docText

class NodeTree:
    def __init__(self, name, isNode):
        self.name = name
        self.isNode = isNode
        self.children = []
        self.parent = None

    def getPath(self):
        str = ""
        if self.parent != None:
            str = self.parent.getPath()
        str += self.name
        if not self.isNode:
            str += "/"
        return str

class ObjectModel:
    def __init__(self, dm):
        self.name = "<undefined>"
        self.spriteName = ""
        self.parentName = ""
        self.parent = None
        self.docText = ""
        self.vars = [] # variables
        self.children = []
        self.assetPath = ""
        self._varnames = []
        self._docmodel = dm
        self.sidebarScript = ""
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
            self._linked = True
            self.parent = self._docmodel.getObject(self.parentName)
            if self.parent != None:
                self.parent.linkParent()
                for var in self.parent.vars:
                    foundVar = False
                    for myVar in self.vars:
                        if var.name == myVar.name:
                            foundVar = True
                            myVar.baseObject = var.baseObject
                            if len(myVar.docText.strip()) > 0:
                                myVar.docText = var.docText + "</p><p>Notes for " + self.name + ":</p><p>\n" + myVar.docText
                            else:
                                myVar.docText = var.docText
                    if not foundVar:
                        self.vars.append(copy.copy(var))
            

    def getVariable(self, varName):
        for var in self.vars:
            if var.name == varName:
                return var
        if self.parentName == "":
            return None
        parent = self._docmodel.getObject(self.parentName)
        if parent != None:
            return parent.getVariable(varName)

class DocModel:
    def __init__(self):
        self.objects = []
        self.scripts = []
        self.pages = []
        self.assetTreeObjects = NodeTree("objects", False)
        self.assetTreeScripts = NodeTree("scripts", False)
        
        # cache
        self.topLevelObjects = []
        
        # style
        self.footerMessage = ""
        self.assetsDir = ""
        
        self.projectPath = ""
        self.docPath = ""
        
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
    
    def parseDocText(self, lines, flagBuffer = []):
        text = ""
        for l in lines:
            l1 = l[1].strip()
            # parse @flags
            while True:
               m = reFlag.search(l1)
               if m == None:
                   break
               flag = m.group(1)
               l1 = l1[m.end(1):]
               if flag not in flagBuffer:
                   flagBuffer.append(flag)
            text += "<p>" + l1 + "</p>\n"
        return self.getMarkdown(text.strip())
    
    def getMarkdown(self, md):
        html = markdown.markdown(md, extensions=['markdown.extensions.extra'])
        html = html.replace("%WIKIBUILDDATE%", buildDate + " (GMT)")
        return html
    
    # recursively find sidebar script for object and all children
    def findObjectSidebarInfo(self, object):
        sidebarFile = os.path.join(self.docPath, "objects", "sidebars", object.name + ".py")
        if os.path.isfile(sidebarFile):
            object.sidebarScript = sidebarFile
        for child in object.children:
            child.sidebarScript = object.sidebarScript
            self.findObjectSidebarInfo(child)
    
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
        if obj.spriteName == "<undefined>":
            obj.spriteName = ""
        eltParentName = root.find("parentName")
        obj.parentName = eltParentName.text
        if obj.parentName == "<undefined>":
            obj.parentName = ""
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
                    
                    j = 0
                    while j <= i:
                        j+=1
                        if lines[i-j][0] != LT_COMMENT:
                            j -= 1
                            break
                        
                    proposedDocIDX = i-j
                    var.docText = self.parseDocText(lines[i-j:i], var.flags)
                    if len(lines) > i + 1:
                        if lines[i+1][0] == LT_POSTCOMMENT:
                            proposedDocIDX = i
                            var.docText = self.parseDocText([lines[i+1]], var.flags)
                    if var.name not in obj._varnames and var.name not in builtIn:
                        obj._varnames.append(var.name)
                        var.baseObject = obj
                        obj.vars.append(var)
                if not docTextParsed:
                    docTextParsed = True
                    obj.docText = self.parseDocText(lines[0:proposedDocIDX])
        
        self.objects.append(obj)
        if obj.parentName == "":
            self.topLevelObjects.append(obj)

    def parseAssetsScript(self, scriptElt, assetTree):
        for subElt in scriptElt:
            if subElt.tag == "scripts":
                subTree = NodeTree(subElt.attrib["name"], False)
                assetTree.children.append(subTree)
                subTree.parent = assetTree
                self.parseAssetsScript(subElt, subTree)
            if subElt.tag == "script":
                assetTree.children.append(NodeTree(subElt.text[len("scripts/"):], True))

    def parseAssetsObject(self, objectElt, assetTree):
        for subElt in objectElt:
            if subElt.tag == "objects":
                subTree = NodeTree(subElt.attrib["name"], False)
                assetTree.children.append(subTree)
                subTree.parent = assetTree
                self.parseAssetsObject(subElt, subTree)
            if subElt.tag == "object":
                objectName = subElt.text[len("objects/"):]
                object = self.getObject(objectName)
                if object == None:
                    print("Warning: " + objectName + " referenced in .project.gmx but not found on disk.")
                    continue
                object.assetPath = assetTree.getPath()
                assetTree.children.append(NodeTree(objectName, True))

    def parseProjectFile(self, file):
        tree = ET.parse(file)
        assets = tree.getroot()
        if assets.tag != "assets":
            assets = assets.find("assets")
        self.parseAssetsScript(assets.find("scripts"), self.assetTreeScripts)
        self.parseAssetsObject(assets.find("objects"), self.assetTreeObjects)

    def parsePage(self, pageFile):
        with open(pageFile, 'r') as file:
            dstPath = os.path.basename(pageFile)
            dstPath = os.path.splitext(dstPath)[0]
            if dstPath != "index":
                dstPath = "pages/" + dstPath
            dstPath += ".html"
            pageModel = PageModel()
            pageModel.path = dstPath
            pageModel.contents = self.getMarkdown(open(pageFile, "r").read())
            pageModel.title = "~"
            self.pages.append(pageModel)

    def parseProject(self, projectpath, docpath):
        print("Parsing project...")
        self.projectPath = projectpath
        self.docPath = docpath
        print("  Obtaining file lists")
        objectFiles = glob.glob(os.path.join(projectpath, "objects/*.object.gmx"))
        scriptFiles = glob.glob(os.path.join(projectpath, "scripts/*.gml"))
        projectFile = glob.glob(os.path.join(projectpath, "*.project.gmx"))[0]
        pageFiles = glob.glob(os.path.join(docpath, "pages/*.md"))

        # parse objects
        print("  Parsing objects")
        for objectFile in objectFiles:
            self.parseObject(objectFile)
        print("  Linking object inheritance")
        for object in self.objects:
            object.linkParent()
            if object.parent != None:
                object.parent.children.append(object)
        print("  Finding sidebar info")
        defaultSidebarFile = os.path.join(self.docPath, "objects", "sidebars", ".py")
        if not os.path.isfile(defaultSidebarFile):
            defaultSidebarFile = ""
        for object in self.topLevelObjects:
            object.sidebarScript = defaultSidebarFile
            self.findObjectSidebarInfo(object)
        
        # parse pages
        print("  Parsing pages")
        for page in pageFiles:
            self.parsePage(page)

        print("  Parsing .project.gmx file")
        self.parseProjectFile(projectFile)
        
        self.assetsDir = os.path.join(docpath, "assets")
        if not os.path.exists(self.assetsDir):
            self.assetsDir = ""
        
    def cleanCreateValue(self, str):
        if str == None:
            return ""
        str = str.strip()
        if str.endswith(";"):
            str = str[:-1]
        return str

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
                            var.createValue = self.cleanCreateValue(m.group(3))
                            if m.group(5) != None:
                                lines.append((LT_POSTCOMMENT, m.group(5)))
                        prev = m.end()
            lines.append((LT_SEP, "---- action separator ----"))
        return lines
