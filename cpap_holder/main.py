import FreeCAD, Part, math

document = FreeCAD.newDocument("cpap_holder")

includeMaskHolder = False
height = 40.0
width = 41.5
topExtension = 20.0
clampedWidth = 38.0
sideOffset = (width - clampedWidth) / 2.0
extrusionDepth = 30.0
innerDiameter = 22.0
arcRadius = innerDiameter / 2.0
margin = 3.0

arcAngleOffset = (234 / 360 * 2 * math.pi) - math.pi

# Define vertices for the base profile
basePoints = [
    FreeCAD.Vector(sideOffset, 0, 0),                        # pt_innerBottomLeft
    FreeCAD.Vector(0, height, 0),                             # pt_innerTopLeft
    FreeCAD.Vector(width, height, 0),                         # pt_innerTopRight
    FreeCAD.Vector(width - sideOffset, 0, 0),                 # pt_innerBottomRight
    FreeCAD.Vector(width - sideOffset + margin, 0, 0),        # pt_extendedBottomRight
    FreeCAD.Vector(width + margin, height + margin, 0),       # pt_extendedTopRight
] + (
    [
    FreeCAD.Vector(width + margin, height + margin + topExtension, 0),  # pt_extendedTopRightPeak
    FreeCAD.Vector(width, height + margin + topExtension, 0),  # pt_extendedTopLeftPeak
    ] if includeMaskHolder else []
) + [
    FreeCAD.Vector(width, height + margin, 0),                # pt_transitionTopRight
    FreeCAD.Vector(-margin, height + margin, 0),              # pt_extendedTopLeft
    FreeCAD.Vector(-margin + sideOffset, 0, 0),               # pt_extendedBottomLeft
    FreeCAD.Vector(sideOffset, 0, 0)                          # Closing the loop back to pt_innerBottomLeft
]

baseEdges = []
for i in range(len(basePoints) - 1):
    edge = Part.LineSegment(basePoints[i], basePoints[i + 1]).toShape()
    baseEdges.append(edge)

baseWire = Part.Wire(baseEdges)

arcCenter = FreeCAD.Vector(width / 2, height + arcRadius + margin, 0)
innerArc = Part.ArcOfCircle(
    Part.Circle(arcCenter, FreeCAD.Vector(0, 0, 1), arcRadius),
    -math.pi - arcAngleOffset, arcAngleOffset
)
innerArcShape = innerArc.toShape()

outerArc = Part.ArcOfCircle(
    Part.Circle(arcCenter, FreeCAD.Vector(0, 0, 1), arcRadius + margin),
    -math.pi - arcAngleOffset, arcAngleOffset
)
outerArcShape = outerArc.toShape()

arcEdges = [
    innerArcShape,
    Part.LineSegment(innerArcShape.Vertexes[-1].Point, outerArcShape.Vertexes[-1].Point).toShape(),
    outerArcShape,
    Part.LineSegment(innerArcShape.Vertexes[0].Point, outerArcShape.Vertexes[0].Point).toShape(),
]

arcWire = Part.Wire(arcEdges)

baseFace = Part.Face(baseWire)
arcFace = Part.Face(arcWire)
combinedFace = baseFace.fuse(arcFace).removeSplitter()

extrudedPart = combinedFace.extrude(FreeCAD.Vector(0, 0, extrusionDepth))
solidPart = Part.Solid(extrudedPart)

partFeature = document.addObject("Part::Feature", "Part")
partFeature.ViewObject.Visibility = False
partFeature.Shape = solidPart

refineFeature = document.addObject("Part::Refine", "RefinedShape")
refineFeature.Source = partFeature
refineFeature.ViewObject.Visibility = False
document.recompute()

filletedPart = refineFeature.Shape.makeFillet(0.9, refineFeature.Shape.Edges)

filletFeature = document.addObject("Part::Feature", "Part")
filletFeature.Shape = filletedPart
filletFeature.ViewObject.Visibility = False
document.recompute()

refinedFilletFeature = document.addObject("Part::Refine", "RefinedShape")
refinedFilletFeature.Source = filletFeature
document.recompute()