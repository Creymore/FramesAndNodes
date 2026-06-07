from xmlrpc.client import boolean
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


def TransformIntoSharedCoordinates(P1,P2):
    '''
    P1 : Obj in a coordinate system with Placement
    P2 : Obj in a coordinate system with Placement

    returns (M1,M2)

    M1 : Matrix that Transforms P1 to its Placement in the First common Parent coordinate system
    M2 : Matrix that Transforms P2 to its Placement in the First common Parent coordinate system
    
    There are an unknown amout of Parent and grand parent an so on coordinate system for each P1 and P2 until the first common parent
    '''
    def parent(obj):
        if hasattr(obj, "getParentGeoFeatureGroup"):
            parent_obj = obj.getParentGeoFeatureGroup()
            if parent_obj is not None:
                return parent_obj
        for parent_obj in getattr(obj, "InList", ()):
            if hasattr(parent_obj, "Placement"):
                return parent_obj
        return None

    def ancestors(obj):
        chain = []
        seen = set()
        while obj is not None:
            obj_id = id(obj)
            if obj_id in seen:
                break
            seen.add(obj_id)
            chain.append(obj)
            obj = parent(obj)
        return chain

    def placement_to_ancestor(obj, stop):
        placement = App.Placement()
        while obj is not stop:
            if hasattr(obj, "Placement"):
                placement = obj.Placement.multiply(placement)
            print(f"{obj.Name} Placement: {placement}")
            obj = parent(obj)
        return placement.toMatrix()

    common = None
    chain2_ids = {id(obj) for obj in ancestors(P2)}
    for obj in ancestors(P1):
        if id(obj) in chain2_ids:
            common = obj
            break
    
    print(common.Name)  # ty:ignore[unresolved-attribute]

    return (
        placement_to_ancestor(P1, common),
        placement_to_ancestor(P2, common)
    )

def TransformToGlobalPlacement(P1,P2):
    '''
    P1 : Obj in a coordinate system with Placement
    P2 : Obj in a coordinate system with Placement

    returns (M1,M2)

    M1 : Matrix that Transforms P1 to its Placement in the Global coordinate system
    M2 : Matrix that Transforms P2 to its Placement in the Gloabal coordinate system
    
    '''
    def parent(obj):
        if hasattr(obj, "getParentGeoFeatureGroup"):
            parent_obj = obj.getParentGeoFeatureGroup()
            if parent_obj is not None:
                return parent_obj
        for parent_obj in getattr(obj, "InList", ()):
            if hasattr(parent_obj, "Placement"):
                return parent_obj
        return None

    def placement_to_global(obj):
        get_global_placement = getattr(obj, "getGlobalPlacement", None)
        if get_global_placement is not None:
            try:
                return get_global_placement().toMatrix()
            except Exception:
                pass

        placement = App.Placement()
        seen = set()
        while obj is not None:
            obj_id = id(obj)
            if obj_id in seen:
                break
            seen.add(obj_id)
            if hasattr(obj, "Placement"):
                placement = obj.Placement.multiply(placement)
            obj = parent(obj)
        return placement.toMatrix()

    return (
        placement_to_global(P1),
        placement_to_global(P2)
    )
