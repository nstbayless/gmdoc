import shutil
import os

def copyReplaceDirectory(src, dst):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)

class BuildDoc:
    def __init__(self, docModel, buildPath):
        self.docModel = docModel
        self.buildPath = buildPath

    def makePage(self, file, html, title = ""):
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
        _html += """<div class="row no-gutters">\n"""
        _html += """
            <div class="col-sm-3 col-sm-push-9">
				<h2>Flea</h2>
				<img class="centre" src="https://vignette.wikia.nocookie.net/megaman/images/8/86/Mm1fleasprite.png/revision/latest?cb=20110621041125" alt="">
				<button data-toggle="collapse" data-target="#inGame"><h2>In-Game Information</h2></button>
				<div id="inGame" class="collapse in">
					<div>
						<h3 class="alt">Points:</h3>
						<div>300</div>
					</div>
					<div>
						<h3 class="alt">HP:</h3>
						<div>1</div>
					</div>
					<div>
						<h3 class="alt">Attack Damage:</h3>
						<div>2</div>
					</div>
					<div>
						<h3 class="alt">Weakness:</h3>
						<div><a href="/wiki/Mega_Buster" title="Mega Buster">Mega Buster</a></div>
					</div>
				</div>
				<button data-toggle="collapse" data-target="#series"><h2>Series Information</h2></button>
				<div id="series" class="collapse in">
					<div>
						<h3 class="alt">Filler item:</h3>
						<div>Filler text</div>
						<h3 class="alt">Filler item:</h3>
						<div>Filler text</div>
						<h3 class="alt">Filler item:</h3>
						<div>Filler text</div>
						<h3 class="alt">Filler item:</h3>
						<div>Filler text</div>
					</div>
				</div>
			</div>"""
        _html += """<div class="col-sm-9 col-sm-pull-3">"""
        _html += html
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
        
        # Code-scraped description and defaults
        html += "<h2> Description </h2>\n" + \
            "<p>" + object.docText + "</p>\n"
        varTableName = "Variables"
        varObjectSource = object
        while varObjectSource != None:
            html += "<h2> " + varTableName + " </h2>\n" + \
            "<table><tr><th>Name</th><th>Value</th><th>Description</th></tr>"
            anyDifferent = False
            ccExists = False
            for var in varObjectSource.vars:
                if var.baseObject != varObjectSource:
                     continue
                myVar = object.getVariable(var.name)
                isDifferent = False
                differenceMarker = ""
                if myVar.createValue != var.createValue
                    isDifferent = True
                    anyDifferent = True
                    differenceMarker = " <i>(*)</i>"
                varname = var.name
                if "cc" in var.flags:
                    ccExists = True
                    varname = "<b>" + "</b>"
                html += "<tr><td>" + varname + "</td><td>" + myVar.createValue + differenceMarker + "</td><td>" + myVar.docText + "</td></tr>\n"
            html += "</table>\n"
            if anyDifferent:
                html += "<p><i>* value is modified from the default for " + varObjectSource.name + ".<i></p>"
            if ccExists:
                html += "<p><i>variable names in <b>bold</b> are safe to set in creation code.<i></p>"
            # setup next iteration
            varObjectSource = self.docModel.getObject(varObjectSource.parentName)
            if varObjectSource != None:
                varTableName = "Inherited from " + varObjectSource.name
            
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
