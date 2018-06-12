import os

def getPathComponents(path):
    pathComps = []
    while len(path) > 0:
        (path, x) = os.path.split(path)
        pathComps.append(x)
    return pathComps

def getJoinedPath(components):
    return reduce(os.path.join, components)

def getRelativeNetPath(src, dst):
    pcSrc = getPathComponents(src)
    pcDst = getPathComponents(dst)
    commonPrefix = []
    while True:
        if len(pcSrc) == 0:
            break
        if len(pcDst) == 0:
            break
        if pcSrc[0] != pcDst[0]:
            break
        commonPrefix = pcSrc[0]
        pcSrc = pcSrc[1:]
        pcDst = pcDst[1:]
    return "/".join((['..'] * (len(pcSrc) - 1)) + pcDst)