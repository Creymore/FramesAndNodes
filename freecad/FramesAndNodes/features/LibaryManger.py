






class LibraryManger():
    '''
    Manges Libaries for use 

    Libary requiered Methods:
    .Label --> Returns the Label of the Library defined by the userer or Automaticly during the library connection 
    .Type  --> Returns the Type of the Library All Libraries derived from a connector have the same Type
    .SaveWithID  --> Saves a Node using its NodeID
    .LoadEntries --> Loads DataBase entries with the fitting NodeID
    .LoadMoreEntries --> If there were to many entries to be loaded in the Previous Batch a new Batch Will be returned
    .Load        --> Loads a file from the Library

    optional Methods:
    .NewLinkedFrameMembers --> Creats a new file for a FrameMember in a Database
    .UnlinkFrameMember --> If the FrameMember is linked into a Frame the unlink puts the Frame member in a Place to reused with .NewLinkedFrameMember instead of creating trash data in PDM
    .cacheUnlinkedFrameMembers --> caches FrameMembers which are unlinked/unused in a PDM to be used quickly by .NewLinkedFrameMember
    Note:   If you are using a PDM in which entries are not supposed to be deleted please use implement these methods.
            If not then just delete unused FrameMember files


    
    '''
    def __init__(self):
        return
    
    def AddLibary(self):
        return
    
    def listLibarys(self,Mode,Status):
        '''
        Lists all ActiveLiabrys
        Modes:
        "Sketch" --> List of Librays which contain sketches
        "Node"   --> List of Librays which contain Nodes
        Status:
        "Active" --> Libary which is Active
        "All"    --> All Libarys
        
        return: list(Libray Objects)
        '''
        return

    def getLiabry(self,Name):
        return