import FreeCAD as App  # ty:ignore[unresolved-import]
import FreeCADGui as Gui  # ty:ignore[unresolved-import]

from .ProfileLogic import isValidFrameMember
from .KnotLogic import getAttachmentEdge, ReadKnotsFromFrameMember
from .utils.utils import Most_Common

test1 = "(App.getDocument('TestFrame').getObject('Box'),['Edge2',])"
# return: Edge2
test2 ="(App.getDocument('TestFrame').getObject('Box'),['Edge2','Edge1',])"
# return: Edge2, Edge1
test3 = "(App.getDocument('TestFrame').getObject('Body005'),['Boolean011.;#2ae0b:57;:M#32446;RFI;:H1581:d,E;:H1580,E.Edge94',])"
# return: Edge of Framemember attachment
test4 = "(App.getDocument('TestFrame').getObject('Body005'),['Boolean011.;#2ae6b:51;:M#3244a;RFI;:H1581:d,E;:H1580,E.Edge192','Boolean011.;#2ae0d:55;:M#32447;RFI;:H1581:d,E;:H1580,E.Edge96','Boolean011.;#2ae83:21;:M#3249f;RFI;:H1581:d,F;:H1580,F.Face2',])"
# return: Edge of Framemember attachment
test5 = "(App.getDocument('Unnamed').getObject('Part001'),['Part.Box.Edge2',])"

def getThisFromSelection(This)->tuple:
    '''
    Edge => Edge
    return: tuple((Obj,'Edge...'))
    '''
    results = []
    Selection = Gui.Selection.getCompleteSelection()
    for Sel in Selection:
        Obj = Sel.Object
        names = Sel.SubElementNames
        # Subs = Sel.SubObjects
        for name in names:
            if This in name:
                result = (Obj,name)
                results.append(result)
    
    return tuple(results)


def getEdgesFromSelection()->tuple:
    '''
    Edge => Edge
    return: tuple((Obj,'Edge...'))
    '''
    results = []
    Selection = Gui.Selection.getCompleteSelection()
    for Sel in Selection:
        Obj = Sel.Object
        names = Sel.SubElementNames
        # Subs = Sel.SubObjects
        for name in names:
            if "Edge" in name:
                result = (Obj,name)
                results.append(result)
    
    return tuple(results)

def getEdgesFrameMembersFromSelcection()->tuple:
    '''
    From Gui.Selection This function returns a tuple((obj,Edge),(obj1,Edge1),...)
    It follows this Logic:
    Obj => All Edges TODO
    Edge => Edge
    Face => Edges that belong to that face TODO
    Vertex => Edges that end in set Vertex TODO
    ProfileBody / Geometrie of a ProfileBody => added to tuple of Profiles
    If there are more Profiles then edges selected => tuple(Profile,Profile1,..)
    '''
    doc = App.ActiveDocument
    Edges = getEdgesFromSelection()
    FrameMembers = set(getFrameMembersFromSelection())
    EdgeResults = set()
    for Edge in Edges:
        print(Edge)
        obj = Edge[0]
        # print(obj.Name)
        typ = obj.TypeId
        # print(typ)
  
        if typ.startswith('PartDesign::'):
            parent = obj.getParentGeoFeatureGroup()
        else:
            EdgeResults.add(Edge)
            continue

        if isValidFrameMember(parent) and doc == parent.Document:
            print(f"IsFrameMember:{parent.Name} | {parent.Label}")
            FrameMembers.add(parent)
            continue
        else:
            EdgeResults.add(Edge)
            continue

    if len(FrameMembers) >= len(EdgeResults):
        print(FrameMembers)
        return tuple(FrameMembers)
    else:
        print(EdgeResults)
        return tuple(EdgeResults)





def getFrameMembersFromSelection()->tuple:
    '''
    From Gui.Selection this function returns a tuple(ProfileBody, ProfileBody1, ...)

    It accepts direct FrameMember selections as well as face, edge, and vertex
    selections on geometry that belongs to a FrameMember.
    '''
    doc = App.ActiveDocument
    selection = Gui.Selection.getSelectionEx("",0)
    results = set()
    for sel in selection:
        fullName = sel.FullName
        split = fullName.split("'")
        for sub in split:
            subsplit = sub.split(".")
            # print(f"subspilt:{subsplit}")
            for su in reversed(subsplit):
                # print(f"su: {su}")
                Link = "Link" in su
                Body = "Body" in su
                if Link or Body:
                    # print(f"Obj:{su}")
                    obj = doc.getObject(su) # This does not work if it is a Link in a Link, but should not be anyway
                    testobj = obj
                    if Link :
                        testobj = obj.getLinkedObject()
                    if not isValidFrameMember(body=testobj):
                        continue
                    results.add(obj)
                    break
    return tuple(results)
 

def getKnotFromFrameMembers()->tuple:
    '''
    This Function Return an Inserted Knot that has the selected Frame Members as a part of its FrameMember0..n Property

    Returns: tuple(Knot)

    '''
    FrameMembers = getEdgesFrameMembersFromSelcection()
    Nodes = list()
    FoundNodes = []
    if len(FrameMembers) < 2:
        # App.Console.PrintNotification("Not enought FrameMembers Selected, unable to determine a Node | Please select more FrameMembers ") #They are annoying
        return tuple()
    for FrameMember in FrameMembers:
        Nodes.extend(ReadKnotsFromFrameMember(FrameMember))
        print(Nodes)
    if len(Nodes) == 0:
        # App.Console.PrintNotification("No Node has been inserted") #They are annoying
        return tuple()
    FoundNodes.append(Most_Common(Nodes))
    print(FoundNodes)
    return tuple(FoundNodes)