# TODO: add licence info

"""
Blender exporter for Three.js actions (ASCII JSON format).
"""

import bpy
import mathutils

import shutil
import os
import os.path
import math
import operator
import random
import textwrap

TEMPLATE_VEC4 = '[ %g, %g, %g, %g ]'
TEMPLATE_VEC3 = '[ %g, %g, %g ]'
TEMPLATE_VEC2 = '[ %g, %g ]'
TEMPLATE_STRING = '"%s"'
TEMPLATE_HEX = "0x%06x"

def generate_animation(action, skeleton, option_animation_skeletal, option_frame_step):

    if not option_animation_skeletal or not action or not skeleton:
        return ""

    # TODO: Add scaling influences

    parents = []

    fps = bpy.data.scenes[0].render.fps

    end_frame = action.frame_range[1]
    start_frame = action.frame_range[0]

    frame_length = end_frame - start_frame

    TEMPLATE_ANIMATION = """\
	    "name"      : "%(name)s",
        "fps"       : %(fps)s,
        "length"    : %(length)s,
        "hierarchy" : [
%(hierarchy)s
        ]
"""

    TEMPLATE_HIERARCHY_NODE = """\
            {
                "parent" : %(parent)d,
                "keys"   : [
%(keys)s
                ]
            }\
"""

    #TEMPLATE_KEYFRAME_FULL  = '{"time":%g,"pos":[%g,%g,%g],"rot":[%g,%g,%g,%g],"scl":[1,1,1]}'
    #TEMPLATE_KEYFRAME       = '{"time":%g,"pos":[%g,%g,%g],"rot":[%g,%g,%g,%g]}'
    #TEMPLATE_KEYFRAME_POS   = '{"time":%g,"pos":[%g,%g,%g]}'
    #TEMPLATE_KEYFRAME_ROT   = '{"time":%g,"rot":[%g,%g,%g,%g]}'

    # only for easier DEBUGGING :)

    TEMPLATE_KEYFRAME_FULL = """\
                    {
                        "time":%g,
                        "pos" :[%g,%g,%g],
                        "rot" :[%g,%g,%g,%g],
                        "scl" :[1,1,1]
                    }\
"""
    TEMPLATE_KEYFRAME = """\
                    {
                        "time":%g,
                        "pos" :[%g,%g,%g],
                        "rot" :[%g,%g,%g,%g]
                    }\
"""

    TEMPLATE_KEYFRAME_POS = """\
                    {
                        "time":%g,
                        "pos" :[%g,%g,%g]
                    }\
"""

    TEMPLATE_KEYFRAME_ROT = """\
                    {
                        "time":%g,
                        "rot" :[%g,%g,%g,%g]
                    }\
"""

    for bone_proxy in skeleton.iterBones():

        keys = []

        for frame in range(int(start_frame), int(end_frame / option_frame_step) + 1):

            pos, pchange = position(action, bone_proxy, frame * option_frame_step)
            rot, rchange = rotation(action, bone_proxy, frame * option_frame_step)
            
            px, py, pz = pos.x, pos.y, pos.z
            rx, ry, rz, rw = rot.x, rot.y, rot.z, rot.w

            # START-FRAME: needs pos, rot and scl attributes (required frame)

            if frame == int(start_frame):

                time = (frame * option_frame_step - start_frame) / fps
                keyframe = TEMPLATE_KEYFRAME_FULL % (time, px, py, pz, rx, ry, rz, rw)
                keys.append(keyframe)

            # END-FRAME: needs pos, rot and scl attributes with animation length (required frame)

            elif frame == int(end_frame / option_frame_step):

                time = frame_length / fps
                keyframe = TEMPLATE_KEYFRAME_FULL % (time, px, py, pz, rx, ry, rz, rw)
                keys.append(keyframe)

            # MIDDLE-FRAME: needs only one of the attributes, can be an empty frame (optional frame)

            elif pchange == True or rchange == True:

                time = (frame * option_frame_step - start_frame) / fps

                if pchange == True and rchange == True:
                    keyframe = TEMPLATE_KEYFRAME % (time, px, py, pz, rx, ry, rz, rw)
                elif pchange == True:
                    keyframe = TEMPLATE_KEYFRAME_POS % (time, px, py, pz)
                elif rchange == True:
                    keyframe = TEMPLATE_KEYFRAME_ROT % (time, rx, ry, rz, rw)

                keys.append(keyframe)

        keys_string = ",\n".join(keys)
        parent = TEMPLATE_HIERARCHY_NODE % {
            "parent" : bone_proxy.getParentIndex(),
            "keys"   : keys_string,
        }
        parents.append(parent)

    hierarchy_string = ",\n".join(parents)
    animation_string = TEMPLATE_ANIMATION % {
        "name"      : action.name,
        "fps"       : fps,
        "length"    : frame_length / fps,
        "hierarchy" : hierarchy_string,
    }

    return animation_string

def position(action, bone_proxy, frame):

    index = -1
    change = False

    bone = bone_proxy.getBone()

    for i in range(len(action.groups)):
        if action.groups[i].name == bone.name:
            index = i

    position = None
    
    if index >= 0:
        for channel in action.groups[index].channels:

            if position is None:
                position = mathutils.Vector((0,0,0))

            if "location" in channel.data_path:

                if channel.array_index == 0:
                    for keyframe in channel.keyframe_points:
                        if keyframe.co[0] == frame:
                            change = True
                    position.x = channel.evaluate(frame)

                if channel.array_index == 1:
                    for keyframe in channel.keyframe_points:
                        if keyframe.co[0] == frame:
                            change = True
                    position.y = channel.evaluate(frame)

                if channel.array_index == 2:
                    for keyframe in channel.keyframe_points:
                        if keyframe.co[0] == frame:
                            change = True
                    position.z = channel.evaluate(frame)

    # if position is None, the rest position is retuned
    
    position = bone_proxy.getPosition(position)

    return position, change

def rotation(action, bone_proxy, frame):

    # TODO: Calculate rotation also from rotation_euler channels

    index = -1
    change = False
    
    bone = bone_proxy.getBone()

    for i in range(len(action.groups)):
        if action.groups[i].name == bone.name:
            index = i

    rotation = mathutils.Vector((0,0,0,0))

    quaternion = None
    
    if index >= 0:
        for channel in action.groups[index].channels:

            if "quaternion" in channel.data_path:
                
                if quaternion is None:
                    quaternion = mathutils.Quaternion()
                
                if channel.array_index == 1:
                    for keyframe in channel.keyframe_points:
                        if keyframe.co[0] == frame:
                            change = True
                    quaternion.x = channel.evaluate(frame)

                if channel.array_index == 2:
                    for keyframe in channel.keyframe_points:
                        if keyframe.co[0] == frame:
                            change = True
                    quaternion.y = channel.evaluate(frame)

                if channel.array_index == 3:
                    for keyframe in channel.keyframe_points:
                        if keyframe.co[0] == frame:
                            change = True
                    quaternion.z = channel.evaluate(frame)

                if channel.array_index == 0:
                    for keyframe in channel.keyframe_points:
                        if keyframe.co[0] == frame:
                            change = True
                    quaternion.w = channel.evaluate(frame)      
    
    # if quaternion is None, the rest position is retuned
    
    quaternion = bone_proxy.getQuaternion(quaternion)
    
    return quaternion, change

# #####################################################
# Model exporter - export single mesh
# #####################################################

def extract_meshes(objects, scene, export_single_model, option_scale, option_bones, flipyz):
    
    # for YZ flip
    X_ROT  = mathutils.Matrix.Rotation(-math.pi/2, 4, 'X')
    
    meshes = []

    for object in objects:

        if object.type == "MESH" and object.THREE_exportGeometry:

            # collapse modifiers into mesh

            mesh = object.to_mesh(scene, True, 'RENDER')

            if not mesh:
                raise Exception("Error, could not get mesh data from object [%s]" % object.name)

            if export_single_model:
                if flipyz:
                    # that's what Blender's native export_obj.py does
                    # to flip YZ
                    mesh.transform(X_ROT * object.matrix_world)
                else:
                    mesh.transform(object.matrix_world)

            mesh.calc_normals()
            mesh.calc_tessface()
            # mesh.transform(mathutils.Matrix.Scale(option_scale, 4))
            
            armature = None
            
            if option_bones and object.parent and object.parent_type == 'ARMATURE':
                
                armature_object = object.parent
                armature        = object.parent.data.copy()
                
                offset = None
                                
                if export_single_model:
                    if flipyz:
                        offset = X_ROT * armature_object.matrix_world
                    else:
                        offset = armature_object.matrix_world
                else:
                    offset = object.matrix_world.inverted() * armature_object.matrix_world
                    
                for bone in armature.bones:
                
                    if not bone.parent:
                            
                        #TODO: test it!!!
                        
                        bone.head   = offset * bone.head                       
                        bone.tail   = offset * bone.tail
                        
                        bone.matrix = offset.to_3x3() * bone.matrix
            #endif
            
            meshes.append([mesh, object, armature])
            
    return meshes

def generate_mesh_string(objects, scene,
                option_vertices,
                option_vertices_truncate,
                option_faces,
                option_normals,
                option_uv_coords,
                option_materials,
                option_colors,
                option_bones,
                option_skinning,
                align_model,
                flipyz,
                option_scale,
                export_single_model,
                option_copy_textures,
                filepath,
                option_animation_morph,
                option_animation_skeletal,                                
                option_frame_step):

    meshes = extract_meshes(objects, scene, export_single_model, option_scale, option_bones, flipyz)

    morphs = []

    if option_animation_morph:

        original_frame = scene.frame_current # save animation state

        scene_frames = range(scene.frame_start, scene.frame_end + 1, option_frame_step)

        for frame in scene_frames:
            scene.frame_set(frame, 0.0)

            anim_meshes = extract_meshes(objects, scene, export_single_model, option_scale, False, flipyz)

            frame_vertices = []

            for mesh, object, dummy in anim_meshes:
                frame_vertices.extend(mesh.vertices[:])

            morphVertices = generate_vertices(frame_vertices, option_vertices_truncate, option_vertices)
            morphs.append(morphVertices)

            # remove temp meshes

            for mesh, object, dummy in anim_meshes:
                bpy.data.meshes.remove(mesh)

        scene.frame_set(original_frame, 0.0) # restore animation state


    text, model_string, skeleton = generate_ascii_model(meshes, morphs,
                                scene,
                                option_vertices,
                                option_vertices_truncate,
                                option_faces,
                                option_normals,
                                option_uv_coords,
                                option_materials,
                                option_colors,
                                option_bones,
                                option_skinning,                                
                                align_model,
                                flipyz,
                                option_scale,
                                option_copy_textures,
                                filepath,
                                option_animation_morph,
                                option_animation_skeletal,                                
                                option_frame_step)

    # remove temp meshes and armatures

    for mesh, object, armature in meshes:
        bpy.data.meshes.remove(mesh)
        if armature:
            bpy.data.armatures.remove(armature)

    return text, model_string, skeleton

def export_mesh(objects,
                scene, filepath,
                option_vertices,
                option_vertices_truncate,
                option_faces,
                option_normals,
                option_uv_coords,
                option_materials,
                option_colors,
                option_bones,
                option_skinning,                
                align_model,
                flipyz,
                option_scale,
                export_single_model,
                option_copy_textures,
                option_animation_morph,
                option_animation_skeletal,
                option_frame_step,
                option_all_actions):

    text, model_string, skeleton = generate_mesh_string(objects,
                scene,
                option_vertices,
                option_vertices_truncate,
                option_faces,
                option_normals,
                option_uv_coords,
                option_materials,
                option_colors,
                option_bones,
                option_skinning,
                align_model,
                flipyz,
                option_scale,
                export_single_model,
                option_copy_textures,
                filepath,
                option_animation_morph,
                option_animation_skeletal,                                
                option_frame_step)

    write_file(filepath, text)

    print("writing", filepath, "done")

    if option_all_actions and skeleton.getBonesCount() > 0:
        
        TEMPLATE_ACTION_LIBRARY = '{\n%(actions)s\n}\n'
        TEMPLATE_ACTION         = '    "%(name)s" : {\n%(action)s\n    }'
        
        actions = []
        for action in bpy.data.actions:
            
            actions.append(TEMPLATE_ACTION % {
                "name"   : action.name,
                "action" : generate_animation(action, skeleton, True, option_frame_step),
            })
        
        action_library = TEMPLATE_ACTION_LIBRARY % { 'actions' : ',\n\n'.join(actions) }
                
        filepath = generate_action_library_filename(filepath)
        write_file(filepath, action_library)               
        
        print("writing", filepath, "done")

# #####################################################
# Main
# #####################################################

def save(operator, context, filepath = "",
         option_flip_yz = True,
         option_vertices = True,
         option_vertices_truncate = False,
         option_faces = True,
         option_normals = True,
         option_uv_coords = True,
         option_materials = True,
         option_colors = True,
         option_bones = True,
         option_skinning = True,
         align_model = 0,
         option_export_scene = False,
         option_lights = False,
         option_cameras = False,
         option_scale = 1.0,
         option_embed_meshes = True,
         option_url_base_html = False,
         option_copy_textures = False,
         option_animation_morph = False,
         option_animation_skeletal = False,
         option_frame_step = 1,
         option_all_actions = False,
         option_all_meshes = True):

    #print("URL TYPE", option_url_base_html)

    filepath = ensure_extension(filepath, '.js')

    export_mesh(objects, scene, filepath,
                option_vertices,
                option_vertices_truncate,
                option_faces,
                option_normals,
                option_uv_coords,
                option_materials,
                option_colors,
                option_bones,
                option_skinning,                    
                align_model,
                option_flip_yz,
                option_scale,
                True,            # export_single_model
                option_copy_textures,
                option_animation_morph,
                option_animation_skeletal,
                option_frame_step,
                option_all_actions)

    return {'FINISHED'}
