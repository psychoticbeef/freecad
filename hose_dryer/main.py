import FreeCAD, FreeCADGui, Part, math, os

def save_screenshot(document_name, width=1024, height=1024):
    if not FreeCAD.GuiUp:
        print("Error: FreeCAD GUI is not available.")
        return

    doc = FreeCADGui.getDocument(document_name)
    if not doc:
        print(f"Error: Document {document_name} not found.")
        return

    view = doc.activeView()

    FreeCADGui.updateGui()
    view.setCameraOrientation(FreeCAD.Rotation(0, -45, -35).Q)
    view.fitAll()
    FreeCADGui.updateGui()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    screenshot_path = os.path.join(script_dir, "img", f"{document_name}.png")

    view.saveImage(screenshot_path, width, height, "PNG")
    print(f"Screenshot saved to: {screenshot_path}")

def get_arc_wire(innerDiameter, arc, margin):
    arcRadius = innerDiameter / 2.0
    arcAngleOffset = math.radians(arc) - math.pi

    # inner arc
    arcCenter = FreeCAD.Vector(0, 0, 0)
    innerArc = Part.ArcOfCircle(
        Part.Circle(arcCenter, FreeCAD.Vector(0, 0, 1), arcRadius),
        -math.pi - arcAngleOffset, arcAngleOffset
    ).toShape()
    # outer arc
    outerArc = Part.ArcOfCircle(
        Part.Circle(arcCenter, FreeCAD.Vector(0, 0, 1), arcRadius + margin),
        -math.pi - arcAngleOffset, arcAngleOffset
    ).toShape()
    # connect inner and outer arc
    arcEdges = [
        innerArc,
        Part.LineSegment(innerArc.Vertexes[-1].Point, outerArc.Vertexes[-1].Point).toShape(),
        outerArc,
        Part.LineSegment(innerArc.Vertexes[0].Point, outerArc.Vertexes[0].Point).toShape(),
    ]
    return Part.Wire(arcEdges)


def create_cpap_holder(
    document_name,
    margin,
    height,
    width,
    clampedWidth,
    arc,
    innerDiameter1,
    innerDiameter2,
    extrusionDepth,
    fillet_radius=0.9
):
    document = FreeCAD.newDocument(document_name)

    # wire base
    sideOffset = (width - clampedWidth) / 2.0
    basePoints = [
        FreeCAD.Vector(sideOffset, 0, 0),                         # pt_innerBottomLeft
        FreeCAD.Vector(0, height, 0),                             # pt_innerTopLeft
        FreeCAD.Vector(width, height, 0),                         # pt_innerTopRight
        FreeCAD.Vector(width - sideOffset, 0, 0),                 # pt_innerBottomRight
        FreeCAD.Vector(width - sideOffset + margin, 0, 0),        # pt_extendedBottomRight
        FreeCAD.Vector(width + margin, height + margin, 0),       # pt_extendedTopRight
        FreeCAD.Vector(width, height + margin, 0),                # pt_transitionTopRight
        FreeCAD.Vector(-margin, height + margin, 0),              # pt_extendedTopLeft
        FreeCAD.Vector(-margin + sideOffset, 0, 0),               # pt_extendedBottomLeft
        FreeCAD.Vector(sideOffset, 0, 0)                          # Closing the loop back to pt_innerBottomLeft
    ]
    baseEdges = [Part.LineSegment(basePoints[i], basePoints[i + 1]).toShape() for i in range(len(basePoints) - 1)]
    baseWire = Part.Wire(baseEdges)

    arcWire1 = get_arc_wire(innerDiameter=innerDiameter1, arc=arc, margin=margin)
    arcWire2 = get_arc_wire(innerDiameter=innerDiameter2, arc=arc, margin=margin)

    # Create faces and extrusion
    baseFace = Part.Face(baseWire)
    arc1Face = Part.Face(arcWire1)
    arc2Face = Part.Face(arcWire2)
    extrudedBase = baseFace.extrude(FreeCAD.Vector(0, 0, extrusionDepth))
    hypothenuse = math.hypot(height + margin, sideOffset)
    extrudedArc1 = arc1Face.extrude(FreeCAD.Vector(0, 0, hypothenuse + 10))
    extrudedArc2 = arc2Face.extrude(FreeCAD.Vector(0, 0, hypothenuse + 10))
    wall_angle = -90+math.degrees(math.atan2(height + margin, sideOffset))
    print(f"Angle between x={height}, y={width-clampedWidth} = {wall_angle} degrees")
    # X ist jetzt gut
    # Z ist jetzt gut
    # wtf ist mit Y los
    extrudedArc1.Placement.Base = FreeCAD.Vector(-((innerDiameter1)/2)-margin, 0, innerDiameter1/2 + margin)
    extrudedArc1.Placement.Rotation = App.Rotation(90, 90, wall_angle)
    extrudedArc2.Placement.Base = FreeCAD.Vector(-((innerDiameter2)/2)-margin, 0, extrusionDepth - innerDiameter2/2 - margin)
    extrudedArc2.Placement.Rotation = App.Rotation(90, 90, wall_angle)
    #pad = (extrudedBase.BoundBox.YMax - extrudedArc1.BoundBox.YMax)
    #pad2 = (margin)*math.tan(math.radians(wall_angle))
    pad = -((margin)*(sideOffset / (height + margin)))
    #pad -= pad2
    print(f"padding: {pad} ")
    extrudedArc1.Placement.move(App.Vector(0, -5, 0))
    extrudedArc2.Placement.move(App.Vector(0, -5, 0))
    combinedExtrusion = extrudedBase.fuse(extrudedArc1).fuse(extrudedArc2).removeSplitter()
    solidPart = Part.Solid(combinedExtrusion)
    
    # 1) Get bounding box of ref_obj
    bbox = extrudedBase.BoundBox
    # Define a 1 mm buffer above & below
    ymin = bbox.YMin
    ymax = bbox.YMax
    height = ymax - ymin
    # 2) Build a "clipping box" that is large in X & Y but only spans [zmin, zmax]
    #    For example, we'll pick a big 2000 x 2000 square. Adjust if your model is huge.
    clip_box = Part.makeBox(
        2000,                   # X dimension
        height,                   # Y dimension
        2000,                 # Z dimension
        App.Vector(-1000,ymin,-1000)  # Position so it encloses everything in X & Y
    )
    # 3) Boolean intersection to keep only the portion of the main_obj within [zmin, zmax]
    solidPart = solidPart.common(clip_box)

    # Add to document
    partFeature = document.addObject("Part::Feature", "Part")
    partFeature.ViewObject.Visibility = False
    partFeature.Shape = solidPart

    # Refinement and Filleting
    refineFeature = document.addObject("Part::Refine", "RefinedShape")
    refineFeature.Source = partFeature
    refineFeature.ViewObject.Visibility = False
    document.recompute()

    filletedPart = refineFeature.Shape.makeFillet(0.5, refineFeature.Shape.Edges)

    filletFeature = document.addObject("Part::Feature", "Part")
    filletFeature.Shape = filletedPart
    filletFeature.ViewObject.Visibility = False
    document.recompute()

    refinedFilletFeature = document.addObject("Part::Refine", "RefinedShape")
    refinedFilletFeature.Source = filletFeature
    document.recompute()

    # export step file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    export_path = os.path.join(script_dir, "out", f"{document_name}.step")
    refinedFilletFeature.Shape.exportStep(export_path)
    print(f"STEP file exported to {export_path}")
    # export screenshot
    save_screenshot(f"{document_name}")

    return document

if __name__ == "__main__":
    create_cpap_holder(
        document_name="hose_dryer",
        margin=3.0,
        height=40.0,
        width=9,
        clampedWidth=6.0,
        arc=207,
        innerDiameter1=22.0,
        innerDiameter2=18.0,
        extrusionDepth=60.0
    )
