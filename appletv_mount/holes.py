import FreeCAD as App
import FreeCADGui as Gui
import Part
import os
import sys
sys.path.append("/Users/da/code/freecad/appletv_mount/")
import appletv

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

def render(thickness = 3.52):
    doc = App.ActiveDocument
    if not doc:
        doc = App.newDocument("AppleTV_Vesa_Mount")

    offset_dist   = thickness      # offset shape outward by 5 mm
    extrude_dist  = appletv.get_height() + 2*thickness     # extrude downward 10 mm

    # Retrieve existing objects

    appletv_1d_obj = doc.getObject("AppleTV_1D")
    if not appletv_1d_obj:
        raise ValueError("No object named 'AppleTV_1D' found in the document.")
    
    case_3d_obj = doc.getObject("Case_3D_Hole")
    if not case_3d_obj:
        raise ValueError("No object named 'Case_3D_Hole' found in the document.")

    copy_obj = doc.addObject("Part::Feature", "Hole_1D_Perimeter_Wire")
    copy_obj.Shape = appletv_1d_obj.Shape.copy()
    doc.recompute()
    offset_obj = doc.addObject("Part::Offset2D", "Hole_1D_Offset")
    offset_obj.Source = copy_obj
    offset_obj.Value = -offset_dist
    doc.recompute()
    if not offset_obj.Shape.isClosed():
        print("DEBUG: The Hole_1D_Offset is not recognized as closed. Check endpoints!")
    
    full_face = Part.Face(offset_obj.Shape)
    full_face.fix(1e-6, 1e-6, 1e-6)
    full_face_obj = doc.addObject("Part::Feature", "Hole_2D")
    full_face_obj.Shape = full_face
    doc.recompute()

    solid_3d = full_face.extrude(App.Vector(0,0,31-2*thickness))
    solid_3d.fix(1e-6, 1e-6, 1e-6)
    solid_obj = doc.addObject("Part::Feature", "Hole_3D")
    solid_obj.Shape = solid_3d
    doc.recompute()

    '''
    appletv_translated = center(solid_obj.Shape, case_3d_obj.Shape)
    appletv_translated.translate(App.Vector(0, 0, 5*thickness))
    intermediate_obj = doc.addObject("Part::Feature", "Cut_Hole_Intermediate")
    intermediate_obj.Shape = appletv_translated
    intermediate_obj.ViewObject.Visibility = False
    doc.recompute()
    '''

    atbb = solid_obj.Shape.BoundBox
    cut_box = Part.makeBox(atbb.XLength-6, atbb.YLength-10, atbb.ZLength)
    cut_box_centered = center(cut_box, case_3d_obj.Shape)

    positions = [
        App.Vector(0, 0, 4*thickness),
        App.Vector(4*thickness, 0, 0),
        App.Vector(-4*thickness, 0, 0),
        App.Vector(0, -4*thickness, 0),
    ]
    # Create a list to hold the translated cutter shapes.
    translated_cutters = []
    for pos in positions:
        # Copy the cutter shape so the original remains unchanged.
        cutter_copy = cut_box_centered.copy()
        # Translate the copy by the given vector.
        cutter_copy.translate(pos)
        translated_cutters.append(cutter_copy)

    # Combine all the translated cutters into one compound.
    compound_cutter = Part.Compound(translated_cutters)
    cutter_obj = doc.addObject("Part::Compound", "Cutter")
    cutter_obj.Shape = compound_cutter
    # Perform a single boolean cut: subtract the compound cutter from the main shape.
    result_shape = case_3d_obj.Shape.cut(compound_cutter)

    result_obj = doc.addObject("Part::Feature", "Mount_3D")
    result_obj.Shape = result_shape

    doc.recompute()
    Gui.ActiveDocument.ActiveView.viewAxometric()
    Gui.SendMsgToActiveView("ViewFit")

if __name__ == "__main__":
    render()