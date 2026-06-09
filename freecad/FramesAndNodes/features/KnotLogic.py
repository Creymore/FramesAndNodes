'''
Logic To Generate Knot IDs
Solve for Axis Angel Rotation
Test Fit Logic TODO
Solve All results for Axis Rotation Rotation TODO

'''
################################ IMPORT ####################################################
from sympy import false
from pathlib import Path  # CODE-AUDIT: unused import in KnotLogic.py.
import sys  # CODE-AUDIT: unused import in KnotLogic.py.
import json

import FreeCAD as App  # ty:ignore[unresolved-import]
import FreeCADGui as Gui  # ty:ignore[unresolved-import]
from FreeCAD import Vector  # ty:ignore[unresolved-import]
import Draft  # ty:ignore[unresolved-import]
import math
import copy
from itertools import combinations  # CODE-AUDIT: unused import in KnotLogic.py.
from itertools import permutations
from itertools import combinations_with_replacement
from collections import Counter

#print("hello")

try:
    from .ProfileLogic import insertEndProfile,findEndProfiles
    from .utils.utils import (
        copyVec,VecToTuple,itrToVec, saveDocumentToCache, deleteDocumentFromCache, FindBinders2,
        TransformIntoSharedCoordinates,TransformToGlobalPlacement
    )
except ImportError:
    from ProfileLogic import insertEndProfile,findEndProfiles                        # ty:ignore[unresolved-import]
    from utils.utils import (                                                       # ty:ignore[unresolved-import]
        copyVec,VecToTuple,itrToVec, saveDocumentToCache,
        deleteDocumentFromCache, FindBinders2,
        TransformIntoSharedCoordinates,TransformToGlobalPlacement
    )

##############################################################################################

# https://freecad.github.io/SourceDoc/d1/d13/classBase_1_1Vector3.html#a24f91e91499245ab4282c6d0d0b7630c

#Data structure
Knot1 = [
    {
        "Direction": App.Vector(1,2,5)	, # Direction Always Points away from the Knots center
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

Knot2 = [
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

def getPadOfFrameMember(FrameMember):
    def isProfile(obj):
        if obj.Name.startswith("Pad") and obj.Label.startswith("Profile"):
            return True
        else:
            return False

    Pad = list(filter(isProfile,FrameMember.Group))[0]
    return Pad

def getEndpoints(FrameMember)->list:
    '''
    Input: Valid and Attaches FrameMember
    Output: List[sub.Vertexes[0].Point,sub.Vertexes[1].Point]
    '''
    Feature = FrameMember.AttachmentSupport[0][0].Name
    Support = FrameMember.AttachmentSupport[0][1][0]
    sub = FrameMember.AttachmentSupport[0][0].Document.getObject(Feature).getSubObject(Support)
    return [sub.Vertexes[0].Point,sub.Vertexes[1].Point]

def getKnotCenter(FrameMembers):
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

# This does not account for How Attachment Rotation Works
# CODE-AUDIT: similar to MembersToKnotTuple(), but this is the active version used by commands and ID generation.
def MembersToKnotTuple2(FrameMembers):
    '''
    Input: Iterable filled with valid and attached FrameMembers
    Output: Knot
    Description:
    Turns the Selected Bodies / Frame Members into a Knot to be used in the KnotToID function
    '''

    tol = 1e-6

    KnotCenterPoint= getKnotCenter(FrameMembers=FrameMembers)
    # print(f"MembersToKnotTuple2 KnotCenter: {KnotCenterPoint}") #Debug

    Knot = []
    for FrameMember in FrameMembers:

        EndPoints = getEndpoints(FrameMember=FrameMember)

        # print(f"Enpoint[0]:{EndPoints[0]}")
        # print(f"Enpoint[0]:{EndPoints[1]}")

        if not EndPoints[0].isEqual(KnotCenterPoint,tol):
            EndPoints.reverse()
        if not EndPoints[0].isEqual(KnotCenterPoint,tol):
            print(f"Frame Member:{FrameMember.Name} is not Part of Knot")
            print(f"KnotCenterPoint:{KnotCenterPoint}")
            print(f"Enpoint[0]:{EndPoints[0]}")
            print(f"Enpoint[0]:{EndPoints[1]}")
            continue

        Direction = EndPoints[1] - EndPoints[0]

        Pad = getPadOfFrameMember(FrameMember=FrameMember)
        Nsym = getattr(Pad.Profile[0], "Nsym", 0)
        Type = getattr(Pad.Profile[0], "Type", "ProfileTypeNotAssignt")

        Rotation = math.degrees(FrameMember.AttachmentOffset.Rotation.Angle)
        Offset = FrameMember.AttachmentOffset.Base

        Knot.append({
        "Direction":  Direction ,
        "Offset":   Offset      ,
        "Type": Type	        ,
        "Rotation": Rotation    ,
        "Nsym": Nsym
        })

    return Knot

def MembersToBlankKnot(FrameMembers):

    doc = App.ActiveDocument

    tempDoc = App.newDocument() # TODO Make tempDoc not visibile while the function runs
    tempPath=saveDocumentToCache(doc=tempDoc) # needed when a link is in the document the FrameMembers are in
    part = tempDoc.addObject('Assembly::AssemblyObject','Assembly')
#    part = ndoc.addObject('App::Part','Part')
    part.Label = "Knot"
    # part.addProperty("App::PropertyString","KnotID","Knot")
    part.addProperty("App::PropertyLength","Size","Knot")
    part.addProperty("App::PropertyBool","isKnot","Knot")
    part.isKnot = True
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

    KnotCenter =getKnotCenter(FrameMembers=FrameMembers)

    for FrameMember in FrameMembers:
        EndPoints = getEndpoints(FrameMember)

        reverseMap = False
        if not EndPoints[0].isEqual(KnotCenter,1e-6):
            EndPoints.reverse()
            # reverseMap = True
        if  not EndPoints[0].isEqual(KnotCenter,1e-6):
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
        PadOld = getPadOfFrameMember(FrameMember=newFrameMember) # Default Sketch of the KnotMember
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
    if hasattr(obj,"isKnot") and obj.isKnot==True:
        return True
    else:
        return False

def findBlank(doc):
    return list(filter(isBlank,doc.Objects))[0]

#######################################################################################################
def isValidKnot(K)->bool:
    if not isinstance(K, (list, tuple)) or len(K) == 0:
        return False

    requiredKeys = ("Direction", "Offset", "Type", "Rotation", "Nsym")
    vectorType = type(App.Vector())
    numberTypes = (int, float)

    for Profile in K:
        if not isinstance(Profile, dict):
            return False
        if len(Profile) != 5:
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

def getAngleP2(Knot,n,m,n_key,m_key,deg=True)->float:
    Vn = Knot[n][n_key]
    Vm = Knot[m][m_key]
    alpha = Vn.getAngle(Vm) # returns the angle in rad

    if deg is True: # Is the function used in deg or rad mode
        return math.degrees(alpha)
    else:
        return alpha

def NormalizeKnot(Knot,deg=True):
    '''
    Docstring for NormalizeKnot

    :param K: Knot

    Normalizes the Contents in a Knot, to make them Uniform
    '''
    for Profile in Knot:
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

def KnotToID2(K:tuple,deg=True)->tuple:
    '''
    Converts the Knot into a Rotation independent identifier
    K: Knot
    deg: bool | decides if the calculations are done in Degrees or in Radiants
    '''
    Kn = list(K)
    NormalizeKnot(Kn,deg)
    n = len(K)
    KnotID=[]

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

            KnotID.append((a_min,phi,a_max))

    KnotID.sort(key=lambda x: (x[0],x[1],x[2]))

    return tuple(KnotID)

def AddPropertyKnotID(KnotAss):
    doc = KnotAss.Document
    FrameMembers = doc.findObjects('PartDesign::Body','Body','BaseEndProfile')
    Knot= MembersToKnotTuple2(FrameMembers=FrameMembers)
    KnotID = KnotToID2(K=Knot,deg=True)
    if KnotID is False:
        App.Console.PrintError("KnotID is False, Something is wrong")
        return None
    if not hasattr(KnotAss,"KnotID"):
        KnotAss.addProperty('App::PropertyMap',"KnotID","Knot")
    KnotAss.KnotID = {"KnotID":json.dumps(KnotID)}
    # return KnotID

def convert_to_tuple(element):
    if isinstance(element, list):
        return tuple(convert_to_tuple(e) for e in element)
    return element

def ReadKnotID(KnotAss)->tuple:
    rK= KnotAss.KnotID["KnotID"]
    KnotID = json.loads(rK)
    KnotID = convert_to_tuple(KnotID)
    return KnotID

def ReadKnotIDfromDocument(doc):
    blank = findBlank(doc=doc)
    return ReadKnotID(KnotAss=blank)

def PrintKnotIDfromDocument(doc):
    KnotID = ReadKnotIDfromDocument(doc)
    for entry in KnotID:
        print(entry)

def PrintKnotID(FrameMembers):
    '''
    This funktion was made to help Debuging the KnotID inside of FreeCAD
    To use this simply select all FrameMembers (Bodys) that belong to the Knot you would like to Knot the KnotID of
    This information will be printed in the Report view
    '''
    Knot = MembersToKnotTuple2(FrameMembers)
    print("Knot--------------------------------------------------------------------------------------")
    print(f"isvValidknot = {isValidKnot(Knot)}")
    for entry in Knot:
        print(entry)
    print("KnotID--------------------------------------------------------------------------------------")
    KnotID = KnotToID2(K=Knot,deg=True)
    print(f"TypeOf KnotID = {type(KnotID)}")
    if not type(KnotID) is bool:
        for entry in KnotID:
            print(entry)
    else:
        print(KnotID)


#----------------------------------------------------------------------------------------------------------------------------------
#Find Axis and Rotation

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

def TransformKnot(Knot,axis,angle,deg=True)->tuple:
    if deg is False: 				# Rotation argument for angle is degrees by default
        angle = math.degrees(angle) # so Radiants get converted
    rot = App.Rotation(axis,angle)
    for Profile in Knot:
        Profile["Direction"] = rot.multVec(Profile["Direction"])
    return tuple(Knot)

# CODE-AUDIT: similar to FindallMatches(); this is the active matcher used by InsertPlaceKnot().
def FindallMatches1(K1,K2,tol=1e-6)->tuple:

    '''
    K1: Knot1 Stationary,
    K2: Knot2 gets Transformed
    description:
    Finds all the matches, where K2 gets Transformed into K1 successfully
    retrun: tuple((App.Vector,float),...)
    '''
    L = len(K1) #K1 has the same length as K2, otherwise something went wrong earlier
    per = list(permutations(range(L),2))
    allPairings = list(combinations_with_replacement(per,2))

    def CheckPairing(Pairings,K1,K2,tol=1e-6):
        Results = []
        AllPairngMatch = []
        # [[1,2],[2,1],...]
        for pairing in Pairings:
            A1 = K2[pairing[1][0]]["Direction"] #Transformed
            A2 = K2[pairing[1][1]]["Direction"]

            B1 = K1[pairing[0][0]]["Direction"] #stationary
            B2 = K1[pairing[0][1]]["Direction"]

            A1,B1,A2,B2 = copyVec(A1),copyVec(B1),copyVec(A2),copyVec(B2)
            # print(f"Pairing:{pairing} | A1:{A1} | A2: {A2} | B1: {B1} | B2: {B2}")
            axisAngle:tuple|bool = FindAxisAngle2(A1,B1,A2,B2)

            if axisAngle is False:
                continue

            K2T = TransformKnot(copy.deepcopy(K2),axisAngle[0],axisAngle[1])  # ty:ignore[not-subscriptable]
            PairingMatch = []
            
            for profileK1 in K1:
                D1 = profileK1["Direction"]
                k = 0
                
                Match = False
                for profileK2 in K2T:
                    D2 = profileK2["Direction"]
                    Angle = D1.getAngle(D2)
                    if Angle > tol and Angle < math.radians(1):
                        # print(f"D1:{D1},D2:{D2}")
                        pass
                    if Angle < tol:
                        Match = True
                        PairingMatch.append(k)
                        break
                    k = k+1
                
                if not Match:
                    #print("Not Match")
                    break
            
            if len(PairingMatch) == len(K1):
                #  print(f"Match Found PairingMatch:{PairingMatch}")
                pass
            
            if len(PairingMatch) == len(K1) and not PairingMatch in AllPairngMatch:
                Results.append(axisAngle)
                AllPairngMatch.append(PairingMatch)
                # print("Match added")

        print(f"AllPairngMatch:{AllPairngMatch}")
        return Results

    Pairings =  CheckPairing(allPairings,K1,K2,tol)
    print(Pairings)
    return Pairings

def FindallMatches2(K1,K2,tol=1e-6):
    '''
    K1: Knot1 Stationary,
    K2: Knot2 gets Transformed
    description:
    Finds all the matches, where K2 gets Transformed into K1 successfully
    retrun: tuple((App.Vector,float),...)
    '''
    Results = []
    AllPairnigs = []
    N = len(K1)
    for k in range(N):
        B1 = K1[k]["Direction"]
        for i in range(N):
            if k == i:
                continue
            B2 = K1[i]["Direction"]
            for j in range(N):
                if j == i or j == k:
                    continue
                # B3 = K1[j]["Direction"]
                B3 =  (B1.cross(B2))
                for l in range(N):
                    A1 = K2[l]["Direction"]
                    for m in range(N):
                        if l == m:
                            continue
                        A2 = K2[m]["Direction"]
                        for n in range(N):
                            if n == m or n == l:
                                continue
                            # A3 = K2[n]["Direction"]
                            A3 = A1.cross(A2)

                            # print(f"{k}{i}{j}{l}{m}{n}")
                            # Matrizen V und W konstruieren
                            V = App.Base.Matrix()
                            V.setCol(0, B1)
                            V.setCol(1, B2)
                            V.setCol(2, B3)

                            W = App.Base.Matrix()
                            W.setCol(0, A1)
                            W.setCol(1, A2)
                            W.setCol(2, A3)

                            # Inverse von V berechnen
                            V_inv = V.inverse()

                            # Transformationsmatrix A = W * V_inv
                            A = W.multiply(V_inv)

                            allMacht = True
                            Pairings = []
                            for o in range(N):
                                D1 = A.multVec(K2[o]["Direction"])
                                Match = False
                                r = 0
                                for p in range(N):
                                    D2 = K1[p]["Direction"]
                                    Angle = abs(D1.getAngle(D2))
                                    if Angle < tol:
                                        Match = True
                                        Pairings.append((o,p))
                                        # Pairings.append((p))
                                        # print(f"D1:{D1} \t D2:{D2}\t with {k}{i}{j}{l}{m}{n} Match:{Match}")
                                        break
                                    # print(f"D1:{D1} \t D2:{D2} \t with {k}{i}{j}{l}{m}{n} Match:{Match}")
                                    r = r + 1
                                if Match is False:
                                    allMacht = False
                                    break

                            if allMacht is True:
                                AxisAngle = matrixToAxisAngle(A)
                                # print(A.decompose())
                                # print(AxisAngle)
                                if AxisAngle in Results:
                                    rr = 1
                                elif Pairings in AllPairnigs:
                                    rr = 2
                                else:
                                    Results.append(AxisAngle)
                                    AllPairnigs.append(Pairings)
                                    #print(f"Appended Pairing:{Pairings}")
    print(AllPairnigs)
    print(Results)
    return Results

def procesPairings(pairings):
    newP = []
    for pairing in pairings:
        newP.append((VecToTuple(FreeCADvector=pairing[0]),pairing[1]))
    return newP

def AddMatchesProperty(iKnotAss,pairings:tuple):
    if not hasattr(iKnotAss, "PossibleOrientations"):
        iKnotAss.addProperty('App::PropertyMap', "PossibleOrientations", "Orientations")
    iKnotAss.PossibleOrientations = {"Orientations": json.dumps(procesPairings(pairings))}

def readOrientations(Knot):
    rO = Knot.PossibleOrientations["Orientations"]
    pairings = json.loads(rO)
    newPairings = []
    for p in pairings:
        newPairings.append((itrToVec(itr=p[0]),p[1]))
    return newPairings

def PrintOrientations(Knot):
    print(f"Knot:{Knot.Name}")
    orientations = readOrientations(Knot)
    for orientation in orientations:
        print(f"Orientation:{orientation}")

def InsertKnot(target,Knot,aslink=True):

    if aslink:
        # print(f"InsertedKnotFile:{Knot.Document.FileName}")
        file = Knot.Document.FileName

        doc = App.openDocument(file,False,False)
        App.closeDocument(doc.Name)
        doc = App.openDocument(file,False,False)
        Knot = findBlank(doc)

        link = target.addObject('App::Link','Link')
        link.LinkedObject = Knot
        inserted = link
        link.Label = Knot.Label
    else:
        inserted = target.copyObject(Knot,True)
    return inserted


def PlaceKnot(Knot,KnotCenterPoint)->None:

    Knot.addExtension('Part::AttachExtensionPython')
    Knot.AttachmentSupport = KnotCenterPoint
    Knot.MapMode = "Translate"

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
        App.Console.PrintCritical("Condition: 'Knot.Size < FrameMember.Length / 2' not true \n")
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
            print("Knot is a Link, This is not implemented") #Finish this
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
            App.Console.PrintCritical("Condition: 'Knot.Size < FrameMember.Length / 2' not true \n")
            return
        FrameMember.setExpression(prop,exp)

def removeSizeExpressionFromMembers(FrameMember,ver):
    if ver == 1:
        prop = "OffsetEnd1"
    elif ver == 2:
        prop = "OffsetEnd2"
    else:
        print(" ver should be 1 or 2")
    FrameMember.setExpression(prop, None)

# CODE-AUDIT: unused placeholder; function body is pass and no references were found.
def addCurrentOrientationExpressionToKnot(Knot):
    pass
    

def NodeCenterVertex(KnotCenter, FrameMember):
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

    # Calculate distances to KnotCenter
    distance1 = KnotCenter.distanceToPoint(point1)
    distance2 = KnotCenter.distanceToPoint(point2)

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

def getEndprofiles(Knot):
    doc = Knot.Document
    Endprofiles = doc.findObjects('PartDesign::Body','Body','BaseEndProfile')
    Ends = {}
    for Endprofile in Endprofiles:
        Feature = Endprofile.AttachmentSupport[0][0]
        FeatureName = Feature.Name
        Support = Endprofile.AttachmentSupport[0][1][0]
        Obj = Endprofile.AttachmentSupport[0][0].Document.getObject(FeatureName)
        Edge = Obj.getSubObject(Support)
        Direction = Edge.tangentAt(0.5) # Only attached to line
        Ends.update({Endprofile.Name:Direction})

    return(Ends)

def FindEndProfileMatch(FrameMember,Endprofiles,KnotCenter,Orientation,deg=True):
    tol = 1e-6
    EndPoints = getEndpoints(FrameMember=FrameMember)
    if not EndPoints[0].isEqual(KnotCenter,tol):
            EndPoints.reverse()
    FrameMemberDirection = EndPoints[1] - EndPoints[0]

    axis = Orientation[0]
    angle = Orientation[1]
    if deg is False: 				# Rotation argument for angle is degrees by default
        angle = math.degrees(angle) # so Radiants get converted
    rot = App.Rotation(axis,angle)

    keys = Endprofiles.keys()
    EndProfileName = ""
    for key in keys:
        EndProfileDirection = Endprofiles[key]
        TransformedFrameMemberDirection = rot.multVec(EndProfileDirection)
        if IsSame(TransformedFrameMemberDirection,FrameMemberDirection,tol):
            EndProfileName = key
            break
    
    doc = FrameMember.Document
    EndprofileObj = doc.getObject(EndProfileName)

    return EndprofileObj

def OirentWorkaround(Binder,Endprofile,ver):

    #T = TransformIntoSharedCoordinates(Binder,Endprofile)
    T =TransformToGlobalPlacement(Binder,Endprofile)
    T1,T2 = T[0],T[1]
    T1 = T1.decompose()[1]
    T2 = T2.decompose()[1]

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
    
    print("OirentWorkaround")
    print(f"ver = {ver}")
    print(f"A1 = {A1}")
    print(f"A2 = {A2}")
    print(f"B1 = {B1}")
    print(f"B2 = {B2}")

    matrix = FindAxisAngle2(A1,B1,A2,B2,tol=1e-4,deg=True,matrix=True)
    if matrix is False:
        print("No Workaorund Found")
        return
    matrix = matrix.multiply(T1.inverse())

    AxisAngle = matrixToAxisAngle(matrix,deg=False)
    axis = AxisAngle[0]
    angle = AxisAngle[1]
    print(f"axis:{axis} | angle:{angle}")
    Binder.Placement.Rotation.Axis = axis
    Binder.Placement.Rotation.Angle = angle

def OrientKnot(Knot,Orientation,deg=True):

    axis = Orientation[0]
    angle = Orientation[1] #Angle in degrees
    Knot.Placement.Rotation.Axis = axis
    if deg:
        Knot.Placement.Rotation.Angle = math.radians(angle)
    else:
        Knot.Placement.Rotation.Angle = angle

    # Find FrameMembers
    FrameMembers = ReadFrameMembersFromKnot(Knot=Knot)

    # Find Endprofiles
    EndProfiles = getEndprofiles(Knot=Knot)

    # Find Ends
    KnotCenter = getKnotCenter(FrameMembers=FrameMembers)

    NodeInfo = {}
    for FrameMember in FrameMembers:
        ver = NodeCenterVertex(KnotCenter=KnotCenter,FrameMember=FrameMember)
        NodeInfo.update({FrameMember.Name : ver})
        if FrameMember.TypeId == 'App::Link':
            addLinkSizeExpressionToFrameMember(Node=Knot,LFrameMember=FrameMember,ver=ver)
        else:
            addSizeExpressionToFrameMember(Node=Knot,FrameMember=FrameMember,ver=ver)

        EndProfile = FindEndProfileMatch(FrameMember,EndProfiles,KnotCenter,Orientation,deg)

        Binders = FindBinders2(FrameMember)
        for Binder in Binders:
            if not hasattr(Binder,"EndLabel"):
                continue
            if Binder.EndLabel == 1 and ver == 1 or Binder.EndLabel == 2 and ver == 2:
                Binder.Support = EndProfile
                OirentWorkaround(Binder,EndProfile,ver)

    # Hide EndProfiles and Hide Directions
    Groups = Knot.getObjectsOfType('App::DocumentObjectGroup')
    print(Groups)
    for Group in Groups:
        if hasattr(Group,'EndProfiles'):
            Group.Visibility = False
        if hasattr(Group,'Directions'):
            Group.Visibility = False
    
    doc = Knot.Document
    doc.recompute()

def AddFrameMembersToKnot(Knot,FrameMembers):

    for k in range(len(FrameMembers)):
        newFrameMember = f"FrameMember{k}"
        Prop = Knot.addProperty('App::PropertyString', newFrameMember, "KnotMembers")
        val = f"{FrameMembers[k].Name}.Label"
        Knot.setExpression(newFrameMember, val)
        # print(val)
    Knot.Document.recompute()

def ReadFrameMembersFromKnot(Knot):
    Ex = Knot.ExpressionEngine
    filtered_list = [tup for tup in Ex if tup[0].startswith("FrameMember")]
    second_entries = [tup[1].split('.')[0] for tup in filtered_list]
    doc = App.getDocument(Knot.Document.Name)
    FrameMembers = []
    for str in second_entries:
        FrameMembers.append(doc.getObject(str))

    return FrameMembers

def PrintFrameMembersFromKnot(Knot): #Debug
    print(f"Knot:{Knot.Name}")
    for entry in ReadFrameMembersFromKnot(Knot=Knot):
        print(f"FrameMember:{entry}")

def InsertPlaceKnot(target,Knot,FrameMembers,aslink)->None:
    print("PlaceKnot")
    # print(FrameMembers)
    K1 = MembersToKnotTuple2(FrameMembers=FrameMembers)

    # print("Knot1--------------------------------------------------------------------------------------")
    # for entry in K1:
    #     print(entry)
    K2 = MembersToKnotTuple2(FrameMembers=list(findEndProfiles(Knot)))

    inserted=InsertKnot(target=target,Knot=Knot,aslink=aslink)

    App.setActiveDocument(target.Name)
    App.ActiveDocument=App.getDocument(target.Name)
    Gui.ActiveDocument=Gui.getDocument(target.Name)

    KnotCenter = getKnotCenter(FrameMembers=FrameMembers)

    # CODE-AUDIT: duplicated endpoint/center-vertex logic; similar to NodeCenterVertex().
    Feature = FrameMembers[0].AttachmentSupport[0][0]
    FeatureName = Feature.Name
    Support = FrameMembers[0].AttachmentSupport[0][1][0]
    Obj = FrameMembers[0].AttachmentSupport[0][0].Document.getObject(FeatureName)
    Edge = Obj.getSubObject(Support)
    ElementReverseMap = Edge.ElementReverseMap
    Vertexes= (ElementReverseMap["Vertex1"],ElementReverseMap["Vertex2"])

    if Obj.getSubObject(Vertexes[0]).Point.isEqual(KnotCenter,1e-6):
        ver= Vertexes[0]
        # ver= ElementReverseMap["Vertex1"]
        # print(f"KnotCenter:{KnotCenter} | {Obj.getSubObject(Vertexes[0]).Point} | {ver}") #Debug
    else:
        ver = Vertexes[1]
        # ver = ElementReverseMap["Vertex2"]
        # print(f"KnotCenter:{KnotCenter} | {Obj.getSubObject(Vertexes[1]).Point} | {ver}") #Debug

    attach=(Feature,ver)
    # print(attach)
    PlaceKnot(Knot=inserted,KnotCenterPoint=attach)

    # print("Knot2--------------------------------------------------------------------------------------")
    # for entry in K2:
    #     print(entry)

    tol = 1e-4
    allMatches = FindallMatches2(K1=K1,K2=K2,tol=tol)
    AddMatchesProperty(iKnotAss=inserted,pairings=allMatches)

    AddFrameMembersToKnot(Knot=inserted,FrameMembers=FrameMembers)

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

def RemoveKnot(Knot):
    doc = Knot.Document
    FrameMembers = ReadFrameMembersFromKnot(Knot=Knot)
    KnotCenter = getKnotCenter(FrameMembers=FrameMembers)
    for FrameMember in FrameMembers:
        ver = NodeCenterVertex(KnotCenter=KnotCenter,FrameMember=FrameMember)
        removeSizeExpressionFromMembers(FrameMember=FrameMember,ver=ver)

    delete_object_and_contents(Knot,doc)
    

# CODE-AUDIT: unused incomplete workflow; only calls RemoveKnot() and ignores target/aslink.
def ChangeKnot(target,OldKnot,NewKnot,aslink):
    FrameMembers = ReadFrameMembersFromKnot(OldKnot)
    RemoveKnot(OldKnot)
    InsertPlaceKnot(target,NewKnot,FrameMembers,aslink)
