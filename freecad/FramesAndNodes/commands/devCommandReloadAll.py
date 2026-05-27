from __future__ import annotations

import sys
from importlib import reload
from pathlib import Path
from types import ModuleType

import FreeCAD  # ty: ignore[unresolved-import]
import FreeCADGui  # ty: ignore[unresolved-import]


THIS_FILE = Path(__file__).resolve()
ADDON_DIRECTORY = THIS_FILE.parent
THIS_MODULE_NAME = __name__


def _detect_root_package_name() -> str:
    package_name = (__package__ or __name__).split(".", 1)[0]
    if package_name:
        return package_name
    return THIS_FILE.parent.name


ROOT_PACKAGE_NAME = _detect_root_package_name()


def _print_message(message: str) -> None:
    FreeCAD.Console.PrintMessage(f"{message}\n")


def _print_error(message: str) -> None:
    FreeCAD.Console.PrintError(f"{message}\n")


def _is_module_inside_addon(module: ModuleType, addon_directory: Path) -> bool:
    module_file = getattr(module, "__file__", None)
    if not module_file:
        return False

    try:
        module_path = Path(module_file).resolve()
    except OSError:
        return False

    try:
        module_path.relative_to(addon_directory)
    except ValueError:
        return False

    return True


def _belongs_to_package(module_name: str, package_name: str) -> bool:
    return module_name == package_name or module_name.startswith(f"{package_name}.")


def _should_skip_module(module_name: str) -> bool:
    if module_name == THIS_MODULE_NAME:
        return True
    if module_name.endswith(".init_gui"):
        return True
    return False


def _collect_reloadable_modules(package_name: str, addon_directory: Path) -> dict[str, ModuleType]:
    modules: dict[str, ModuleType] = {}

    for module_name, module in tuple(sys.modules.items()):
        if module is None:
            continue
        if not _belongs_to_package(module_name, package_name):
            continue
        if _should_skip_module(module_name):
            continue
        if not _is_module_inside_addon(module, addon_directory):
            continue
        modules[module_name] = module

    return modules


def _reload_module_recursive(
    module_name: str,
    modules: dict[str, ModuleType],
    reloaded: set[str],
    reloading: set[str],
) -> None:
    if module_name in reloaded or module_name in reloading:
        return

    module = modules.get(module_name)
    if module is None:
        return

    reloading.add(module_name)

    child_names = sorted(
        name
        for name in modules
        if name.startswith(f"{module_name}.")
    )
    for child_name in child_names:
        _reload_module_recursive(child_name, modules, reloaded, reloading)

    try:
        _print_message(f"Reloading: {module_name}")
        reload(module)
        reloaded.add(module_name)
    except Exception as exc:
        _print_error(f"Failed to reload {module_name}: {exc}")
    finally:
        reloading.discard(module_name)


def reload_all_modules(package_name: str) -> None:
    modules = _collect_reloadable_modules(package_name, ADDON_DIRECTORY)
    if not modules:
        _print_message(f"No reloadable modules found for package '{package_name}'")
        return

    reloaded: set[str] = set()
    reloading: set[str] = set()

    root_modules = sorted(modules, key=lambda name: (name.count("."), name))
    for module_name in root_modules:
        _reload_module_recursive(module_name, modules, reloaded, reloading)

    _print_message("Reload complete")


class ReloadAllCommand:
    def GetResources(self) -> dict[str, str]:
        return {
            "Pixmap": "",
            "MenuText": "Reload All",
            "ToolTip": "Reload all modules of this workbench (dev tool)",
        }

    def IsActive(self) -> bool:
        return True

    def Activated(self) -> None:
        try:
            FreeCADGui.Control.closeDialog()
        except Exception as exc:
            _print_error(f"Failed to close dialog before reload: {exc}")

        reload_all_modules(ROOT_PACKAGE_NAME)


FreeCADGui.addCommand("ReloadAll", ReloadAllCommand())
