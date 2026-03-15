import FreeCAD, Part

tol = 1e-3  # tolerance for “almost equal” comparisons

# Create a new document
doc = FreeCAD.newDocument("SymPart")

# === PARAMETERS ===
h = 40.0           # vertical distance (up and down)
w = 41.5           # horizontal distance (length of the horizontal segment)
m_h = 20
w_clamped = 38
w_diff = (w - w_clamped) / 2
depth = 30
inner_diam = 22.0  # inner diameter for the half-circle
arc_radius = inner_diam / 2.0  # 9.0 mm
t = 3.0

# === BUILD THE BASE SHAPE (Lines: up, right, down) ===
# Define key points:
A = FreeCAD.Vector(w_diff, 0, 0)      # bottom left
B = FreeCAD.Vector(0, h, 0)      # top left
C = FreeCAD.Vector(w, h, 0)      # top right
D = FreeCAD.Vector(w - w_diff, 0, 0)      # bottom right
E = FreeCAD.Vector(w - w_diff + t, 0, 0)
F = FreeCAD.Vector(w + t, h + t, 0)
G = FreeCAD.Vector(w + t, h + t + m_h, 0)
H = FreeCAD.Vector(w, h + t + m_h, 0)
I = FreeCAD.Vector(w, h + t, 0)
J = FreeCAD.Vector(-t, h + t, 0)
K = FreeCAD.Vector(-t + w_diff, 0, 0)

# Build a wire from the lines:
wire_base = Part.Wire([
    Part.LineSegment(A, B).toShape(),
    Part.LineSegment(B, C).toShape(),
    Part.LineSegment(C, D).toShape(),
    Part.LineSegment(D, E).toShape(),
    Part.LineSegment(E, F).toShape(),
    Part.LineSegment(F, G).toShape(),
    Part.LineSegment(G, H).toShape(),
    Part.LineSegment(H, I).toShape(),
    Part.LineSegment(I, J).toShape(),
    Part.LineSegment(J, K).toShape(),
    Part.LineSegment(K, A).toShape(),
])

# === BUILD THE HALF-CIRCLE ARC ===
# Our goal is to create a circular arc with a “diameter” of 18 mm
# that touches the horizontal segment (BC) only at its midpoint.
# In our interpretation the arc is not the full half‐disc (i.e. including the chord)
# but only the curved part. To do that we position the circle so that its lowest point 
# (which is unique) is exactly at the midpoint of the horizontal segment.
#
# For a circle, the lowest point is located a distance of the radius below the center.
# Thus we choose the center to be at (w/2, h + arc_radius). Then the lowest point will be:
#   (w/2, h + arc_radius - arc_radius) = (w/2, h)
#
# We then build an arc from –π to 0 (in radians). That produces an arc whose midpoint 
# (at –π/2) is the tangency point.

extra_arc = 234/360*2*3.14159-3.14159

center = FreeCAD.Vector(w/2, h + arc_radius + t, 0)  # center of the circle
# Create the arc from -pi to 0 (clockwise); the midpoint (at -pi/2) is (w/2, h)
arc = Part.ArcOfCircle(
    Part.Circle(center, FreeCAD.Vector(0, 0, 1), arc_radius),
    -3.14159 - extra_arc, extra_arc
#    -3.14159, 0
)
arc_shape = arc.toShape()

# Create the arc from -pi to 0 (clockwise); the midpoint (at -pi/2) is (w/2, h)
arc_o = Part.ArcOfCircle(
    Part.Circle(center, FreeCAD.Vector(0, 0, 1), arc_radius + t),
    -3.14159 - extra_arc, extra_arc
)
arc_shape_o = arc_o.toShape()

face1 = Part.Face(wire_base)
wire2 = Part.Wire([
    arc_shape,
    Part.LineSegment(arc_shape.Vertexes[-1].Point, arc_shape_o.Vertexes[-1].Point).toShape(),
    arc_shape_o,
    Part.LineSegment(arc_shape.Vertexes[0].Point, arc_shape_o.Vertexes[0].Point).toShape(),
])
face2 = Part.Face(wire2)

face = face1.fuse(face2)
face = face.removeSplitter()

part = face.extrude(App.Vector(0, 0, depth))
part = Part.Solid(part)

part_obj = doc.addObject("Part::Feature", "Part")
part_obj.ViewObject.Visibility = False
part_obj.Shape = part

refine_obj = doc.addObject("Part::Refine", "RefinedShape")
refine_obj.Source = part_obj
refine_obj.ViewObject.Visibility = False
doc.recompute()


#internal_orientated_edges = []
#ref_part = refine_obj.Shape.copy()
#for edge in ref_part.Edges:
#    if is_edge_outer(part.BoundBox, edge, tol) or not (is_horizontal(edge, tol) and is_vertical(edge, tol)):
#        internal_orientated_edges.append(edge)
#print("Found {} internal horizontal or vertical edges.".format(len(internal_orientated_edges)))#part = part.makeFillet(2, part_edges)
new_part = refine_obj.Shape.makeFillet(0.9, refine_obj.Shape.Edges)

lol_obj = doc.addObject("Part::Feature", "Part")
lol_obj.Shape = new_part
lol_obj.ViewObject.Visibility = False
doc.recompute()

lolrefine_obj = doc.addObject("Part::Refine", "RefinedShape")
lolrefine_obj.Source = lol_obj
doc.recompute()


#Part.show(part)
doc.recompute()

print("Base geometry created: a U‐shaped wire with a tangential half‐circle arc.")
