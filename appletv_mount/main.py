import FreeCAD as App
import FreeCADGui as Gui
import Part
import os
import sys
sys.path.append("/Users/da/code/freecad/appletv_mount/")
import appletv
import mount
import holes
import screw

if __name__ == "__main__":
    tolerance = 0.25
    appletv.render(tolerance = tolerance)
    m6_senkkopf_kopfhoehe = 3.72
    anti_scratch = 1.0
    mount.render(thickness = m6_senkkopf_kopfhoehe + anti_scratch)
    holes.render(5)
    screw.render()