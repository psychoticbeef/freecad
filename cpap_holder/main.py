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

def create_cpap_holder(
    document_name,
    includeMaskHolder,
    margin,
    height,
    width,
    arc,
    innerDiameter,
    clampedWidth,
    extrusionDepth,
    fillet_radius=0.9
):
    document = FreeCAD.newDocument(document_name)

    arcRadius = innerDiameter / 2.0
    topExtension = (arcRadius + margin) * (1 - math.cos(math.radians(arc) / 2))
    sideOffset = (width - clampedWidth) / 2.0
    arcAngleOffset = math.radians(arc) - math.pi

    basePoints = [
        FreeCAD.Vector(sideOffset, 0, 0),                         # pt_innerBottomLeft
        FreeCAD.Vector(0, height, 0),                             # pt_innerTopLeft
        FreeCAD.Vector(width, height, 0),                         # pt_innerTopRight
        FreeCAD.Vector(width - sideOffset, 0, 0),                 # pt_innerBottomRight
        FreeCAD.Vector(width - sideOffset + margin, 0, 0),        # pt_extendedBottomRight
        FreeCAD.Vector(width + margin, height + margin, 0),       # pt_extendedTopRight
    ] + (
        [
        FreeCAD.Vector(width + margin, height + margin + topExtension, 0),  # pt_extendedTopRightPeak
        FreeCAD.Vector(width, height + margin + topExtension, 0), # pt_extendedTopLeftPeak
        ] if includeMaskHolder else []
    ) + [
        FreeCAD.Vector(width, height + margin, 0),                # pt_transitionTopRight
        FreeCAD.Vector(-margin, height + margin, 0),              # pt_extendedTopLeft
        FreeCAD.Vector(-margin + sideOffset, 0, 0),               # pt_extendedBottomLeft
        FreeCAD.Vector(sideOffset, 0, 0)                          # Closing the loop back to pt_innerBottomLeft
    ]

    baseEdges = [Part.LineSegment(basePoints[i], basePoints[i + 1]).toShape() for i in range(len(basePoints) - 1)]
    baseWire = Part.Wire(baseEdges)

    # Define arc features
    arcCenter = FreeCAD.Vector(width / 2, height + arcRadius + margin, 0)
    innerArc = Part.ArcOfCircle(
        Part.Circle(arcCenter, FreeCAD.Vector(0, 0, 1), arcRadius),
        -math.pi - arcAngleOffset, arcAngleOffset
    ).toShape()

    outerArc = Part.ArcOfCircle(
        Part.Circle(arcCenter, FreeCAD.Vector(0, 0, 1), arcRadius + margin),
        -math.pi - arcAngleOffset, arcAngleOffset
    ).toShape()

    arcEdges = [
        innerArc,
        Part.LineSegment(innerArc.Vertexes[-1].Point, outerArc.Vertexes[-1].Point).toShape(),
        outerArc,
        Part.LineSegment(innerArc.Vertexes[0].Point, outerArc.Vertexes[0].Point).toShape(),
    ]
    arcWire = Part.Wire(arcEdges)

    # Create faces and extrusion
    baseFace = Part.Face(baseWire)
    arcFace = Part.Face(arcWire)
    combinedFace = baseFace.fuse(arcFace).removeSplitter()
    extrudedPart = combinedFace.extrude(FreeCAD.Vector(0, 0, extrusionDepth))
    solidPart = Part.Solid(extrudedPart)

    # Add to document
    partFeature = document.addObject("Part::Feature", "Part")
    partFeature.ViewObject.Visibility = False
    partFeature.Shape = solidPart

    # Refinement and Filleting
    refineFeature = document.addObject("Part::Refine", "RefinedShape")
    refineFeature.Source = partFeature
    refineFeature.ViewObject.Visibility = False
    document.recompute()

    filletedPart = refineFeature.Shape.makeFillet(fillet_radius, refineFeature.Shape.Edges)

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
        document_name="cpap_holder",
        includeMaskHolder=False,
        margin=3.0,
        height=40.0,
        width=41.5,
        arc=234,
        innerDiameter=22.0,
        clampedWidth=38.0,
        extrusionDepth=30.0
    )
    create_cpap_holder(
        document_name="cpap_holder_with_mask_holder",
        includeMaskHolder=True,
        margin=3.0,
        height=40.0,
        width=41.5,
        arc=207,
        innerDiameter=22.0,
        clampedWidth=38.0,
        extrusionDepth=30.0
    )
