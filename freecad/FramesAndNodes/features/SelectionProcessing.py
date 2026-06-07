import FreeCAD as APP  # ty:ignore[unresolved-import]
import FreeCADGui as Gui  # ty:ignore[unresolved-import]

from .ProfileLogic import isValidProfileBody


def _shape_type_of(sub_object) -> str:
    return getattr(sub_object, "ShapeType", "")


def _sub_element_leaf_name(sub_element_name: str) -> str:
    if not sub_element_name:
        return ""
    return sub_element_name.rsplit(".", 1)[-1]


def _shape_element_index(sub_element_name: str, prefix: str) -> int | None:
    leaf_name = _sub_element_leaf_name(sub_element_name)
    if not leaf_name.startswith(prefix):
        return None

    try:
        return int(leaf_name[len(prefix):]) - 1
    except (TypeError, ValueError):
        return None


def _is_profile_body(obj) -> bool:
    if obj is None:
        return False

    if isValidProfileBody(obj):
        return True

    if getattr(obj, "TypeId", "") != "PartDesign::Body":
        return False

    required_attributes = ("Alignment", "OffsetX", "OffsetY", "AttachmentSupport")
    if not all(hasattr(obj, attribute) for attribute in required_attributes):
        return False

    for feature in getattr(obj, "Group", ()):
        feature_name = getattr(feature, "Name", "")
        feature_label = getattr(feature, "Label", "")
        if feature_name.startswith("Pad") and feature_label.startswith("Profile"):
            return True

    return False


def _iter_shape_edges(shape):
    edges = getattr(shape, "Edges", ())
    for index, edge in enumerate(edges, start=1):
        yield f"Edge{index}", edge


def _shape_element_from_index(shape, attribute_name: str, index: int | None):
    if index is None or index < 0:
        return None

    elements = getattr(shape, attribute_name, ())
    if index >= len(elements):
        return None

    return elements[index]


def _is_same_shape(left, right) -> bool:
    if left is right:
        return True

    is_same = getattr(left, "isSame", None)
    if callable(is_same):
        try:
            return bool(is_same(right))
        except Exception:
            pass

    left_hash = getattr(left, "hashCode", None)
    right_hash = getattr(right, "hashCode", None)
    if callable(left_hash) and callable(right_hash):
        try:
            return left_hash() == right_hash()
        except Exception:
            return False

    return False


def _find_profile_body_in_hierarchy(obj):
    current = obj
    visited = set()

    while current is not None and id(current) not in visited:
        visited.add(id(current))
        if _is_profile_body(current):
            return current

        get_parent = getattr(current, "getParentGeoFeatureGroup", None)
        if callable(get_parent):
            try:
                current = get_parent()
                continue
            except Exception:
                pass
        current = None

    return None


def _get_selected_profile_body(selection_object):
    obj = getattr(selection_object, "Object", None)
    if obj is None:
        return None

    profile_body = _find_profile_body_in_hierarchy(obj)
    if profile_body is not None:
        return profile_body

    document = getattr(obj, "Document", None)
    if document is None:
        return None

    for sub_element_name in getattr(selection_object, "SubElementNames", ()):
        tokens = sub_element_name.split(".")[:-1]
        for candidate in _selection_path_objects(obj, document, tokens):
            profile_body = _find_profile_body_in_hierarchy(candidate)
            if profile_body is not None:
                return profile_body

    return None


def _is_document_object(obj) -> bool:
    return obj is not None and hasattr(obj, "Document") and hasattr(obj, "Name")


def _selection_path_objects(root_obj, document, tokens):
    get_sub_object = getattr(root_obj, "getSubObject", None)
    if callable(get_sub_object):
        for index in range(len(tokens), 0, -1):
            path = ".".join(tokens[:index])
            for suffix in (".", ""):
                try:
                    candidate = get_sub_object(path + suffix)
                except Exception:
                    candidate = None

                if _is_document_object(candidate):
                    yield candidate
                    return

    for token in reversed(tokens):
        candidate = document.getObject(token)
        if candidate is not None:
            yield candidate


def _resolve_selection_target_object(selection_object, sub_element_name):
    obj = getattr(selection_object, "Object", None)
    if obj is None:
        return None

    document = getattr(obj, "Document", None)
    if document is None:
        return obj

    target_object = obj
    for candidate in _selection_path_objects(obj, document, sub_element_name.split(".")[:-1]):
        target_object = candidate
        break

    return target_object


def _edge_names_from_vertex(shape, vertex):
    edge_names = []
    point = getattr(vertex, "Point", None)
    if point is None:
        return edge_names

    for edge_name, edge in _iter_shape_edges(shape):
        for edge_vertex in getattr(edge, "Vertexes", ()):
            edge_point = getattr(edge_vertex, "Point", None)
            if edge_point == point:
                edge_names.append(edge_name)
                break

    return edge_names


def _resolve_sub_object(shape, sub_element_name, sub_object):
    if sub_object is not None and _shape_type_of(sub_object):
        return sub_object

    face = _shape_element_from_index(
        shape,
        "Faces",
        _shape_element_index(sub_element_name, "Face"),
    )
    if face is not None:
        return face

    edge = _shape_element_from_index(
        shape,
        "Edges",
        _shape_element_index(sub_element_name, "Edge"),
    )
    if edge is not None:
        return edge

    vertex = _shape_element_from_index(
        shape,
        "Vertexes",
        _shape_element_index(sub_element_name, "Vertex"),
    )
    if vertex is not None:
        return vertex

    return sub_object


def _edge_names_from_sub_object(obj, sub_element_name, sub_object):
    shape = getattr(obj, "Shape", None)
    if shape is None:
        return ()

    sub_object = _resolve_sub_object(shape, sub_element_name, sub_object)
    shape_type = _shape_type_of(sub_object)
    if shape_type == "Edge":
        leaf_name = _sub_element_leaf_name(sub_element_name)
        return (leaf_name,) if leaf_name.startswith("Edge") else ()

    if shape_type == "Face":
        face_edge_names = []
        for edge_name, edge in _iter_shape_edges(shape):
            if any(_is_same_shape(edge, face_edge) for face_edge in getattr(sub_object, "Edges", ())):
                face_edge_names.append(edge_name)

        if face_edge_names:
            return tuple(face_edge_names)

        face = _shape_element_from_index(
            shape,
            "Faces",
            _shape_element_index(sub_element_name, "Face"),
        )
        if face is not None:
            return tuple(
                edge_name
                for edge_name, edge in _iter_shape_edges(shape)
                if any(_is_same_shape(edge, face_edge) for face_edge in getattr(face, "Edges", ()))
            )

        return tuple(face_edge_names)

    if shape_type == "Vertex":
        return tuple(_edge_names_from_vertex(shape, sub_object))

    return ()


def _edge_names_from_object(obj):
    shape = getattr(obj, "Shape", None)
    if shape is None:
        return ()
    return tuple(edge_name for edge_name, _edge in _iter_shape_edges(shape))


def _iter_group_geometry_objects(obj, include_root=True):
    stack = [(obj, include_root)]
    visited = set()

    while stack:
        current, include_current = stack.pop()
        if current is None or id(current) in visited:
            continue

        visited.add(id(current))
        if include_current and getattr(current, "Shape", None) is not None:
            yield current

        stack.extend((child, True) for child in reversed(tuple(getattr(current, "Group", ()) or ())))


def _iter_selection_geometry_objects(obj):
    group = tuple(getattr(obj, "Group", ()) or ())
    if group:
        return _iter_group_geometry_objects(obj, include_root=False)

    return (candidate for candidate in (obj,) if getattr(candidate, "Shape", None) is not None)


def _append_unique_edges(target_obj, edge_names, edges, edge_keys):
    for edge_name in edge_names:
        edge_key = (id(target_obj), edge_name)
        if edge_key not in edge_keys:
            edge_keys.add(edge_key)
            edges.append((target_obj, edge_name))


def _group_edge_names_from_sub_object(obj, sub_object):
    shape_type = _shape_type_of(sub_object)
    if not shape_type:
        return ()

    matches = []
    for target_obj in _iter_group_geometry_objects(obj):
        shape = getattr(target_obj, "Shape", None)
        if shape is None:
            continue

        if shape_type == "Edge":
            edge_names = tuple(
                edge_name
                for edge_name, edge in _iter_shape_edges(shape)
                if _is_same_shape(edge, sub_object)
            )
        elif shape_type == "Face":
            sub_edges = getattr(sub_object, "Edges", ())
            edge_names = tuple(
                edge_name
                for edge_name, edge in _iter_shape_edges(shape)
                if any(_is_same_shape(edge, sub_edge) for sub_edge in sub_edges)
            )
        elif shape_type == "Vertex":
            edge_names = tuple(_edge_names_from_vertex(shape, sub_object))
        else:
            edge_names = ()

        if edge_names:
            matches.append((target_obj, edge_names))

    return tuple(matches)


def _iter_profile_bodies(document):
    if document is None:
        return

    for obj in getattr(document, "Objects", ()):
        if _is_profile_body(obj):
            yield obj


def _attachment_support_entries(profile_body):
    attachment_support = getattr(profile_body, "AttachmentSupport", None)
    if not attachment_support:
        return ()

    # FreeCAD stores attachment support entries as `(object, ("Edge1",))`.
    if (
        len(attachment_support) == 2
        and not isinstance(attachment_support[0], tuple)
        and isinstance(attachment_support[1], (tuple, list, str))
    ):
        attachment_support = (attachment_support,)

    entries = []
    for entry in attachment_support:
        try:
            support_obj, support_names = entry
        except (TypeError, ValueError):
            continue

        if isinstance(support_names, str):
            support_names = (support_names,)

        entries.append((support_obj, tuple(support_names)))

    return tuple(entries)


def _frame_members_from_support_edges(target_obj, edge_names):
    document = getattr(target_obj, "Document", None)
    if document is None or not edge_names:
        return ()

    matched_members = []
    seen_profile_ids = set()
    edge_name_set = set(edge_names)

    for profile_body in _iter_profile_bodies(document):
        for support_obj, support_names in _attachment_support_entries(profile_body):
            if support_obj is not target_obj:
                continue

            if not edge_name_set.intersection(support_names):
                continue

            profile_id = id(profile_body)
            if profile_id in seen_profile_ids:
                break

            seen_profile_ids.add(profile_id)
            matched_members.append(profile_body)
            break

    return tuple(matched_members)


def getEdgesFromSelcection()->tuple:
    '''
    From Gui.Selection This function returns a tuple((obj,Edge),(obj1,Edge1),...)
    It follows this Logic:
    Obj => All Edges
    Edge => Edge
    Face => Edges that belong to that face
    Vertex => Edges that end in set Vertex
    ProfileBody / Geometrie of a ProfileBody => added to tuple of Profiles
    If there are more Profiles then edges selected => tuple(Profile,Profile1,..)
    '''
    profiles = []
    profile_ids = set()
    edges = []
    edge_keys = set()

    selection = Gui.Selection.getSelectionEx("", 0)
    for selection_object in selection:
        obj = getattr(selection_object, "Object", None)
        if obj is None:
            continue

        profile_body = _get_selected_profile_body(selection_object)
        if profile_body is not None:
            profile_id = id(profile_body)
            if profile_id not in profile_ids:
                profile_ids.add(profile_id)
                profiles.append(profile_body)
            continue

        sub_element_names = tuple(getattr(selection_object, "SubElementNames", ()))
        sub_objects = tuple(getattr(selection_object, "SubObjects", ()))

        if not sub_element_names:
            for target_obj in _iter_selection_geometry_objects(obj):
                _append_unique_edges(target_obj, _edge_names_from_object(target_obj), edges, edge_keys)
            continue

        for sub_element_name, sub_object in zip(sub_element_names, sub_objects):
            target_obj = _resolve_selection_target_object(selection_object, sub_element_name)
            if target_obj is None:
                continue

            edge_names = _edge_names_from_sub_object(target_obj, sub_element_name, sub_object)
            _append_unique_edges(target_obj, edge_names, edges, edge_keys)

            if edge_names:
                continue

            for grouped_obj, grouped_edge_names in _group_edge_names_from_sub_object(obj, sub_object):
                _append_unique_edges(grouped_obj, grouped_edge_names, edges, edge_keys)

    if len(profiles) > len(edges):
        return tuple(profiles)

    return tuple(edges)


def getFrameMembersFromSelection() -> tuple:
    '''
    From Gui.Selection this function returns a tuple(ProfileBody, ProfileBody1, ...)
    using the same selection resolution rules as getEdgesFromSelcection().

    It accepts direct FrameMember selections as well as face, edge, and vertex
    selections on geometry that belongs to a FrameMember.
    '''
    frame_members = []
    seen_profile_ids = set()

    selection = Gui.Selection.getSelectionEx("", 0)
    # print(selection)
    for selection_object in selection:
        profile_body = _get_selected_profile_body(selection_object)
        if profile_body is None:
            obj = getattr(selection_object, "Object", None)
            if obj is None:
                continue

            sub_element_names = tuple(getattr(selection_object, "SubElementNames", ()))
            sub_objects = tuple(getattr(selection_object, "SubObjects", ()))

            if not sub_element_names:
                for target_obj in _iter_selection_geometry_objects(obj):
                    edge_names = _edge_names_from_object(target_obj)
                    for matched_member in _frame_members_from_support_edges(target_obj, edge_names):
                        profile_id = id(matched_member)
                        if profile_id in seen_profile_ids:
                            continue

                        seen_profile_ids.add(profile_id)
                        frame_members.append(matched_member)
                continue

            for sub_element_name, sub_object in zip(sub_element_names, sub_objects):
                target_obj = _resolve_selection_target_object(selection_object, sub_element_name)
                if target_obj is None:
                    continue

                edge_names = _edge_names_from_sub_object(target_obj, sub_element_name, sub_object)
                matched_any = False
                for matched_member in _frame_members_from_support_edges(target_obj, edge_names):
                    matched_any = True
                    profile_id = id(matched_member)
                    if profile_id in seen_profile_ids:
                        continue

                    seen_profile_ids.add(profile_id)
                    frame_members.append(matched_member)

                if matched_any:
                    continue

                for grouped_obj, grouped_edge_names in _group_edge_names_from_sub_object(obj, sub_object):
                    for matched_member in _frame_members_from_support_edges(grouped_obj, grouped_edge_names):
                        profile_id = id(matched_member)
                        if profile_id in seen_profile_ids:
                            continue

                        seen_profile_ids.add(profile_id)
                        frame_members.append(matched_member)
            continue

        profile_id = id(profile_body)
        if profile_id in seen_profile_ids:
            continue

        seen_profile_ids.add(profile_id)
        frame_members.append(profile_body)

    return tuple(frame_members)

def _frame_member_expression_names(obj) -> set:
    expression_engine = getattr(obj, "ExpressionEngine", ())
    if not expression_engine:
        return set()

    return {
        expression.split(".", 1)[0]
        for property_name, expression in expression_engine
        if property_name.startswith("FrameMember") and isinstance(expression, str)
    }


def _is_knot_object(obj) -> bool:
    if obj is None:
        return False

    if getattr(obj, "isKnot", False) is True:
        return True

    linked_object = getattr(obj, "LinkedObject", None)
    if getattr(linked_object, "isKnot", False) is True:
        return True

    return bool(_frame_member_expression_names(obj))


def _find_knot_in_hierarchy(obj):
    current = obj
    visited = set()

    while current is not None and id(current) not in visited:
        visited.add(id(current))
        if _is_knot_object(current):
            return current

        get_parent = getattr(current, "getParentGeoFeatureGroup", None)
        if not callable(get_parent):
            break

        try:
            current = get_parent()
        except Exception:
            break

    return None


def _get_selected_knot(selection_object):
    obj = getattr(selection_object, "Object", None)
    knot = _find_knot_in_hierarchy(obj)
    if knot is not None:
        return knot

    document = getattr(obj, "Document", None)
    if document is None:
        return None

    for sub_element_name in getattr(selection_object, "SubElementNames", ()):
        tokens = sub_element_name.split(".")[:-1]
        for candidate in _selection_path_objects(obj, document, tokens):
            knot = _find_knot_in_hierarchy(candidate)
            if knot is not None:
                return knot

    return None


def getKnotFromFrameMembers()->tuple:
    '''
    This Function Return an Inserted Knot that has the selected Frame Members as a part of its FrameMember0..n Property

    Returns: tuple(Knot)

    '''
    matched_knots = []
    seen_knot_ids = set()

    for selection_object in Gui.Selection.getSelectionEx("", 0):
        knot = _get_selected_knot(selection_object)
        if knot is None:
            continue

        knot_id = id(knot)
        if knot_id in seen_knot_ids:
            continue

        seen_knot_ids.add(knot_id)
        matched_knots.append(knot)

    frame_members = getFrameMembersFromSelection()
    if len(frame_members) < 2:
        return tuple(matched_knots)

    selected_member_names = {member.Name for member in frame_members}
    documents = []
    seen_document_ids = set()
    for member in frame_members:
        document = getattr(member, "Document", None)
        if document is None:
            continue

        document_id = id(document)
        if document_id in seen_document_ids:
            continue

        seen_document_ids.add(document_id)
        documents.append(document)

    for document in documents:
        for obj in getattr(document, "Objects", ()):
            knot_member_names = _frame_member_expression_names(obj)
            if not selected_member_names.issubset(knot_member_names):
                continue

            knot_id = id(obj)
            if knot_id in seen_knot_ids:
                continue

            seen_knot_ids.add(knot_id)
            matched_knots.append(obj)

    return tuple(matched_knots)
