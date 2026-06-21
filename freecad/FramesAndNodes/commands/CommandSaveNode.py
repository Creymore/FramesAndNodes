import FreeCAD as App  # ty:ignore[unresolved-import]
import FreeCADGui as Gui  # ty:ignore[unresolved-import]
from importlib.resources import files
from typing import ClassVar

from ..features.SaveAndLoad import SaveInLibary,dummyLibaryPaths
from .. import resources
from ..resources import Resources
from PySide.QtCore import QT_TRANSLATE_NOOP  # ty:ignore[unresolved-import]

Libarys = dummyLibaryPaths()
SAVE_KNOT_UI = str(files(resources).joinpath("panels", "TaskFramesAndNodesSaveNode.ui"))  # ty:ignore[too-many-positional-arguments]


class CommandSaveNode():
    Name: ClassVar[str] = "SaveKnot"

    def __init__(self):
        pass

    def GetResources(self):
        return {
            "Pixmap":""
            ,
            "MenuText": QT_TRANSLATE_NOOP(
                "FramesAndNodes",
                "Save Knot",
            ),
            "ToolTip": QT_TRANSLATE_NOOP(
                "FramesAndNodes",
                "Saves the current knot to a knot library",
            ),
        }

    def IsActive(self):
        return True

    def Activated(self):
        panel = TaskSaveKnot()
        Gui.Control.showDialog(panel)

class TaskSaveKnot():
    def __init__(self):
        self.form = Gui.PySideUic.loadUi(SAVE_KNOT_UI)
        self.libary_list = getattr(self.form, "LibaryList", None)
        self.enter_name = getattr(self.form, "EneterName", None)

        self._populate_libaries()

    def _populate_libaries(self):
        if self.libary_list is None:
            return

        self.libary_list.clear()
        self.libary_list.addItems(list(Libarys.keys()))

    def reject(self):
        Gui.Control.closeDialog()
        return True

    def accept(self):
        doc = App.ActiveDocument
        if doc is None:
            App.Console.PrintError("TaskSaveKnot: no active document to save\n")
            return False

        if self.libary_list is None:
            App.Console.PrintError("TaskSaveKnot: library selector is missing in the UI\n")
            return False

        libary_name = self.libary_list.currentText()
        if not libary_name or libary_name not in Libarys:
            App.Console.PrintError("TaskSaveKnot: no valid library selected\n")
            return False

        knot_name = ""
        if self.enter_name is not None:
            knot_name = self.enter_name.text().strip()
        if not knot_name:
            App.Console.PrintError("TaskSaveKnot: enter a name before saving\n")
            return False

        try:
            succes=SaveInLibary(doc=doc, lib=Libarys[libary_name], Name=knot_name)
        except Exception as exc:
            App.Console.PrintError(f"TaskSaveKnot: failed to save knot: {exc}\n")
            return False

        if succes:
            Gui.Control.closeDialog()
        return True

Gui.addCommand("SaveKnot",CommandSaveNode())
