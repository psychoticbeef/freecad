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

def render(thickness = 5.0):
    doc = App.ActiveDocument
    if not doc:
        doc = App.newDocument("AppleTV_Vesa_Mount")

    offset_dist   = thickness      # offset shape outward by 5 mm
    extrude_dist  = appletv.get_height() + 2*thickness     # extrude downward 10 mm

    # Retrieve existing objects

    appletv_1d_obj = doc.getObject("AppleTV_1D")
    if not appletv_1d_obj:
        raise ValueError("No object named 'AppleTV_1D' found in the document.")

    appletv_3d_obj = doc.getObject("AppleTV_3D")
    if not appletv_3d_obj:
        raise ValueError("No object named 'AppleTV_3D' found in the document.")

    # -----------------------------
    # 3) Make an offset of the 1D shape
    # -----------------------------
    copy_obj = doc.addObject("Part::Feature", "Case_1D_Perimeter_Wire")
    copy_obj.Shape = appletv_1d_obj.Shape.copy()
    doc.recompute()
    offset_obj = doc.addObject("Part::Offset2D", "Case_1D_Offset")
    offset_obj.Source = copy_obj
    offset_obj.Value = offset_dist
    doc.recompute()
    if not offset_obj.Shape.isClosed():
        print("DEBUG: The Case_1D_Offset is not recognized as closed. Check endpoints!")
    
    face = Part.Face(offset_obj.Shape)
    face.fix(1e-6, 1e-6, 1e-6)
    face_obj = doc.addObject("Part::Feature", "Case_2D")
    face_obj.Shape = face
    doc.recompute()

    extruded_mount_shape = face.extrude(App.Vector(0,0,extrude_dist))
    extruded_mount_obj = doc.addObject("Part::Feature", "Case_3D")
    extruded_mount_obj.Shape = extruded_mount_shape
    doc.recompute()

    appletv_translated = center(appletv_3d_obj.Shape, extruded_mount_obj.Shape)
    result_shape = extruded_mount_obj.Shape.cut(appletv_translated)
    doc.recompute()

    result_obj = doc.addObject("Part::Feature", "Case_3D_Hole_Intermediate")
    result_obj.Shape = result_shape
    result_obj.ViewObject.Visibility = False
    doc.recompute()

    atbb = appletv_translated.BoundBox
    cut_box = Part.makeBox(atbb.XLength, atbb.YLength, atbb.ZLength)
    cut_box_centered = center(cut_box, result_obj.Shape)
    cut_box_centered.translate(App.Vector(0, 15, 0))
    resultier_shape = result_shape.cut(cut_box_centered)
    doc.recompute()

    # -----------------------------
    # 5) Create a new object to hold the result
    # -----------------------------
    result_obj = doc.addObject("Part::Feature", "Case_3D_Hole")
    result_obj.Shape = resultier_shape
    doc.recompute()
    
    copy_obj.ViewObject.Visibility = False
    offset_obj.ViewObject.Visibility = False
    face_obj.ViewObject.Visibility = False
    extruded_mount_obj.ViewObject.Visibility = False
    result_obj.ViewObject.Transparency = 50
    result_obj.ViewObject.Visibility = False


    doc.recompute()
    Gui.ActiveDocument.ActiveView.viewAxometric()
    Gui.SendMsgToActiveView("ViewFit")

if __name__ == "__main__":
    #appletv.render()
    render()