import FreeCAD as App
import FreeCADGui as Gui
import Part

def render_appletv(tolerance = 0.0):
    doc = App.ActiveDocument
    if not doc:
        doc = App.newDocument("AppleTVDesign")

    # -----------------------------
    # 1) Constants & Corner Data
    # -----------------------------
    base_size = 93.24 + tolerance     # total square side length
    height = 31.0 + tolerance          # final extrude thickness
    maxX = 27.14           # from Apple corner guidelines
    maxY = 25.83           # from Apple corner guidelines
    # thought using gap and inner_space were introducing float errors. turns out, the float problems are there anyway, but don't matter:
    #   within some tolerances (about 10^-7) points are considered equal.
    # now I feel like the new representation is better readable. keeping for maybe useful.
    #gap = maxX - maxY
    #inner_space = base_size - maxX - maxY

    # Apple’s corner coordinates: from (0,0) to (27.14,25.83)
    # For reference, see:
    # https://developer.apple.com/accessories/Accessory-Design-Guidelines.pdf
    # Release R24, page 570
    raw_corner_coords = [
        (0.00, 0.00), (2.00, 0.01), (4.00, 0.03), (6.00, 0.09), (7.99, 0.23),
        (9.98, 0.49), (11.93, 0.89), (13.85, 1.46), (15.71, 2.21), (17.47, 3.15),
        (19.13, 4.27), (20.66, 5.55), (22.05, 6.99), (23.27, 8.57), (24.33, 10.27),
        (25.21, 12.06), (25.89, 13.94), (26.40, 15.87), (26.75, 17.84), (26.96, 19.83),
        (27.07, 21.83), (27.12, 23.83), (27.14, 25.83)
    ]
    # This arc is a single BSpline in local coords:
    #   Start = (0,0), End = (maxX,maxY).

    # -----------------------------
    # 2) Build One BSpline Arc Edge
    # -----------------------------
    corner_crv = Part.BSplineCurve()
    corner_crv.interpolate([App.Vector(x, y, 0) for (x,y) in raw_corner_coords])
    arc_edge_local = corner_crv.toShape()

    # We will replicate this arc to each corner of the 93.24 mm square.

    # Helper function to transform an Edge: rotate + translate
    def transform_edge(edge, rotation_deg, translate_vec):
        """Return a copy of `edge` rotated around (0,0,0) by `rotation_deg` 
           about the Z-axis, then translated by translate_vec."""
        new_edge = edge.copy()
        new_edge.rotate(App.Vector(0,0,0), App.Vector(0,0,1), rotation_deg)
        new_edge.translate(App.Vector(translate_vec))
        return new_edge

    # -----------------------------
    # 3) Place 4 corner arcs
    # -----------------------------
    # We want a final bounding box [0..93.24, 0..93.24].

    corner_br = transform_edge(arc_edge_local,    0, (0,0,0))           # bottom-right
    corner_tr = transform_edge(arc_edge_local,  90, (maxX,base_size - maxX,0))   # top-right
    corner_tl = transform_edge(arc_edge_local, 180, (2*maxX - base_size, base_size,0))  # top-left
    corner_bl = transform_edge(arc_edge_local, 270, (-base_size + maxX,maxX,0))   # top-left
    #corner_tr = transform_edge(arc_edge_local,  90, (maxX,maxY+inner_space,0))   # top-right
    #corner_tl = transform_edge(arc_edge_local, 180, (gap-inner_space,maxY+maxX+inner_space,0))  # top-left
    #corner_bl = transform_edge(arc_edge_local, 270, (0 -maxX+gap-inner_space,maxX,0))   # bottom-left

    # visualize to make it easier to move them appropriately
    '''
    arc_obj_bl = doc.addObject("Part::Feature", "ArcCornerBL")
    arc_obj_bl.Shape = corner_bl
    arc_obj_br = doc.addObject("Part::Feature", "ArcCornerBR")
    arc_obj_br.Shape = corner_br
    arc_obj_tr = doc.addObject("Part::Feature", "ArcCornerTR")
    arc_obj_tr.Shape = corner_tr
    arc_obj_tl = doc.addObject("Part::Feature", "ArcCornerTL")
    arc_obj_tl.Shape = corner_tl
    doc.recompute()
    '''

    # -----------------------------
    # 4) Build 4 bridging lines
    # -----------------------------
    # Each arc has 2 endpoints: arc.Vertexes[0].Point and arc.Vertexes[-1].Point.
    # We want lines connecting the "outer corners" of the arcs. 
    #
    # The arcs meet in 4 corners,  and we have 4 lines forming the sides: 
    #   bottom line between corner_bl's right endpoint -> corner_br's left endpoint
    #   right line between corner_br's top endpoint -> corner_tr's bottom endpoint
    #   top line between corner_tr's left endpoint -> corner_tl's right endpoint
    #   left line between corner_tl's bottom endpoint -> corner_bl's top endpoint
    #
    # But we need to ensure we pick the correct endpoints from each arc 
    # (the arcs might be reversed).

    def endpoints(edge):
        """Return (startPoint, endPoint) for the given Edge."""
        v0 = edge.Vertexes[0].Point
        v1 = edge.Vertexes[-1].Point
        return (v0, v1)

    bl_v0, bl_v1 = endpoints(corner_bl)
    br_v0, br_v1 = endpoints(corner_br)
    tr_v0, tr_v1 = endpoints(corner_tr)
    tl_v0, tl_v1 = endpoints(corner_tl)

    # Print debug to see which might be correct
    '''
    print("BL arc endpoints:", bl_v0, bl_v1)
    print("BR arc endpoints:", br_v0, br_v1)
    print("TR arc endpoints:", tr_v0, tr_v1)
    print("TL arc endpoints:", tl_v0, tl_v1)
    '''

    # Now we can define bridging lines:
    # Bottom line: from BR's lower to BL's lower
    line_bottom = Part.LineSegment(br_v0, bl_v1).toShape()
    # Left line: from BL's upper to TL's lower
    line_left   = Part.LineSegment(bl_v0, tl_v1).toShape()
    # Top line: from TL's upper to TR's upper
    line_top    = Part.LineSegment(tl_v0, tr_v1).toShape()
    # Right line: from TR's lower to BR's upper
    line_right  = Part.LineSegment(tr_v0, br_v1).toShape()

    # -----------------------------
    # 5) Combine All 8 Edges into One Wire
    # -----------------------------
    # Edges: 4 arcs (corner_bl, corner_br, corner_tr, corner_tl) + 4 lines
    all_edges = [
        corner_br,
        line_bottom,
        corner_bl,
        line_left,
        corner_tl,
        line_top,
        corner_tr,
        line_right,
    ]

    # Create one Wire
    full_wire = Part.Wire(all_edges)
    if not full_wire.isClosed():
        print("DEBUG: The full_wire is not recognized as closed. Check endpoints!")
    full_face = Part.Face(full_wire)
    full_face.fix(1e-7, 1e-7, 1e-7)

    face_obj = doc.addObject("Part::Feature", "AppleTV_2D")
    face_obj.Label = "AppleTV_Outline_Face"
    face_obj.Shape = full_face

    # -----------------------------
    # 6) Extrude to 31 mm
    # -----------------------------
    solid_3d = full_face.extrude(App.Vector(0,0,height))
    solid_3d.fix(1e-7, 1e-7, 1e-7)
    solid_obj = doc.addObject("Part::Feature", "AppleTV_3D")
    solid_obj.Label = "AppleTV_Extruded"
    solid_obj.Shape = solid_3d
    
    print("X: " , solid_3d.BoundBox.XLength, " mm")
    print("Y: " , solid_3d.BoundBox.YLength, " mm")
    print("Z: " , solid_3d.BoundBox.ZLength, " mm")

    face_obj.ViewObject.hide()

    doc.recompute()
    Gui.ActiveDocument.ActiveView.viewAxometric()
    Gui.SendMsgToActiveView("ViewFit")

if __name__ == "__main__":
    render_appletv()
