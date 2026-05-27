# Utilities from ChatGBT that are ment to help during Devolpment
# I wanted to seperate the code from ChatGBT from mine because of clarity

import FreeCAD as App  # ty:ignore[unresolved-import]
import time
from functools import wraps
import FreeCADGui as Gui  # ty:ignore[unresolved-import]



# from ChatGBT
def print_list(d, indent=0):
    for key, value in d.items():
        print(" " * indent + str(key) + ":")
        if isinstance(value, dict):
            print_list(value, indent + 4)
        else:
            print(" " * (indent + 4) + str(value))

def convert_vectors_to_list(data):
    """
    Recursively convert App.Vector(x, y, z) to [x, y, z] in any nested structure.
    """
    if isinstance(data, dict):
        return {k: convert_vectors_to_list(v) for k, v in data.items()}
    elif isinstance(data, (list, tuple)):
        return [convert_vectors_to_list(v) for v in data]
    elif hasattr(data, "x") and hasattr(data, "y") and hasattr(data, "z"):
        # likely an App.Vector
        return [data.x, data.y, data.z]
    else:
        return data

def convert_lists_to_vectors(data):
    """
    Recursively convert [x, y, z] lists back into App.Vector(x, y, z)
    if and only if they look like coordinate triplets.
    """
    if isinstance(data, dict):
        return {k: convert_lists_to_vectors(v) for k, v in data.items()}

    elif isinstance(data, list) and len(data) == 3 \
         and all(isinstance(n, (int, float)) for n in data):
        return App.Vector(*data)

    elif isinstance(data, list):
        return [convert_lists_to_vectors(v) for v in data]

    else:
        return data

def vector_to_list(obj):
    """
    Recursively convert all App.Vector instances inside a data structure
    into plain Python lists [x, y, z].
    """

    # Case 1: Direct Vector
    if isinstance(obj, App.Vector):
        return [obj.x, obj.y, obj.z]

    # Case 2: List
    elif isinstance(obj, list):
        return [vector_to_list(item) for item in obj]

    # Case 3: Tuple
    elif isinstance(obj, tuple):
        return tuple(vector_to_list(item) for item in obj)

    # Case 4: Set
    elif isinstance(obj, set):
        return {vector_to_list(item) for item in obj}

    # Case 5: Dict (convert keys and values)
    elif isinstance(obj, dict):
        return {
            vector_to_list(key): vector_to_list(value)
            for key, value in obj.items()
        }

    # Case 6: Custom objects
    elif hasattr(obj, "__dict__"):
        new_obj = obj.__class__.__new__(obj.__class__)
        for attr, value in obj.__dict__.items():
            setattr(new_obj, attr, vector_to_list(value))
        return new_obj

    # Default: return unchanged
    else:
        return obj


def print_list(data, indent=2):
    """
    Pretty-print a list of dictionaries with arbitrary value types.

    This function is intended for structures like:
        list[dict[str, Any]]

    Each dictionary is printed as a block, with one key–value pair per line.
    Values may be basic Python types or objects such as FreeCAD's App.Vector.

    Parameters
    ----------
    data : list[dict]
        A list of dictionaries to print.
    indent : int, optional
        Number of spaces used to indent dictionary entries.
        Default is 2.

    Returns
    -------
    None
        The function prints the formatted output to stdout.
    """
    for i, item in enumerate(data):
        print(f"Item {i}:")
        for key, value in item.items():
            print(" " * indent + f"{key}: {value}")



def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f"{func.__name__} took {end - start:.6f} seconds")
        return result
    return wrapper


def SelectionToMembers():
    def get_body(obj):
        while obj:
            if obj.TypeId == "PartDesign::Body":
                return obj
            obj = obj.getParentGeoFeatureGroup()
        return None

    bodies = set()

    for obj in Gui.Selection.getSelection():
        body = get_body(obj)
        if body:
            bodies.add(body)

    return list(bodies)