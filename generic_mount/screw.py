import FreeCAD as App
import FreeCADGui as Gui
import Part
from enum import Enum, auto
from dataclasses import dataclass

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

class ScrewType(Enum):
    M4 = auto()
    M6 = auto()
    M8 = auto()

@dataclass
class ScrewDimensions:
    dk: float
    k: float
    d: float
    l: int

def getScrewDimensions(screwType = ScrewType.M6, length = 12):
    match screwType:
        case ScrewType.M4:
            k = 2.48
            return ScrewDimensions(dk=7.62, k=k, d=4, l=length-k)
        case ScrewType.M6:
            k = 3.72
            return ScrewDimensions(dk=12.16, k=k, d=6, l=length-k)
        case ScrewType.M8:
            k = 4.96
            return ScrewDimensions(dk=16.43, k=k, d=8, l=length-k)

def render(screwType = ScrewType.M6, screwLength = 12, tolerance = 0.5):
    # Create or use an existing document
    doc = App.ActiveDocument
    if not doc:
        doc = App.newDocument("CountersunkM6Screw")
    
    # ----------------------------------------------------
    # 1) Define Dimensions (in mm)
    # ----------------------------------------------------
    screwDimensions = getScrewDimensions(screwType=screwType, length=screwLength)
    
    # ----------------------------------------------------
    # 2) Define a Closed 2D Profile in the XZ Plane
    #    (X = radial direction, Z = vertical direction)
    #    For a proper revolution, the profile must be closed.
    # ----------------------------------------------------

    A = App.Vector(0, 0, 0) # kopfmitte
    B = App.Vector(screwDimensions.dk/2, 0, 0) # kopf aussen
    C = App.Vector(screwDimensions.dk/2, 0, tolerance) # gerade runter zur toleranz
    D = App.Vector(screwDimensions.d/2, 0, screwDimensions.k/2 + tolerance) # kopf innen, stueckerl direkt unterm kopf
    E = App.Vector(screwDimensions.d/2, 0, screwDimensions.k/2 + tolerance + screwDimensions.l ) # nach unten
    F = App.Vector(0, 0, screwDimensions.k/2 + tolerance + screwDimensions.l) # unten mitte
    
    # Create edges between the points
    edge_AB = Part.makeLine(A, B)
    edge_BC = Part.makeLine(B, C)
    edge_CD = Part.makeLine(C, D)
    edge_DE = Part.makeLine(D, E)
    edge_EF = Part.makeLine(E, F)
    edge_FA = Part.makeLine(F, A)  # closing edge
    
    # Combine edges into a wire (the profile must be closed)
    profile_wire = Part.Wire([edge_AB, edge_BC, edge_CD, edge_DE, edge_EF, edge_FA])
    
    # Create a face from the wire
    try:
        profile_face = Part.Face(profile_wire)
    except Exception as e:
        App.Console.PrintError("Failed to create face from wire: " + str(e) + "\n")
        return
    
    # ----------------------------------------------------
    # 3) Create the 3D Screw by Revolving the Profile
    # ----------------------------------------------------
    # We revolve the profile face around the Z-axis.
    # Using the 'revolve' method (available in many FreeCAD versions):
    axis_point = App.Vector(0,0,0)
    axis_dir   = App.Vector(0,0,1)
    angle = 360  # degrees
    
    # This will create a solid by revolving the closed profile.
    screw_solid = profile_face.revolve(axis_point, axis_dir, angle)
    screw_solid.rotate(App.Vector(0,0,0), App.Vector(1,0,0), 180)
    return screw_solid

    
if __name__ == "__main__":
    render()