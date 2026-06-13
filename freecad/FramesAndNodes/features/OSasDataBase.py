"""
Uses The Operating System as a "Data Base"
Search for Vaild Knot ID
Save File
Load File
"""

import FreeCAD as App  # ty:ignore[unresolved-import]
import FreeCADGui as Gui  # ty:ignore[unresolved-import]
import os
import hashlib
import random

from pathlib import Path
import sys

from .KnotLogic import ReadKnotIDfromDocument
from .utils.utils import isFCfile

'''
This uses the Os (Windows/Linux/Mac) as a database
for the Knots. Probarbly not the ideal solution.
The idea is to have a two leveled system.
DataBase
-> 00001 ... 10000
-> -> 00001 ...
# 10.000 Knots should be enouth
Save
    Hash
    Modulo
    Go in folder
    Handel collition
        compare document in folder
        if match put in folder
        if not check next folder
'''

#Check if the name already exist
#Somehow give that info to the user about needing an diffrent name
def SaveFCfile(doc,Name,path)->bool:
    savePath = Path(path) / (Name + ".FCStd")
    if savePath.exists():
        App.Console.PrintCritical("File already existes, PleaseCange the Name")
        return False
    else:
        doc.saveAs(str(savePath))
        return True

# Loads all Valid Knot files in a direktory/folder
def LoadFCfiles(path):

    pass

# The Function should check for Vaild Path DONE, Valid file formate DONE, Valid "Knot" in Part in file
def ReadKnotID(path): # path of file
    path = str(path)
    cdoc = App.activeDocument()
    # print(f"Read{path}")
    if not os.path.exists(path): # check Valid Path
        return False
    if not isFCfile(path):
        return False
    normalized_path = os.path.normcase(os.path.abspath(path))
    doc = None
    opened_here = False
    for open_doc in App.listDocuments().values():
        if os.path.normcase(os.path.abspath(open_doc.FileName)) == normalized_path:
            doc = open_doc
            break
    if doc is None:
        doc = App.openDocument(path,hidden=False)
        opened_here = True
    KnotID= ReadKnotIDfromDocument(doc)
    if opened_here:
        App.closeDocument(doc.Name)

    if App.GuiUp and cdoc is not None:
        Gui.setActiveDocument(cdoc.Name)
    return KnotID

def ReadKnotID2(path):
    path = str(path)
    if not os.path.exists(path): # check Valid Path
        return False
    if not isFCfile(path):
        return False

    cdoc = App.activeDocument()

    doc = App.openDocument(path,True,True)
    Gui.setActiveDocument(cdoc.Name)
    KnotID = ReadKnotIDfromDocument(doc)
    # App.closeDocument(doc.Name)
    App.setActiveDocument(cdoc.Name)
    App.ActiveDocument=App.getDocument(cdoc.Name)
    Gui.ActiveDocument=Gui.getDocument(cdoc.Name)
    return KnotID


#default for N is 10.000 because in some forum post it was said that 100.000 would make it slow
def findPos(KnotID,N=10000):
    KnotID = KnotID.encode("utf-8")
    Pos = hashlib.sha256(KnotID).hexdigest()
    Pos = int(Pos,32)
    Pos = Pos % N
    Pos = str(Pos).zfill(len(str(N)))
    # Pos = "01000" #to debug, test collition
    return Pos

# structure: folder/subfolder => Knot.FCstd files
def SearchValidPaths(KnotID:tuple,BASEPATH,Mode="Save",N=10000): # Mode = "Save" => Valid path to save in | Mode = "Load" => Valid path to Load
    '''
    Searches for a Valid path to load from Mode = "Load"
    Searches or creates for a Valid path to Save in Mode = "Save"
    '''
    print("SearchValidPaths")
    if not (Mode == "Save" or Mode == "Load"):
        print("Mode is not: 'Save' or 'Load' Please enter the Correct Mode.")
        return None
    Pos = findPos(KnotID=str(KnotID),N=N)
    path = Path(BASEPATH) / Pos
    ValidPath = []
    if not path.exists() and Mode == "Save":
        path.mkdir()
    if not path.exists() and Mode == "Load":
        print("Path does not exist")
        print(path)
        return(ValidPath)
    folders: list[Path] = list(path.iterdir())
    for SubPath in folders:
        if not SubPath.is_dir(): #Skips files that somehow landed in Pos folder directly
            continue
        files = list(SubPath.iterdir())
        for filepath in files:
            if ReadKnotID2(filepath) == KnotID and str(SubPath) not in ValidPath:
                ValidPath.append(str(SubPath))
                # return(ValidPath) #would make it faster
        if len(files) == 0 and len(ValidPath) == 0 and Mode == "Save":
            ValidPath.append(str(SubPath))
    if len(ValidPath) == 0:
        newpath = path / str(len(list(path.iterdir()))).zfill(5) # zfill maybe not enouth ???
        if not newpath.exists() and Mode == "Save":
            newpath.mkdir()
            print(f"new Path was Created ad: {newpath}")
            ValidPath.append(str(newpath))
            # AddFileWithID(KnotID,newpath) #Adds a file with the KnotID Probarly should check
        elif Mode == "Save":
            print(f"The Path {newpath} already exist, without files")
    if len(ValidPath) > 1 :
        print("There is more then one Valid Path, Something is wrong")
        for p in ValidPath:
            print(p)
    return(ValidPath)

def SaveKnotWithID(KnotID,Name,doc,BASEPATH,Size)->bool: # BASEPATH is the "DataBase" path
    path = SearchValidPaths(KnotID,BASEPATH,Mode="Save",N=Size)
    path = path[0]
    print(f"KnotID of saved Knot:{KnotID}")
    print(f"Knot was Saved under:{path}")
    file = doc
    if SaveFCfile(doc=file,Name=Name,path=path):
        return True
    else:
        return False

def LoadKnotID(KnotID,BASEPATH:str,Size:int)->dict:
        paths = SearchValidPaths(KnotID,BASEPATH,Mode="Load",N=Size)
        if not paths:
            print("No Matches found")
            return {}

        results = {}
        for path in paths:
            for file in Path(path).iterdir():
                if file.name.endswith(".FCStd"):
                    results.update({file.stem:str(Path(path) / file.name)})

        # print(results)
        return results

def MigrationScript(TargetPath,InputPath,N):
    '''
    Recursivly searches through the InputPath for .FCstd files that classify as Knots
    Then sorts them into the TargetPath "Data Base"
    effectivly combining two "Data Bases" to one
    '''
    pass


if __name__ == "__main__":
    pass
