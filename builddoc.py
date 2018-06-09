import os

class BuildDoc:
    def __init__(self, docModel, buildPath):
        self.docModel = docModel
        self.buildPath = buildPath

    def makePage(self, file, html, title = ""):
        pathDepth = file.count("/")
        pathPrepend = "../" * pathDepth
        _html = ""
        if title != "":
            _html  += '<title>' + title+ '</title>' 
        _html += '<link rel="stylesheet" href="' + os.path.join(pathPrepend , 'styles/default.css') + '" type="text/css">\n'
        _html += "<body>\n"
        _html += html
        if self.docModel.footerMessage != "":
            _html += "\n<h5>" + self.docModel.footerMessage + "</h5>"
        _html += "\n</body>"
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
        
        self.makePage(file, html, object.name)
    
    def buildObjectsRoot(self):
        html = "<h1> Objects Listing </h1><h3>All Objects:</h3>"
        for object in self.docModel.objects:
            html += '<p><a href="objects/' + object.name + '.html">' + object.name + '</a></p>'
        self.makePage("objectsListing.html", html, "Objects Listing")
    
    def build(self):
        self.mkdir("objects")
        self.mkdir("scripts")
        self.mkdir("pages")
        self.mkdir("styles")
        with open(os.path.join(self.buildPath, "styles", "default.css"), "w") as f:
            f.write(self.docModel.css)
        with open(os.path.join(self.buildPath, ".gitignore"), "w") as f:
            f.write("*")
        for object in self.docModel.objects:
            self.buildObject(object)
        self.buildObjectsRoot()

def build(docModel, buildPath):
    bd = BuildDoc(docModel, buildPath)
    bd.build()