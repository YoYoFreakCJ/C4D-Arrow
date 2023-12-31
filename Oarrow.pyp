"""
Copyright: Software Schmid
Author: Daniel Schmid

Description:
    - Creates an arrow.

"""

from logging.config import BaseConfigurator
from typing import Tuple, Union
import c4d
import os

from c4d import BaseObject, BaseTag, DescID, Description, GeListNode
from c4d.documents import BaseDocument
from c4d.threading import BaseThread

Oarrow_PLUGINID = 1062186
Tcalculatearrowlength_PLUGINID = 1062203

class Oarrow(c4d.plugins.ObjectData):
    flat_orientations_per_orientation = None
    axis_names = None

    """ Creates an arrow primitive. """
    def __init__(self, *args):
        super().__init__(*args)
        self.SetOptimizeCache(True)
    
    def Init(self, op, isCloneInit):
        """Called when Cinema 4D Initialize the ObjectData (used to define, default values).

        Args:
            op: (c4d.GeListNode): The instance of the ObjectData.

        Returns:
            bool: True on success, otherwise False.
        """

        self.InitAttr(op, float, c4d.OARROW_LENGTH)
        self.InitAttr(op, bool, c4d.OARROW_FLAT_ENABLE)
        self.InitAttr(op, int, c4d.OARROW_ROTATION_SEGMENTS)
        self.InitAttr(op, int, c4d.OARROW_FLAT_ORIENTATION)
        self.InitAttr(op, float, c4d.OARROW_BASE_RADIUS)
        self.InitAttr(op, float, c4d.OARROW_TIP_RADIUS)
        self.InitAttr(op, float, c4d.OARROW_TIP_LENGTH)
        self.InitAttr(op, int, c4d.PRIM_AXIS)

        op[c4d.OARROW_LENGTH] = 100.0
        op[c4d.OARROW_FLAT_ENABLE] = False
        op[c4d.OARROW_ROTATION_SEGMENTS] = 12
        op[c4d.OARROW_FLAT_ORIENTATION] = c4d.OARROW_FLAT_ORIENTATION_XP
        op[c4d.OARROW_BASE_RADIUS] = 10.0
        op[c4d.OARROW_TIP_RADIUS] = 20.0
        op[c4d.OARROW_TIP_LENGTH] = 30.0
        op[c4d.PRIM_AXIS] = c4d.PRIM_AXIS_YP

        self.flat_orientations_per_orientation = {
            None: [None],
            c4d.PRIM_AXIS_XN: [c4d.OARROW_FLAT_ORIENTATION_YP, c4d.OARROW_FLAT_ORIENTATION_YN, c4d.OARROW_FLAT_ORIENTATION_ZP, c4d.OARROW_FLAT_ORIENTATION_ZN],
            c4d.PRIM_AXIS_XP: [c4d.OARROW_FLAT_ORIENTATION_YP, c4d.OARROW_FLAT_ORIENTATION_YN, c4d.OARROW_FLAT_ORIENTATION_ZP, c4d.OARROW_FLAT_ORIENTATION_ZN],
            c4d.PRIM_AXIS_YN: [c4d.OARROW_FLAT_ORIENTATION_XP, c4d.OARROW_FLAT_ORIENTATION_XN, c4d.OARROW_FLAT_ORIENTATION_ZP, c4d.OARROW_FLAT_ORIENTATION_ZN],
            c4d.PRIM_AXIS_YP: [c4d.OARROW_FLAT_ORIENTATION_XP, c4d.OARROW_FLAT_ORIENTATION_XN, c4d.OARROW_FLAT_ORIENTATION_ZP, c4d.OARROW_FLAT_ORIENTATION_ZN],
            c4d.PRIM_AXIS_ZN: [c4d.OARROW_FLAT_ORIENTATION_XP, c4d.OARROW_FLAT_ORIENTATION_XN, c4d.OARROW_FLAT_ORIENTATION_YP, c4d.OARROW_FLAT_ORIENTATION_YN],
            c4d.PRIM_AXIS_ZP: [c4d.OARROW_FLAT_ORIENTATION_XP, c4d.OARROW_FLAT_ORIENTATION_XN, c4d.OARROW_FLAT_ORIENTATION_YP, c4d.OARROW_FLAT_ORIENTATION_YN]
        }

        self.axis_names = {
            c4d.OARROW_FLAT_ORIENTATION_XN: "-X",
            c4d.OARROW_FLAT_ORIENTATION_XP: "+X",
            c4d.OARROW_FLAT_ORIENTATION_YN: "-Y",
            c4d.OARROW_FLAT_ORIENTATION_YP: "+Y",
            c4d.OARROW_FLAT_ORIENTATION_ZN: "-Z",
            c4d.OARROW_FLAT_ORIENTATION_ZP: "+Z"
        }

        return True

    def GetVirtualObjects(self, op, hierarchyhelp):
        # Prepare base values.
        length = op[c4d.OARROW_LENGTH]
        rotation_segments = op[c4d.OARROW_ROTATION_SEGMENTS]
        base_radius = op[c4d.OARROW_BASE_RADIUS]
        tip_radius = op[c4d.OARROW_TIP_RADIUS]
        tip_length = op[c4d.OARROW_TIP_LENGTH]

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
                points[i] = c4d.Vector(point.x, point.z, -point.y)

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

            if not isinstance(node, c4d.BaseObject):
                return False
            
            length_calculator_tag = node.GetTag(c4d.Tcalculatearrowlength)

            if length_calculator_tag is None:
                length_calculator_tag = node.MakeTag(c4d.Tcalculatearrowlength)

            aim_constraint_tag = node.GetTag(c4d.Tcaconstraint)

            if aim_constraint_tag is None:
                node_data = node.GetDataInstance()
                orientation = node_data.GetInt32(c4d.PRIM_AXIS)

                aim_constraint_tag = node.MakeTag(c4d.Tcaconstraint)
                #aim_constraint_tag.ChangeNBit(c4d.NBIT_OHIDE, True)
                aim_constraint_tag[c4d.EXPRESSION_ENABLE] = False
                aim_constraint_tag[c4d.ID_CA_CONSTRAINT_TAG_AIM] = True
                aim_constraint_tag[c4d.ID_CA_CONSTRAINT_TAG_AIM_TARGET_COUNT] = 1
                aim_axis = self.__getAimConstraintAxisFromArrowOrientation(orientation)
                aim_constraint_tag[c4d.ID_CA_CONSTRAINT_TAG_AIM_TARGET_COUNT + 4] = aim_axis

        elif type == c4d.MSG_DESCRIPTION_POSTSETPARAMETER:
            target_id = c4d.DescID(c4d.OARROW_TARGET)
            target_offset_id = c4d.DescID(c4d.OARROW_TARGET_OFFSET)
            orientation_id = c4d.DescID(c4d.PRIM_AXIS)
            changed_descid = data["descid"]

            if not isinstance(node, c4d.BaseObject):
                return False

            node_data = node.GetDataInstance()

            target_changed = target_id.IsPartOf(changed_descid)[0]
            orientation_changed = orientation_id.IsPartOf(changed_descid)[0]
            target_offset_changed = target_offset_id.IsPartOf(changed_descid)[0]

            aim_constraint_tag = node.GetTag(c4d.Tcaconstraint)

            if aim_constraint_tag is None:
                return False
            
            if target_changed:                
                target = node_data.GetLink(c4d.OARROW_TARGET)

                if target is None:
                    aim_constraint_tag[c4d.EXPRESSION_ENABLE] = False
                else:
                    aim_constraint_tag[c4d.EXPRESSION_ENABLE] = True       
                    aim_constraint_tag[c4d.ID_CA_CONSTRAINT_TAG_AIM_TARGET_COUNT + 1]  = target             

            elif orientation_changed:
                orientation = node_data.GetInt32(c4d.PRIM_AXIS)
                
                if orientation is None:
                    return False

                # When changing the aim axis it sometimes deviates from the actual aim by a bit.
                # To circumvent this behavior the rotation of the object must be reset before
                # changing the aim axis.
                was_enabled = aim_constraint_tag[c4d.EXPRESSION_ENABLE]
                if was_enabled:
                    node.SetAbsRot(c4d.Vector(0))
                
                aim_axis = self.__getAimConstraintAxisFromArrowOrientation(orientation)
                aim_constraint_tag[c4d.ID_CA_CONSTRAINT_TAG_AIM_TARGET_COUNT + 4] = aim_axis

            if self.flat_orientations_per_orientation is None:
                return False

            # If the current flat orientation is not in the list of available values
            # set it to an available value.
            orientation = node[c4d.PRIM_AXIS]
            flat_orientation = node[c4d.OARROW_FLAT_ORIENTATION]
            available_orientations = self.flat_orientations_per_orientation[orientation]

            if flat_orientation not in available_orientations:
                new_flat_orientation = available_orientations[0]

                if new_flat_orientation is not None and new_flat_orientation != flat_orientation:
                    node[c4d.OARROW_FLAT_ORIENTATION] = new_flat_orientation
        
        elif type == c4d.MSG_DESCRIPTION_CHECKDRAGANDDROP:
            return False

            dragged_element = data["element"]
            is_same_object = node == dragged_element
            return not is_same_object

        return True
    
    def __getAimConstraintAxisFromArrowOrientation(self, arrow_orientation: int) -> int:
        aim_constraint_axis: int

        match arrow_orientation:
            case c4d.PRIM_AXIS_XP:
                aim_constraint_axis = 0
            case c4d.PRIM_AXIS_YP:
                aim_constraint_axis = 1
            case c4d.PRIM_AXIS_ZP:
                aim_constraint_axis = 2
            case c4d.PRIM_AXIS_XN:
                aim_constraint_axis = 3
            case c4d.PRIM_AXIS_YN:
                aim_constraint_axis = 4
            case c4d.PRIM_AXIS_ZN:
                aim_constraint_axis = 5
        
        return aim_constraint_axis
        
    def GetDDescription(self, node: c4d.GeListNode, description: c4d.Description, flags: int) -> bool | Tuple[bool, int]:
        # Load the description resource.
        if not description.LoadDescription(node.GetType()):
            return False

        single_id = description.GetSingleDescID()
       
        if not isinstance(node, c4d.BaseList2D):
            return False

        flat_orientation_id = c4d.DescID(c4d.OARROW_FLAT_ORIENTATION)

        if single_id is None or flat_orientation_id.IsPartOf(single_id)[0]:
            orientation = node[c4d.PRIM_AXIS]

            if orientation is None:
                return False

            if self.flat_orientations_per_orientation is None or self.axis_names is None:
                return False

            flat_orientations = self.flat_orientations_per_orientation[orientation]

            items = c4d.BaseContainer()

            # Define the available flat orientations for the chosen orientation.
            for flat_orientation in flat_orientations:
                items.SetString(flat_orientation, self.axis_names[flat_orientation])
            
            flat_orientation_param = description.GetParameterI(flat_orientation_id)
            if flat_orientation_param is None:
                return False

            flat_orientation_param.SetContainer(c4d.DESC_CYCLE, items)

        return (True, flags | c4d.DESCFLAGS_DESC_LOADED)

    def GetDEnabling(self, node: c4d.GeListNode, id: c4d.DescID, t_data: object, flags: int, itemdesc: c4d.BaseContainer) -> bool:
        rotation_segments_id = c4d.DescID(c4d.OARROW_ROTATION_SEGMENTS)
        flat_direction_id = c4d.DescID(c4d.OARROW_FLAT_ORIENTATION)
        length_id = c4d.DescID(c4d.OARROW_LENGTH)
        target_offset_id = c4d.DescID(c4d.OARROW_TARGET_OFFSET)

        if not isinstance(node, c4d.BaseList2D):
            return False
       
        data: c4d.BaseContainer = node.GetDataInstance()

        if rotation_segments_id.IsPartOf(id)[0]:
            flat_enable = data.GetBool(c4d.OARROW_FLAT_ENABLE)
            return not flat_enable
        
        elif flat_direction_id.IsPartOf(id)[0]:
            flat_enable = data.GetBool(c4d.OARROW_FLAT_ENABLE)
            return flat_enable
        
        elif length_id.IsPartOf(id)[0]:
            link_is_set = data.GetLink(c4d.OARROW_TARGET) is not None
            return not link_is_set
        
        elif target_offset_id.IsPartOf(id)[0]:
            target_is_set = data.GetLink(c4d.OARROW_TARGET) is not None
            return target_is_set
        
        return True

class Tcalculatearrowlength(c4d.plugins.TagData):
    def Execute(self, tag: BaseTag, doc: BaseDocument, op: BaseObject, bt: BaseThread, priority: int, flags: int) -> int:

        op_is_arrow = op.GetType() == Oarrow_PLUGINID

        if not op_is_arrow:
            print('op must be Oarrow.')
            return c4d.EXECUTIONRESULT_USERBREAK

        data = op.GetDataInstance()

        target = data.GetLink(c4d.OARROW_TARGET)

        if target is None:
            return c4d.EXECUTIONRESULT_OK
        
        if not isinstance(target, c4d.BaseObject):
            print('Target must be BaseObject.')
            return c4d.EXECUTIONRESULT_USERBREAK

        distance_to_target = (target.GetAbsPos() - op.GetAbsPos()).GetLength()

        offset = data.GetFloat(c4d.OARROW_TARGET_OFFSET)

        length = distance_to_target - offset

        op[c4d.OARROW_LENGTH] = length

        return c4d.EXECUTIONRESULT_OK

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
    
    # Registers the object plugin
    c4d.plugins.RegisterObjectPlugin(id=Oarrow_PLUGINID,
                                     str=c4d.plugins.GeLoadString(Oarrow_PLUGINID),
                                     g=Oarrow,
                                     description="oarrow",
                                     icon=bmp,
                                     info=c4d.OBJECT_GENERATOR | c4d.PLUGINFLAG_HIDEPLUGINMENU,
                                     disklevel=1)
    
    c4d.plugins.RegisterTagPlugin(id=Tcalculatearrowlength_PLUGINID,
                                  str="Calculate Arrow Length",
                                  g=Tcalculatearrowlength,
                                  description="tcalculatearrowlength",
                                  icon=None,
                                  info=c4d.TAG_EXPRESSION,
                                  disklevel=1)