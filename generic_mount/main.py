import FreeCAD as App
import FreeCADGui as Gui
import Part
sys.path.append("/Users/da/code/freecad/generic_mount/")
import screw

def center(small, large):
    # center appletv inside mount
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

def render(tolerance = 0.5, x = 100, y = 100, z = 25, thickness = 4.22, lip = 2):
    doc = App.ActiveDocument
    if not doc:
        doc = App.newDocument("AppleTV_VESA_Mount")

    object_x = x + tolerance
    object_y = y + tolerance
    object_z = z + tolerance

    case_x = object_x + 2*thickness
    case_y = object_y + 1*thickness # object can be inserted flush
    case_z = object_z + 2*thickness

    lip_x = object_x - 2*lip
    lip_y = object_y - 2*lip
    lip_z = object_z - 2*lip

    # make boxes and screw, and center them
    object = Part.makeBox(object_x, object_y, object_z)
    case = Part.makeBox(case_x, case_y, case_z)
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

    # needs to be adjusted by BBoxes
    positions = [
        App.Vector(0, 0, 10),
        App.Vector(10, 0, 0),
        App.Vector(-10, 0, 0),
        App.Vector(0, 10, 0),
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

    refine_doc = doc.addObject("Part::Refine", "Refine_Shape")
    refine_doc.Source = result_doc
    doc.recompute()

    Gui.ActiveDocument.ActiveView.viewAxometric()
    Gui.SendMsgToActiveView("ViewFit")

if __name__ == "__main__":
    render(0.5)
