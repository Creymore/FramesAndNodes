import json
import FreeCAD as App  # ty:ignore[unresolved-import]
import os


from .OSasDataBase import SaveKnotWithID,LoadKnotID
from .KnotLogic import AddPropertyKnotID,findBlank,ReadKnotID

# DisplayName, InternalName, Type
def dummyLibaryPaths()->dict:
    return{
        "Default":(
            {"Size":10000,
            "InternalName":"IntegratedDefault",
            "Type":"DIR"
           }
         ,f"{App.getUserAppDataDir()}Mod\\FramesAndNodes\\ExampleModels\\DefalutLibary"),
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

def SaveInLibary(doc,lib,Name):
    Blank = findBlank(doc)
    AddPropertyKnotID(KnotAss=Blank)
    KnotID = ReadKnotID(Blank)
    # print(f"SavedKnotID:{KnotID} \n Type:{type(KnotID)}")
    match LibaryType(lib):
        case "DIR":
            path = LibaryLink(lib)
            if not os.path.exists(path):
                App.Console.PrintError("Path is Wrong")
                return False
            Size = LibaryInfo(lib)["Size"]
            return SaveKnotWithID(KnotID=KnotID,Name=Name,doc=doc,BASEPATH=path,Size=Size)

        case _:
            App.Console.PrintCritical("This Libary Type does not exist or is not Supported yet")
            return False


def LoadFromLibary(KnotID,lib):
    # print(f"KnotID:{KnotID}")
    # json.loads(json.dumps(KnotID))
    # print(f"LoadedKnotID:{KnotID} \n Type:{type(KnotID)}")
    match LibaryType(lib):
        case "DIR":
            path = LibaryLink(lib)
            if not os.path.exists(path):
                App.Console.PrintError("Path is Wrong")
            Size = LibaryInfo(lib)["Size"]
            return LoadKnotID(KnotID=KnotID,BASEPATH=path,Size=Size)

        case _ :
            App.Console.PrintCritical("This Libary Type does not exist or is not Supported yet")

def OpenFromLibary(Name,lib):
    pass
