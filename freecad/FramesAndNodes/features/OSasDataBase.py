"""
Uses The Operating System as a "Data Base"
Search for Vaild Node ID
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

from .NodeLogic import ReadNodeIDfromDocument
from .utils.utils import isFCfile

'''
This uses the Os (Windows/Linux/Mac) as a database
for the Nodes. Probarbly not the ideal solution.
The idea is to have a two leveled system.
DataBase
-> 00001 ... 10000
-> -> 00001 ...
# 10.000 Nodes should be enouth
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

# Loads all Valid Node files in a direktory/folder
def LoadFCfiles(path):

    pass

def ReadNodeID2(path):
    path = str(path)
    if not os.path.exists(path): # check Valid Path
        return False
    if not isFCfile(path):
        return False

    cdoc = App.activeDocument()

    doc = App.openDocument(path,True,True)
    if  App.GuiUp == 1 :
        Gui.setActiveDocument(cdoc.Name)
    NodeID = ReadNodeIDfromDocument(doc)
    # App.closeDocument(doc.Name)
    App.setActiveDocument(cdoc.Name)
    App.ActiveDocument=App.getDocument(cdoc.Name)
    if  App.GuiUp == 1 :
        Gui.ActiveDocument=Gui.getDocument(cdoc.Name)
    return NodeID


#default for N is 10.000 because in some forum post it was said that 100.000 would make it slow
def findPos(NodeID,N=10000):
    NodeID = NodeID.encode("utf-8")
    Pos = hashlib.sha256(NodeID).hexdigest()
    Pos = int(Pos,32)
    Pos = Pos % N
    Pos = str(Pos).zfill(len(str(N)))
    # Pos = "01000" #to debug, test collition
    return Pos

# structure: folder/subfolder => Node.FCstd files
def SearchValidPaths(NodeID:tuple,BASEPATH,Mode="Save",N=10000): # Mode = "Save" => Valid path to save in | Mode = "Load" => Valid path to Load
    '''
    Searches for a Valid path to load from Mode = "Load"
    Searches or creates for a Valid path to Save in Mode = "Save"
    '''
    print("SearchValidPaths")
    if not (Mode == "Save" or Mode == "Load"):
        print("Mode is not: 'Save' or 'Load' Please enter the Correct Mode.")
        return None
    Pos = findPos(NodeID=str(NodeID),N=N)
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
            if ReadNodeID2(filepath) == NodeID and str(SubPath) not in ValidPath:
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
            # AddFileWithID(NodeID,newpath) #Adds a file with the NodeID Probarly should check
        elif Mode == "Save":
            print(f"The Path {newpath} already exist, without files")
    if len(ValidPath) > 1 :
        print("There is more then one Valid Path, Something is wrong")
        for p in ValidPath:
            print(p)
    return(ValidPath)

def SaveNodeWithID(NodeID,Name,doc,BASEPATH,Size)->bool: # BASEPATH is the "DataBase" path
    path = SearchValidPaths(NodeID,BASEPATH,Mode="Save",N=Size)
    path = path[0]
    print(f"NodeID of saved Node:{NodeID}")
    print(f"Node was Saved under:{path}")
    file = doc
    if SaveFCfile(doc=file,Name=Name,path=path):
        return True
    else:
        return False

def LoadNodeID(NodeID,BASEPATH:str,Size:int)->dict:
        paths = SearchValidPaths(NodeID,BASEPATH,Mode="Load",N=Size)
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
    Recursivly searches through the InputPath for .FCstd files that classify as Nodes
    Then sorts them into the TargetPath "Data Base"
    effectivly combining two "Data Bases" to one
    '''
    pass


if __name__ == "__main__":
    pass
