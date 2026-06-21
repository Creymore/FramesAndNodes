'''
Logic To Generate Node IDs
Solve for Axis Angel Rotations
Insert Node
Orient Node
'''
################################ IMPORT ####################################################
import json

import FreeCAD as App  # ty:ignore[unresolved-import]
import FreeCADGui as Gui  # ty:ignore[unresolved-import]
from FreeCAD import Vector  # ty:ignore[unresolved-import]
import Draft  # ty:ignore[unresolved-import]
import math
import copy
from itertools import combinations  # CODE-AUDIT: unused import in NodeLogic.py.
from itertools import permutations
from itertools import combinations_with_replacement
from collections import Counter

# try:
from .ProfileLogic import insertEndProfile,findEndProfiles
from .utils.utils import (
    copyVec,VecToTuple,itrToVec, saveDocumentToCache,
    deleteDocumentFromCache, FindBinders2,
    TransformToGlobalPlacement,IsOpposite,IsSame,roundVector,
    delete_object_and_contents,convert_to_tuple
)
# except ImportError:
#     from ProfileLogic import insertEndProfile,findEndProfiles                        # ty:ignore[unresolved-import, unused-ignore-comment]
#     from utils.utils import (                                                       # ty:ignore[unresolved-import, unused-ignore-comment]
#         copyVec,VecToTuple,itrToVec, saveDocumentToCache,
#         deleteDocumentFromCache, FindBinders2,
#         TransformToGlobalPlacement,IsOpposite,IsSame,roundVector,
#         delete_object_and_contents,convert_to_tuple
#     )

##############################################################################################

# https://freecad.github.io/SourceDoc/d1/d13/classBase_1_1Vector3.html#a24f91e91499245ab4282c6d0d0b7630c

#Data structure
Node1 = [
    {
        "Direction": App.Vector(1,2,5)	, # Direction Always Points away from the Nodes center
        "Offset": App.Vector(10,0,0)	,
        "Type": "x"						,
        "Rotation":10					, #Should this be just the direction of the X or Y Axis of the Body
        "Nsym":4						, # How often the cross section Matches itself along a 360 deg turn around its Geometric Center
    },
    {
        "Direction": App.Vector(0,-2,5) ,
        "Offset": App.Vector(0,10,0)    ,
        "Type": "x"				        ,
        "Rotation":-20			       	,
        "Nsym":4
    },
    {
        "Direction": App.Vector(2,-5,15),
        "Offset": App.Vector(0,10,0)    ,
        "Type": "x"			        	,
        "Rotation":-1055				,
        "Nsym":4
    },
    {
        "Direction": App.Vector(2,5,0)  ,
        "Offset": App.Vector(0,10,0)    ,
        "Type": "x"			        	,
        "Rotation":322		    		,
        "Nsym":4
    }
]

Node2 = [
    {
        "Direction": App.Vector(5,2,-1)	,
        "Offset": App.Vector(10,0,0)	,
        "Type": "x"						,
        "Rotation":10					,
        "Nsym":4						,
    },
    {
        "Direction": App.Vector(5,-2,0)	,
        "Offset": App.Vector(0,10,0)    ,
        "Type": "x"				        ,
        "Rotation":-20			    	,
        "Nsym":4
    },
    {
        "Direction": App.Vector(15,-5,-2)   ,
        "Offset": App.Vector(0,10,0)        ,
        "Type": "x"			        	    ,
        "Rotation":-1055				    ,
        "Nsym":4
    },
    {
        "Direction": App.Vector(0,5,-2) ,
        "Offset": App.Vector(0,10,0)    ,
        "Type": "x"				        ,
        "Rotation":322			    	,
        "Nsym":4
    }
]


def getPadOfFrameMember(FrameMember):
    def isProfile(obj):
        if obj.Name.startswith("Pad") and obj.Label.startswith("Profile"):
            return True
        else:
            return False

    Pad = list(filter(isProfile,FrameMember.Group))[0]
    return Pad

def getAttachmentEdge(FrameMember):
    Feature = FrameMember.AttachmentSupport[0][0].Name
    Support = FrameMember.AttachmentSupport[0][1][0]
    Edge = FrameMember.AttachmentSupport[0][0].Document.getObject(Feature).getSubObject(Support)
    return Edge

def getEndpoints(FrameMember)->list:
    '''
    Input: Valid and Attaches FrameMember
    Output: List[sub.Vertexes[0].Point,sub.Vertexes[1].Point]
    '''
    sub = getAttachmentEdge(FrameMember=FrameMember)
    return [sub.Vertexes[0].Point,sub.Vertexes[1].Point]

def getNodeCenter(FrameMembers):
    '''
    Input: Iterable filled with valid and attached FrameMembers
    Output: FreeCAD.Vector(x,y,z)
    '''
    allEndpoints = []
    for FrameMember in FrameMembers:
        allEndpoints.append(getEndpoints(FrameMember))

    comparePoints = []
    for pair in allEndpoints:
        for point in pair:
            comparePoints.append((point.x,point.y,point.z))

    mostCommonPoint = Counter(comparePoints).most_common(1)[0][0]
    return App.Vector(mostCommonPoint[0],mostCommonPoint[1],mostCommonPoint[2])

def MembersToBlankNode(FrameMembers):

    doc = App.ActiveDocument

    tempDoc = App.newDocument()
    tempPath=saveDocumentToCache(doc=tempDoc) # needed when a link is in the document the FrameMembers are in
    part = tempDoc.addObject('Assembly::AssemblyObject','Assembly')
#    part = ndoc.addObject('App::Part','Part')
    part.Label = "Node"
    # part.addProperty("App::PropertyString","NodeID","Node")
    part.addProperty("App::PropertyLength","Size","Node")
    part.addProperty("App::PropertyBool","isNode","Node")
    part.isNode = True
    part.Size = "100mm"

    GroupeDirections = tempDoc.addObject('App::DocumentObjectGroup','Group')
    part.addObject(GroupeDirections)
    GroupeDirections.Label = "Directions"
    GroupeDirections.addProperty('App::PropertyBool', 'Directions', 'Directions', '')
    GroupeDirections.Directions = True

    GroupeEndProfiles = tempDoc.addObject('App::DocumentObjectGroup','Group')
    part.addObject(GroupeEndProfiles)
    GroupeEndProfiles.Label = "EndProfiles"
    GroupeEndProfiles.addProperty('App::PropertyBool', 'EndProfiles', 'EndProfiles', '')
    GroupeEndProfiles.EndProfiles = True

    NodeCenter =getNodeCenter(FrameMembers=FrameMembers)

    for FrameMember in FrameMembers:
        EndPoints = getEndpoints(FrameMember)

        reverseMap = False
        if not EndPoints[0].isEqual(NodeCenter,1e-6):
            EndPoints.reverse()
            # reverseMap = True
        if  not EndPoints[0].isEqual(NodeCenter,1e-6):
            continue

        ###### Insert Line#####################
        Direction = EndPoints[1] - EndPoints[0]
        points = [App.Vector(0,0,0),Direction]
        line = Draft.makeWire(points)
        line.setExpression("Length",f"href({part.Name}.Size)")
        GroupeDirections.addObject(line)
        
        ##################Insert newFrameMember################
        newFrameMember = insertEndProfile(target=tempDoc)

        newFrameMember.addExtension('Part::AttachExtensionPython')
        newFrameMember.AttachmentSupport = (line,'Edge1')
        newFrameMember.MapMode = 'NormalToEdge'
        newFrameMember.MapPathParameter = 1

        ###################Change Sketch########################

        PadNew = getPadOfFrameMember(FrameMember=FrameMember)
        newSketch = PadNew.Profile[0]
        # print(FrameMember.Label,newSketch.Name)
        newSketch = tempDoc.copyObject(newSketch,True)
        PadOld = getPadOfFrameMember(FrameMember=newFrameMember) # Default Sketch of the NodeMember
        oldSketch = PadOld.Profile[0]
        newFrameMember.addObject(newSketch)
        PadOld.Profile = newSketch
        tempDoc.removeObject(oldSketch.Name)

        ################# SetAlignment

        Alignment:int = FrameMember.Alignment
        newFrameMember.Alignment = Alignment
        newFrameMember.MapReversed = reverseMap

        ###################
        GroupeEndProfiles.addObject(newFrameMember)
        

    tempDoc.recompute()

    ndoc = App.newDocument()
    ndoc.copyObject(part,True)

    deleteDocumentFromCache(path=tempPath)
    App.closeDocument(tempDoc.Name)
    ndoc.recompute()

    if App.GuiUp:
        Gui.setActiveDocument(ndoc.Name)
    return part

def isBlank(obj):
    if hasattr(obj,"isNode") and obj.isNode==True:
        return True
    else:
        return False

def findBlank(doc):
    return list(filter(isBlank,doc.Objects))[0]

#################### Node To NodeID  Start ######################################
# This does not account for How Attachment Rotation Works
def MembersToNodeTuple2(FrameMembers):
    '''
    Input: Iterable filled with valid and attached FrameMembers
    Output: Node
    Description:
    Turns the Selected Bodies / Frame Members into a Node to be used in the NodeToID function
    '''

    tol = 1e-6

    NodeCenterPoint= getNodeCenter(FrameMembers=FrameMembers)
    # print(f"MembersToNodeTuple2 NodeCenter: {NodeCenterPoint}") #Debug

    Node = []
    for FrameMember in FrameMembers:

        EndPoints = getEndpoints(FrameMember=FrameMember)

        # print(f"Enpoint[0]:{EndPoints[0]}")
        # print(f"Enpoint[0]:{EndPoints[1]}")

        if not EndPoints[0].isEqual(NodeCenterPoint,tol):
            EndPoints.reverse()
        if not EndPoints[0].isEqual(NodeCenterPoint,tol):
            print(f"Frame Member:{FrameMember.Name} is not Part of Node")
            print(f"NodeCenterPoint:{NodeCenterPoint}")
            print(f"Enpoint[0]:{EndPoints[0]}")
            print(f"Enpoint[0]:{EndPoints[1]}")
            continue

        Direction = EndPoints[1] - EndPoints[0]

        Pad = getPadOfFrameMember(FrameMember=FrameMember)
        Nsym = getattr(Pad.Profile[0], "Nsym", 0)
        Type = getattr(Pad.Profile[0], "Type", "ProfileTypeNotAssignt")

        Rotation = math.degrees(FrameMember.AttachmentOffset.Rotation.Angle)
        Offset = FrameMember.AttachmentOffset.Base

        Node.append({
        "Direction":  Direction ,
        "Offset":   Offset      ,
        "Type": Type	        ,
        "Rotation": Rotation    ,
        "Nsym": Nsym
        })

    return Node

def isValidNode(K)->bool:
    if not isinstance(K, (list, tuple)) or len(K) == 0:
        return False

    requiredKeys = ("Direction", "Offset", "Type", "Rotation", "Nsym")
    vectorType = type(App.Vector())
    numberTypes = (int, float)

    for Profile in K:
        if not isinstance(Profile, dict):
            return False
        for key in requiredKeys:
            if key not in Profile:
                return False
        if not isinstance(Profile["Direction"], vectorType):
            return False
        if not isinstance(Profile["Offset"], vectorType):
            return False
        if not isinstance(Profile["Type"], str):
            return False
        if not isinstance(Profile["Rotation"], numberTypes):
            return False
        if not isinstance(Profile["Nsym"], int):
            return False

    return True

def getAngleP2(Node,n,m,n_key,m_key,deg=True)->float:
    Vn = Node[n][n_key]
    Vm = Node[m][m_key]
    alpha = Vn.getAngle(Vm) # returns the angle in rad

    if deg is True: # Is the function used in deg or rad mode
        return math.degrees(alpha)
    else:
        return alpha

def NormalizeNode(Node,deg=True):
    '''
    Docstring for NormalizeNode

    :param K: Node

    Normalizes the Contents in a Node, to make them Uniform
    '''
    for Profile in Node:
        #normalizes the Direction of the Profile
        D = Profile["Direction"]
        Profile.update({"Direction":D.normalize()})
        #Normalizes the Offset of the Profile
        O = Profile["Offset"]
        Profile.update({"Offset":O.projectToPlane(Vector(0,0,0),D)})
        #Normalizes the rotation
        R = Profile["Rotation"] #Rotation Degrees not Radiants
        Nsym = Profile["Nsym"]
        if Nsym != -1 and Nsym != 0: # Is only -1 if there is No symmetry like a circler or Ring Profile | 0 for not assignt
            if R < 0: R = 360+(R % -360)
            Profile.update({"Rotation": R % (360/Nsym)})
        else:
            Profile.update({"Rotation": 0}) # Rotation does not Matter for a circular Profile

def NodeToID2(K:tuple,deg=True)->tuple:
    '''
    Converts the Node into a Rotation independent identifier
    K: Node
    deg: bool | decides if the calculations are done in Degrees or in Radiants
    '''
    Kn = list(K)
    NormalizeNode(Kn,deg)
    n = len(K)
    NodeID=[]

    roundDigets = 10

    for i in range(n):
        for j in range(i+1,n):

            # print(f"{i},{j}") #Debug

            Type_i = Kn[i]["Type"]
            Type_j= Kn[j]["Type"]
            Nsym_i= Kn[i]["Nsym"]
            Nsym_j= Kn[j]["Nsym"]
            Rotation_i = Kn[i]["Rotation"]
            Rotation_j = Kn[j]["Rotation"]
            offsetX_i = round(Kn[i]["Offset"].x,roundDigets)
            offsetY_i = round(Kn[i]["Offset"].y,roundDigets)
            offsetX_j = round(Kn[j]["Offset"].x,roundDigets)
            offsetY_j= round(Kn[j]["Offset"].y,roundDigets)

            offsetX_i = 0.0 if offsetX_i == -0.0 else offsetX_i
            offsetY_i = 0.0 if offsetY_i == -0.0 else offsetY_i
            offsetX_j = 0.0 if offsetX_j == -0.0 else offsetX_j
            offsetY_j = 0.0 if offsetY_j == -0.0 else offsetY_j

            phi = getAngleP2(K,i,j,"Direction","Direction",deg)

            a_i = (Type_i,Nsym_i,Rotation_i,offsetX_i,offsetY_i)
            a_j = (Type_j,Nsym_j,Rotation_j,offsetX_j,offsetY_j)

            if a_i <= a_i:
                a_min = a_i
                a_max = a_j
            else:
                a_min = a_j
                a_max = a_i

            NodeID.append((a_min,phi,a_max))

    NodeID.sort(key=lambda x: (x[0],x[1],x[2]))

    return tuple(NodeID)

def AddPropertyNodeID(NodeAss):
    doc = NodeAss.Document
    FrameMembers = doc.findObjects('PartDesign::Body','Body','BaseEndProfile')
    Node= MembersToNodeTuple2(FrameMembers=FrameMembers)
    NodeID = NodeToID2(K=Node,deg=True)
    if NodeID is False:
        App.Console.PrintError("NodeID is False, Something is wrong")
        return None
    if not hasattr(NodeAss,"NodeID"):
        NodeAss.addProperty('App::PropertyMap',"NodeID","Node")
    NodeAss.NodeID = {"NodeID":json.dumps(NodeID)}

def ReadNodeID(NodeAss)->tuple:
    rK= NodeAss.NodeID["NodeID"]
    NodeID = json.loads(rK)
    NodeID = convert_to_tuple(NodeID)
    return NodeID

def ReadNodeIDfromDocument(doc):
    blank = findBlank(doc=doc)
    return ReadNodeID(NodeAss=blank)

def PrintNodeIDfromDocument(doc):
    NodeID = ReadNodeIDfromDocument(doc)
    for entry in NodeID:
        print(entry)

def PrintNodeID(FrameMembers):
    '''
    This funktion was made to help Debuging the NodeID inside of FreeCAD
    To use this simply select all FrameMembers (Bodys) that belong to the Node you would like to Node the NodeID of
    This information will be printed in the Report view
    '''
    Node = MembersToNodeTuple2(FrameMembers)
    print("Node--------------------------------------------------------------------------------------")
    print(f"isvValidNode = {isValidNode(Node)}")
    for entry in Node:
        print(entry)
    print("NodeID--------------------------------------------------------------------------------------")
    NodeID = NodeToID2(K=Node,deg=True)
    print(f"TypeOf NodeID = {type(NodeID)}")
    if not type(NodeID) is bool:
        for entry in NodeID:
            print(entry)
    else:
        print(NodeID)

#################### Node To NodeID  End ######################################

################### Find All Matches start ####################################
def IsTransformed(A1,B1,A2,B2,tol = 1e-6)->bool:
    a = abs(A1.getAngle(A2))
    b = abs(B1.getAngle(B2))
    if abs(a - b) < tol: #What about Tolerance
        return True
    else:
        print(f"Vector Pairs A1 A2 does not Match B1 B2 \n with: Angle1 = {a} Angle2 = {b} delta = {abs(a - b)}")
        print(f"A1 = {A1}")
        print(f"A2 = {A2}")
        print(f"B1 = {B1}")
        print(f"B2 = {B2}")
        return False

def matrixToAxisAngle(matrix,deg=True):
    Ap = App.Placement()
    Ap.Matrix = matrix
    axis = Ap.Rotation.Axis
    angle = Ap.Rotation.Angle

    if deg is True: # Is the function used in deg or rad mode
        return (axis,math.degrees(angle))
    else:
        return (axis,angle)

# CODE-AUDIT: similar responsibility as FindAxisAngle(), but used by FindallMatches2().
def FindAxisAngle2(A1,B1,A2,B2,deg = True,tol = 1e-6,matrix = False):
    '''
    Find Axis Rotation, Returns the Axis and Rotation Transformation, That A1 and A2 get
    transformed into B1 and B2 around the Origin(0,0,0).
    A1 transforms into B1
    A2 transforms into B2
    A gets Transformed / Start
    B is Stationary / Target
    returns: (axis,angle)
        axis as FreeCAD.Vector(x,y,z)
        angle as float
    OR
    returns False
        if there is no match found
    '''

    A1, B1, A2, B2 = A1.normalize(), B1.normalize(), A2.normalize(), B2.normalize()
    if not IsTransformed(A1, B1, A2, B2, tol):
        return False
    
    if A1.isEqual(A2,tol) or B1.isEqual(B2,tol):
        return False

    # Basisvektoren als FreeCAD.Vector
    v1_vec = App.Base.Vector(A1)
    v2_vec = App.Base.Vector(A2)

    # Dritten Basisvektor als Kreuzprodukt von A1 und A2
    v3_vec = v1_vec.cross(v2_vec)

    # Bildvektoren
    w1_vec = App.Base.Vector(B1)
    w2_vec = App.Base.Vector(B2)
    w3_vec = v3_vec  # Beliebig, hier: v3 bleibt unverändert

    # Matrizen V und W konstruieren
    V = App.Base.Matrix()
    V.setCol(0, v1_vec)
    V.setCol(1, v2_vec)
    V.setCol(2, v3_vec)

    W = App.Base.Matrix()
    W.setCol(0, w1_vec)
    W.setCol(1, w2_vec)
    W.setCol(2, w3_vec)

    # Inverse von V berechnen
    V_inv = V.inverse()

    # Transformationsmatrix A = W * V_inv
    A = W.multiply(V_inv)

    if matrix is True:
        return A

    return matrixToAxisAngle(matrix=A,deg=deg)

def TransformNode(Node,axis,angle,deg=True)->tuple:
    if deg is False: 				# Rotation argument for angle is degrees by default
        angle = math.degrees(angle) # so Radiants get converted
    rot = App.Rotation(axis,angle)
    for Profile in Node:
        Profile["Direction"] = rot.multVec(Profile["Direction"])
    return tuple(Node)

def FindallMatches2(K1,K2,tol=1e-6):
    '''
    K1: Node1 Stationary,
    K2: Node2 gets Transformed
    description:
    Finds all the matches, where K2 gets Transformed into K1 successfully
    retrun: tuple((App.Vector,float),...)

    {
        "Direction": App.Vector(0,-2,5) ,
        "Offset": App.Vector(0,10,0)    ,
        "Type": "x"				        ,
        "Rotation":-20			       	,
        "Nsym":4
    }
    '''
    Results = []
    AllPairnigs = []
    N = len(K1)
    for n in range(N):
        V1= K1[n]["Direction"]
        for m in range(N):
            if n == m:
                continue
            V2 = K1[m]["Direction"]
            for j in range(N):
                W1 = K2[j]["Direction"]
                for k in range(N):
                    if j == k:
                        continue
                    W2 = K2[k]["Direction"]

                    V1c = App.Vector(V1.x,V1.y,V1.z)
                    V2c = App.Vector(V2.x,V2.y,V2.z)
                    W1c = App.Vector(W1.x,W1.y,W1.z)
                    W2c = App.Vector(W2.x,W2.y,W2.z)

                    V3c = V1c.cross(V2c)
                    W3c = W1c.cross(W2c)

                    M1 = App.Base.Matrix()
                    M1.setCol(0, V1c)
                    M1.setCol(1, V2c)
                    M1.setCol(2, V3c)

                    M2 = App.Base.Matrix()
                    M2.setCol(0, W1c)
                    M2.setCol(1, W2c)
                    M2.setCol(2, W3c)

                    M2inv = M2.inverse()

                    rot = M1.multiply(M2inv)

                    allMacht = True
                    Pairings = []
                    for o in range(N):
                        D1 = rot.multVec(K2[o]["Direction"])
                        Type1 = K2[o]["Type"]
                        Nsym1 = K2[o]["Nsym"]
                        Offset1 = K2[o]["Offset"]
                        Rotation1 = K2[o]["Rotation"]
                        Match = False
                        r = 0
                        for p in range(N):
                            D2 = K1[p]["Direction"]
                            Angle = abs(D1.getAngle(D2))
                            if Angle > tol:
                                continue
                            Type2 = K1[p]["Type"]
                            if not Type1 == Type2:
                                continue
                            Nsym2 = K1[p]["Nsym"]
                            if not Nsym1 == Nsym2:
                                continue
                            Offset2 = K1[p]["Offset"]
                            if not Offset1.isEqual(Offset2,tol):
                                continue
                            Rotation2 = K1[p]["Rotation"]
                            if Rotation1 == Rotation2:
                                Match = True
                                # Pairings.append((o,p))
                                Pairings.append((p))
                                # print(f"D1:{D1} \t D2:{D2}\t with {n}{m}{j}{k} Match:{Match}")
                                break
                            # print(f"D1:{D1} \t D2:{D2} \t with {n}{m}{j}{k} Match:{Match}")
                            r = r + 1
                        if Match is False:
                            allMacht = False
                            break

                    if allMacht is True:
                        AxisAngle = matrixToAxisAngle(rot)
                        # print(A.decompose())
                        # print(AxisAngle)
                        if AxisAngle in Results:
                            rr = 1
                        elif Pairings in AllPairnigs:
                            rr = 2
                        else:
                            Results.append(AxisAngle)
                            AllPairnigs.append(Pairings)
                            # print(f"Appended Pairing:{Pairings}")
    print(AllPairnigs)
    print(Results)
    return Results

def procesPairings(pairings):
    newP = []
    for pairing in pairings:
        newP.append((VecToTuple(FreeCADvector=pairing[0]),pairing[1]))
    return newP

def AddMatchesProperty(iNodeAss,pairings:tuple):
    if not hasattr(iNodeAss, "PossibleOrientations"):
        iNodeAss.addProperty('App::PropertyMap', "PossibleOrientations", "Orientations")
    iNodeAss.PossibleOrientations = {"Orientations": json.dumps(procesPairings(pairings))}

def readOrientations(Node):
    rO = Node.PossibleOrientations["Orientations"]
    pairings = json.loads(rO)
    newPairings = []
    for p in pairings:
        newPairings.append((itrToVec(itr=p[0]),p[1]))
    return newPairings

def PrintOrientations(Node):
    print(f"Node:{Node.Name}")
    orientations = readOrientations(Node)
    for orientation in orientations:
        print(f"Orientation:{orientation}")

################### Find All Matches End ####################################

################### Insertion and Ortion of Nodes ####################################
def InsertNode(target,Node,aslink=True):

    if aslink:
        # print(f"InsertedNodeFile:{Node.Document.FileName}")
        file = Node.Document.FileName

        doc = App.openDocument(file,False,False)
        App.closeDocument(doc.Name)
        print(f"file:{file}")
        doc = App.openDocument(file,False,False)
        Node = findBlank(doc)

        link = target.addObject('App::Link','Link')
        link.LinkedObject = Node
        inserted = link
        link.Label = Node.Label
    else:
        inserted = target.copyObject(Node,True)
    return inserted

def PlaceNode(Node,NodeCenterPoint)->None:

    Node.addExtension('Part::AttachExtensionPython')
    Node.AttachmentSupport = NodeCenterPoint
    Node.MapMode = "Translate"

def addSizeExpressionToFrameMember(Node,FrameMember,ver):
    exp = f"-href({Node.Name}.Size)"
    if ver == 1:
        prop = "OffsetEnd1"
    elif ver == 2:
        prop = "OffsetEnd2"
    else:
        print(" ver should be 1 or 2 ")
        return
    if Node.Size > FrameMember.Length / 2:
        App.Console.PrintCritical("Condition: 'Node.Size < FrameMember.Length / 2' not true \n")
        return
    FrameMember.setExpression(prop,exp)

def addLinkSizeExpressionToFrameMember(Node,LFrameMember,ver):
    LinkProperty = "ForFrameMember"
    FrameMember = LFrameMember.getLinkedObject()
    # Add Link to FrameMemberDocument
    doc = FrameMember.Document
    links = doc.findObjects('App::Link')
    hasLink = False
    for link in links:
        if getattr(link,LinkProperty,False) == ver:
            hasLink = True
            break

    if not hasLink:
        newlink = doc.addObject('App::Link','Link')
        newlink.addProperty('App::PropertyInteger',LinkProperty,"LinkInfo")
        newlink.setExpression(LinkProperty,str(ver))
        if Node.isDerivedFrom("App::Link"):
            Node = Node.getLinkedObject()
            newlink.LinkedObject = Node
        else:
            newlink.LinkedObject = Node

        exp = "-href(Link.Size)"
        if ver == 1:
            prop = "OffsetEnd1"
        elif ver == 2:
            prop = "OffsetEnd2"
        else:
            print(" ver should be 1 or 2 ")
            return
        if Node.Size > LFrameMember.Length / 2:
            App.Console.PrintCritical("Condition: 'Node.Size < FrameMember.Length / 2' not true \n")
            return
        FrameMember.setExpression(prop,exp)

    doc.recompute()

# Should i combine those into into one function ?
def removeSizeExpressionFromMembers(FrameMember,ver):
    if ver == 1:
        prop = "OffsetEnd1"
    elif ver == 2:
        prop = "OffsetEnd2"
    else:
        print(" ver should be 1 or 2")
    FrameMember.setExpression(prop, None) # Should The length be set as well ?  

def removeLinkSizeExpression(LFrameMember,ver):
    LinkProperty = "ForFrameMember"
    FrameMember = LFrameMember.getLinkedObject()
    doc = FrameMember.Document
    links = doc.findObjects('App::Link')
    hasLink = False
    for link in links:
        if getattr(link,LinkProperty,False) == ver:
            doc.removeObject(link.Name)
            doc.recompute()
            break

    if ver == 1:
        prop = "OffsetEnd1"
    elif ver == 2:
        prop = "OffsetEnd2"
    else:
        print(" ver should be 1 or 2")
    FrameMember.setExpression(prop, None) # Should The length be set as well ? 

def NodeCenterVertex(NodeCenter, FrameMember):
    Feature = FrameMember.AttachmentSupport[0][0]
    FeatureName = Feature.Name
    Support = FrameMember.AttachmentSupport[0][1][0]
    Obj = FrameMember.AttachmentSupport[0][0].Document.getObject(FeatureName)
    Edge = Obj.getSubObject(Support)
    ElementReverseMap = Edge.ElementReverseMap

    # Get the vertex objects
    vertex1 = Obj.getSubObject(ElementReverseMap["Vertex1"])
    vertex2 = Obj.getSubObject(ElementReverseMap["Vertex2"])

    # Get the points of the vertices
    point1 = vertex1.Point
    point2 = vertex2.Point

    # Calculate distances to NodeCenter
    distance1 = NodeCenter.distanceToPoint(point1)
    distance2 = NodeCenter.distanceToPoint(point2)

    #Check if the Map is reversed to how it is expected
    Reversed = False
    tol = 1e-6
    ExpectedEdgeDirection = point2 - point1
    #ActualDirection = Edge.tangentAt(0.5) # Maybe i should check against the Z-driection of the FrameMember in case it is maped Reversed
    rot = FrameMember.Placement.Rotation
    ActualDirection = rot.multVec(App.Vector(0,0,-1))
    if IsSame(ExpectedEdgeDirection,ActualDirection,tol):
        #Reversed = False
        pass
    elif IsOpposite(ExpectedEdgeDirection,ActualDirection,tol):
        Reversed = True
    else:
        print(f"NodeCenterVetex: FrameMember:{FrameMember.Name} is not on the expected line")

    if distance1 < tol:
        if not Reversed:
            ver = 1
        else:
            ver = 2
    elif distance2 < tol:
        if not Reversed:
            ver = 2
        else:
            ver = 1

    return ver

def getEndprofiles(Node):
    print(f"{Node.TypeId}")
    if Node.TypeId == 'App::Link':
        Node = Node.getLinkedObject()
    # print(f"{Node.TypeId}")
    doc = Node.Document
    # print(f"doc:{doc} Node:{Node.Name}")
    Endprofiles = doc.findObjects('PartDesign::Body','Body','BaseEndProfile')
    Ends = {}
    for Endprofile in Endprofiles:
        # print(f"Endprofile:{Endprofile} | {Endprofile.Name} | {Endprofile.Label}")
        Feature = Endprofile.AttachmentSupport[0][0]
        FeatureName = Feature.Name
        Support = Endprofile.AttachmentSupport[0][1][0]
        Obj = Endprofile.AttachmentSupport[0][0].Document.getObject(FeatureName)
        Edge = Obj.getSubObject(Support)
        Direction = Edge.tangentAt(0.5) # Only attached to line
        Ends.update({Endprofile:Direction}) # Using an obj as a key feels weird, but it works ¯\_(ツ)_/¯

    return(Ends)

def FindEndProfileMatch(FrameMember,Endprofiles,NodeCenter,Orientation,deg=True):
    # print("FindEndProfileMatch")
    # print(f"Endprofiles: {Endprofiles}")
    tol = 1e-6
    EndPoints = getEndpoints(FrameMember=FrameMember)
    if not EndPoints[0].isEqual(NodeCenter,tol):
            EndPoints.reverse()
    FrameMemberDirection = EndPoints[1] - EndPoints[0]

    axis = Orientation[0]
    angle = Orientation[1]
    if deg is False: 				# Rotation argument for angle is degrees by default
        angle = math.degrees(angle) # so Radiants get converted
    rot = App.Rotation(axis,angle)

    keys = Endprofiles.keys() # Key is the Body Obj of Ebdframe Profile ¯\_(ツ)_/¯
    EndProfileName = ""
    for key in keys:
        # print(f"Endprofile:{key}")
        EndProfileDirection = Endprofiles[key]
        TransformedFrameMemberDirection = rot.multVec(EndProfileDirection)
        if IsSame(TransformedFrameMemberDirection,FrameMemberDirection,tol):
            EndprofileObj = key
            break
    
    return EndprofileObj

def OirentWorkaround(Binder,Endprofile,ver):

    T1,T2 = TransformToGlobalPlacement(Binder),TransformToGlobalPlacement(Endprofile)
    T1 = T1.Matrix.decompose()[1]
    T2 = T2.Matrix.decompose()[1]

    ReversedMap = Endprofile.MapReversed

    if ver == 1 and not ReversedMap:
        X1 = App.Vector(1,0,0)
        Y1 = App.Vector(0,1,0)
    elif ver == 2 and not ReversedMap:
        X1 = App.Vector(1,0,0)
        Y1 = App.Vector(0,-1,0)
    elif ver == 1 and ReversedMap:
        X1 = App.Vector(1,0,0)
        Y1 = App.Vector(0,-1,0)
    elif ver == 2 and ReversedMap:
        X1 = App.Vector(1,0,0)
        Y1 = App.Vector(0,1,0)
    else:
        print(" ver should be 1 or 2 ")
        return

    A1 = T1.multVec(X1) # Binder Transformed
    A2 = T1.multVec(Y1)

    B1 = T2.multVec(App.Vector(1,0,0)) # Endprofile Stationary
    B2 = T2.multVec(App.Vector(0,1,0))
    
    # print("OirentWorkaround")
    # print(f"ver = {ver}")
    # print(f"A1 = {A1}")
    # print(f"A2 = {A2}")
    # print(f"B1 = {B1}")
    # print(f"B2 = {B2}")

    matrix = FindAxisAngle2(A1,B1,A2,B2,tol=1e-4,deg=True,matrix=True)
    if matrix is False:
        print("No Workaorund Found")
        return
    matrix = matrix.multiply(T1.inverse())

    AxisAngle = matrixToAxisAngle(matrix,deg=False)
    axis = AxisAngle[0]
    angle = AxisAngle[1]
    # print(f"axis:{axis} | angle:{angle}")
    Binder.Placement.Rotation.Axis = axis
    Binder.Placement.Rotation.Angle = angle

def OrientNode(Node,Orientation,deg=True):

    axis = Orientation[0]
    angle = Orientation[1] #Angle in degrees
    Node.Placement.Rotation.Axis = axis
    if deg:
        Node.Placement.Rotation.Angle = math.radians(angle)
    else:
        Node.Placement.Rotation.Angle = angle

    # Find FrameMembers
    FrameMembers = ReadFrameMembersFromNode(Node=Node)

    # Find Endprofiles
    EndProfiles = getEndprofiles(Node=Node)

    # Find Ends
    NodeCenter = getNodeCenter(FrameMembers=FrameMembers)

    NodeInfo = {}
    for FrameMember in FrameMembers:
        ver = NodeCenterVertex(NodeCenter=NodeCenter,FrameMember=FrameMember)
        NodeInfo.update({FrameMember.Name : ver})
        if FrameMember.TypeId == 'App::Link':
            addLinkSizeExpressionToFrameMember(Node=Node,LFrameMember=FrameMember,ver=ver)
        else:
            addSizeExpressionToFrameMember(Node=Node,FrameMember=FrameMember,ver=ver)

        EndProfile = FindEndProfileMatch(FrameMember,EndProfiles,NodeCenter,Orientation,deg)

        Binders = FindBinders2(FrameMember)
        for Binder in Binders:
            if not hasattr(Binder,"EndLabel"):
                continue
            if Binder.EndLabel == 1 and ver == 1 or Binder.EndLabel == 2 and ver == 2:
                Binder.Support = EndProfile
                # print(f"Endprofile: {EndProfile} | {EndProfile.Name} | {EndProfile.Label}")
                OirentWorkaround(Binder,EndProfile,ver)

    # Hide EndProfiles and Hide Directions
    if Node.TypeId == 'App::Link':
        LNode = Node.getLinkedObject()
    else:
        LNode = Node
    Groups = LNode.getObjectsOfType('App::DocumentObjectGroup')
    print(Groups)
    for Group in Groups:
        if hasattr(Group,'EndProfiles'):
            Group.Visibility = False
        if hasattr(Group,'Directions'):
            Group.Visibility = False
    
    doc = Node.Document
    doc.recompute()

def AddFrameMembersToNode(Node,FrameMembers):

    for k in range(len(FrameMembers)):
        newFrameMember = f"FrameMember{k}"
        Prop = Node.addProperty('App::PropertyString', newFrameMember, "NodeMembers")
        val = f"{FrameMembers[k].Name}.Label"
        Node.setExpression(newFrameMember, val)
        # print(val)
    Node.Document.recompute()

def ReadFrameMembersFromNode(Node):
    Ex = Node.ExpressionEngine
    filtered_list = [tup for tup in Ex if tup[0].startswith("FrameMember")]
    second_entries = [tup[1].split('.')[0] for tup in filtered_list]
    doc = App.getDocument(Node.Document.Name)
    FrameMembers = []
    for str in second_entries:
        FrameMembers.append(doc.getObject(str))

    return FrameMembers

def PrintFrameMembersFromNode(Node): #Debug
    print(f"Node:{Node.Name}")
    for entry in ReadFrameMembersFromNode(Node=Node):
        print(f"FrameMember:{entry} | {entry.Name}")

def AddNodePropertyToFrameMembers(Node,FrameMembers):
    NodeCenter = getNodeCenter(FrameMembers=FrameMembers)
    val = f"href({Node.Name}.Label)"
    print(val)
    for FrameMember in FrameMembers:
        ver = NodeCenterVertex(NodeCenter,FrameMember)
        if ver == 1:
            if not hasattr(FrameMember,'NodeEnd1'):
                FrameMember.addProperty('App::PropertyString', 'NodeEnd1', 'Node', '')
            FrameMember.setExpression('NodeEnd1',val)
        else:
            if not hasattr(FrameMember,'NodeEnd2'):
                FrameMember.addProperty('App::PropertyString', 'NodeEnd2', 'Node', '')
            FrameMember.setExpression('NodeEnd2',val)
    Node.Document.recompute()

def ReadNodesFromFrameMember(FrameMember):
    expressions = FrameMember.ExpressionEngine
    doc = FrameMember.Document
    Nodes = []
    for expression in expressions:
        prop = expression[0]
        if prop.startswith("NodeEnd"):
            expressionstr = expression[1]
            objstr = expressionstr.split("(")[1]
            objstr = objstr.split(".")[0]
            Nodes.append(doc.getObject(objstr))
    return tuple(Nodes)

def removeNodePropertyFromFrameMembers(FrameMembers):
    NodeCenter = getNodeCenter(FrameMembers=FrameMembers)
    for FrameMember in FrameMembers:
        ver = NodeCenterVertex(NodeCenter,FrameMember)
        if ver == 1:
            if hasattr(FrameMember,'NodeEnd1'):
                FrameMember.setExpression('NodeEnd1',None)
        else:
            if hasattr(FrameMember,'NodeEnd2'):
                FrameMember.setExpression('NodeEnd2',None)

def InsertPlaceNode(target,Node,FrameMembers,aslink)->None:
    print("PlaceNode")
    K1 = MembersToNodeTuple2(FrameMembers=FrameMembers)
    K2 = MembersToNodeTuple2(FrameMembers=list(findEndProfiles(Node)))

    inserted=InsertNode(target=target,Node=Node,aslink=aslink)

    App.setActiveDocument(target.Name)
    App.ActiveDocument=App.getDocument(target.Name)
    if App.GuiUp == 1:
        Gui.ActiveDocument=Gui.getDocument(target.Name)

    NodeCenter = getNodeCenter(FrameMembers=FrameMembers)

    Feature = FrameMembers[0].AttachmentSupport[0][0]
    FeatureName = Feature.Name
    Support = FrameMembers[0].AttachmentSupport[0][1][0]
    Obj = FrameMembers[0].AttachmentSupport[0][0].Document.getObject(FeatureName)
    Edge = Obj.getSubObject(Support)
    ElementReverseMap = Edge.ElementReverseMap
    Vertexes= (ElementReverseMap["Vertex1"],ElementReverseMap["Vertex2"])

    if Obj.getSubObject(Vertexes[0]).Point.isEqual(NodeCenter,1e-6):
        ver= Vertexes[0]
    else:
        ver = Vertexes[1]

    attach=(Feature,ver)
    PlaceNode(Node=inserted,NodeCenterPoint=attach)

    tol = 1e-4
    allMatches = FindallMatches2(K1=K1,K2=K2,tol=tol)
    AddMatchesProperty(iNodeAss=inserted,pairings=allMatches)

    AddFrameMembersToNode(Node=inserted,FrameMembers=FrameMembers)
    AddNodePropertyToFrameMembers(Node=inserted,FrameMembers=FrameMembers)

def RemoveNode(Node):
    doc = Node.Document
    FrameMembers = ReadFrameMembersFromNode(Node=Node)
    NodeCenter = getNodeCenter(FrameMembers=FrameMembers)
    # removeNodePropertyFromFrameMembers(FrameMembers=FrameMembers)
    for FrameMember in FrameMembers:
        ver = NodeCenterVertex(NodeCenter=NodeCenter,FrameMember=FrameMember)
        if FrameMember.TypeId == 'App::Link':
            removeLinkSizeExpression(FrameMember,ver)
        else:
            removeSizeExpressionFromMembers(FrameMember=FrameMember,ver=ver)
        
        if ver == 1:
            if hasattr(FrameMember,'NodeEnd1'):
                FrameMember.setExpression('NodeEnd1',None)
        else:
            if hasattr(FrameMember,'NodeEnd2'):
                FrameMember.setExpression('NodeEnd2',None)

        Binders = FindBinders2(FrameMember)
        for Binder in Binders:
            if not hasattr(Binder,"EndLabel"):
                continue
            if Binder.EndLabel == 1 and ver == 1 or Binder.EndLabel == 2 and ver == 2:
                Binder.Support = None

    if Node.TypeId == 'App::Link':
        doc.removeObject(Node.Name)
    else:
        delete_object_and_contents(Node,doc)
    doc.recompute()

def ChangeNode(target,OldNode,NewNode,aslink):
    FrameMembers = ReadFrameMembersFromNode(OldNode)
    RemoveNode(OldNode)
    InsertPlaceNode(target,NewNode,FrameMembers,aslink)