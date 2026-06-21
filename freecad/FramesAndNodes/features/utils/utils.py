from xmlrpc.client import boolean
import math
import os
import uuid
from collections import Counter
import FreeCAD as App  # ty:ignore[unresolved-import]

def IsOpposite(V1,V2,tol = 1e-6)->bool:
    C = abs(V1.getAngle(V2) - math.pi)
    if C < tol:
        return True
    else:
        return False

def IsSame(V1,V2,tol=1e-6)->bool:
    C = abs(V1.getAngle(V2))
    if C < tol:
        return True
    else:
        return False

def roundVector(vec,places=6):
    return App.Vector(round(vec.x,places),round(vec.y,places),round(vec.z,places))

def isFCfile(path)->bool:
    if str(path).endswith(".FCStd"):
        return True
    return False

def getDirection(edge):
    return (edge.Vertexes[0].Point - edge.Vertexes[1].Point).normalize()

def VecToTuple(FreeCADvector):
    return (
        FreeCADvector.x,
        FreeCADvector.y,
        FreeCADvector.z
    )

def copyVec(Vec):
    return App.Vector(
        Vec.x,
        Vec.y,
        Vec.z
    )

def itrToVec(itr):
    return App.Vector(itr[0],itr[1],itr[2])


# Source - https://stackoverflow.com/a/20872750
# Posted by Alex, modified by community. See post 'Timeline' for change history
# Retrieved 2026-06-21, License - CC BY-SA 4.0
def Most_Common(lst):
    data = Counter(lst)
    return data.most_common(1)[0][0]

def delete_object_and_contents(obj,doc):
    stack = [obj]
    order = []
    seen = set()

    while stack:
        current = stack.pop()
        name = current.Name
        if name in seen:
            continue

        seen.add(name)
        order.append(name)
        group = getattr(current, "Group", None)
        if group:
            stack.extend(group)

    for name in reversed(order):
        if doc.getObject(name) is not None:
            doc.removeObject(name)

def convert_to_tuple(element):
    if isinstance(element, list):
        return tuple(convert_to_tuple(e) for e in element)
    return element

def saveDocumentToCache(doc, prefix="FramesAndKnots")->str:
    '''
    Save a FreeCAD document temporarily into the user's cache directory.

    Input:
        doc: FreeCAD document object
        prefix: optional filename prefix for the temporary file

    Returns:
        str: absolute path to the cached .FCStd file
    '''
    cache_dir = App.getUserCachePath()
    temp_dir = os.path.join(cache_dir, "FramesAndKnots")
    os.makedirs(temp_dir, exist_ok=True)

    pathexists = True
    n = 0
    while pathexists:
        safe_prefix = str(prefix).strip() 
        file_name = f"{safe_prefix}_{uuid.uuid4().hex}.FCStd"
        file_path = os.path.join(temp_dir, file_name)
        if not os.path.exists(file_path) or n > 10:
            pathexists = False
        n = n + 1

    doc.saveAs(file_path)
    return file_path

def deleteDocumentFromCache(path)->bool:
    '''
    Delete a cached FreeCAD document created in the user's cache directory.

    Input:
        path: absolute path to the cached .FCStd file

    Returns:
        bool: True if the file was deleted, False otherwise
    '''
    if not path:
        return False

    normalized_path = os.path.abspath(path)
    cache_root = os.path.abspath(os.path.join(App.getUserCachePath(), "FramesAndKnots"))

    if not normalized_path.startswith(cache_root):
        App.Console.PrintError("Refused to delete file outside the FramesAndKnots cache directory.\n")
        return False

    if not os.path.exists(normalized_path):
        return False

    os.remove(normalized_path)
    return True


# Maybe this Belongs in Profile Logic section
def FindBinders(Body):
    Features = Body.Group
    Binders = []
    for Feature in Features:
        if Feature.TypeId == 'PartDesign::SubShapeBinder':
            Binders.append(Feature)
    return Binders

def FindBoolean(Body):
    Features = Body.Group
    Booleans = []
    for Feature in Features:
        if Feature.TypeId == 'PartDesign::Boolean':
            Booleans.append(Feature)
    return Booleans

def FindBinders2(Body):
    booleans = FindBoolean(Body)
    Binders = []
    if len(booleans) == 0:
        Binders = FindBinders(Body)
    for bo in booleans:
        Binders.append(FindBinders(bo)[0])
    # print(f"Binders found:{Binders}")
    return Binders

def FindLinks(doc):
    return doc.findObjects('App::Link')

def TransformToGlobalPlacement(P):
    target = P
    sub =""

    root = P
    while True:
        parent = root.getParentGeoFeatureGroup()
        if parent is None:
            break
        root = parent

    placement =  P.getGlobalPlacementOf(target,root,sub)
    return placement