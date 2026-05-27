'''
Logic To Generate Knot IDs
Solve for Axis Angel Rotation
Test Fit Logic TODO
Solve All results for Axis Rotation Rotation TODO

'''
################################ IMPORT ####################################################
from pathlib import Path
import sys
import json

import FreeCAD as App  # ty:ignore[unresolved-import]
import FreeCADGui as Gui  # ty:ignore[unresolved-import]
from FreeCAD import Vector  # ty:ignore[unresolved-import]
import Draft  # ty:ignore[unresolved-import]
import math
import copy
from itertools import combinations
from itertools import permutations
from itertools import combinations_with_replacement
from collections import Counter


from .ProfileLogic import insertEndProfile,findEndProfiles
from .utils.utils import copyVec,VecToTuple,itrToVec, saveDocumentToCache, deleteDocumentFromCache


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

def MembersToKnotTuple(FrameMembers)->tuple: #Selection only works with Bodies/Profiles that Belong to one Knot
	'''
	Input: Iterable filled with valid and attached FrameMembers
	Output: Knot
	Description:
	Turns the Selected Bodies / Frame Members into a Knot to be used in the KnotToID function
	'''
	################################################################################################
	#Get information from Bodies to turn into a "PreKnot" which then gets Processed into a Knot
	for Member in FrameMembers:
		print(Member.Label)
	# print(FrameMembers)
	PreKnot = []
	for obj in FrameMembers:
		# print("N")
		Feature = obj.AttachmentSupport[0][0].Name
		Support = obj.AttachmentSupport[0][1][0]
		# print(Feature)
		# print(Support)
		direction = obj.Placement.Rotation * App.Vector(0,0,1) # Not used
		Position = obj.Placement.Base # In the Local Coordinate System of the Parent Part/ Assembly | Results in Offset somehow
		Rotation = obj.AttachmentOffset.Rotation.Angle # In radiants
		Rotation = math.degrees(Rotation)



		# How do I determine which orientation of the Profile Faces the Knot, Directions always must show away from the Knot center Point

		Pad = getPadOfFrameMember(FrameMember=obj)
		Type = getattr(Pad.Profile[0], "Type", "ProfileTypeNotAssignt")
		sym = getattr(Pad.Profile[0], "Nsym", False)

		sub = App.ActiveDocument.getObject(Feature).getSubObject(Support)
		EndPoints = [sub.Vertexes[0].Point,sub.Vertexes[1].Point]

		data:dict =	{
				"Feature": Feature,
				"Support": Support,
				"direction":direction, #Not uses
				"Position": Position,
				"Rotation":Rotation,
				"Type": Type,
				"nsym": sym,
				"Points": EndPoints,
				}
		PreKnot.append(
			data
		)
	# print(PreKnot)
	#################################################################################

	KnotCenter = getKnotCenter(FrameMembers=FrameMembers)
	print(KnotCenter)

	PreKnot2 = []
	for data in PreKnot:
		if not data["Points"][0].isEqual(KnotCenter,1e-5):
			data["Points"].reverse()
		if  data["Points"][0].isEqual(KnotCenter,1e-5):
			PreKnot2.append(data)
		else:
			print("Rejected")
			print(data["Points"])

	##################################################################################

	Knot = []
	for i in range(len(PreKnot2)):
		d = PreKnot2[i]["Points"][1] - PreKnot2[i]["Points"][0]
		# if IsOpposite(d,PreKnot[i]["direction"]): #This was an experiment
		# 	d = -PreKnot[i]["direction"]
		# else:
		# 	d = PreKnot[i]["direction"]
		# print("II")

		Knot.append({
			"Direction": d	,
			"Offset": roundVector(PreKnot2[i]["Position"] - KnotCenter,6)	, # Is rounding the best solution? No normal use has an offset under 1mm anyway
			"Type": PreKnot2[i]["Type"]										,
			"Rotation": PreKnot2[i]["Rotation"]								,
			"Nsym": PreKnot2[i]["nsym"]										,
		})
	# print(Knot)
	return tuple(Knot)


# This does not account for How Attachment Rotation Works
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

#print(isValidKnot(Knot1))



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

########################################### Start | OLD Knot to ID | Not used

def updateKnot(K,Pn,data): # data = {"name":"value/Stuff"}
	Profile = K[Pn]
	Profile.update(data)
	return K

def removeKnotData(K,Pn,data): # data = "String"
	Profile = K[Pn]
	Profile.pop(data)
	return K

def removeKnotData2(Knot,data): # data = "String"
	for Profile in Knot:
		Profile.pop(data)

def SortProfiles(K)->list:
	'''
	Docstring for SortProfiles

	:param K: Knot
	:param tol: Tolerance
	Sorts the Profiles According to there Angle Sums
	'''
	def TypeSort(S):
		return S["Type"]
	K.sort(key=TypeSort)

	def RotationSort(S):
		return S["Rotation"]
	K.sort(key = RotationSort)

	for i in range(len(K)):
		AngelSum = 0
		for n in range(len(K)):
			alpha = getAngleP2(K,i,n,"Direction","Direction")
			AngelSum = AngelSum + alpha
		updateKnot(K,i,{"AngleSum":AngelSum})
	def AngleSort(S):
		return S["AngleSum"]
	K.sort(key=AngleSort)
	removeKnotData2(K,"AngleSum")
	return K

def KnotToID(K:tuple,deg=True)->tuple | bool:
	'''
	Converts the Knot into a Rotation independent identifier
	K: Knot
	deg: bool | decides if the calculations are done in Degrees or in Radiants
	'''
	if not isValidKnot(K):
		App.Console.PrintError("Knot is not Valid")
		return False
	Kn = list(K) # Does not Mute the original data
	NormalizeKnot(Kn,deg)
	SortProfiles(Kn)
	L= len(Kn)
	for i in range(L):
		Kn[i].update({
			"DirectionAngels":[
				getAngleP2(Kn,i,(i+1)%L,"Direction","Direction",deg),
				getAngleP2(Kn,i,(i+2)%L,"Direction","Direction",deg),
				getAngleP2(Kn,i,(i+3)%L,"Direction","Direction",deg),
			]
		})
		Kn[i].update({
			"OffsetAngels":[
				getAngleP2(Kn,i,(i+1)%L,"Offset","Direction",deg),
				getAngleP2(Kn,i,(i+2)%L,"Offset","Direction",deg),
				getAngleP2(Kn,i,(i+3)%L,"Offset","Direction",deg),
			]
		})
		for n in range(len(Kn[i]["OffsetAngels"])): #Because nan is not equal to nan, it gets replaced by "NotaNumber"
			if math.isnan(Kn[i]["OffsetAngels"][n]):
				Kn[i]["OffsetAngels"][n] = "NotaNumber"
		Kn[i].update({
			"OffsetRadius": Kn[i]["Offset"].Length
		})
	for Profile in Kn:
		Profile.pop("Direction")
		Profile.pop("Offset")
	return tuple(map(lambda x: x, Kn))
########################################### End | OLD Knot to ID | Not used

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

def FindAxisAngle(A1,B1,A2,B2,deg = True,tol = 1e-6)->tuple | bool:
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
	# print(A1,A2,B1,B2,"Results in")
	A1,B1,A2,B2 = A1.normalize(),B1.normalize(),A2.normalize(),B2.normalize()
	if not IsTransformend(A1,B1,A2,B2):
		return False

	if IsOpposite(A1,B1):
		E1 = A1
	else:
		N1 = A1.cross(B1)
		C1 = (A1+B1).normalize()
		E1 = N1.cross(C1)

	if IsOpposite(A2,B2): # Should Always be True if the first is True => Could be consolidated
		E2 = A2
	else:
		N2 = A2.cross(B2)
		C2 = (A2+B2).normalize()
		E2 = N2.cross(C2)

	# print(f"{E1}cross{E2}")
	axis = E1.cross(E2)
	# print(axis)
	if axis.Length<tol:
		# print("The Orientation does already fit")
		return (App.Vector(0,0,1),0) # This is when nothing needs to be changed
	axis = axis.normalize()

	A1p = A1.projectToPlane(Vector(0,0,0),axis)
	B1p = B1.projectToPlane(Vector(0,0,0),axis)

	angle = A1p.getAngle(B1p)

	# Test if angle needs a negative sign
	A1 = A1.normalize()
	rot = App.Rotation(axis, math.degrees(angle))
	T1 = rot.multVec(A1)
	T1 = T1.normalize()
	#print(T1.getAngle(B1))
	if T1.getAngle(B1)>tol: #getAngle interval 0,pi
		angle = -angle

	# One of the Printed Angels is Always Zer0
	# print(T1.getAngle(B1))
	# rot = App.Rotation(axis, math.degrees(angle))
	# T1 = rot.multVec(A1)
	# T1 = T1.normalize()
	# print(T1.getAngle(B1))

	if deg is True: # Is the function used in deg or rad mode
		# print((axis,math.degrees(angle)))
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

def isKnotMatch(K1,K2,tol = 1e-6)->bool: #What about tolerance ?????
	'''
	Finds out if the Knot 1 does match Knot 2
	Knot 1 is the Knot that is transformed to
	Knot 2 is the Transformed Knot
	'''

	for profileK1 in K1:
		D1 = profileK1["Direction"]
		Match = False
		for profileK2 in K2:
			D2 = profileK2["Direction"]
			if D2.getAngle(D1) <= tol:
				Match = True
		if not Match:
			return False

	return True

def isAxisAngleInList(axisAngle,list,tol = 1e-6)->bool:
	'''
	This function returns if an axisAngle Transformation is already in the list
	axisAngle: (App.Vector(x,y,z),Angle)
	axis: App.Vector
	Angle: float
	tol: float | tolerance of being considered the same
	'''
	for axisAngle1 in list:
		axis1 = axisAngle1[0]
		axis2 = axisAngle[0]
		angle1 = axisAngle1[1]
		angle2 = axisAngle[1]
		if angle2 == 0 or IsOpposite(axis1,axis2,tol) and abs(angle1 + angle2) < tol or IsSame(axis1,axis2,tol) and abs(angle1 - angle2) < tol: #and ( or angle1 + angle2 < tol)or angle2 == 0:
			return True
	return False

# Add Multithreading Worker and Collector style to improve Computation speed
def FindallMatches(K1,K2)->tuple:
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
        for pairing in Pairings:
            A1 = K2[pairing[1][0]]["Direction"] #Transformed
            A2 = K2[pairing[1][1]]["Direction"]

            B1 = K1[pairing[0][0]]["Direction"] #stationary
            B2 = K1[pairing[0][1]]["Direction"]

            A1,B1,A2,B2 = copyVec(A1),copyVec(B1),copyVec(A2),copyVec(B2)

            axisAngle:tuple|bool = FindAxisAngle(A1,B1,A2,B2)
            # print(axisAngle)
            if axisAngle is not False and isAxisAngleInList(axisAngle,Results):
                # print("skipped as already in Results") #Debug
                continue
            if axisAngle is not False:
                K2T = TransformKnot(copy.deepcopy(K2),axisAngle[0],axisAngle[1]) # deepcopy to not mute the original knot  # ty:ignore[not-subscriptable]

                #Debug
                # for i in range(len(K1)):
                # 	print(K1[i])
                # 	print(K2T[i])
                # print(pairing)
                # print(axisAngle)

                if isKnotMatch(K1=K1,K2=K2T) is True: #Rework the is match function
                    Results.append(axisAngle)
                    # print("Success") #Debug
                    # print(axisAngle)

        return tuple(Results)

    return CheckPairing(allPairings,K1,K2)

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

def OrientKnot(Knot,Orientation):
    axis = Orientation[0]
    angle = Orientation[1]
    Knot.Placement.Rotation.Axis = axis
    Knot.Placement.Rotation.Angle = angle

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
    return second_entries

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

    allMatches = FindallMatches(K1=K1,K2=K2)
    AddMatchesProperty(iKnotAss=inserted,pairings=allMatches)

    AddFrameMembersToKnot(Knot=inserted,FrameMembers=FrameMembers)
