'''
Logic To Generate Knot IDs
Solve for Axis Angel Rotation
Test Fit Logic TODO
Solve All results for Axis Rotation Rotation TODO

'''
################################ IMPORT ####################################################
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


from .ProfileLogic import insertEndProfile,findEndProfiles
from .utils.utils import copyVec,VecToTuple,itrToVec, saveDocumentToCache, deleteDocumentFromCache, FindBinders2


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
    GroupeEndProfiles = tempDoc.addObject('App::DocumentObjectGroup','Group')
    part.addObject(GroupeEndProfiles)
    GroupeEndProfiles.Label = "EndProfiles"

    KnotCenter =getKnotCenter(FrameMembers=FrameMembers)

    for FrameMember in FrameMembers:
        EndPoints = getEndpoints(FrameMember)

        reverseMap = False
        if not EndPoints[0].isEqual(KnotCenter,1e-6):
            EndPoints.reverse()
            reverseMap = True
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

def IsTransformend(A1,B1,A2,B2,tol = 1e-6)->bool:
	a = A1.getAngle(A2)
	b = B1.getAngle(B2)
	if a - b < tol: #What about Tolerance
		return True
	else:
		print("Vector Pairs A1 A2 does not Match B1 B2") #Debug
		return False

# CODE-AUDIT: similar responsibility as FindAxisAngle(), but used by FindallMatches2().
def FindAxisAngle2(A1,B1,A2,B2,deg = True,tol = 1e-6):
	'''
	Find Axis Rotation, Returns the Axis and Rotation Transformation, That A1 and A2 get Transformend into B1 and B2 around the Origin(0,0,0)
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

	A1,B1,A2,B2 = A1.normalize(),B1.normalize(),A2.normalize(),B2.normalize()
	if not IsTransformend(A1,B1,A2,B2):
		return False
	
	if IsSame(A1,B1,tol) and IsSame(A2,B2,tol): #Is already transformed
		return(App.Vector(1,0,0),0)


	if IsOpposite(A1,A2,tol): #If A1 is opposite to A2 then B1 is also oppisite to B2 when IsTransformend is True
		axis = A1.cross(B1)
		angle = A1.getAngle(B1)

		rot = App.Rotation(axis, math.degrees(angle))
		T1 = rot.multVec(A1)
		#print(T1.getAngle(B1))
		if T1.getAngle(B1)>tol: #getAngle interval 0,pi
			angle = -angle

		if deg is True: # Is the function used in deg or rad mode
			return (axis,math.degrees(angle))
		else:
			return (axis,angle)


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

	Ap = App.Placement()
	Ap.Matrix = A
	axis = Ap.Rotation.Axis
	angle = Ap.Rotation.Angle

	if deg is True: # Is the function used in deg or rad mode
		return (axis,math.degrees(angle))
	else:
		return (axis,angle)


def TransformKnot(Knot,axis,angle,deg=True)->tuple:
	if deg is False: 				# Rotation argument for angle is degrees by default
		angle = math.degrees(angle) # so Radiants get converted
	rot = App.Rotation(axis,angle)
	for Profile in Knot:
		Profile["Direction"] = rot.multVec(Profile["Direction"])
	return tuple(Knot)

# CODE-AUDIT: similar to FindallMatches(); this is the active matcher used by InsertPlaceKnot().
def FindallMatches2(K1,K2)->tuple:
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

	def CheckPairing(Pairings,K1,K2):
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
			PairingMatch = [] #[[]] * len(K1)
			# M = [1,2,3]
			n = 0
			tol = 1e-5
			
			for profileK2 in K2T:
				D1 = profileK2["Direction"]
				k = 0
				
				Match = False
				for profileK1 in K1:
					D2 = profileK1["Direction"]
					Angle = D2.getAngle(D1)
					if Angle <= tol:
						PairingMatch.append(k)
						Match = True
						# print("This is a Match")
						break
					
					# print(f"Angle D1:{D1} D2:{D2} is:{Angle}")
					k = k +1
				if not Match:
					# App.Console.PrintDeveloperError(f"Not Match: {axisAngle},Continue to next pairing \n")
					break
			if PairingMatch in AllPairngMatch:
				print(f"Duplicate Found:{PairingMatch}")
				continue
			elif not Match:
				continue
			print("Matach Found")
			AllPairngMatch.append(PairingMatch)
			Results.append(axisAngle)
		print(AllPairngMatch)
		return tuple(Results)
	
	Pairings =  CheckPairing(allPairings,K1,K2)
	print(Pairings)
	return Pairings

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
	if ver == 0:
		prop = "OffsetEnd2"
	elif ver == 1:
		prop = "OffsetEnd1"
	else:
		print(" ver should be 0 or 1 ")
		return
	if Node.Size > FrameMember.Length / 2:
		App.Console.PrintCritical("Condition: 'Knot.Size < FrameMember.Length / 2' not true \n")
		return
	FrameMember.setExpression(prop,exp)

def removeSizeExpressionFromMembers(FrameMember,ver):
	if ver == 0:
		prop = "OffsetEnd2"
	elif ver == 1:
		prop = "OffsetEnd1"
	else:
		print(" ver should be 0 or 1 ")
	FrameMember.setExpression(prop, None)

# CODE-AUDIT: unused placeholder; function body is pass and no references were found.
def addCurrentOrientationExpressionToKnot(Knot):
	pass

def NodeCenterVertex(KnotCenter,FrameMember):
	Feature = FrameMember.AttachmentSupport[0][0]
	FeatureName = Feature.Name
	Support = FrameMember.AttachmentSupport[0][1][0]
	Obj = FrameMember.AttachmentSupport[0][0].Document.getObject(FeatureName)
	Edge = Obj.getSubObject(Support)
	ElementReverseMap = Edge.ElementReverseMap
	Vertexes= (ElementReverseMap["Vertex1"],ElementReverseMap["Vertex2"])

	if Obj.getSubObject(Vertexes[0]).Point.isEqual(KnotCenter,1e-6):
		ver = 0
		# ver= ElementReverseMap["Vertex1"]
		# print(f"KnotCenter:{KnotCenter} | {Obj.getSubObject(Vertexes[0]).Point} | {ver}") #Debug
	else:
		ver = 1
		# ver = ElementReverseMap["Vertex2"]
        # print(f"KnotCenter:{KnotCenter} | {Obj.getSubObject(Vertexes[1]).Point} | {ver}") #Debug
	return ver


def OrientKnot(Knot,Orientation):

    # Find FrameMembers
	FrameMembers = ReadFrameMembersFromKnot(Knot=Knot)

    # Find Ends
	KnotCenter = getKnotCenter(FrameMembers=FrameMembers)

	NodeInfo = {}
	for FrameMember in FrameMembers:
		ver = NodeCenterVertex(KnotCenter=KnotCenter,FrameMember=FrameMember)
		NodeInfo.update({FrameMember.Name : ver})
		addSizeExpressionToFrameMember(Node=Knot,FrameMember=FrameMember,ver=ver)

		EndProfile = 1 #TODO Find the Fitting Endprofile from the Knot for this orientation

		Binders = FindBinders2(FrameMember)
		for Binder in Binders:
			if Binder.EndLabel == 2 and ver == 0 or Binder.EndLabel == 1 and ver == 1:
				#Binder.Support = EndProfile
				print("Binder")


	axis = Orientation[0]
	angle = Orientation[1]
	Knot.Placement.Rotation.Axis = axis
	Knot.Placement.Rotation.Angle = math.radians(angle)

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

    allMatches = FindallMatches2(K1=K1,K2=K2)
    AddMatchesProperty(iKnotAss=inserted,pairings=allMatches)

    AddFrameMembersToKnot(Knot=inserted,FrameMembers=FrameMembers)

def delete_object_and_contents(obj):
    doc = obj.Document
    if hasattr(obj, "Group"):
        # Alle Objekte in der Gruppe löschen
        for sub_obj in obj.Group:
            delete_object_and_contents(sub_obj)
    doc.removeObject(obj.Name)

def RemoveKnot(Knot):
	FrameMembers = ReadFrameMembersFromKnot(Knot=Knot)
	KnotCenter = getKnotCenter(FrameMembers=FrameMembers)
	for FrameMember in FrameMembers:
		ver = NodeCenterVertex(KnotCenter=KnotCenter,FrameMember=FrameMember)
		removeSizeExpressionFromMembers(FrameMember=FrameMember,ver=ver)

	delete_object_and_contents(Knot)
	

# CODE-AUDIT: unused incomplete workflow; only calls RemoveKnot() and ignores target/aslink.
def ChangeKnot(target,OldKnot,aslink):
	RemoveKnot(OldKnot)
