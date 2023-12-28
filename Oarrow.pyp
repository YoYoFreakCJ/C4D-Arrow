"""
Copyright: Software Schmid
Author: Daniel Schmid

Description:
    - Creates an arrow.

"""

import c4d
import os

from c4d import GeListNode

class Oarrow(c4d.plugins.ObjectData):
    def __init__(self, *args):
        super(Oarrow, self).__init__(*args)
        self.SetOptimizeCache(True)
    
    def Init(self, op, isCloneInit):
        """Called when Cinema 4D Initialize the ObjectData (used to define, default values).

        Args:
            op: (c4d.GeListNode): The instance of the ObjectData.

        Returns:
            bool: True on success, otherwise False.
        """

        self.InitAttr(op, float, c4d.OARROW_LENGTH)
        self.InitAttr(op, int, c4d.OARROW_ROTATION_SEGMENTS)
        self.InitAttr(op, float, c4d.OARROW_BASE_RADIUS)
        self.InitAttr(op, float, c4d.OARROW_TIP_RADIUS)
        self.InitAttr(op, float, c4d.OARROW_TIP_LENGTH)
        self.InitAttr(op, bool, c4d.OARROW_BEVEL_ENABLE)
        self.InitAttr(op, float, c4d.OARROW_BEVEL_RATIO)
        self.InitAttr(op, int, c4d.OARROW_BEVEL_SUBDIVISIONS)
        self.InitAttr(op, int, c4d.PRIM_AXIS)

        op[c4d.OARROW_LENGTH] = 100.0
        op[c4d.OARROW_ROTATION_SEGMENTS] = 12
        op[c4d.OARROW_BASE_RADIUS] = 10.0
        op[c4d.OARROW_TIP_RADIUS] = 20.0
        op[c4d.OARROW_TIP_LENGTH] = 30.0
        op[c4d.OARROW_BEVEL_ENABLE] = True
        op[c4d.OARROW_BEVEL_RATIO] = 0.1
        op[c4d.OARROW_BEVEL_SUBDIVISIONS] = 1
        op[c4d.PRIM_AXIS] = c4d.PRIM_AXIS_YP

        return True

    def GetVirtualObjects(self, op, hierarchyhelp):
        # Prepare base values.
        length = op[c4d.OARROW_LENGTH]
        rotation_segments = op[c4d.OARROW_ROTATION_SEGMENTS]
        base_radius = op[c4d.OARROW_BASE_RADIUS]
        tip_radius = op[c4d.OARROW_TIP_RADIUS]
        tip_length = op[c4d.OARROW_TIP_LENGTH]
        bevel = op[c4d.OARROW_BEVEL_ENABLE]
        bevel_ratio = op[c4d.OARROW_BEVEL_RATIO]
        bevel_subdivisions = op[c4d.OARROW_BEVEL_SUBDIVISIONS]

        bevel_offset = tip_radius * bevel_ratio

        base_length = length - tip_length

        points = []
        polys = []

        base_polys = []
        base_to_tip_polys = []
        tip_polys = []

        # First point: Center point of base.
        points.append(c4d.Vector(0))

        # Second point: Arrow target.
        points.append(c4d.Vector(0, 0, length))

        onehundredeighty_deg = c4d.utils.DegToRad(180)

        first_rotation_segment_point_index = 2
        points_per_rotation_segment = 3

        total_rotation_segments_points = rotation_segments * points_per_rotation_segment

        for rotation_segment in range(rotation_segments):
            is_last_segment = rotation_segment == rotation_segments - 1

            angle = (rotation_segment / float(rotation_segments)) * 2.0 * onehundredeighty_deg

            x,y = c4d.utils.SinCos(angle)

            # Append base points.
            points.append(c4d.Vector(x * base_radius, y * base_radius, 0))
            points.append(c4d.Vector(x * base_radius, y * base_radius, base_length))

            # Append tip points.
            points.append(c4d.Vector(x * tip_radius, y * tip_radius, base_length))

            # Define first point index of this rotation segment.
            first_point_index = first_rotation_segment_point_index + rotation_segment * points_per_rotation_segment

            # Append base polys. Connect to the points of the next rotation segment.
            # Append the poly for the bottom of the base.
            a = 0
            b = first_point_index
            c = (first_point_index + points_per_rotation_segment) % total_rotation_segments_points
            base_polys.append(c4d.CPolygon(a, b, c))

            # Append the poly for the length of the base.
            a = first_rotation_segment_point_index + rotation_segment * points_per_rotation_segment
            b = a + 1
            c = a + points_per_rotation_segment + 1
            d = c - 1

            if is_last_segment:
                c -= total_rotation_segments_points
                d -= total_rotation_segments_points

            base_polys.append(c4d.CPolygon(a, b, c, d))

            # Append the poly connecting the base to the tip.
            a = first_rotation_segment_point_index + rotation_segment * points_per_rotation_segment + 1
            b = a + 1
            c = b + points_per_rotation_segment
            d = c - 1

            if is_last_segment:
                c -= total_rotation_segments_points
                d -= total_rotation_segments_points

            base_to_tip_polys.append(c4d.CPolygon(a, b, c, d))

            # Append the poly connecting the tip to the arrow target.
            a = first_rotation_segment_point_index + rotation_segment * points_per_rotation_segment + 2
            b = 1
            c = a + points_per_rotation_segment

            if is_last_segment:
                c -= total_rotation_segments_points

            tip_polys.append(c4d.CPolygon(a, b, c))
        
        polys = base_polys + base_to_tip_polys + tip_polys

        poly_obj = c4d.BaseObject(c4d.Opolygon)

        self.__setAxis(op, points)

        self.__fillPolyObj(poly_obj, points, polys)

        phong_tag = op.GetTag(c4d.Tphong)
        if phong_tag is not None:
            phong_tag_clone = phong_tag.GetClone(c4d.COPYFLAGS_NONE)
            poly_obj.InsertTag(phong_tag_clone)
        else:
            poly_obj.SetPhong(True, True, c4d.utils.Rad(40.0))

        if bevel:
            bevel = c4d.BaseObject(c4d.Obevel)
            bevel[c4d.O_BEVEL_MODE_COMPONENT_TYPE] = c4d.O_BEVEL_MODE_COMPONENT_TYPE_EDGE
            bevel[c4d.O_BEVEL_MODE_SELECTION_ANGLE_USE] = True
            bevel[c4d.O_BEVEL_MODE_SELECTION_ANGLE_VAL] = c4d.utils.Rad(90.0)
            bevel[c4d.O_BEVEL_MASTER_MODE] = c4d.O_BEVEL_MASTER_MODE_CHAMFER
            bevel[c4d.O_BEVEL_OFFSET_MODE] = c4d.O_BEVEL_OFFSET_MODE_RADIAL
            bevel[c4d.O_BEVEL_RADIUS] = bevel_offset
            bevel[c4d.O_BEVEL_SUB] = bevel_subdivisions
            bevel[c4d.O_BEVEL_LIMIT] = True

            bevel.InsertUnder(poly_obj)

        return poly_obj

    def __setAxis(self, op: c4d.BaseObject, points: list[c4d.Vector]):
        orientation = op[c4d.PRIM_AXIS]

        if orientation == c4d.PRIM_AXIS_ZP:
            return

        if orientation == c4d.PRIM_AXIS_ZN:
            for i, point in enumerate(points):
                points[i] = c4d.Vector(-point.x, point.y, -point.z)

        elif orientation == c4d.PRIM_AXIS_XP:
            for i, point in enumerate(points):
                points[i] = c4d.Vector(point.z, point.y, -point.x)

        elif orientation == c4d.PRIM_AXIS_XN:
            for i, point in enumerate(points):
                points[i] = c4d.Vector(-point.z, point.y, point.x)

        elif orientation == c4d.PRIM_AXIS_YP:
            for i, point in enumerate(points):
                points[i] = c4d.Vector(-point.x, point.z, -point.y)

        elif orientation == c4d.PRIM_AXIS_YN:
            for i, point in enumerate(points):
                points[i] = c4d.Vector(-point.x, -point.z, -point.y)

    def __fillPolyObj(self, poly_obj: c4d.PolygonObject, points: list[c4d.Vector], polys: list[c4d.CPolygon]):
        poly_obj.ResizeObject(len(points), len(polys))

        for i, point in enumerate(points):
            poly_obj.SetPoint(i, point)

        for i, poly in enumerate(polys):
            poly_obj.SetPolygon(i, poly)

    def Message(self, node: GeListNode, type: int, data: object) -> bool:
        
        if type == c4d.MSG_MENUPREPARE:
            node.SetPhong(True, True, c4d.utils.DegToRad(40.0))
        
        return True

if __name__ == "__main__":
    # Retrieves the icon path
    directory, _ = os.path.split(__file__)
    fn = os.path.join(directory, "res", "OarrowIcon.tiff")

    # Creates a BaseBitmap
    bmp = c4d.bitmaps.BaseBitmap()
    if bmp is None:
        raise MemoryError("Failed to create a BaseBitmap.")

    # Init the BaseBitmap with the icon
    if bmp.InitWith(fn)[0] != c4d.IMAGERESULT_OK:
        raise MemoryError("Failed to initialize the BaseBitmap.")
    
    plugin_id = 1062186

    # Registers the object plugin
    c4d.plugins.RegisterObjectPlugin(id=plugin_id,
                                     str=c4d.plugins.GeLoadString(plugin_id),
                                     g=Oarrow,
                                     description="oarrow",
                                     icon=bmp,
                                     info=c4d.OBJECT_GENERATOR|c4d.PLUGINFLAG_HIDEPLUGINMENU,
                                     disklevel=1)