import ast

def _get_source_segment(source_code_lines, node):
    """
    Extracts the source code segment for a given AST node.
    """
    if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
        # AST line numbers are 1-indexed, list indices are 0-indexed
        return "\n".join(source_code_lines[node.lineno - 1:node.end_lineno])
    return None

def _parse_arguments(args_node):
    """
    Parses ast.arguments node to a list of strings.
    e.g., "a, b=None, *args, **kwargs"
    """
    args = []
    # Positional and keyword-only arguments
    for arg in args_node.posonlyargs + args_node.args:
        arg_name = arg.arg
        if arg.annotation:
            # ast.unparse is not available in 3.8, so we'll skip annotation for now
            # arg_name += f": {ast.unparse(arg.annotation)}"
            pass
        args.append(arg_name)

    # Default values
    # Defaults are applied from right to left
    num_defaults = len(args_node.defaults)
    for i, default in enumerate(args_node.defaults):
        # This is a bit tricky as ast.unparse is not in 3.8
        # For simplicity, we'll just indicate a default exists.
        # A more robust solution would be to slice the source code for the default value.
        arg_index = len(args_node.args) - num_defaults + i
        if arg_index < len(args_node.args): # Ensure it's a regular arg, not kwonly
             # A more robust way to get default value source:
             # default_value_source = _get_source_segment(source_code_lines, default)
             # args[arg_index] += f"={default_value_source}"
             # For now, just indicate a default exists if we can't easily get source
             args[arg_index] += "=..."


    if args_node.vararg:
        args.append(f"*{args_node.vararg.arg}")
    
    for i, kwarg in enumerate(args_node.kwonlyargs):
        arg_name = kwarg.arg
        if args_node.kw_defaults[i]:
            # default_value_source = _get_source_segment(source_code_lines, args_node.kw_defaults[i])
            # arg_name += f"={default_value_source}"
            arg_name += "=..." # Simplified
        args.append(arg_name)

    if args_node.kwarg:
        args.append(f"**{args_node.kwarg.arg}")
    return args

def parse_code(source_code_string):
    """
    Parses Python source code and extracts information about global variables,
    functions, classes, and methods.

    Args:
        source_code_string (str): The Python source code to parse.

    Returns:
        list: A list of dictionaries, where each dictionary represents an
              extracted unit (variable, function, class, or method).
    """
    if not source_code_string:
        return []

    source_code_lines = source_code_string.splitlines()
    parsed_ast = ast.parse(source_code_string)
    extracted_units = []

    for node in parsed_ast.body:
        if isinstance(node, ast.Assign):
            # Consider only simple global assignments (not attributes or subscripts)
            # For multiple targets, like x = y = 10, we'll record each.
            for target in node.targets:
                if isinstance(target, ast.Name):
                    unit = {
                        "name": target.id,
                        "type": "global_variable",
                        "start_line": node.lineno,
                        "end_line": node.end_lineno,
                        "source_code": _get_source_segment(source_code_lines, node),
                        "docstring": None # ast.get_docstring cannot be used on ast.Assign
                    }
                    extracted_units.append(unit)

        elif isinstance(node, ast.FunctionDef):
            unit = {
                "name": node.name,
                "type": "function",
                "start_line": node.lineno,
                "end_line": node.end_lineno,
                "arguments": _parse_arguments(node.args),
                "docstring": ast.get_docstring(node, clean=False),
                "source_code": _get_source_segment(source_code_lines, node)
            }
            extracted_units.append(unit)

        elif isinstance(node, ast.ClassDef):
            class_unit = {
                "name": node.name,
                "type": "class",
                "start_line": node.lineno,
                "end_line": node.end_lineno,
                "base_classes": [base.id for base in node.bases if isinstance(base, ast.Name)], # Simple names
                "docstring": ast.get_docstring(node, clean=False),
                "source_code": _get_source_segment(source_code_lines, node)
            }
            extracted_units.append(class_unit)

            # Extract methods within the class
            for method_node in node.body:
                if isinstance(method_node, ast.FunctionDef):
                    method_unit = {
                        "name": method_node.name,
                        "type": "method",
                        "class_name": node.name, # Add class context
                        "start_line": method_node.lineno,
                        "end_line": method_node.end_lineno,
                        "arguments": _parse_arguments(method_node.args),
                        "docstring": ast.get_docstring(method_node, clean=False),
                        "source_code": _get_source_segment(source_code_lines, method_node)
                    }
                    extracted_units.append(method_unit)
        
        # Also consider AnnAssign for global typed variables if needed
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.value is not None: # Ensure it's an assignment
                 unit = {
                        "name": node.target.id,
                        "type": "global_variable",
                        "start_line": node.lineno,
                        "end_line": node.end_lineno, # AnnAssign might not have end_lineno in older Pythons
                                                  # or when it's just a declaration.
                                                  # We'll rely on lineno for single-line AnnAssign.
                        "source_code": _get_source_segment(source_code_lines, node),
                        "docstring": None # Docstrings are not typically associated with AnnAssign
                    }
                 extracted_units.append(unit)


    return extracted_units

if __name__ == '__main__':
    # Example Usage:
    sample_code = """
x = 10 # A global variable
y: int = 20

'''Module level docstring, not captured by current logic for specific nodes.'''

class MyClass(Base1, Base2):
    \"\"\"This is a class docstring.\"\"\"
    CLASS_VAR = "class_variable"

    def __init__(self, param1, param2="default"):
        \"\"\"This is the constructor docstring.\"\"\"
        self.param1 = param1
        self.param2 = param2

    def my_method(self, arg1: int) -> str:
        \"\"\"This is a method docstring.
        With multiple lines.
        \"\"\"
        return f"Hello {arg1}"

def my_function(a, b=None, *args, **kwargs):
    \"\"\"This is a function docstring.
    It also has multiple lines.\"\"\"
    local_var = a + 1
    return local_var

# Another global variable
z = "hello" + \\
    " world"

# A function without a docstring
def no_doc_func():
    pass
    """
    
    parsed_items = parse_code(sample_code)
    for item in parsed_items:
        print(f"Type: {item['type']}, Name: {item['name']}")
        print(f"  Lines: {item['start_line']}-{item.get('end_line', item['start_line'])}")
        if "arguments" in item:
            print(f"  Arguments: {item['arguments']}")
        if "base_classes" in item:
            print(f"  Base Classes: {item['base_classes']}")
        if "class_name" in item:
            print(f"  In Class: {item['class_name']}")
        print(f"  Docstring: '{item['docstring']}'")
        # print(f"  Source Code:\n---\n{item['source_code']}\n---")
        print("-" * 20)

    empty_code_test = parse_code("")
    print(f"Empty code test: {empty_code_test}")

    no_defs_code = "print('hello')"
    no_defs_test = parse_code(no_defs_code)
    print(f"No defs test: {no_defs_test}")
    
    multiline_var_code = "my_list = [\n    1, 2, 3,\n    4, 5, 6\n]" # Corrected: removed double backslashes
    multiline_var_test = parse_code(multiline_var_code)
    print("Multiline var test:")
    for item in multiline_var_test:
        print(f"Type: {item['type']}, Name: {item['name']}")
        print(f"  Lines: {item['start_line']}-{item.get('end_line', item['start_line'])}")
        print(f"  Source Code:\n---\n{item['source_code']}\n---")
        print("-" * 20)

    assign_expr_code = "if (val := my_func()) > 0: print(val)" # Not a global variable, should not be picked up
    assign_expr_test = parse_code(assign_expr_code)
    print(f"Assignment expression test: {assign_expr_test}")

    multi_target_assign = "a = b = c = 100"
    multi_target_test = parse_code(multi_target_assign)
    print("Multi-target assignment test:")
    for item in multi_target_test:
        print(f"Type: {item['type']}, Name: {item['name']}")
        print(f"  Lines: {item['start_line']}-{item.get('end_line', item['start_line'])}")
        print(f"  Source Code:\n---\n{item['source_code']}\n---")

"""
Expected output structure (simplified for one function example):
{
  "name": "my_function",
  "type": "function",
  "start_line": 20,
  "end_line": 24,
  "arguments": ["a", "b=None", "*args", "**kwargs"],
  "docstring": "This is a function docstring.\\nIt also has multiple lines.",
  "source_code": "def my_function(a, b=None, *args, **kwargs):\\n    \"\"\"This is a function docstring.\\n    It also has multiple lines.\"\"\"\\n    local_var = a + 1\\n    return local_var"
}
"""
