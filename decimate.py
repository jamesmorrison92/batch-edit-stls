import bpy
import os
import argparse
import shutil
import numpy as np
from mathutils import Vector


def process_stl(input_path, output_path, decimation_ratio, resize_factor):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.delete()

    bpy.ops.import_mesh.stl(filepath=input_path)

    if bpy.context.selected_objects:
        bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]

        # Apply the decimation modifier if ratio is provided
        if decimation_ratio is not None:
            bpy.ops.object.modifier_add(type='DECIMATE')
            bpy.context.object.modifiers["Decimate"].ratio = decimation_ratio

        # Apply resizing if resize factor is provided
        if resize_factor is not None:
            bpy.ops.transform.resize(value=(resize_factor, resize_factor, resize_factor))

        # Convert the object to apply the modifiers
        bpy.ops.object.convert(target='MESH')

        # Export the processed mesh to STL
        bpy.ops.export_mesh.stl(filepath=output_path)

    else:
        print(f"Skipping {input_path}: No valid mesh data found.")


def get_oriented_bounding_box(obj):
    # Convert object to numpy array of vertices
    verts = np.array([obj.matrix_world @ Vector(v.co) for v in obj.data.vertices])

    # Compute the covariance matrix and eigenvectors
    cov_matrix = np.cov(verts.T)
    eigvals, eigvecs = np.linalg.eigh(cov_matrix)

    # Sort eigenvectors by eigenvalues
    order = eigvals.argsort()[::-1]
    eigvecs = eigvecs[:, order]

    # Rotate the vertices to the principal component frame
    rotated_verts = verts @ eigvecs

    # Find the minimum and maximum points in the principal component frame
    min_coords = rotated_verts.min(axis=0)
    max_coords = rotated_verts.max(axis=0)

    # Compute dimensions in the principal component frame
    dimensions = max_coords - min_coords

    return dimensions


def get_axis_aligned_bounding_box(obj):
    local_coords = np.array([v.co for v in obj.data.vertices])
    dimensions = local_coords.max(axis=0) - local_coords.min(axis=0)
    return dimensions


def process_and_write_dimensions(input_directory, output_directory, decimation_ratio, resize_factor, prepend_str, append_str, recursive, dimensions_flag, dimension_method):
    use_blender = decimation_ratio is not None or resize_factor is not None
    dimension_lines = []

    if recursive:
        for root, dirs, files in os.walk(input_directory):
            for filename in files:
                if filename.endswith(".stl"):
                    input_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(input_path, input_directory)
                    output_path = os.path.join(output_directory, relative_path)
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    base_filename, ext = os.path.splitext(filename)
                    if prepend_str is not None:
                        base_filename = prepend_str + base_filename
                    if append_str is not None:
                        base_filename = base_filename + append_str
                    new_output_path = os.path.join(os.path.dirname(output_path), base_filename + ext)

                    bpy.ops.object.select_all(action='DESELECT')
                    bpy.ops.object.select_by_type(type='MESH')
                    bpy.ops.object.delete()
                    bpy.ops.import_mesh.stl(filepath=input_path)
                    if bpy.context.selected_objects:
                        obj = bpy.context.selected_objects[0]

                        # Apply the modifications
                        if use_blender:
                            if decimation_ratio is not None:
                                bpy.ops.object.modifier_add(type='DECIMATE')
                                bpy.context.object.modifiers["Decimate"].ratio = decimation_ratio
                            if resize_factor is not None:
                                bpy.ops.transform.resize(value=(resize_factor, resize_factor, resize_factor))
                            bpy.ops.object.convert(target='MESH')

                        # Compute dimensions based on the chosen method
                        if dimension_method == "obb":
                            dimensions = get_oriented_bounding_box(obj)
                        else:
                            dimensions = get_axis_aligned_bounding_box(obj) * (resize_factor if resize_factor is not None else 1)

                        dimension_lines.append(f"{filename}: {dimensions[0]:.3f}, {dimensions[1]:.3f}, {dimensions[2]:.3f}")

                        if use_blender:
                            process_stl(input_path, new_output_path, decimation_ratio, resize_factor)
                        else:
                            shutil.copy(input_path, new_output_path)

    else:
        files = [f for f in os.listdir(input_directory) if f.endswith(".stl")]
        for filename in files:
            input_path = os.path.join(input_directory, filename)
            relative_path = os.path.relpath(input_path, input_directory)
            output_path = os.path.join(output_directory, relative_path)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            base_filename, ext = os.path.splitext(filename)
            if prepend_str is not None:
                base_filename = prepend_str + base_filename
            if append_str is not None:
                base_filename = base_filename + append_str
            new_output_path = os.path.join(os.path.dirname(output_path), base_filename + ext)

            bpy.ops.object.select_all(action='DESELECT')
            bpy.ops.object.select_by_type(type='MESH')
            bpy.ops.object.delete()
            bpy.ops.import_mesh.stl(filepath=input_path)
            if bpy.context.selected_objects:
                obj = bpy.context.selected_objects[0]

                # Apply the modifications
                if use_blender:
                    if decimation_ratio is not None:
                        bpy.ops.object.modifier_add(type='DECIMATE')
                        bpy.context.object.modifiers["Decimate"].ratio = decimation_ratio
                    if resize_factor is not None:
                        bpy.ops.transform.resize(value=(resize_factor, resize_factor, resize_factor))
                    bpy.ops.object.convert(target='MESH')

                # Compute dimensions based on the chosen method
                if dimension_method == "obb":
                    dimensions = get_oriented_bounding_box(obj)
                else:
                    dimensions = get_axis_aligned_bounding_box(obj) * (resize_factor if resize_factor is not None else 1)

                dimension_lines.append(f"{filename}: {dimensions[0]:.3f}, {dimensions[1]:.3f}, {dimensions[2]:.3f}")

                if use_blender:
                    process_stl(input_path, new_output_path, decimation_ratio, resize_factor)
                else:
                    shutil.copy(input_path, new_output_path)

    if dimensions_flag and dimension_lines:
        dimensions_file_path = os.path.join(output_directory, "dimensions.txt")
        with open(dimensions_file_path, 'w') as f:
            f.write("\n".join(dimension_lines))

    print("Done.")


def parse_args():
    parser = argparse.ArgumentParser(description="Mass decimate and/or rename STL files using Blender.")
    parser.add_argument("-i", "--input", help="Path to the input directory containing STL files. Defaults to the current working directory.")
    parser.add_argument("-o", "--output", default="decimate_output", help="Path to the output directory for storing processed STL files.")
    parser.add_argument("-d", "--decimation-ratio", type=float, help="Decimation ratio for the mesh.")
    parser.add_argument("-s", "--resize", type=float, help="Resize factor for the mesh.")
    parser.add_argument("-p", "--prepend", help="String to be prepended to the file name.")
    parser.add_argument("-a", "--append", help="String to be appended to the file name.")
    parser.add_argument("-r", "--recursive", action="store_true", help="Recursively process all STL files in child directories.")
    parser.add_argument("--dimensions", action="store_true", help="Output a .txt file with the dimensions of each model.")
    parser.add_argument("--dimension-method", choices=["obb", "axis-aligned"], default="axis-aligned", help="Method to compute dimensions: 'obb' (Oriented Bounding Box) or 'axis-aligned' (Axis-Aligned Bounding Box).")

    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()

    # If input directory is not provided, use the current working directory
    if args.input is None:
        args.input = os.getcwd()

    process_and_write_dimensions(args.input, args.output, args.decimation_ratio, args.resize, args.prepend, args.append, args.recursive, args.dimensions, args.dimension_method)
