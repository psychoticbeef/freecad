import FreeCAD as App
import FreeCADGui as Gui
import Part
from enum import Enum, auto
from dataclasses import dataclass

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
    k_tolerance: float

def getScrewDimensions(screwType=ScrewType.M6, length=12, head_tolerance=2):
    match screwType:
        case ScrewType.M4:
            k = 2.48
            return ScrewDimensions(dk=7.62, k=k, d=4, l=length-k, k_tolerance=k+head_tolerance)
        case ScrewType.M6:
            k = 3.72
            return ScrewDimensions(dk=12.16, k=k, d=6, l=length-k, k_tolerance=k+head_tolerance)
        case ScrewType.M8:
            k = 4.96
            return ScrewDimensions(dk=16.43, k=k, d=8, l=length-k, k_tolerance=k+head_tolerance)

def render(screwType = ScrewType.M6, screwLength = 12, tolerance = 0.5, head_tolerance=2):
    # Create or use an existing document
    doc = App.ActiveDocument
    if not doc:
        doc = App.newDocument("CountersunkMScrew")
    
    screwDimensions = getScrewDimensions(screwType=screwType, length=screwLength)

    # see: https://www.schraubenking-shop.de/M6-x-12mm-Senkschrauben-ISO10642-Stahl-verzinkt-FKL-88-P000687
    A = App.Vector(0, 0, 0) # kopfmitte
    B = App.Vector(screwDimensions.dk/2 + tolerance, 0, 0) # kopf aussen
    C = App.Vector(screwDimensions.dk/2 + tolerance, 0, head_tolerance) # gerade runter zur kopf toleranz [kopf ragt gerade heraus]
    D = App.Vector(screwDimensions.d/2 + tolerance, 0, screwDimensions.k/2 + head_tolerance) # kopf innen, stueckerl direkt unterm kopf
    E = App.Vector(screwDimensions.d/2 + tolerance, 0, screwDimensions.k/2 + head_tolerance + screwDimensions.l ) # nach unten
    F = App.Vector(0, 0, screwDimensions.k/2 + head_tolerance + screwDimensions.l) # unten mitte
    
    # Create edges between the points
    edge_AB = Part.makeLine(A, B)
    edge_BC = Part.makeLine(B, C)
    edge_CD = Part.makeLine(C, D)
    edge_DE = Part.makeLine(D, E)
    edge_EF = Part.makeLine(E, F)
    edge_FA = Part.makeLine(F, A)  # closing edge
    
    # Combine edges into a wire (the profile must be closed)
    profile_wire = Part.Wire([edge_AB, edge_BC, edge_CD, edge_DE, edge_EF, edge_FA])
    profile_face = Part.Face(profile_wire)
    # We revolve the profile face around the Z-axis.
    axis_point = App.Vector(0,0,0)
    axis_dir   = App.Vector(0,0,1)
    screw_solid = profile_face.revolve(axis_point, axis_dir, 360)
    screw_solid.rotate(App.Vector(0,0,0), App.Vector(1,0,0), 180) # it's upside-down in coordinate space, rotate around x
    return screw_solid

    
if __name__ == "__main__":
    render()