import FreeCAD as App  # ty:ignore[unresolved-import]
import FreeCADGui as Gui  # ty:ignore[unresolved-import]


from ..features.ProfileLogic import SetAlignementProperties, isValidProfileBody
from ..features.KnotLogic import MembersToBlankKnot,AddPropertyKnotID, PrintKnotID, PrintKnotIDfromDocument, PrintOrientations, PrintFrameMembersFromKnot

DEV_COMMANDS = [
    "AddAlignmentPorperties",
    "MakeBlankKnot",
    "AddKnotID",
    "PrintKnotID",
    "PrintKnotIDFromDoc",
    "PrintOrientations",
    "PrintFrameMembers",
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

Gui.addCommand("AddAlignmentPorperties",CommandSetAlinementProperties())

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
            if isValidProfileBody(obj):
                Bodies.append(obj)
                print("True")
        print(Bodies)
        MembersToBlankKnot(FrameMembers=Bodies)

Gui.addCommand("MakeBlankKnot",CommandMakeBlankKnot())

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
        AddPropertyKnotID(KnotAss=sel[0])

Gui.addCommand("AddKnotID",CommandAddPropertyKnotID())

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
        PrintKnotID(sel)

Gui.addCommand("PrintKnotID",CommandPrintKnotID())

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
        PrintKnotIDfromDocument(doc)

Gui.addCommand("PrintKnotIDFromDoc",CommandPrintKnotIDFromDoc())

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

Gui.addCommand("PrintOrientations",CommandPrintOrientations())

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
        PrintFrameMembersFromKnot(sel)

Gui.addCommand("PrintFrameMembers",CommandPrintFrameMembers())
