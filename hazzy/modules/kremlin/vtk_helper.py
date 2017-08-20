import math

from vtk.vtkCommonComputationalGeometryPython import vtkParametricSuperToroid
from vtk.vtkCommonCorePython import vtkPoints, vtkUnsignedCharArray, VTK_MAJOR_VERSION
from vtk.vtkCommonDataModelPython import vtkCellArray, vtkLine, vtkPolyData, vtkTriangle, vtkVertex
from vtk.vtkCommonTransformsPython import vtkTransform
from vtk.vtkFiltersCorePython import vtkTubeFilter
from vtk.vtkFiltersGeneralPython import vtkTransformPolyDataFilter, vtkAxes
from vtk.vtkFiltersSourcesPython import vtkConeSource, vtkSphereSource, vtkCubeSource, vtkLineSource, vtkCylinderSource, \
    vtkPointSource, vtkArrowSource, vtkParametricFunctionSource, vtkPlaneSource
from vtk.vtkRenderingCorePython import vtkActor, vtkFollower, vtkPolyDataMapper, vtkTextActor

# color definitions
from vtk.vtkRenderingFreeTypePython import vtkVectorText

white = (1, 1, 1)
black = (0, 0, 0)
grey = (float(127) / 255, float(127) / 255, float(127) / 255)

red = (1, 0, 0)
pink = (float(255) / 255, float(192) / 255, float(203) / 255)
orange = (float(255) / 255, float(165) / 255, float(0) / 255)
yellow = (1, 1, 0)
purple = (float(255) / 255, float(0) / 255, float(176) / 255)

green = (0, 1, 0)
lgreen = (float(150) / 255, float(255) / 255, float(150) / 255)
dgreen = (float(21) / 255, float(119) / 255, float(41) / 255)
grass = (float(182) / 255, float(248) / 255, float(71) / 255)

blue = (0, 0, 1)
lblue = (float(125) / 255, float(191) / 255, float(255) / 255)
blue2 = (float(0) / 255, float(188) / 255, float(255) / 255)
cyan = (0, 1, 1)
mag2 = (float(123) / 255, float(35) / 255, float(251) / 255)
magenta = (float(153) / 255, float(42) / 255, float(165) / 255)


class CamvtkActor(vtkActor):
    """ base class for actors"""

    def __init__(self):
        """ do nothing"""
        pass

    def Delete(self):
        self.Delete()

    def SetColor(self, color):
        """ set color of actor"""
        self.GetProperty().SetColor(color)

    def SetOpacity(self, op=0.5):
        """ set opacity of actor, 0 is see-thru (invisible)"""
        self.GetProperty().SetOpacity(op)

    def SetWireframe(self):
        """ set surface to wireframe"""
        self.GetProperty().SetRepresentationToWireframe()

    def SetSurface(self):
        """ set surface rendering on"""
        self.GetProperty().SetRepresentationToSurface()

    def SetPoints(self):
        """ render only points"""
        self.GetProperty().SetRepresentationToPoints()

    def SetFlat(self):
        """ set flat shading"""
        self.GetProperty().SetInterpolationToFlat()

    def SetGouraud(self):
        """ set gouraud shading"""
        self.GetProperty().SetInterpolationToGouraud()

    def SetPhong(self):
        """ set phong shading"""
        self.GetProperty().SetInterpolationToPhong()

        # possible TODOs
        # specular
        # diffuse
        # ambient


class FollowerText(vtkFollower):
    """ 3D text """

    def __init__(self, text="test", color=cyan, center=(0, 0, 0), scale=1):
        self.textSource = vtkVectorText()
        self.textSource.SetText(text)
        self.scale = scale

        self.transform = vtkTransform()

        self.transform.Translate(center[0], center[1], center[2])
        self.transform.Scale(self.scale, self.scale, self.scale)
        self.transformFilter = vtkTransformPolyDataFilter()
        self.transformFilter.SetTransform(self.transform)
        self.transformFilter.SetInputConnection(self.textSource.GetOutputPort())
        self.transformFilter.Update()

        self.mapper = vtkPolyDataMapper()
        self.mapper.SetInputConnection(self.transformFilter.GetOutputPort())
        self.SetMapper(self.mapper)
        self.SetColor(color)

    def SetScale(self, scale):
        self.scale = scale
        self.transform.Scale(self.scale, self.scale, self.scale)
        self.transformFilter.Update()

    def SetText(self, text):
        self.textSource.SetText(text)

    def SetColor(self, color):
        """ set color of actor"""
        self.GetProperty().SetColor(color)


class Cone(CamvtkActor):
    """ a cone"""

    def __init__(self, center=(-2, 0, 0), radius=1, angle=45, height=1.5, color=(1, 1, 0), resolution=60):
        CamvtkActor.__init__(self)

        """ cone"""
        self.src = vtkConeSource()

        self.src.SetResolution(resolution)
        self.src.SetRadius(radius)
        self.src.SetHeight(height)

        transform = vtkTransform()

        transform.Translate(center[0], center[1], center[2] - self.src.GetHeight() / 2)
        transform.RotateY(-90)

        transform_filter = vtkTransformPolyDataFilter()

        transform_filter.SetTransform(transform)
        transform_filter.SetInputConnection(self.src.GetOutputPort())
        transform_filter.Update()

        self.mapper = vtkPolyDataMapper()

        self.mapper.SetInputConnection(transform_filter.GetOutputPort())

        self.SetMapper(self.mapper)
        self.SetColor(color)


class Sphere(CamvtkActor):
    """ a sphere"""

    def __init__(self, radius=1, resolution=20, center=(0, 2, 0), color=(1, 0, 0)):
        CamvtkActor.__init__(self)

        """ create sphere"""
        self.src = vtkSphereSource()
        self.src.SetRadius(radius)
        self.src.SetCenter(center)
        self.src.SetThetaResolution(resolution)
        self.src.SetPhiResolution(resolution)

        self.mapper = vtkPolyDataMapper()
        self.mapper.SetInput(self.src.GetOutput())
        self.SetMapper(self.mapper)
        self.SetColor(color)


class Cube(CamvtkActor):
    """ a cube"""

    def __init__(self, center=(2, 2, 0), length=1, color=(0, 1, 0)):
        CamvtkActor.__init__(self)

        """ create cube"""
        self.src = vtkCubeSource()
        self.src.SetCenter(center)
        self.src.SetXLength(length)
        self.src.SetYLength(length)
        self.src.SetZLength(length)

        self.mapper = vtkPolyDataMapper()
        self.mapper.SetInput(self.src.GetOutput())
        self.SetMapper(self.mapper)
        self.SetColor(color)


class Cylinder(CamvtkActor):
    """ cylinder """

    def __init__(self, center=(0, -2, 0), radius=0.5, height=2, color=(0, 1, 1), rotXYZ=(0, 0, 0), resolution=50):
        CamvtkActor.__init__(self)

        """ cylinder """
        self.src = vtkCylinderSource()
        self.src.SetCenter(0, 0, 0)
        self.src.SetHeight(height)
        self.src.SetRadius(radius)
        self.src.SetResolution(resolution)
        # SetResolution
        # SetCapping(int)
        # CappingOn() CappingOff()

        # this transform rotates the cylinder so it is vertical
        # and then translates the lower tip to the center point
        transform = vtkTransform()
        transform.Translate(center[0], center[1], center[2] + height / 2)
        transform.RotateX(rotXYZ[0])
        transformFilter = vtkTransformPolyDataFilter()
        transformFilter.SetTransform(transform)
        transformFilter.SetInputConnection(self.src.GetOutputPort())
        transformFilter.Update()

        self.mapper = vtkPolyDataMapper()
        # self.mapper.SetInput(self.src.GetOutput())
        self.mapper.SetInput(transformFilter.GetOutput())
        self.SetMapper(self.mapper)
        self.SetColor(color)


class Line(CamvtkActor):
    """ line """

    def __init__(self, p1=(0, 0, 0), p2=(1, 1, 1), color=(0, 1, 1)):
        CamvtkActor.__init__(self)

        """ line """
        self.src = vtkLineSource()

        self.src.SetPoint1(p1)
        self.src.SetPoint2(p2)

        self.mapper = vtkPolyDataMapper()

        self.mapper.SetInputConnection(self.src.GetOutputPort())

        self.SetMapper(self.mapper)

        self.SetColor(color)


class PolyLine(CamvtkActor):
    def __init__(self, pointList=[], color=(1, 1, 1)):
        CamvtkActor.__init__(self)

        self.src = []
        points = vtkPoints()
        polyline = vtkCellArray()

        idx = 0
        first = 1
        last_idx = 0
        segs = []
        for p in pointList:
            points.InsertNextPoint(p.x, p.y, 0)
            # print "p = ",p
            if first == 0:
                seg = [last_idx, idx]
                segs.append(seg)
            first = 0
            last_idx = idx
            idx = idx + 1

        for seg in segs:
            line = vtkLine()
            line.GetPointIds().SetId(0, seg[0])
            line.GetPointIds().SetId(1, seg[1])
            # print " indexes: ", seg[0]," to ",seg[1]
            polyline.InsertNextCell(line)

        polydata = vtkPolyData()
        polydata.SetPoints(points)
        polydata.SetLines(polyline)
        polydata.Modified()
        polydata.Update()
        self.src = polydata

        self.mapper = vtkPolyDataMapper()
        self.mapper.SetInput(self.src)
        self.SetMapper(self.mapper)
        self.SetColor(color)
        polydata.Modified()
        polydata.Update()

        # SetScaleFactor(double)
        # GetOrigin


class Circle(CamvtkActor):
    """ circle"""

    def __init__(self, center=(0, 0, 0), radius=1, color=(0, 1, 1), resolution=50):
        CamvtkActor.__init__(self)

        """ create circle """
        lines = vtkCellArray()
        id = 0
        points = vtkPoints()
        for n in xrange(0, resolution):
            line = vtkLine()
            angle1 = (float(n) / (float(resolution))) * 2 * math.pi
            angle2 = (float(n + 1) / (float(resolution))) * 2 * math.pi
            p1 = (center[0] + radius * math.cos(angle1), center[1] + radius * math.sin(angle1), center[2])
            p2 = (center[0] + radius * math.cos(angle2), center[1] + radius * math.sin(angle2), center[2])
            points.InsertNextPoint(p1)
            points.InsertNextPoint(p2)
            line.GetPointIds().SetId(0, id)
            id = id + 1
            line.GetPointIds().SetId(1, id)
            id = id + 1
            lines.InsertNextCell(line)

        self.pdata = vtkPolyData()
        self.pdata.SetPoints(points)
        self.pdata.SetLines(lines)

        self.mapper = vtkPolyDataMapper()
        self.mapper.SetInput(self.pdata)
        self.SetMapper(self.mapper)
        self.SetColor(color)


class Tube(CamvtkActor):
    """ a Tube is a line with thickness"""

    def __init__(self, p1=(0, 0, 0), p2=(1, 1, 1), radius=0.2, color=(0, 1, 1)):
        CamvtkActor.__init__(self)

        """ tube"""
        points = vtkPoints()
        points.InsertNextPoint(p1)
        points.InsertNextPoint(p2)
        line = vtkLine()
        line.GetPointIds().SetId(0, 0)
        line.GetPointIds().SetId(1, 1)
        lines = vtkCellArray()
        lines.InsertNextCell(line)
        self.pdata = vtkPolyData()
        self.pdata.SetPoints(points)
        self.pdata.SetLines(lines)

        tubefilter = vtkTubeFilter()
        tubefilter.SetInput(self.pdata)
        tubefilter.SetRadius(radius)
        tubefilter.SetNumberOfSides(50)
        tubefilter.Update()

        self.mapper = vtkPolyDataMapper()
        self.mapper.SetInput(tubefilter.GetOutput())
        self.SetMapper(self.mapper)
        self.SetColor(color)


class Point(CamvtkActor):
    """ point"""

    def __init__(self, center=(0, 0, 0), color=(1, 2, 3)):
        CamvtkActor.__init__(self)

        """ create point """
        self.src = vtkPointSource()
        self.src.SetCenter(center)
        self.src.SetRadius(0)
        self.src.SetNumberOfPoints(1)

        self.mapper = vtkPolyDataMapper()
        self.mapper.SetInput(self.src.GetOutput())
        self.SetMapper(self.mapper)
        self.SetColor(color)


class Arrow(CamvtkActor):
    """ arrow """

    def __init__(self, center=(0, 0, 0), color=(0, 0, 1), rotXYZ=(0, 0, 0)):
        CamvtkActor.__init__(self)


        """ arrow """
        self.src = vtkArrowSource()
        # self.src.SetCenter(center)

        transform = vtkTransform()
        transform.Translate(center[0], center[1], center[2])
        transform.RotateX(rotXYZ[0])
        transform.RotateY(rotXYZ[1])
        transform.RotateZ(rotXYZ[2])
        transformFilter = vtkTransformPolyDataFilter()
        transformFilter.SetTransform(transform)
        transformFilter.SetInputConnection(self.src.GetOutputPort())
        transformFilter.Update()

        self.mapper = vtkPolyDataMapper()
        self.mapper.SetInput(transformFilter.GetOutput())
        self.SetMapper(self.mapper)
        self.SetColor(color)


class Text(vtkTextActor):
    """ 2D text, HUD-type"""

    def __init__(self, text="text", size=18, color=(1, 1, 1), pos=(100, 100)):

        """create text"""
        self.SetText(text)
        self.properties = self.GetTextProperty()
        self.properties.SetFontFamilyToArial()
        self.properties.SetFontSize(size)

        self.SetColor(color)
        self.SetPos(pos)

    def SetColor(self, color):
        """ set color of text """
        self.properties.SetColor(color)

    def SetPos(self, pos):
        """ set position on screen """
        self.SetDisplayPosition(pos[0], pos[1])

    def SetText(self, text):
        """ set text to be displayed """
        self.SetInput(text)

    def SetSize(self, size):
        self.properties.SetFontSize(size)


class Text3D(vtkFollower):
    """ 3D text rendered in the scene"""

    def __init__(self, color=(1, 1, 1), center=(0, 0, 0), text="hello", scale=1, camera=[]):

        """ create text """
        self.src = vtkVectorText()
        self.SetText(text)
        # self.SetCamera(camera)
        transform = vtkTransform()

        transform.Translate(center[0], center[1], center[2])
        transform.Scale(scale, scale, scale)
        # transform.RotateY(90)
        # transform2 = vtk.vtkTransform()
        # transform.Concatenate(transform2)
        # transformFilter=vtk.vtkTransformPolyDataFilter()
        # transformFilter.SetTransform(transform)
        # transformFilter.SetInputConnection(self.src.GetOutputPort())
        # transformFilter.Update()

        # follower = vtk.vtkFollower()
        # follower.SetMapper

        self.SetUserTransform(transform)
        self.mapper = vtkPolyDataMapper()
        self.mapper.SetInputConnection(self.src.GetOutputPort())
        self.SetMapper(self.mapper)
        self.SetColor(color)

    def SetText(self, text):
        """ set text to be displayed"""
        self.src.SetText(text)

    def SetColor(self, color):
        """ set color of text"""
        self.GetProperty().SetColor(color)


class Axes(vtkActor):
    """ axes (x,y,z) """

    def __init__(self, center=(0, 0, 0), color=(0, 0, 1)):
        """ create axes """
        self.src = vtkAxes()
        # self.src.SetCenter(center)

        self.mapper = vtkPolyDataMapper()
        self.mapper.SetInput(self.src.GetOutput())
        self.SetMapper(self.mapper)

        self.SetColor(color)
        self.SetOrigin(center)
        # SetScaleFactor(double)
        # GetOrigin

    def SetColor(self, color):
        self.GetProperty().SetColor(color)

    def SetOrigin(self, center=(0, 0, 0)):
        self.src.SetOrigin(center[0], center[1], center[2])


class Toroid(CamvtkActor):
    def __init__(self, r1=1, r2=0.25, center=(0, 0, 0), rotXYZ=(0, 0, 0), color=(1, 0, 0)):
        CamvtkActor.__init__(self)

        self.parfun = vtkParametricSuperToroid()
        self.parfun.SetRingRadius(r1)
        self.parfun.SetCrossSectionRadius(r2)
        self.parfun.SetN1(1)
        self.parfun.SetN2(1)

        self.src = vtkParametricFunctionSource()
        self.src.SetParametricFunction(self.parfun)

        transform = vtkTransform()
        transform.Translate(center[0], center[1], center[2])
        transform.RotateX(rotXYZ[0])
        transform.RotateY(rotXYZ[1])
        transform.RotateZ(rotXYZ[2])
        transformFilter = vtkTransformPolyDataFilter()
        transformFilter.SetTransform(transform)
        transformFilter.SetInputConnection(self.src.GetOutputPort())
        transformFilter.Update()

        self.mapper = vtkPolyDataMapper()
        self.mapper.SetInput(transformFilter.GetOutput())
        self.SetMapper(self.mapper)
        self.SetColor(color)


"""
class TrilistReader(vtk.vtkPolyDataAlgorithm):
    def __init__(self, triangleList):
        vtk.vtkPolyDataAlgorithm.__init__(self)
        self.FileName = None
        self.SetNumberOfInputPorts(0)
        self.SetNumberOfOutputPorts(1)

    def FillOutputPortInfornmation(self, port, info):
        if port == 0:
            info.Set( vtk.vtkDataObject.DATA_TYPE_NAME(), "vtkPolyData")
            return 1
        return 0

    def RequestData(self, request, inputVector, outputVector):
        outInfo = outputVector.GetInformationObject(0)
        output = outInfo.Get( vtk.vtkDataObject.DATA_OBJECT() )
        polydata = vtk.vtkPolyData()
        points = vtk.vtkPoints()
        points.InsertNextPoint(0,0,0)
        polydata.SetPoints(points)

        output.ShallowCopy(polydata)
        return 1
"""


class STLSurf(CamvtkActor):
    def __init__(self, filename=None, triangleList=[], color=(1, 1, 1)):
        CamvtkActor.__init__(self)

        self.src = []

        points = vtkPoints()
        triangles = vtkCellArray()
        n = 0
        for t in triangleList:
            triangle = vtkTriangle()
            for p in t:
                points.InsertNextPoint(p.x, p.y, p.z)
            triangle.GetPointIds().SetId(0, n)
            n = n + 1
            triangle.GetPointIds().SetId(1, n)
            n = n + 1
            triangle.GetPointIds().SetId(2, n)
            n = n + 1
            triangles.InsertNextCell(triangle)
        polydata = vtkPolyData()
        polydata.SetPoints(points)
        polydata.SetPolys(triangles)
        polydata.Modified()
        polydata.Update()
        self.src = polydata
        self.mapper = vtkPolyDataMapper()
        self.mapper.SetInput(self.src)
        self.SetMapper(self.mapper)

        self.SetColor(color)
        # SetScaleFactor(double)
        # GetOrigin


class PointCloud(CamvtkActor):
    def __init__(self, pointlist=[]):
        CamvtkActor.__init__(self)

        points = vtkPoints()
        cellArr = vtkCellArray()
        # Colors = vtk.vtkUnsignedCharArray()
        # Colors.SetNumberOfComponents(3)
        # Colors.SetName("Colors")
        self.zheight = 0

        n = 0
        for p in pointlist:
            vert = vtkVertex()
            points.InsertNextPoint(p.x, p.y, self.zheight)
            vert.GetPointIds().SetId(0, n)
            cellArr.InsertNextCell(vert)
            # col = clColor(p.cc())
            # Colors.InsertNextTuple3( float(255)*col[0], float(255)*col[1], float(255)*col[2] )
            n = n + 1

        polydata = vtkPolyData()
        polydata.SetPoints(points)
        polydata.SetVerts(cellArr)
        # polydata.GetPointData().SetScalars(Colors)

        polydata.Modified()
        polydata.Update()
        self.src = polydata
        self.mapper = vtkPolyDataMapper()
        self.mapper.SetInput(self.src)
        self.SetMapper(self.mapper)
        # self.SetColor(color)


class CLPointCloud(CamvtkActor):
    def __init__(self, pointlist=[]):
        CamvtkActor.__init__(self)

        points = vtkPoints()
        cellArr = vtkCellArray()
        Colors = vtkUnsignedCharArray()
        Colors.SetNumberOfComponents(3)
        Colors.SetName("Colors")

        n = 0
        for p in pointlist:
            vert = vtkVertex()
            points.InsertNextPoint(p.x, p.y, p.z)
            vert.GetPointIds().SetId(0, n)
            cellArr.InsertNextCell(vert)
            col = clColor(p.cc())
            Colors.InsertNextTuple3(float(255) * col[0], float(255) * col[1], float(255) * col[2])
            n = n + 1

        polydata = vtkPolyData()
        polydata.SetPoints(points)
        polydata.SetVerts(cellArr)
        polydata.GetPointData().SetScalars(Colors)

        polydata.Modified()
        polydata.Update()
        self.src = polydata
        self.mapper = vtkPolyDataMapper()
        self.mapper.SetInput(self.src)
        self.SetMapper(self.mapper)
        # self.SetColor(color)


class Plane(CamvtkActor):
    def __init__(self, center=(0, 0, 0), color=(0, 0, 1)):
        CamvtkActor.__init__(self)

        self.src = vtkPlaneSource()
        # self.src.SetCenter(center)
        self.mapper = vtkPolyDataMapper()
        self.mapper.SetInput(self.src.GetOutput())
        self.SetMapper(self.mapper)

        self.SetColor(color)
        self.SetOrigin(center)
        # SetScaleFactor(double)
        # GetOrigin
