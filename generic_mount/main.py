import FreeCAD as App
import FreeCADGui as Gui
import Part
sys.path.append("/Users/da/code/freecad/generic_mount/")
import screw
from enum import Enum, auto

class MountType(Enum):
    VESA = auto()
    Wall = auto()
    NoMount = auto()

def center(small, large):
    bb_small = small.BoundBox
    bb_large = large.BoundBox
    center_small = App.Vector(
        (bb_small.XMin + bb_small.XMax) / 2.0,
        (bb_small.YMin + bb_small.YMax) / 2.0,
        (bb_small.ZMin + bb_small.ZMax) / 2.0
    )
    center_large = App.Vector(
        (bb_large.XMin + bb_large.XMax) / 2.0,
        (bb_large.YMin + bb_large.YMax) / 2.0,
        (bb_large.ZMin + bb_large.ZMax) / 2.0
    )
    translation_vector = center_large - center_small
    print("Translation vector to center object:", translation_vector)
    
    result = small.copy()
    result.translate(translation_vector)
    return result

def getTopEdges(shape, chamfer_distance = 1):
    top_face = max(shape.Faces, key=lambda f: f.CenterOfMass.z)
    return list(top_face.Edges)
    #top_face_edges = list(top_face.Edges)
    #return shape.makeChamfer(chamfer_distance, top_face_edges)

def getOuterEdges(shape, chamfer_distance = 1):
    tol = 1e-6
    # Find the vertical edges (those that go straight up the Z-axis)
    vertical_edges = []
    for edge in shape.Edges:
        # Get the start and end vertices of the edge.
        v0 = edge.Vertexes[0].Point
        v1 = edge.Vertexes[1].Point
        # Calculate differences in coordinates.
        dx = abs(v1.x - v0.x)
        dy = abs(v1.y - v0.y)
        dz = abs(v1.z - v0.z)
        # If the x and y differences are nearly zero and z is different,
        # then this edge is vertical.
        if dx < tol and dy < tol and dz > tol:
            vertical_edges.append(edge)
    return vertical_edges
    #chamfer_distance = 1
    #return shape.makeChamfer(chamfer_distance, vertical_edges)

def render(tolerance = 0.5, x = 76.5, y = 89.5, z = 49, thickness = 4.22, lip = 2):
    doc = App.ActiveDocument
    if not doc:
        doc = App.newDocument("Generic_VESA_Mount")

    # TODO: bottom thickness = max(thickness, screw head depth)
    #       bad idea. even though not pretty, add and fuse extended bottom afterwards. everything else gets complicated.
    # TODO: screwType as parameter
    # TODO: MountType as parameter - VESA single screw center, Wall dual screw with alignment guides
    # TODO: input either wire + height or cuboid
    # TODO: is offset usable if we want to insert the object flush? maybe cut away the front by 1*thickness?
    #       or, maybe there is a way to scale it down in one dimension [preferred]

    object_x = x + tolerance
    object_y = y + tolerance
    object_z = z + tolerance

    case_x = object_x + 2*thickness
    case_y = object_y + 1*thickness # object can be inserted flush
    case_z = object_z + 2*thickness

    lip_x = object_x - 2*lip
    lip_y = object_y - 2*lip - thickness
    lip_z = object_z - 2*lip

    # make boxes and screw, chamfer the outsides of the case, and center them
    object = Part.makeBox(object_x, object_y, object_z)
    case = Part.makeBox(case_x, case_y, case_z)
    edges = getTopEdges(case)
    edges.extend(getOuterEdges(case))
    case = case.makeFillet(2, edges)

    lipb = Part.makeBox(lip_x, lip_y, lip_z)
    object = center(object, case)
    object.translate(App.Vector(0, object.BoundBox.YMax - case.BoundBox.YMax, object.BoundBox.ZMin - case.BoundBox.ZMin - thickness)) # translate for flush cut
    lipb = center(lipb, case)
    screwm = screw.render(screw.ScrewType.M6, 12)
    screwm = center(screwm, case)
    screwm.translate(App.Vector(0, 0, case.BoundBox.ZMin + thickness - screwm.BoundBox.ZMax)) # top of screw to top of bottom of case

    # put into objects for posterity
    object_doc = doc.addObject("Part::Feature", "Object")
    object_doc.Shape = object
    object_doc.ViewObject.Visibility = False
    case_doc = doc.addObject("Part::Feature", "Case")
    case_doc.Shape = case
    case_doc.ViewObject.Visibility = False
    lip_doc = doc.addObject("Part::Feature", "Lip")
    lip_doc.Shape = lipb
    lip_doc.ViewObject.Visibility = False
    screw_doc = doc.addObject("Part::Feature", "Screw")
    screw_doc.Shape = screwm
    screw_doc.ViewObject.Visibility = False
    doc.recompute()

    # align cutter on the outer / inner-most faces
    positions = [
        App.Vector(0, 0, case.BoundBox.ZMax - lipb.BoundBox.ZMax),
        App.Vector(case.BoundBox.XMax - lipb.BoundBox.XMax, 0, 0),
        App.Vector(case.BoundBox.XMin - lipb.BoundBox.XMin, 0, 0),
        App.Vector(0, case.BoundBox.YMax - lipb.BoundBox.YMax, 0),
    ]
    cutters = []
    for pos in positions:
        # Copy the cutter shape so the original remains unchanged.
        cutter_copy = lipb.copy()
        cutter_copy.translate(pos)
        cutters.append(cutter_copy)
    cutters.append(object)
    cutters.append(screwm)
    # Combine all the translated and regular cutters into one compound.
    compound_cutter = Part.Compound(cutters)
    cutter_doc = doc.addObject("Part::Compound", "Cutter")
    cutter_doc.ViewObject.Visibility = False
    cutter_doc.Shape = compound_cutter
    doc.recompute()

    result_shape = case_doc.Shape.cut(compound_cutter)
    result_doc = doc.addObject("Part::Feature", "Result")
    result_doc.ViewObject.Visibility = False
    result_doc.Shape = result_shape

    refine_doc = doc.addObject("Part::Refine", "Refined_Result")
    refine_doc.Source = result_doc
    doc.recompute()

    Gui.ActiveDocument.ActiveView.viewAxometric()
    Gui.SendMsgToActiveView("ViewFit")

if __name__ == "__main__":
    render(0.5)
