import FreeCAD as App  # ty:ignore[unresolved-import]
import FreeCADGui as Gui  # ty:ignore[unresolved-import]
import os
from pathlib import Path


import math
import json

############################# Sketch Logic ####################################

#Sadly this is not accurate, So i need to TODO find a better method
#proceed anyway because it has not that high priority
def getAlignments(sketch)->tuple:
	'''
	What it does:
		Extracts bounding box coordinates from a sketch geometry.

	Input:
		sketch: FreeCAD sketch object with a Shape attribute

	Returns:
		tuple[float]: (left, middleH, right, top, middleV, bottom) coordinates in mm

	NOTE: if this still uses BoundingBox it is sadly not that accurate (0.1mm)
	'''
	if Gui is None:
		raise RuntimeError("getAlignments requires FreeCADGui. Use getAligments2 in App/headless code.")

	previousVisibility = sketch.Visibility
	sketch.Visibility = True
	sketchGui = Gui.getDocument(sketch.Document).getObject(sketch.Name)
	previousDeviation =sketchGui.Deviation
	sketchGui.Deviation = 0.01

	shp  = sketch.Shape
	bbx = shp.BoundBox
	left:float = bbx.XMin
	right:float = bbx.XMax
	middleH:float = bbx.Center.x
	top:float = bbx.YMax
	bottom:float = bbx.YMin
	middleV:float = bbx.Center.y

	sketchGui.Deviation = previousDeviation
	sketch.Visibility = previousVisibility
	return (left , middleH , right , top , middleV , bottom)


#################################_getAligments2_MadeWithCodex#########################################
def _normalizeAngle(angle: float) -> float:
    return angle % (2 * math.pi)

def _isAngleOnArc(start: float, end: float, angle: float, tolerance: float = 1e-9) -> bool:
    start = _normalizeAngle(start)
    end = _normalizeAngle(end)
    angle = _normalizeAngle(angle)

    if math.isclose(start, end, abs_tol=tolerance):
        return True

    sweep = (end - start) % (2 * math.pi)
    position = (angle - start) % (2 * math.pi)
    return position <= sweep + tolerance

def _collectDiscretizedPoints(geometry, point_count: int = 200) -> list[tuple[float, float]]:
    try:
        shape = geometry.toShape()
        points = shape.discretize(Number=point_count)
    except Exception:
        points = []

    return [(point.x, point.y) for point in points]

def _getGeometryPoints(geometry) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []

    if hasattr(geometry, "StartPoint"):
        points.append((geometry.StartPoint.x, geometry.StartPoint.y))
    if hasattr(geometry, "EndPoint"):
        points.append((geometry.EndPoint.x, geometry.EndPoint.y))
    if hasattr(geometry, "Point"):
        points.append((geometry.Point.x, geometry.Point.y))

    if hasattr(geometry, "Center") and hasattr(geometry, "Radius"):
        center_x = geometry.Center.x
        center_y = geometry.Center.y
        radius = geometry.Radius
        candidate_angles = (0.0, math.pi / 2, math.pi, 3 * math.pi / 2)

        if hasattr(geometry, "FirstParameter") and hasattr(geometry, "LastParameter"):
            start = geometry.FirstParameter
            end = geometry.LastParameter
            for angle in candidate_angles:
                if _isAngleOnArc(start, end, angle):
                    points.append((center_x + radius * math.cos(angle), center_y + radius * math.sin(angle)))
        else:
            points.extend([
                (center_x + radius, center_y),
                (center_x - radius, center_y),
                (center_x, center_y + radius),
                (center_x, center_y - radius),
            ])

    if hasattr(geometry, "Center") and hasattr(geometry, "MajorAxis") and hasattr(geometry, "MinorAxis"):
        center_x = geometry.Center.x
        center_y = geometry.Center.y
        major_axis = geometry.MajorAxis
        minor_axis = geometry.MinorAxis
        candidate_angles = [
            math.atan2(minor_axis.x, major_axis.x),
            math.atan2(minor_axis.y, major_axis.y),
        ]

        for angle in list(candidate_angles):
            candidate_angles.append(angle + math.pi)

        first_parameter = getattr(geometry, "FirstParameter", None)
        last_parameter = getattr(geometry, "LastParameter", None)

        for angle in candidate_angles:
            if first_parameter is not None and last_parameter is not None:
                if not _isAngleOnArc(first_parameter, last_parameter, angle):
                    continue
            x = center_x + major_axis.x * math.cos(angle) + minor_axis.x * math.sin(angle)
            y = center_y + major_axis.y * math.cos(angle) + minor_axis.y * math.sin(angle)
            points.append((x, y))

    if len(points) < 2:
        points.extend(_collectDiscretizedPoints(geometry))

    return points

def getAligments2(sketch) -> tuple:
    '''
    What it does:
        Extracts the same alignment coordinates as getAlignments, but only from
        App-side sketch geometry without using Shape.BoundBox or FreeCADGui.

    Input:
        sketch: FreeCAD sketch object with Geometry data

    Returns:
        tuple[float]: (left, middleH, right, top, middleV, bottom) coordinates in mm
    '''
    points: list[tuple[float, float]] = []

    for geometry in getattr(sketch, "Geometry", ()):
        points.extend(_getGeometryPoints(geometry))

    if not points:
        raise ValueError(f"Sketch {sketch.Name} does not contain usable geometry for alignment extraction.")

    x_values = [point[0] for point in points]
    y_values = [point[1] for point in points]

    left = min(x_values)
    right = max(x_values)
    top = max(y_values)
    bottom = min(y_values)
    middleH = (left + right) / 2
    middleV = (top + bottom) / 2

    return (left, middleH, right, top, middleV, bottom)

########################################################################################

def getArea(sketch,Rotation:float, deg=True)->float:
	'''
	What it does:
		Calculates intersection area between original sketch and rotated copy using Boolean cut operation.

	Input:
		sketch: FreeCAD sketch object
		Rotation: rotation angle value (float)
		deg: if True, Rotation is in degrees; if False, in radians (bool, default=True)

	Returns:
		float: intersection area value in mm²; returns 0.0 for perfect rotational symmetry
	'''
	doc = sketch.Document
	Face1 = doc.addObject("Part::Face", "Face")
	Face1.Sources = (sketch,)
	Face2 = doc.addObject("Part::Face", "Face")
	Face2.Sources = (sketch,)

	if deg is True:
		Rotation: int | float = math.radians(Rotation)

	Face2.Placement.Rotation.Angle = Rotation

	from BOPTools import BOPFeatures  # ty:ignore[unresolved-import]
	bp = BOPFeatures.BOPFeatures(doc)
	cut =bp.make_cut([Face1.Name, Face2.Name, ])
	doc.recompute()

	Area = cut.Shape.Area
	doc.removeObject(cut.Name)
	doc.removeObject(Face1.Name)
	doc.removeObject(Face2.Name)
	return Area

def getNsym(sketch,MaxNsym:int)->int:
	'''
	What it does:
		Determines rotational symmetry order by iterating through possible divisions
		and checking if intersection area equals zero (perfect symmetry).

	Input:
		sketch: FreeCAD sketch object to analyze
		MaxNsym: maximum symmetry order to test (int)

	Returns:
		int: symmetry order Nsym (number of identical rotations);
		     -1 if number of matches equals MaxNsym (inconclusive result)
	'''
	Nsym:int = 1
	matches = 0
	for iNsym in range(1,MaxNsym+1):
		Angle:float = 360/iNsym
		Area:float = getArea(sketch=sketch,Rotation=Angle,deg=True)
		if Area == 0.0:
			Nsym: int = iNsym
			matches: int = matches + 1

	if matches == MaxNsym:
		Nsym = -1

	return Nsym

def addInfoToSketch(sketch,MaxNsym:int)->None:
    '''
    What it does:
        Calculates symmetry properties and alignment coordinates, then adds them as
        read-only properties to the sketch object.

    Input:
        sketch: FreeCAD sketch object to annotate
        MaxNsym: maximum rotational symmetry order to test (int)

    Returns:
        None; modifies sketch in-place by adding properties:
        - Nsym: PropertyInteger with rotational symmetry count
        - left, middleH, right, top, middleV, bottom: PropertyDistance values (read-only)
    '''
    Nsym: int = getNsym(sketch=sketch,MaxNsym=MaxNsym)
    if not hasattr(sketch, "Nsym"):
        sketch.addProperty('App::PropertyInteger', 'Nsym', 'Info', '')
    sketch.setPropertyStatus('Nsym',"-ReadOnly")
    sketch.Nsym = Nsym
    sketch.setPropertyStatus('Nsym',"ReadOnly")

    Alignments: tuple[float] = getAligments2(sketch=sketch)

    AlignmentData: dict[str, float] = {
    "left":Alignments[0],
    "middleH":Alignments[1],    # ty:ignore[index-out-of-bounds]
    "right":Alignments[2],      # ty:ignore[index-out-of-bounds]
    "top":Alignments[3],        # ty:ignore[index-out-of-bounds]
    "middleV":Alignments[4],    # ty:ignore[index-out-of-bounds]
    "bottom":Alignments[5]      # ty:ignore[index-out-of-bounds]
    }

    for Alignment in AlignmentData:
        if not hasattr(sketch,Alignment):
            sketch.addProperty('App::PropertyDistance',Alignment,'Info','')
        expression = f"{AlignmentData[Alignment]}mm"
        sketch.setPropertyStatus(Alignment,"-ReadOnly")
        sketch.setExpression(Alignment,expression)
        sketch.Document.recompute()
        sketch.setExpression(Alignment,None)
        sketch.setPropertyStatus(Alignment,"ReadOnly")

    if not hasattr(sketch,'Type'):
        sketch.addProperty('App::PropertyString','Type','ProfileType','The Type of the Sketch is Critical to Finding the fitting Knot, for cleaity it should match the Sketch label')
        sketch.Type = "Unknown"

    sketch.Document.recompute()

    return None

def addInfoToSketches(sketches,MaxNsym:int)->None:
    '''

    '''
    for sketch in sketches:
        addInfoToSketch(sketch=sketch,MaxNsym=MaxNsym)
    return None

def isValidProfileSketch(sketch)->bool:
	'''
	What it does:
		Validates that a sketch has all required annotation properties.

	Input:
		sketch: FreeCAD sketch object to validate

	Returns:
		bool: True if sketch has all required properties (Nsym and alignment coordinates);
		      False otherwise
	'''
	required_attributes = ("Nsym", "left", "middleH", "right", "top", "middleV", "bottom")
	return all(hasattr(sketch, attr) for attr in required_attributes)

###############################################################################

def getBaseProfilePath(experiment=False)->str|None:
    addon_path = Path(App.getUserAppDataDir()) / "Mod" / "FramesAndNodes" / "freecad" / "FramesAndNodes" / "resources"
    BaseProfilePath = addon_path / "BaseModels" / "BaseProfile.FCstd"
    if experiment:
         BaseProfilePath = addon_path / "BaseModels" / "BaseProfileTest1.FCstd"
         print("Experiment mode for Profiles is Aktive")

    if not os.path.exists(BaseProfilePath):
        App.Console.PrintError(r"The File Path was not correctly found. | FramesAndNodes\freecad\FramesAndNodes\resources\BaseModels")
        return None

    return str(BaseProfilePath)

def getEndProfilePath()->str|None:
    addon_path = Path(App.getUserAppDataDir()) / "Mod" / "FramesAndNodes" / "freecad" / "FramesAndNodes" / "resources"
    EndProfilePath = addon_path / "BaseModels" / "BaseEndProfile.FCstd"

    if not os.path.exists(EndProfilePath):
        App.Console.PrintError(r"The File Path was not correctly found. | FramesAndNodes\freecad\FramesAndNodes\resources\BaseModels")
        return None

    return str(EndProfilePath)

# Should i do this in the TaskPanel or the Prefrences of this Workbench Addon
# Probaly in prefrences as it would not be appropiate to create Multi-Body files in a professional setting
# Hobby useres would be annoied at generating so much new files when making a Frame
# Maybe i could add a settings field like in the Modern PartDesign TaskPanels
def insertProfile(target,asLink=False,createDir=True,Dir="FrameMembers"):
    BaseProfileFile = App.openDocument(getBaseProfilePath(experiment=False))
    BaseProfile = BaseProfileFile.getObject("Body")
    FrameMemberLabel = 'FrameMember'
    if asLink:
        if not target.isSaved():
            App.Console.PrintError("File is not saved, please save file")
            App.closeDocument(BaseProfileFile.Name)
            return None
        ndoc = App.newDocument()
        targetdir = Path(target.FileName).parent
        if createDir:
            targetdir = targetdir / Dir
            targetdir.mkdir(parents=True, exist_ok=True)
        n = 1
        FileName = FrameMemberLabel
        name = targetdir / (FileName + ".FCStd")
        while name.exists():
            name = targetdir / (FileName + "{:03}.FCStd".format(n))
            n = n + 1
        ndoc.saveAs(str(name))
        ndoc.save()                                                                     # Should this be Asked about instead ?
        # ndoc.setAutoCreated = True
        linkinsert=ndoc.copyObject(BaseProfile,True)
        link = target.addObject('App::Link','Link')
        link.Label = f"{FileName}{n:03}"
        # link.LinkCopyOnChange = "Enabled"
        link.LinkedObject =linkinsert
        inserted = link
    else:
        inserted = target.copyObject(BaseProfile,True)
        target.findObjects('PartDesign::Body','Body',FrameMemberLabel)
        inserted.Label = "FrameMember"
    target.recompute()
    App.closeDocument(BaseProfileFile.Name)
    App.setActiveDocument(target.Name)
    if App.GuiUp:
        Gui.setActiveDocument(target.Name)
    return inserted

def insertEndProfile(target):
    BaseProfileFile = App.openDocument(getEndProfilePath())
    BaseProfile = BaseProfileFile.getObject("Body")
    inserted = target.copyObject(BaseProfile,True)
    target.recompute()
    App.closeDocument(BaseProfileFile.Name)
    return inserted

def isEndProfile(obj)->bool:
    required_attributes = ("Alignment", "left", "middleH", "right", "top", "middleV", "bottom")
    if not all(hasattr(obj,attr) for attr in required_attributes):
        return False
    return True

# Expand to work with lists and KnotAssambly / Knot Part
def findEndProfiles(Knot):
    return list(filter(isEndProfile,Knot.Group))

def isValidFrameMember(body)->bool:
	required_attributes = ("Length","Alignment", "OffsetEnd1", "OffsetEnd2", "OffsetX", "OffsetY"
							, "left", "middleH", "right", "top", "middleV", "bottom")
	if not all(hasattr(body, attr) for attr in required_attributes):
		return False
	return True


#   0   1   2
#   3   4   5
#   6   7   8

# 0 => Top | Left
# 1 => Top | Middle
# 2 => Top | Right
# 3 => Middle | Left
# 4 => Middle | Middle
# 5 => Middle | Right
# 6 => Bottom | Left
# 7 => Bottom | Middle
# 8 => Bottom | Right


def SetAlignementProperties(profile)->None:
    if not hasattr(profile,"Alignment"):
        profile.addProperty('App::PropertyEnumeration',"Alignment","Profile")
    Alignment: list[str] = ["Top | Left","Top | Middle","Top | Right","Middle | Left","Middle | Middle","Middle | Right","Bottom | Left","Bottom | Middle","Bottom | Right","Coustom | Coustom"]
    profile.Alignment: list[str] = Alignment  # ty:ignore[invalid-type-form]
    if not hasattr(profile,"AttachOffset"):
        profile.addExtension('Part::AttachExtensionPython')
    expressionX = "Alignment == 0 ? -left : (Alignment == 3 ? -left : (Alignment == 6 ? -left : (Alignment == 1 ? middleH : (Alignment == 4 ? middleH : (Alignment == 7 ? middleH : (Alignment == 2 ? -right : (Alignment == 5 ? -right : (Alignment == 8 ? -right : OffsetX))))))))"
    profile.setExpression(".AttachmentOffset.Base.x",expressionX)
    expressionY = "Alignment == 0 ? -top : (Alignment == 1 ? -top : (Alignment == 2 ? -top : (Alignment == 3 ? middleV : (Alignment == 4 ? middleV : (Alignment == 5 ? middleV : (Alignment == 6 ? -bottom : (Alignment == 7 ? -bottom : (Alignment == 8 ? -bottom : OffsetY))))))))"
    profile.setExpression(".AttachmentOffset.Base.y",expressionY)

    RequiredProperties = ("left", "middleH", "right", "top", "middleV", "bottom")
    for Property in RequiredProperties:
        if not hasattr(profile,Property):
            profile.addProperty('App::PropertyDistance',Property,'SketchData')
        expression = f"Pad.Profile[0].{Property} ? Pad.Profile[0].{Property} : 0"
        profile.setExpression(Property,expression)

def SetLinkedProperties(link)->None:

    expressionX = "Alignment == 0 ? -LinkedObject.left : (Alignment == 3 ? -LinkedObject.left : (Alignment == 6 ? -LinkedObject.left : (Alignment == 1 ? LinkedObject.middleH : (Alignment == 4 ? LinkedObject.middleH : (Alignment == 7 ? LinkedObject.middleH : (Alignment == 2 ? -LinkedObject.right : (Alignment == 5 ? -LinkedObject.right : (Alignment == 8 ? -LinkedObject.right : LinkedObject.OffsetX))))))))"
    link.setExpression(".AttachmentOffset.Base.x",expressionX)
    expressionY = "Alignment == 0 ? -LinkedObject.top : (Alignment == 1 ? -LinkedObject.top : (Alignment == 2 ? -LinkedObject.top : (Alignment == 3 ? LinkedObject.middleV : (Alignment == 4 ? LinkedObject.middleV : (Alignment == 5 ? LinkedObject.middleV : (Alignment == 6 ? -LinkedObject.bottom : (Alignment == 7 ? -LinkedObject.bottom : (Alignment == 8 ? -LinkedObject.bottom : LinkedObject.OffsetY))))))))"
    link.setExpression(".AttachmentOffset.Base.y",expressionY)

    link.setExpression(".AttachmentOffset.Rotation.Angle","LinkedObject.RotationAngle")

def AddlengthExpression(profile):
    Feature = profile.AttachmentSupport[0][0].Name
    Support = profile.AttachmentSupport[0][1][0]
    expression = f"{Feature}.Shape.{Support}.Length"
    profile.setExpression("Length",expression)

# This works but looks ver ugly in the TreeView
def AddLinkedLengthExpression(link):
    Body = link.getLinkedObject()
    Binder =Body.newObject('PartDesign::SubShapeBinder') #Maybe work with a link instead of a subshape binder
    Body.Document.recompute()
    Binder.Support = link.AttachmentSupport
    group = Body.Group
    if group and group[0] != Binder:
        Body.Group = [Binder] + [feature for feature in group if feature != Binder]
    expression = f"{Binder.Name}.Shape.Length"
    Body.setExpression("Length",expression)
    Binder.Visibility = False


def AttachFrameMember(FrameMember,Edge,OffsetX,OffsetY,Alignment,RotationAngle, deg = True):
    '''
    FrameMember: Body
    Edge: (Object,Edge)
    OffsetX: float
    OffsetY: flaot
    Alignment: int (1->8) 9=> Coustom | Coustom
    #   0   1   2
    #   3   4   5
    #   6   7   8
    '''


    FrameMember.addExtension('Part::AttachExtensionPython')
    FrameMember.AttachmentSupport = Edge
    FrameMember.MapMode = 'NormalToEdge'
    FrameMember.MapPathParameter = 0.5
    FrameMember.Document.recompute()

    FrameMember.OffsetX = OffsetX
    FrameMember.OffsetY = OffsetY

    FrameMember.Alignment = Alignment

    if not FrameMember.isDerivedFrom("App::Link"):
        AddlengthExpression(profile=FrameMember)

    if FrameMember.isDerivedFrom("App::Link"):
        SetLinkedProperties(FrameMember)
        AddLinkedLengthExpression(FrameMember)

    if deg is True:
        RotationAngle:float = math.radians(RotationAngle)
    FrameMember.RotationAngle = RotationAngle



def ReplaceSketch(profile,Sketch)->None:
    '''
    profile: Body
    Sketch: SketchObj
    '''

    if profile.isDerivedFrom("App::Link"):
        profile= profile.getLinkedObject()
    targetDoc = profile.Document

    # This should be a utililty function it is used more then ones like: getPadFromProfile(Profile)
    def isProfile(obj):
        if obj.Name.startswith("Pad") and obj.Label.startswith("Profile"):
            return True
        else:
            return False

    # print(profile.Group)
    Pad = list(filter(isProfile,profile.Group))[0]

    oldSketch = Pad.Profile[0]
    newSketch = targetDoc.copyObject(Sketch,True)
    newSketch.Visibility = False
    profile.addObject(newSketch)
    Pad.Profile = newSketch
    targetDoc.removeObject(oldSketch.Name)

    # App.closeDocument(Sketch.Document.Name)

    targetDoc.recompute()



def PlaceProfiles(Edges,Sketch,OffsetX,OffsetY,Alignment,RotationAngle,deg=True,asLink=False,CreateDir=False,Dir="FrameMembers"):
    '''
    Edges: ((Obj,Edge),(Obj,Edge), . . .)
    Sektch: SketchObject

    '''
    for Edge in Edges:
        doc = Edge[0].Document
        profile = insertProfile(doc,asLink,CreateDir,Dir)
        AttachFrameMember(FrameMember=profile,Edge=Edge,OffsetX=OffsetX,OffsetY=OffsetY,Alignment=Alignment,RotationAngle=RotationAngle,deg = deg)
        ReplaceSketch(profile=profile,Sketch=Sketch)

    doc.recompute()

def EditProfile(profile,Sketch,ChangeSketch,OffsetX,OffsetY,Alignment,RotationAngle,deg=True):
    '''


    '''
    if ChangeSketch is True:
        ReplaceSketch(profile=profile,Sketch=Sketch)

    if profile.isDerivedFrom("App::Link"):
        profile= profile.getLinkedObject()

    profile.OffsetX = OffsetX
    profile.OffsetY = OffsetY

    profile.Alignment = Alignment

    if deg is True:
        RotationAngle:float = math.radians(RotationAngle)
    profile.RotationAngle = RotationAngle

def EditProfiles(Profiles,Sketch,ChangeSketch,OffsetX,OffsetY,Alignment,RotationAngle,deg=True):
    '''


    '''
    for profile in Profiles:
        EditProfile(profile,Sketch,ChangeSketch,OffsetX,OffsetY,Alignment,RotationAngle,deg)

    Profiles[0].Document.recompute()



if __name__ == "__main__":
    pass
