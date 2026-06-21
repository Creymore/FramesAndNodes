import json
import FreeCAD as App  # ty:ignore[unresolved-import]
import os
from pathlib import Path


from .OSasDataBase import SaveNodeWithID,LoadNodeID
from .NodeLogic import AddPropertyNodeID,findBlank,ReadNodeID

# DisplayName, InternalName, Type
def dummyLibaryPaths()->dict:
    return{
        "Default":(
            {"Size":10000,
            "InternalName":"IntegratedDefault",
            "Type":"DIR"
           }
         ,str(Path(App.getUserAppDataDir()) / "Mod" / "FramesAndNodes" / "ExampleModels" / "DefalutLibary")),
        "RemoteMockup":("REM","SomeLink")
    }

def LibaryType(lib):
    return lib[0]["Type"]

def LibaryLink(lib):
    return lib[1]

def LibaryInfo(lib):
    match LibaryType(lib):
        case "DIR":
            return lib[0]

        case _ :
            print("This Libary Type does not exist or is not Supported yet")

# TODO Create an Libary class, that allows other libarys to register
# Libarys should provide both acces to Nodes and Acces to Profile Sketches
def SaveInLibary(doc,lib,Name):
    Blank = findBlank(doc)
    AddPropertyNodeID(Blank)
    NodeID = ReadNodeID(Blank)
    match LibaryType(lib):
        case "DIR":
            path = LibaryLink(lib)
            if not os.path.exists(path):
                App.Console.PrintError("Path is Wrong")
                return False
            Size = LibaryInfo(lib)["Size"]
            return SaveNodeWithID(NodeID=NodeID,Name=Name,doc=doc,BASEPATH=path,Size=Size)

        case _:
            App.Console.PrintCritical("This Libary Type does not exist or is not Supported yet")
            return False


def LoadFromLibary(NodeID,lib):
    # json.loads(json.dumps(NodeID))
    match LibaryType(lib):
        case "DIR":
            path = LibaryLink(lib)
            if not os.path.exists(path):
                App.Console.PrintError("Path is Wrong")
            Size = LibaryInfo(lib)["Size"]
            return LoadNodeID(NodeID=NodeID,BASEPATH=path,Size=Size)

        case _ :
            App.Console.PrintCritical("This Libary Type does not exist or is not Supported yet")

def OpenFromLibary(Name,lib):
    pass
