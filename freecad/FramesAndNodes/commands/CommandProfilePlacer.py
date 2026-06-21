import FreeCAD as App  # ty:ignore[unresolved-import]
import FreeCADGui as Gui  # ty:ignore[unresolved-import]
from PySide import QtCore  # ty:ignore[unresolved-import]
from importlib.resources import files
from pathlib import Path
from typing import ClassVar

from PySide import QtCore  # ty:ignore[unresolved-import]
from ..resources import Resources

from PySide.QtCore import QT_TRANSLATE_NOOP  # ty:ignore[unresolved-import]

# Use propper FreeCAd widgest for the .ui file

#TODO Create a PrefrencePage to edit Availible Profile Sketch folders 
# Gloabel dict for Testing 
WORKBENCH_ROOT = Path(__file__).resolve().parents[3]
BaseSketchPath = str(WORKBENCH_ROOT / "ExampleModels" / "Sketches")
Baspaths = {
    "Default": BaseSketchPath,
    "Coustom1": "Path",
    "Coustom2": "Path",
}

#import os
#print(f"BaseSketchPath:{os.path.exists(BaseSketchPath)}")

from ..resources import Resources
from .. import resources
from ..features.ProfileLogic import PlaceProfiles, isValidProfileSketch, EditProfiles
# from ..features.SelectionProcessing import getEdgesFrameMembersFromSelcection
from ..features.SelectionProcessing2 import getEdgesFrameMembersFromSelcection

DEBUG = False
PROFILE_PLACER_UI = str(files(resources).joinpath("panels", "TaskFramesAndNodesProfilePlacer.ui"))  # ty:ignore[too-many-positional-arguments]

class CommandProfilePlacer():
    Name: ClassVar[str] = "ProfilePlacer"

    def __init__(self):
        pass

    def GetResources(self):
        return {
            "Pixmap":""
            ,
            "MenuText": QT_TRANSLATE_NOOP(
                "FramesAndNodes",
                "Profile Placer",
            ),
            "ToolTip": QT_TRANSLATE_NOOP(
                "FramesAndNodes",
                "Places or edits profiles on selected frame geometry",
            ),
        }

    def IsActive(self):
        return True

    def Activated(self):
        panel = TaskProfilePlacer()
        Gui.Control.showDialog(panel)

        return

# Should i add an "insert" Button, that just insertes the Frame Member as a Body with no Attachment ?
class TaskProfilePlacer():
    '''
    Task panel for placing new profiles on selected geometry or editing
    existing FramesAndKnots profile bodies.

    What it does:
    - Loads the `TaskFramesAndKnotsProfilePlacer` UI and binds its widgets.
    - Watches the current FreeCAD selection and derives the working mode from it:
      edge-based selections switch the panel to placing mode, while selected
      profile bodies switch it to editing mode.
    - Lets the user choose a profile library directory, a `.FCStd` file, and a
      sketch inside that file. The selected file is opened as a temporary hidden
      document so the available sketch labels can be listed.
    - Stores placement parameters from the UI such as alignment, optional custom
      X/Y offsets, and rotation angle.
    - On accept, validates the chosen sketch metadata and then either:
      places new profile bodies on the selected edges via `PlaceProfiles`, or
      updates the selected existing profile bodies via `EditProfiles`.
    - Cleans up the temporary document and selection observer when the task panel
      is accepted or canceled.
    '''
    NO_CHANGE_SKETCH_LABEL = "No change"

    def __init__(self):
        self.form = Gui.PySideUic.loadUi(PROFILE_PLACER_UI)
        self._profile_doc = None
        self._owns_profile_doc = False
        self._selection_observer_active = False
        self._ignore_selection_events = False
        self.state = {
            "base_dir_key": None,
            "base_dir": None,
            "profile_file": None,
            "profile_file_path": None,
            "profile_sketch": None,
            "mode": None,
            "selection_items": (),
            "selection": None,
            "alignment": None,
            "use_custom": False,
            "offset_x": 0.0,
            "offset_y": 0.0,
            "rotation": 0.0,
        }
        self._selection_model = QtCore.QStringListModel(self.form)

        self._bind_widgets()
        self._connect_signals()
        self._load_initial_data()
        self._register_selection_observer()

    def _bind_widgets(self):
        self.edit_mode_label = self._get_widget("EditMode")
        self.selection_list = self._get_widget("listView", "SelectionList")
        self.base_dir_combo = self._get_widget("ProfilBaseDir")
        self.profile_files_combo = self._get_widget("ProfileFiles")
        self.profile_sketches_combo = self._get_widget("ProfileSketches")
        self.use_custom_checkbox = self._get_widget("checkBox")
        self.offset_x_spin = self._get_widget("OffsetX")
        self.offset_y_spin = self._get_widget("OffsetY")
        self.rotation_spin = self._get_widget("RotationAngle")
        self.as_link_checkbox = self._get_widget("AsLink")

        self.alignment_buttons = {
            0: self._get_widget("AlignTopLeft"),
            1: self._get_widget("AlignTopMiddle"),
            2: self._get_widget("AlignTopRight"),
            3: self._get_widget("AlignMiddleLeft"),
            4: self._get_widget("AlignMiddleMiddle"),
            5: self._get_widget("AlignMiddleRight"),
            6: self._get_widget("AlignBottomLeft"),
            7: self._get_widget("AlignBottomMiddle"),
            8: self._get_widget("AlignBottomRight"),
        }

    def _connect_signals(self):
        self.selection_list.setModel(self._selection_model)

        selection_model = self.selection_list.selectionModel()
        if selection_model is not None:
            selection_model.currentChanged.connect(self.on_selection_changed)

        self.base_dir_combo.currentTextChanged.connect(self.on_base_dir_changed)
        self.profile_files_combo.currentTextChanged.connect(self.on_profile_file_changed)
        self.profile_sketches_combo.currentTextChanged.connect(self.on_profile_sketch_changed)
        self.use_custom_checkbox.toggled.connect(self.on_use_custom_toggled)
        self.offset_x_spin.valueChanged.connect(self.on_offset_x_changed)
        self.offset_y_spin.valueChanged.connect(self.on_offset_y_changed)
        self.rotation_spin.valueChanged.connect(self.on_rotation_changed)

        for alignment, button in self.alignment_buttons.items():
            button.clicked.connect(
                lambda checked=False, alignment=alignment: self.on_alignment_clicked(alignment)
            )

    def _load_initial_data(self):
        self._populate_base_dirs()
        self._populate_selection_list()
        self._sync_custom_controls()
        self._set_alignment(4)

    def _populate_base_dirs(self):
        combo = self.base_dir_combo
        combo.blockSignals(True)
        combo.clear()

        combo.addItems(list(Baspaths.keys()))
        combo.blockSignals(False)

        if combo.count():
            self.on_base_dir_changed(combo.currentText())

    def _populate_profile_files(self, base_path):
        combo = self.profile_files_combo
        combo.blockSignals(True)
        combo.clear()

        labels = []
        if base_path:
            base_dir = Path(base_path)
            try:
                if base_dir.exists() and base_dir.is_dir():
                    labels = sorted(
                        file_path.name
                        for file_path in base_dir.glob("*")
                        if file_path.is_file() and file_path.name.lower().endswith(".fcstd")
                    )
            except Exception as exc:
                App.Console.PrintError(
                    f"TaskProfilePlacer: failed to list profile files in {base_dir}: {exc}\n"
                )

        if not labels:
            labels = ["<No .FCStd files>"]
        App.Console.PrintMessage(
            f"TaskProfilePlacer: profile files in {base_path}: {labels}\n"
        )

        combo.addItems(labels)
        combo.setEnabled(bool(labels) and not labels[0].startswith("<"))

        if combo.count():
            combo.setCurrentIndex(0)

        current_text = combo.currentText() if combo.count() else None
        combo.blockSignals(False)

        if current_text:
            self.on_profile_file_changed(current_text)

    def _populate_profile_sketches(self, profile_file_path):
        combo = self.profile_sketches_combo
        combo.blockSignals(True)
        combo.clear()

        sketches = []
        if self._is_editing_mode():
            sketches.append(self.NO_CHANGE_SKETCH_LABEL)
        profile_doc = self._open_profile_document(profile_file_path)
        if profile_doc is not None:
            sketches.extend(
                obj.Label for obj in profile_doc.Objects
                if getattr(obj, "TypeId", "") == "Sketcher::SketchObject"
            )

        combo.addItems(sketches)
        combo.blockSignals(False)

        if combo.count():
            if self._is_editing_mode():
                combo.setCurrentIndex(combo.findText(self.NO_CHANGE_SKETCH_LABEL))
            self.on_profile_sketch_changed(combo.currentText())

    def _current_mode(self, selection_items=None):
        if self._is_placing_mode(selection_items):
            return "placing"
        if self._is_editing_mode(selection_items):
            return "editing"
        return None

    def _sync_profile_sketch_mode(self, mode):
        combo = self.profile_sketches_combo
        no_change_index = combo.findText(self.NO_CHANGE_SKETCH_LABEL)

        combo.blockSignals(True)
        if mode == "editing":
            if no_change_index < 0:
                combo.insertItem(0, self.NO_CHANGE_SKETCH_LABEL)
            combo.setCurrentIndex(combo.findText(self.NO_CHANGE_SKETCH_LABEL))
        else:
            if no_change_index >= 0:
                was_selected = combo.currentIndex() == no_change_index
                combo.removeItem(no_change_index)
                if was_selected and combo.count():
                    combo.setCurrentIndex(0)
        combo.blockSignals(False)

        if combo.count():
            self.on_profile_sketch_changed(combo.currentText())
        else:
            self.on_profile_sketch_changed(None)

    def _is_placing_mode(self, selection_items=None):
        if selection_items is None:
            selection_items = self.state["selection_items"]
        return bool(selection_items) and all(
            isinstance(item, tuple) and len(item) == 2 for item in selection_items  # ty:ignore[not-iterable]
        )

    def _is_editing_mode(self, selection_items=None):
        if selection_items is None:
            selection_items = self.state["selection_items"]
        return bool(selection_items) and all(
            not (isinstance(item, tuple) and len(item) == 2) for item in selection_items  # ty:ignore[not-iterable]
        )

    def _capture_selection(self):
        captured_selection = []
        for selection_object in Gui.Selection.getSelectionEx("", 0):
            captured_selection.append(
                (
                    selection_object.DocumentName,
                    selection_object.ObjectName,
                    tuple(selection_object.SubElementNames),
                )
            )
        return captured_selection

    def _restore_selection(self, captured_selection):
        self._ignore_selection_events = True
        try:
            Gui.Selection.clearSelection()
            for doc_name, obj_name, sub_element_names in captured_selection:
                if sub_element_names:
                    for sub_element_name in sub_element_names:
                        Gui.Selection.addSelection(doc_name, obj_name, sub_element_name)
                else:
                    Gui.Selection.addSelection(doc_name, obj_name)
        finally:
            self._ignore_selection_events = False
            self._populate_selection_list()

    def _preserve_gui_selection(self, callback, *args):
        captured_selection = self._capture_selection()
        result = callback(*args)
        self._restore_selection(captured_selection)
        return result

    def _populate_selection_list(self):
        selection_items = getEdgesFrameMembersFromSelcection()
        self.state["selection_items"] = selection_items
        is_placing_mode = self._is_placing_mode(selection_items)
        previous_mode = self.state["mode"]
        current_mode = self._current_mode(selection_items)
        self.state["mode"] = current_mode

        if selection_items and is_placing_mode:
            self.edit_mode_label.setText("Mode: Placing")
        elif selection_items:
            self.edit_mode_label.setText("Mode: Editing")
        else:
            self.edit_mode_label.setText("Mode: Placing / Editing")

        selection_labels = []
        if is_placing_mode:
            for selection_item in selection_items:
                obj, sub_element = selection_item
                object_name = getattr(obj, "Label", getattr(obj, "Name", str(obj)))
                selection_labels.append(
                    f"{object_name}.{self._format_selection_sub_element_label(obj, sub_element)}"
                )
        else:
            for item in selection_items:
                selection_labels.append(f"{item.Label} | {item.Name}")

        if not selection_labels:
            selection_labels = ["<Nothing selected>"]

        self._selection_model.setStringList(selection_labels)
        first_index = self._selection_model.index(0, 0)
        if first_index.isValid():
            self.selection_list.setCurrentIndex(first_index)

        if current_mode != previous_mode:
            self._sync_profile_sketch_mode(current_mode)

    def _format_selection_sub_element_label(self, obj, sub_element):
        label = str(sub_element)
        if ";" in label:
            label = next(
                (token for token in reversed(label.split(";")) if token),
                label,
            )

        if getattr(obj, "TypeId", "") == "Sketcher::SketchObject" and "." in label:
            label = label.rsplit(".", 1)[-1]

        return label

    def _open_profile_document(self, profile_file_path, temporary=True):
        self._close_profile_document()

        if not profile_file_path:
            return None

        target_path = str(Path(profile_file_path).resolve())
        previous_active_document = App.ActiveDocument

        try:
            self._profile_doc = App.openDocument(
                target_path,
                hidden=True,
                temporary=temporary,
            )
            self._owns_profile_doc = True
            if previous_active_document is not None:
                App.setActiveDocument(previous_active_document.Name)
                gui_document = Gui.getDocument(previous_active_document.Name)
                if gui_document is not None:
                    Gui.ActiveDocument = gui_document
        except Exception as exc:
            self._profile_doc = None
            self._owns_profile_doc = False
            App.Console.PrintError(
                f"TaskProfilePlacer: failed to open profile file {target_path}: {exc}\n"
            )
            return None

        return self._profile_doc

    def _resolve_profile_sketch(self, profile_doc, profile_sketch_name):
        if profile_doc is None:
            return None

        return next(
            (
                obj for obj in profile_doc.Objects
                if getattr(obj, "TypeId", "") == "Sketcher::SketchObject"
                and obj.Label == profile_sketch_name
            ),
            None,
        )

    def _close_profile_document(self):
        if self._profile_doc is not None and self._owns_profile_doc:
            App.closeDocument(self._profile_doc.Name)
        self._profile_doc = None
        self._owns_profile_doc = False

    def _register_selection_observer(self):
        if not self._selection_observer_active:
            Gui.Selection.addObserver(self)
            self._selection_observer_active = True

    def _unregister_selection_observer(self):
        if self._selection_observer_active:
            Gui.Selection.removeObserver(self)
            self._selection_observer_active = False

    def _get_widget(self, *names):
        for name in names:
            widget = getattr(self.form, name, None)
            if widget is not None:
                return widget
        raise AttributeError(f"Could not find any widget named {names!r} in TaskProfilePlacer UI")

    def _set_alignment(self, alignment):
        self.state["alignment"] = alignment
        for index, button in self.alignment_buttons.items():
            button.setDefault(index == alignment)
            button.setAutoDefault(index == alignment)

    def _sync_custom_controls(self):
        use_custom = self.use_custom_checkbox.isChecked()
        self.state["use_custom"] = use_custom
        self.offset_x_spin.setEnabled(use_custom)
        self.offset_y_spin.setEnabled(use_custom)

    def _print_state_change(self, message):
        if DEBUG:
            App.Console.PrintMessage(f"TaskProfilePlacer: {message}\n")

    def on_selection_changed(self, current, previous):
        del previous
        value = current.data() if current.isValid() else None
        self.state["selection"] = value
        self._print_state_change(f"selection -> {value}")

    def on_base_dir_changed(self, text):
        value = Baspaths.get(text)
        self.state["base_dir_key"] = text
        self.state["base_dir"] = value  # ty:ignore[invalid-assignment]
        self._preserve_gui_selection(self._populate_profile_files, value)
        self._print_state_change(f"base dir -> {text}: {value}")
        return value

    def on_profile_file_changed(self, text):
        self.state["profile_file"] = text
        base_path = self.state["base_dir"]
        if base_path and not text.startswith("<"):
            self.state["profile_file_path"] = str(Path(base_path) / text)  # ty:ignore[invalid-assignment, invalid-argument-type]
        else:
            self.state["profile_file_path"] = None
        self._preserve_gui_selection(
            self._populate_profile_sketches,
            self.state["profile_file_path"],
        )
        self._print_state_change(
            f"profile file -> {text}: {self.state['profile_file_path']}"
        )

    def on_profile_sketch_changed(self, text):
        self.state["profile_sketch"] = text
        self._print_state_change(f"profile sketch -> {text}")

    def on_use_custom_toggled(self, checked):
        self._sync_custom_controls()
        if checked:
            self._set_alignment(9)
        elif self.state["alignment"] == 9:
            self._set_alignment(4)
        self._print_state_change(f"use custom -> {checked}")

    def on_offset_x_changed(self, value):
        self.state["offset_x"] = value
        self._print_state_change(f"offset x -> {value}")

    def on_offset_y_changed(self, value):
        self.state["offset_y"] = value
        self._print_state_change(f"offset y -> {value}")

    def on_rotation_changed(self, value):
        self.state["rotation"] = value
        self._print_state_change(f"rotation -> {value}")

    def on_alignment_clicked(self, alignment):
        self.use_custom_checkbox.setChecked(False)
        self._set_alignment(alignment)
        self._print_state_change(f"alignment -> {alignment}")

    def addSelection(self, doc_name, obj_name, sub_name, point):
        del doc_name, obj_name, sub_name, point
        if not self._ignore_selection_events:
            self._populate_selection_list()

    def removeSelection(self, doc_name, obj_name, sub_name):
        del doc_name, obj_name, sub_name
        if not self._ignore_selection_events:
            self._populate_selection_list()

    def setSelection(self, doc_name):
        del doc_name
        if not self._ignore_selection_events:
            self._populate_selection_list()

    def clearSelection(self, doc_name):
        del doc_name
        if not self._ignore_selection_events:
            self._populate_selection_list()


    def reject(self):
        """Called when Cancel button is pressed"""
        self._unregister_selection_observer()
        self._close_profile_document()
        App.Console.PrintMessage("TaskProfilePlacer: canceled\n")
        Gui.Control.closeDialog()
        return True

    def accept(self):
        """Called when OK button is pressed"""
        selection_items = self.state["selection_items"]
        if not selection_items:
            App.Console.PrintError("TaskProfilePlacer: no edges selected\n")
            return False

        profile_sketch_name = self.state["profile_sketch"]
        is_placing_mode = self._is_placing_mode(selection_items)
        is_editing_mode = self._is_editing_mode(selection_items)

        if not is_placing_mode and not is_editing_mode:
            App.Console.PrintError(
                "TaskProfilePlacer: current selection is a mixed edit/place selection\n"
            )
            return False

        change_sketch = profile_sketch_name != self.NO_CHANGE_SKETCH_LABEL
        profile_sketch = None

        if is_placing_mode or change_sketch:
            if not profile_sketch_name or profile_sketch_name.startswith("<"):  # ty:ignore[unresolved-attribute]
                App.Console.PrintError("TaskProfilePlacer: no profile sketch selected\n")
                return False

            profile_doc = self._open_profile_document(
                self.state["profile_file_path"],
                temporary=False,
            )

            if profile_doc is None:
                App.Console.PrintError("TaskProfilePlacer: could not open profile document\n")
                return False

            profile_sketch = self._resolve_profile_sketch(profile_doc, profile_sketch_name)
            if profile_sketch is None:
                App.Console.PrintError(
                    f"TaskProfilePlacer: sketch '{profile_sketch_name}' not found\n"
                )
                return False

            if not isValidProfileSketch(profile_sketch):
                App.Console.PrintError(
                    f"TaskProfilePlacer: sketch '{profile_sketch_name}' is missing profile metadata\n"
                )
                return False

        if is_placing_mode:
            PlaceProfiles(
                Edges=selection_items,
                Sketch=profile_sketch,
                OffsetX=self.state["offset_x"],
                OffsetY=self.state["offset_y"],
                Alignment=self.state["alignment"],
                RotationAngle=self.state["rotation"],
                deg=True,
                asLink=self.as_link_checkbox.isChecked(),
                CreateDir=True
            )
        else:
            EditProfiles(
                Profiles=selection_items,
                Sketch=profile_sketch,
                ChangeSketch=change_sketch,
                OffsetX=self.state["offset_x"],
                OffsetY=self.state["offset_y"],
                Alignment=self.state["alignment"],
                RotationAngle=self.state["rotation"],
                deg=True,
            )

        self._unregister_selection_observer()
        self._close_profile_document()
        App.Console.PrintMessage("TaskProfilePlacer: accepted\n")
        Gui.Control.closeDialog()

        return True

Gui.addCommand("ProfilePlacer",CommandProfilePlacer())
