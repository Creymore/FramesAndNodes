import math
import os
import uuid
from collections import Counter
import FreeCAD as App  # ty:ignore[unresolved-import]

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

    safe_prefix = str(prefix).strip() or "FramesAndKnots"
    file_name = f"{safe_prefix}_{uuid.uuid4().hex}.FCStd"
    file_path = os.path.join(temp_dir, file_name)

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
def FindBinder(Body):
    Features = Body.Group

    for i in range(len(Features)):
        Feature = Features[i]
        if Feature.TypeId == 'PartDesign::SubShapeBinder':
            return Feature
    print("No Binder in Body")
    return False
