import FreeCAD as App  # ty:ignore[unresolved-import]
import FreeCADGui as Gui  # ty:ignore[unresolved-import]


from ..features.FrameMemberLogic import SetAlignementProperties, isValidFrameMember
from ..features.NodeLogic import MembersToBlankNode,AddPropertyNodeID, PrintNodeID, PrintNodeIDfromDocument, PrintOrientations, PrintFrameMembersFromNode

DEV_COMMANDS = [
    "FramesAndNodes_AddAlignmentPorperties",
    "FramesAndNodes_MakeBlankKnot",
    "FramesAndNodes_AddKnotID",
    "FramesAndNodes_PrintKnotID",
    "FramesAndNodes_PrintKnotIDFromDoc",
    "FramesAndNodes_PrintOrientations",
    "FramesAndNodes_PrintFrameMembers",
]


class CommandSetAlinementProperties():

    def __init__(self):
        pass

    def GetResources(self):
        return{
            "Pixmap":"",
            "Acces":"",
            "MenuText": "AddAlignmentProperties",
            "Tooltip":"Adds Alignmenet Properties to a Body"
        }

    def IsActive(self):
        return True

    def Activated(self):
        sel = Gui.Selection.getSelection()
        for obj in sel:
            SetAlignementProperties(obj)

Gui.addCommand("FramesAndNodes_AddAlignmentPorperties",CommandSetAlinementProperties())

class CommandMakeBlankKnot():

    def __init__(self):
        pass

    def GetResources(self):
        return{
            "Pixmap":"",
            "Acces":"",
            "MenuText":"MakeBlankKnot",
            "Tooltp":"Makes a Blank Knot Assambly"
        }

    def IsActive(self):
        return True

    def Activated(self):
        sel = Gui.Selection.getSelection()
        Bodies = []
        for obj in sel:
            print(obj)
            if isValidFrameMember(obj):
                Bodies.append(obj)
                print("True")
        print(Bodies)
        MembersToBlankNode(FrameMembers=Bodies)

Gui.addCommand("FramesAndNodes_MakeBlankKnot",CommandMakeBlankKnot())

class CommandAddPropertyKnotID():

    def __init__(self):
        pass

    def GetResources(self):
        return{
            "Pixmap":"",
            "Acces":"",
            "MenuText":"AddKnotID",
            "Tooltp":"Adds a Knot ID to a Knot Assambly or Knot Part"
        }

    def IsActive(self):
        return True

    def Activated(self):
        sel = Gui.Selection.getSelection()
        AddPropertyNodeID(NodeAss=sel[0])

Gui.addCommand("FramesAndNodes_AddKnotID",CommandAddPropertyKnotID())

class CommandPrintKnotID():

    def __init__(self):
        pass

    def GetResources(self):
        return{
            "Pixmap":"",
            "Acces":"",
            "MenuText":"PrintKnotID",
            "Tooltp":""
        }

    def IsActive(self):
        return True

    def Activated(self):
        sel = Gui.Selection.getSelection()
        PrintNodeID(sel)

Gui.addCommand("FramesAndNodes_PrintKnotID",CommandPrintKnotID())

class CommandPrintKnotIDFromDoc():

    def __init__(self):
        pass

    def GetResources(self):
        return{
            "Pixmap":"",
            "Acces":"",
            "MenuText":"PrintKnotIDFromDoc",
            "Tooltp":""
        }

    def IsActive(self):
        return True

    def Activated(self):
        doc = App.ActiveDocument
        PrintNodeIDfromDocument(doc)

Gui.addCommand("FramesAndNodes_PrintKnotIDFromDoc",CommandPrintKnotIDFromDoc())

class CommandPrintOrientations():

    def __init__(self):
        pass

    def GetResources(self):
        return{
            "Pixmap":"",
            "Acces":"",
            "MenuText":"PrintOrientations",
            "Tooltp":""
        }

    def IsActive(self):
        return True

    def Activated(self):
        sel = Gui.Selection.getSelection()[0]
        # print(sel)
        PrintOrientations(sel)

Gui.addCommand("FramesAndNodes_PrintOrientations",CommandPrintOrientations())

class CommandPrintFrameMembers():

    def __init__(self):
        pass

    def GetResources(self):
        return{
            "Pixmap":"",
            "Acces":"",
            "MenuText":"PrintFrameMembers",
            "Tooltp":""
        }

    def IsActive(self):
        return True

    def Activated(self):
        sel = Gui.Selection.getSelection()[0]
        # print(sel)
        PrintFrameMembersFromNode(sel)

Gui.addCommand("FramesAndNodes_PrintFrameMembers",CommandPrintFrameMembers())
