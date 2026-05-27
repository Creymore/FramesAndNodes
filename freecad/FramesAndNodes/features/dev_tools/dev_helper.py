
'''
The dev_helper is only supposed to help me Test my work
Non of these Funtions should be used in the Main file in normal opperation
Note to self: ALWAYS close Documents after modefing them with a function
'''
############################### IMPORTS #####################################################
from pathlib import Path
import sys

# Support running this file directly (python App/dev_tools/dev_helper.py)
# and as a module inside the App package.
if __package__ is None or __package__ == "":
    project_root = Path(__file__).resolve().parents[3]
    project_root_str = str(project_root)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)
    from freecad.App.utils.ChatGBTs_utils import (
        print_list,
        convert_vectors_to_list,
        convert_lists_to_vectors,
    )
else:
    from ..utils.ChatGBTs_utils import (
        print_list,
        convert_vectors_to_list,
        convert_lists_to_vectors,
    )

import FreeCAD as App  # ty:ignore[unresolved-import]
import random
import json
import os
import Draft #No worries it works, dispite of "Import "Draft" could not be resolved"  # ty:ignore[unresolved-import]
# import FreeCADGui.Selection

###########################################################################################


def TransformKnot(Knot,axis,angle): # angle in deg
    rot = App.Rotation(axis,angle)
    n = 0
    while n < len(Knot): #Would be more elegant with a for Loop but i dont know how
        V = Knot[n]["Direction"]
        V = rot.multVec(V)
        Knot[n].update({"Direction":V})
        n = n+1
    return(Knot)

def GenerateVector(range=100,step=1):
    x = random.randrange(-range,range,step)
    y = random.randrange(-range,range,step)
    z = random.randrange(-range,range,step)
    return App.Vector(x,y,z)

def GenerateProfile(type="x",angle=0,sym=4):
    Profile = {
        "Direction": GenerateVector(),
        "Offset": App.Vector(0,0,0),
        "Type": type,
        "Rotation":angle,
        "Nsym":sym
    }
    return Profile

def GenerateKnot(proflies=20,type="x",angle=0,sym=4):
    knot = []
    for i in range(proflies):
        knot.append(GenerateProfile())
    return knot

# K = GenerateKnot()
# print(K)

def GenerateKnots(n=2):
    knots = {}
    for i in range(n):
        knots.update({f"Knot{i}":GenerateKnot()})
    return knots

def GenerateKnotPair(Knot):
    angle = random.randrange(-180,180,1)
    axis = GenerateVector()
    transformnedKnot = TransformKnot(Knot,axis,angle)
    return [transformnedKnot,Knot]

def FcVecToVecArray(V):
    v = [
        V.x,
        V.y,
        V.z
    ]
    return v

def VecArrayToFcVec(V):
    v = App.Vector(V[0],V[1],V[2])
    return v

def SaveKnots(knots,dir="freecad/App/dev_tools/DummyKnots.json"):
    knots = convert_vectors_to_list(knots) # Somehow the FreeCAD Json does not like FreeCAD Vector Objects https://github.com/FreeCAD/FreeCAD/issues/25566
    jknots = json.dumps(knots,indent=4)
    with open(dir,"w") as f:
        f.write(jknots)

def LoadKnot(n=0,dir="freecad\App\dev_tools\DummyKnots.json"):
    with open(dir,"r") as f:
        data = json.load(f)
        try:
            data = data[f"Knot{n}"]
            data = convert_lists_to_vectors(data) # Needs converting back https://github.com/FreeCAD/FreeCAD/issues/25566
            return data
        except:
            print(f"Knot{n} does not exsit")
            return False

#-------------------------------------------------------------------------------------------------

def GenerateDocTest(name,BASEPATH,KnotID):

    doc = App.newDocument(name)
    mypart = doc.addObject('App::Part','Part') # Somehow need to make it visibal
    # Gui.getDocument(name).getObject("Part").Visibility = True
    # mypart.addProperty("App::PropertyString", "ThePropertyName", "Subsection", "Description for tooltip")
    mypart.addProperty("App::PropertyString", "KnotID", "KnotInformation", "This is the Knot ID")
    mypart.KnotID = KnotID
    doc.recompute()

    path = f"{BASEPATH}/{name}"
    App.getDocument(name).saveAs(path)

def ReadKnotID(name,BASEPATH):
    path = f"{BASEPATH}/{name}.FCstd"
    if os.path.exists(path):
        open(path)
    else:
        return False
    doc = App.getDocument(name)
    mypart = doc.getObject("Part")
    KnotID = mypart.KnotID
    # print(KnotID)
    return KnotID


def loadBASEPATH(dir="APP/myPC.json"):
    with open(dir,"r") as f:
        data = json.load(f)
    return data

def MakeLine(Vector):
    pl = App.Placement()
    pl.Rotation.Q = (0.0, 0.0, 0.0, 1.0)
    pl.Base = App.Vector(0.0, 0.0, 0.0)
    points = [App.Vector(0.0, 0.0, 0.0), Vector]
    line = Draft.make_wire(points, placement=pl, closed=False, face=True, support=None)
    return line

def makeBody(doc):
    Body=doc.addObject('PartDesign::Body','Body')
    return Body

#https://wiki.freecad.org/index.php?title=Scripted_objects_with_attachment&section=5
def AktivateAttachment(obj): # Why did this take so laong :(
    obj.addExtension('Part::AttachExtensionPython')


def AttachBody(Body,edge):
    AktivateAttachment(Body)
    Body.AttachmentSupport = edge
    Body.MapMode = 'NormalToEdge'
    Body.MapPathParameter = 1.0

    pass

'''
Idea: get the information, what Edge a Body/Part is attached to.
>>> # doc = App.getDocument("Unnamed")
>>> # obj = doc.getObject("Box")
>>> # shp = obj.Shape
>>> # sub = obj.getSubObject("Edge10")
sub.CenterOfGravity

>>> # doc = App.getDocument("Unnamed")
>>> # obj = doc.getObject("Body001")
obj.Placement

sub.CenterOfGravity = obj.Placement
'''

def GenerateTestKnotFile(name,path):
    doc = App.newDocument(name)
    part = doc.addObject('App::Part','Knot')
    part.addObject(doc.addObject('App::DocumentObjectGroup','Directions'))
    for i in range(3):
        V = GenerateVector()
        V.normalize()
        V = V * 100
        line = MakeLine(V)
        part.addObject(line)
        body = makeBody(doc)
        part.addObject(body)
        AttachBody(body,[line,'Edge1'])




    doc.recompute()
    path = f"{path}/{name}"
    doc.saveAs(path)
    App.closeDocument(doc.Name)

'''
part.Placement.Base
Vector (100.00000000000001, 100.00000000000001, 0.0)
==
# doc = App.getDocument("AttachmentSearcherTest")
>>> # obj = doc.getObject("Line002")
>>> # shp = obj.Shape
>>> # sub = obj.getSubObject("Vertex2")
>>> ### End command Std_SendToPythonConsole
>>> sub.Point
Vector (100.0, 100.0, 0.0)

'''

def PlaceNormalToEdge():

    pass

# Vertex and Obj(Part) must be placed in the Same Coordinate system
def ProjectIntoPart(Vertex,Obj):
    inv = Obj.Placement.inverse
    Position = Vertex.Point
    PositionLocal = inv.multVec(Position)
    return PositionLocal




if __name__ == "__main__" :


    # myBASEPATH = loadBASEPATH()
    # myBASEPATH = f"{myBASEPATH}/DataBase/09071/00001"
    myname = "TEST1"
    myKnotID = "Test1"
    # GenerateDocTest(name=myname,BASEPATH=myBASEPATH,KnotID=myKnotID )
    # print(ReadKnotID(name=myname,BASEPATH=myBASEPATH))
    # print(myBASEPATH)
    # GenerateTestKnotFile("test1",myBASEPATH)

    Knots = GenerateKnots(10)
    # print(Knots[0])
    SaveKnots(Knots)
    K = LoadKnot(2)
    print(K)
    #TransformKnot()

    pass
