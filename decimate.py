import bpy
import os
import argparse
import shutil

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


def decimate_and_rename(input_directory, output_directory, decimation_ratio, resize_factor, prepend_str, append_str, recursive):
    use_blender = decimation_ratio is not None or resize_factor is not None

    if recursive:
        for root, dirs, files in os.walk(input_directory):
            for filename in files:
                if filename.endswith(".stl"):
                    input_path = os.path.join(root, filename)
                    # Create a relative path from the input directory
                    relative_path = os.path.relpath(input_path, input_directory)

                    # Use 'low-poly' directory in the output directory if provided
                    output_path = os.path.join(output_directory, relative_path)

                    # Create output directory structure if not exists
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)

                    # Extract file name and extension
                    base_filename, ext = os.path.splitext(filename)

                    # Modify the base filename with prepend and/or append strings
                    if prepend_str is not None:
                        base_filename = prepend_str + base_filename
                    if append_str is not None:
                        base_filename = base_filename + append_str

                    # Construct the final output path
                    new_output_path = os.path.join(os.path.dirname(output_path), base_filename + ext)

                    if use_blender:
                        process_stl(input_path, new_output_path, decimation_ratio, resize_factor)
                    else:
                        shutil.copy(input_path, new_output_path)

    else:
        files = [f for f in os.listdir(input_directory) if f.endswith(".stl")]
        for filename in files:
            input_path = os.path.join(input_directory, filename)
            # Create a relative path from the input directory
            relative_path = os.path.relpath(input_path, input_directory)

            # Set output path
            output_path = os.path.join(output_directory, relative_path)

            # Create output directory structure if not exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Extract file name and extension
            base_filename, ext = os.path.splitext(filename)

            # Modify the base filename with prepend and/or append strings
            if prepend_str is not None:
                base_filename = prepend_str + base_filename
            if append_str is not None:
                base_filename = base_filename + append_str

            # Construct the final output path
            new_output_path = os.path.join(os.path.dirname(output_path), base_filename + ext)

            if use_blender:
                process_stl(input_path, new_output_path, decimation_ratio, resize_factor)
            else:
                shutil.copy(input_path, new_output_path)
    print("Done.")


def parse_args():
    parser = argparse.ArgumentParser(description="Mass decimate and/or rename STL files using Blender.")
    parser.add_argument("-i", "--input", required=True, help="Path to the input directory containing STL files.")
    parser.add_argument("-o", "--output", default="decimate_output", help="Path to the output directory for storing processed STL files.")
    parser.add_argument("-d", "--decimation-ratio", type=float, help="Decimation ratio for the mesh.")
    parser.add_argument("-s", "--resize", type=float, help="Resize factor for the mesh.")
    parser.add_argument("-p", "--prepend", help="String to be prepended to the file name.")
    parser.add_argument("-a", "--append", help="String to be appended to the file name.")
    parser.add_argument("-r", "--recursive", action="store_true", help="Recursively process all STL files in child directories.")

    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()

    # If output directory is not provided, use the input directory
    if args.output is None:
        args.output = args.input

    decimate_and_rename(args.input, args.output, args.decimation_ratio, args.resize, args.prepend, args.append, args.recursive)
