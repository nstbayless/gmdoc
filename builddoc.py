import shutil
import os
import util
import importlib.util
import glob

def copyReplaceDirectory(src, dst):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)

def sanitizeAnchor(str):
    str = str.replace(" ","") \
              .replace("\n","") \
              .replace("\t","") \
              .replace("\r","")
    if str == "":
        return "A"
    return str

class SidebarInfo:
    def __init__(self, object):
        self.object = object
        self.title = object.name
        self.imagePath = ""
        if object.spriteName != "":
            self.imagePath = util.getRelativeNetPath("objects/"+object.name+".html","assets/images/objects/" + object.spriteName + ".png")
        self.collapseTitles = []
        self.collapseInfo = []
        self.enabled = False
        if (self.object.sidebarScript != ""):
            sidebar = self
            exec(open(self.object.sidebarScript, "r").read())
            
        
    def build(self):
        html = """<div class="col-sm-3 col-sm-push-9">\n"""
        html += "<h2>" + self.title + "</h2>"
        if self.imagePath != "":
            html += '<img class = "centre" src="' + self.imagePath + '" alt="' + self.object.spriteName + '">\n'
        i = -1
        for title in self.collapseTitles:
            i+=1
            html += '<button data-toggle="collapse" data-target="#' + sanitizeAnchor(title) + '"><h2>' + title + '</h2></button>\n'
            html += '<div id="' + sanitizeAnchor(title) + '" class="collapse in">\n'
            for field, value in self.collapseInfo[i]:
                html += '<div><h3 class="alt">' + field + '</h3>\n'
                html += '<div>' + value + '</div>'
                html += '  </div>'
            html += ' </div>'
        html += '</div>'
        return html

class BuildDoc:
    def __init__(self, docModel, buildPath):
        self.docModel = docModel
        self.buildPath = buildPath

    def makePage(self, file, html, title = "", sidebar = None):
        pathDepth = file.count("/")
        pathPrepend = "../" * pathDepth
        _html = "<html>"
        if title != "":
            _html  += '<title>' + title+ '</title>'
        # bootstrap
        _html += """<!-- Latest compiled and minified CSS -->
		<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css">
		<!-- jQuery library -->
		<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.3.1/jquery.min.js"></script>
		<!-- Latest compiled JavaScript -->
		<script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js"></script>\n"""
        _html += '<link rel="stylesheet" href="' + os.path.join(pathPrepend , 'assets/styles/default.css') + '" type="text/css">\n'
        _html += '<body><div class="page">\n'
        if sidebar != None:
            _html += """<div class="row no-gutters">\n"""
            _html += sidebar.build()
            _html += """<div class="col-sm-9 col-sm-pull-3">"""
        _html += html
        if sidebar != None:
            _html += "</div></div>"
        if self.docModel.footerMessage != "":
            _html += "\n<h5>" + self.docModel.footerMessage + "</h5>"
        _html += "\n</body></div></html>"
        with open(os.path.join(self.buildPath, file), "w") as f:
            f.write(_html)
    
    def mkdir(self, subDir):
        dir = os.path.join(self.buildPath, subDir)
        if not os.path.exists(dir):
            os.makedirs(dir)

    def buildInheritanceTree(self, object):
        if len(object.children) == 0:
            return ""
        html = "<ul>\n"
        for child in object.children:
            html += "<li>"
            html += '<a href="' + child.name + '.html">' + child.name
            html += "</li>\n"
            html += self.buildInheritanceTree(child)
        html += "</ul>"
        return html

    def buildPage(self, page):
        file = page.path
        print("    " + file)
        self.makePage(file, page.contents, page.title)

    def buildObject(self, object):
        # sidebar
        sidebar = None
        if object.sidebarScript != "":
            sidebar = SidebarInfo(object)
            if not sidebar.enabled:
                sidebar = None
        
        # main html
        file = "objects/" + object.name + ".html"
        # name (header)
        html = "<h1>" + object.name + "</h1>\n";
        
        # Parents
        if object.parent == None:
            html += "<p><i>This object has no parent.</i></p>\n"
        else:
            hObj = object
            hhtml = ""
            while hObj != None:
                hhtml = (' <b>&gt;</b> ' if hObj.parent != None else "") + '<a href="' + hObj.name + '.html">' + hObj.name + "</a>" + hhtml
                hObj = hObj.parent
            html += hhtml + "\n"
        
        # Code-scraped description and defaults
        html += "<h2> Description </h2>\n" + \
            "<p>" + object.docText + "</p>\n"
        varTableName = "Variables"
        varObjectSource = object
        while varObjectSource != None:
            html += "<h2> " + varTableName + " </h2>\n" + \
            "<table class=centre><tr><th>Name</th><th>Value</th><th>Description</th></tr>"
            anyDifferent = False
            ccExists = False
            for var in varObjectSource.vars:
                if var.baseObject != varObjectSource:
                    continue
                myVar = object.getVariable(var.name)
                isDifferent = False
                differenceMarker = ""
                if myVar.createValue != var.createValue:
                    isDifferent = True
                    anyDifferent = True
                    differenceMarker = " <i>(*)</i>"
                varname = var.name
                if "cc" in var.flags:
                    ccExists = True
                    varname = "<span class=\"cc\">" + varname + "</span>"
                html += "<tr><td>" + varname + "</td><td>" + myVar.createValue + differenceMarker + "</td><td>" + myVar.docText + "</td></tr>\n"
            html += "</table>\n"
            if anyDifferent:
                html += "<p><i>* value is modified from the default for " + varObjectSource.name + ".<i></p>"
            if ccExists:
                html += "<p><i>variable names in <span class=\"cc\">bold</span> are safe to set in creation code.<i></p>"
            # setup next iteration
            varObjectSource = self.docModel.getObject(varObjectSource.parentName)
            if varObjectSource != None:
                varTableName = "Inherited from " + varObjectSource.name
            
        if len(object.children) > 0:
            html += "<h2> Descendents of " + object.name + " </h2>"
            html += self.buildInheritanceTree(object)
        self.makePage(file, html, object.name, sidebar)
    
    def buildListingsHelper(self, assetTree):
        html = "<b>" + assetTree.name + "</b>\n<ul>"
        for subTree in assetTree.children:
            if subTree.isNode:
                object = self.docModel.getObject(subTree.name)
                if object != None:
                    html += '<li><a href="objects/' + object.name + '.html">' + object.name + '</a></li>\n'
                else:
                    html += '<li>' + subTree.name + ' (missing)</li>'
            else:
                html += "<li>" + self.buildListingsHelper(subTree) + "</li>"
        return html + '</ul>'
    
    def buildListings(self):
        html = "<h1> Objects Listing </h1><h3>All Objects:</h3>"
        html += self.buildListingsHelper(self.docModel.assetTreeObjects)
        self.makePage("objectsListing.html", html, "Objects Listing")
    
    def copySpriteFiles(self):
        files = glob.glob(os.path.join(self.docModel.projectPath, "sprites", "images", "*_0.png"))
        for file in files:
            fileNoNumber = os.path.basename(file[:-6] + ".png")
            shutil.copyfile(file, os.path.join(self.buildPath, "assets", "images", "objects", fileNoNumber))
    
    def build(self):
        print("Building...")
        self.mkdir("objects")
        self.mkdir("scripts")
        self.mkdir("pages")
        if self.docModel.assetsDir != "":
            print("  Copying assets")
            copyReplaceDirectory(self.docModel.assetsDir, os.path.join(self.buildPath, "assets"))
            self.mkdir(os.path.join("assets", "images"))
            self.mkdir(os.path.join("assets", "images", "objects"))
            print("  Copying sprites")
            self.copySpriteFiles()
        print("  Adding .gitignore")
        with open(os.path.join(self.buildPath, ".gitignore"), "w") as f:
            f.write("*")
        print("  building objects")
        for object in self.docModel.objects:
            self.buildObject(object)
        print("  building pages")
        for page in self.docModel.pages:
            self.buildPage(page)
        print("  building listings")
        self.buildListings()

def build(docModel, buildPath):
    bd = BuildDoc(docModel, buildPath)
    bd.build()
