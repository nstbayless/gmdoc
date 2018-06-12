import shutil
import os
import util
import importlib.util

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
        self.imagePath = util.getRelativeNetPath("objects/"+object.name+".html","assets/images/objects/" + object.spriteName + ".png")
        self.collapseTitles = []
        self.collapseInfo = []
        if (self.object.sidebarScript != ""):
            exec(open(self.object.sidebarScript, "r").read())
        
    def build(self):
        html = """<div class="col-sm-3 col-sm-push-9">\n"""
        html += "<h2>" + self.title + "</h2>"
        html += '<img class = "centre" src="' + self.imagePath + '" alt="' + self.object.spriteName + '">\n'
        for title in self.collapseTitles:
            html += '<button data-toggle="collapse" data-target="#' + sanitizeAnchor(title) + '"><h2>' + title + '</h2></button>\n'
            html += '<div id="' + sanitizeAnchor(title) + '" class="collapse in">\n'
            for field, value in self.collapseInfo:
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
        _html += "<body>\n"
        if sidebar != None:
            _html += """<div class="row no-gutters">\n"""
            _html += sidebar.build()
            _html += """<div class="col-sm-9 col-sm-pull-3">"""
        _html += html
        if sidebar != None:
            _html += "</div></div>"
        if self.docModel.footerMessage != "":
            _html += "\n<h5>" + self.docModel.footerMessage + "</h5>"
        _html += "\n</body></html>"
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

    def buildObject(self, object):
        # sidebar
        sidebar = None
        if object.sidebarScript != "":
            sidebar = SidebarInfo(object)
        
        # main html
        file = os.path.join("objects", object.name + ".html")
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
        
        # Code-scraped description
        html += "<h2> Description </h2>\n" + \
            "<p>" + object.docText + "</p>\n"
        varTableName = "Variables"
        varObjectSource = object
        while varObjectSource != None:
            html += "<h2> " + varTableName + " </h2>\n" + \
            "<table><tr><th>Name</th><th>Description</th></tr>"
            for var in varObjectSource.vars:
                html += "<tr><td>" + var.name + "</td><td>" + var.docText + "</td></tr>\n"
            varObjectSource = self.docModel.getObject(varObjectSource.parentName)
            if varObjectSource != None:
                varTableName = "Inherited from " + varObjectSource.name
            html += "</table>\n"
            
        if len(object.children) > 0:
            html += "<h2> Descendents of " + object.name + " </h2>"
            html += self.buildInheritanceTree(object)
        self.makePage(file, html, object.name, sidebar)
    
    def buildObjectsRoot(self):
        html = "<h1> Objects Listing </h1><h3>All Objects:</h3>"
        for object in self.docModel.objects:
            html += '<p><a href="objects/' + object.name + '.html">' + object.name + '</a></p>'
        self.makePage("objectsListing.html", html, "Objects Listing")
    
    def build(self):
        self.mkdir("objects")
        self.mkdir("scripts")
        self.mkdir("pages")
        if self.docModel.assetsDir != "":
            copyReplaceDirectory(self.docModel.assetsDir, os.path.join(self.buildPath, "assets"))
        with open(os.path.join(self.buildPath, ".gitignore"), "w") as f:
            f.write("*")
        for object in self.docModel.objects:
            self.buildObject(object)
        self.buildObjectsRoot()

def build(docModel, buildPath):
    bd = BuildDoc(docModel, buildPath)
    bd.build()