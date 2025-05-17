import yaml
class ProjectFileIO:
    def str2bool(self, value):
        """
        Converts a string to a boolean.
        """
        if isinstance(value, bool):
            return value
        if value.lower() in ('yes', 'true', 't', '1'):
            return True
        elif value.lower() in ('no', 'false', 'f', '0'):
            return False
        else:
            raise ValueError(f"Invalid boolean string: {value}")
        
    def read_project_file(self, project_file):
        """
        Reads a project file and returns a dictionary of the data.
        """
        with open(project_file, 'r') as file:
            lines = [item.strip() for item in file.readlines()]

        project_data = {}

        for line in lines:
            if not line.startswith('//') and line:
                # take anything before the first whitespace as the key and the rest as the value
                key, value = line.split(maxsplit=1)
                # remove any thing after a // in the value
                if '//' in value:
                    value = value.split('//')[0].strip()
                # remove any whitespace from the key and value
                key = key.strip()
                value = value.strip()
                # if the key is not already in the dictionary, add it
                if key not in project_data:
                    project_data[key] = value

        return project_data

    def write_project_file(self, project_dict, project_file):
        """
        Writes a project file from a dictionary of the data.
        """
        with open(project_file, 'w') as file:
            for key, value in project_dict.items():
                # write the key and value to the file
                file.write(f"{key}    {value}\n")


class MaterialFileIO:
    def read_material_file(self, material_file, multiline_tags = ['source']):
        """
        Reads a material file and returns a nested dictionary of the data,
        dynamically handling any tag structure and multiple materials.
        """

        with open(material_file, 'r') as file:
            lines = [
                line.strip()
                for line in file
                if line.strip() and not line.strip().startswith('#') and not line.strip().startswith('//')
            ]

        stack = []
        key_stack = []
        materials = []

        for line in lines:
            # End tag
            if line.startswith("End"):
                tag = line[3:].strip()
                finished = stack.pop()
                finished_key = key_stack.pop()
                if isinstance(finished, list):
                    finished = "\n".join(finished)
                if not stack:
                    materials.append(finished)
                else:
                    parent = stack[-1]
                    parent_key = key_stack[-1]
                    if isinstance(parent, dict):
                        # --- Support multiple blocks with the same tag ---
                        if finished_key in parent:
                            if not isinstance(parent[finished_key], list):
                                parent[finished_key] = [parent[finished_key]]
                            parent[finished_key].append(finished)
                        else:
                            parent[finished_key] = finished
                continue

            # If we're inside a multi-line block (like Source), always append
            if stack and isinstance(stack[-1], list):
                stack[-1].append(line)
                continue

            # Start tag (no '=' and not an End tag)
            if "=" not in line:
                if line.lower() in multiline_tags:
                    stack.append([])
                else:
                    stack.append({})
                key_stack.append(line)
                continue

            # Key-value line
            if "=" in line and stack:
                key, value = line.split("=", 1)
                if isinstance(stack[-1], dict):
                    stack[-1][key.strip()] = value.strip()
                continue

        # After parsing, unwind the stack and add any remaining dicts to materials
        while stack:
            item = stack.pop()
            key = key_stack.pop()
            if isinstance(item, dict):
                materials.append(item)

        # Convert lists (like Source) to joined strings
        def flatten(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if isinstance(v, list):
                        # If it's a list of dicts, flatten each dict
                        if all(isinstance(i, dict) for i in v):
                            obj[k] = [flatten(i) for i in v]
                        # If it's a list of strings, join them
                        elif all(isinstance(i, str) for i in v):
                            obj[k] = "\n".join(v)
                        # Mixed types: leave as-is or handle as needed
                    elif isinstance(v, dict):
                        flatten(v)
            return obj

        result = {}
        for mat in materials:
            flatten(mat)
            name = mat.get("name", f"material_{len(result)}")
            result[name] = mat

        return result
    
    def write_material_file(self, material_dict, material_file, start_tag = 'Material', header_lines=['#OpenParEMmaterials 1.0']):
        """
        Writes the nested material dictionary back to the original file format.
        """
        def write_block(obj, file, indent=0):
            indent_str = "   " * indent
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k == "name":
                        file.write(f"{indent_str}{k}={v}\n")
                    elif isinstance(v, dict):
                        file.write(f"{indent_str}{k}\n")
                        write_block(v, file, indent + 1)
                        file.write(f"{indent_str}End{k}\n")
                    elif isinstance(v, list):
                        for item in v:
                            file.write(f"{indent_str}{k}\n")
                            write_block(item, file, indent + 1)
                            file.write(f"{indent_str}End{k}\n")
                    elif isinstance(v, str) and "\n" in v:
                        file.write(f"{indent_str}{k}\n")
                        for line in v.splitlines():
                            file.write(f"{indent_str}   {line}\n")
                        file.write(f"{indent_str}End{k}\n")
                    else:
                        file.write(f"{indent_str}{k}={v}\n")
            elif isinstance(obj, str):
                for line in obj.splitlines():
                    file.write(f"{indent_str}{line}\n")

        with open(material_file, 'w') as file:
            for item in header_lines:
                file.write(item + "\n")
            for mat in material_dict.values():
                file.write(start_tag +"\n")
                write_block(mat, file, 1)
                file.write("End" + start_tag + "\n\n")

if __name__ == "__main__":
    # Example usage
    project_file = 'monopole_antenna_fields.proj'
    output_project_file = 'monopole_antenna_fields2.proj'

    # Read and write project file
    pfio = ProjectFileIO()
    proj_file_dict = pfio.read_project_file(project_file)
    pfio.write_project_file(proj_file_dict, output_project_file)

    mfio = MaterialFileIO()
    material_file_dict = mfio.read_material_file('global_materials.txt')
    mfio.write_material_file(material_file_dict, 'global_materials_out.txt')
    print(proj_file_dict)
    print(material_file_dict)