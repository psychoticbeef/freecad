import FreeCADGui

doc = FreeCADGui.getDocument("cpap_holder")
view = doc.activeView()
orientation = view.getCameraOrientation()
print(orientation.toEuler())