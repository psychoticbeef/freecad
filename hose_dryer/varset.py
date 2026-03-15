import FreeCAD, FreeCADGui, Part, math, os

#-------------------------------
# VarSet Proxy: Watches its properties for changes
#-------------------------------
class VarSetProxy:
    def __init__(self, obj):
        obj.Proxy = self  # assign this proxy to the VarSet object

    def onChanged(self, obj, prop):
        """
        Called when a VarSet property is changed.
        Notify any dependent CPAPHolder objects to update.
        """
        doc = obj.Document
        for o in doc.Objects:
            # Look for FeaturePython objects with a linked VarSet
            if o.TypeId == "Part::FeaturePython" and "VarSet" in o.PropertiesList and o.VarSet == obj:
                o.touch()  # mark the object as modified for recompute
        doc.recompute()

#-------------------------------
# CPAPHolder Feature Proxy: Builds the geometry
#-------------------------------
class CPAPHolderFeature:
    def __init__(self, obj):
        obj.Proxy = self
        # Only add the VarSet property if it does not already exist.
        if "VarSet" not in obj.PropertiesList:
            obj.addProperty("App::PropertyLink", "VarSet", "Parameters", "Link to the VarSet object")

    def execute(self, obj):
        # Retrieve parameters from the linked VarSet.
        varset = obj.VarSet
        if varset is None:
            print("No VarSet linked!")
            return

        margin         = varset.margin
        height         = varset.height
        width          = varset.width
        clampedWidth   = varset.clampedWidth
        arc            = varset.arc
        innerDiameter1 = varset.innerDiameter1
        innerDiameter2 = varset.innerDiameter2
        extrusionDepth = varset.extrusionDepth

        # --- Build the base wire ---
        sideOffset = (width - clampedWidth) / 2.0
        basePoints = [
            FreeCAD.Vector(sideOffset, 0, 0),                         # innerBottomLeft
            FreeCAD.Vector(0, height, 0),                             # innerTopLeft
            FreeCAD.Vector(width, height, 0),                         # innerTopRight
            FreeCAD.Vector(width - sideOffset, 0, 0),                 # innerBottomRight
            FreeCAD.Vector(width - sideOffset + margin, 0, 0),        # extendedBottomRight
            FreeCAD.Vector(width + margin, height + margin, 0),       # extendedTopRight
            FreeCAD.Vector(width, height + margin, 0),                # transitionTopRight
            FreeCAD.Vector(-margin, height + margin, 0),              # extendedTopLeft
            FreeCAD.Vector(-margin + sideOffset, 0, 0),               # extendedBottomLeft
            FreeCAD.Vector(sideOffset, 0, 0)                          # close loop
        ]
        baseEdges = [Part.LineSegment(basePoints[i], basePoints[i+1]).toShape() 
                     for i in range(len(basePoints)-1)]
        baseWire = Part.Wire(baseEdges)

        # --- Get arc wires ---
        arcWire1 = get_arc_wire(innerDiameter1, arc, margin)
        arcWire2 = get_arc_wire(innerDiameter2, arc, margin)

        # --- Create faces and extrusions ---
        baseFace = Part.Face(baseWire)
        arc1Face = Part.Face(arcWire1)
        arc2Face = Part.Face(arcWire2)
        extrudedBase = baseFace.extrude(FreeCAD.Vector(0, 0, extrusionDepth))
        hypothenuse = math.hypot(height + margin, sideOffset)
        extrudedArc1 = arc1Face.extrude(FreeCAD.Vector(0, 0, hypothenuse + 10))
        extrudedArc2 = arc2Face.extrude(FreeCAD.Vector(0, 0, hypothenuse + 10))
        wall_angle = -90 + math.degrees(math.atan2(height + margin, sideOffset))
        print(f"Angle: {wall_angle} degrees")

        # Instead of modifying placements in place, compute new placements.
        # Compute the base positions and apply a fixed offset.
        offset = FreeCAD.Vector(0, -5, 0)
        placement1_base = FreeCAD.Vector(-innerDiameter1 / 2 - margin, 0, innerDiameter1 / 2 + margin) + offset
        placement2_base = FreeCAD.Vector(-innerDiameter2 / 2 - margin, 0, extrusionDepth - innerDiameter2 / 2 - margin) + offset
        rotation = App.Rotation(90, 90, wall_angle)
        extrudedArc1.Placement = FreeCAD.Placement(placement1_base, rotation)
        extrudedArc2.Placement = FreeCAD.Placement(placement2_base, rotation)

        combinedExtrusion = extrudedBase.fuse(extrudedArc1).fuse(extrudedArc2).removeSplitter()
        solidPart = Part.Solid(combinedExtrusion)
        
        # --- Clip the solid ---
        bbox = extrudedBase.BoundBox
        ymin = bbox.YMin
        ymax = bbox.YMax
        height_bbox = ymax - ymin
        clip_box = Part.makeBox(2000, height_bbox, 2000, App.Vector(-1000, ymin, -1000))
        solidPart = solidPart.common(clip_box)

        # --- Fillet (refinement) ---
        try:
            filleted = solidPart.makeFillet(0.5, solidPart.Edges)
        except Exception as e:
            print("Filleting failed:", e)
            filleted = solidPart

        # Set the final shape.
        obj.Shape = filleted

#-------------------------------
# Utility function: get_arc_wire()
#-------------------------------
def get_arc_wire(innerDiameter, arc, margin):
    arcRadius = innerDiameter / 2.0
    arcAngleOffset = math.radians(arc) - math.pi

    arcCenter = FreeCAD.Vector(0, 0, 0)
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
        Part.LineSegment(innerArc.Vertexes[0].Point, outerArc.Vertexes[0].Point).toShape()
    ]
    return Part.Wire(arcEdges)

#-------------------------------
# Creation function: Creates VarSet and CPAPHolder objects
#-------------------------------
def create_cpap_holder(document_name):
    doc = FreeCAD.newDocument(document_name)

    # Create the VarSet object with its proxy.
    varset = doc.addObject("App::FeaturePython", "VarSet")
    varset.addProperty("App::PropertyFloat", "margin", "Parameters", "Margin")
    varset.addProperty("App::PropertyFloat", "height", "Parameters", "Height")
    varset.addProperty("App::PropertyFloat", "width", "Parameters", "Width")
    varset.addProperty("App::PropertyFloat", "clampedWidth", "Parameters", "Clamped Width")
    varset.addProperty("App::PropertyFloat", "arc", "Parameters", "Arc angle (degrees)")
    varset.addProperty("App::PropertyFloat", "innerDiameter1", "Parameters", "Inner Diameter 1")
    varset.addProperty("App::PropertyFloat", "innerDiameter2", "Parameters", "Inner Diameter 2")
    varset.addProperty("App::PropertyFloat", "extrusionDepth", "Parameters", "Extrusion Depth")
    # Set default values:
    varset.margin = 3.0
    varset.height = 40.0
    varset.width = 9.0
    varset.clampedWidth = 6.0
    varset.arc = 207.0
    varset.innerDiameter1 = 22.0
    varset.innerDiameter2 = 18.0
    varset.extrusionDepth = 60.0
    VarSetProxy(varset)  # Attach proxy to handle property changes

    # Create the CPAPHolder feature.
    cpap_holder = doc.addObject("Part::FeaturePython", "CPAPHolder")
    CPAPHolderFeature(cpap_holder)
    cpap_holder.VarSet = varset  # Link the VarSet (the property now exists)
    cpap_holder.ViewObject.Proxy = 0  # Use default view

    doc.recompute()
    return doc

#-------------------------------
# Main
#-------------------------------
if __name__ == "__main__":
    doc = create_cpap_holder("hose_dryer")