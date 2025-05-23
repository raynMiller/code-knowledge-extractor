import unittest
from pykb.parser import parse_code, _get_source_segment, _parse_arguments # Allow testing helper functions if needed

class TestParser(unittest.TestCase):

    def test_empty_string(self):
        self.assertEqual(parse_code(""), [])

    def test_no_definitions(self):
        code = "print('hello')\n# This is a comment\n1 + 2 # Just an expression"
        self.assertEqual(parse_code(code), [])

    def test_global_variable_simple(self):
        code = "x = 10"
        expected = [{
            "name": "x",
            "type": "global_variable",
            "start_line": 1,
            "end_line": 1,
            "source_code": "x = 10",
            "docstring": None
        }]
        results = parse_code(code)
        self.assertEqual(len(results), 1)
        self.assertDictEqual(results[0], expected[0])

    def test_global_variable_multiline(self):
        code = "my_list = [\n    1, 2, 3,\n    4, 5, 6\n]"
        results = parse_code(code)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'my_list')
        self.assertEqual(results[0]['type'], 'global_variable')
        self.assertEqual(results[0]['start_line'], 1)
        self.assertEqual(results[0]['end_line'], 4) # AST node covers the whole assignment
        self.assertEqual(results[0]['source_code'], code)

    def test_global_variable_annotated(self):
        code = "y: int = 20"
        expected = [{
            "name": "y",
            "type": "global_variable",
            "start_line": 1,
            "end_line": 1,
            "source_code": "y: int = 20",
            "docstring": None
        }]
        results = parse_code(code)
        self.assertEqual(len(results), 1)
        self.assertDictEqual(results[0], expected[0])
        
    def test_global_variable_multi_target(self):
        code = "a = b = 30"
        results = parse_code(code)
        self.assertEqual(len(results), 2)
        self.assertTrue(any(r['name'] == 'a' and r['type'] == 'global_variable' for r in results))
        self.assertTrue(any(r['name'] == 'b' and r['type'] == 'global_variable' for r in results))
        for r in results:
            self.assertEqual(r['start_line'], 1)
            self.assertEqual(r['end_line'], 1)
            self.assertEqual(r['source_code'], "a = b = 30")


    def test_function_definition_simple_no_doc(self):
        code = "def greet():\n    print('Hello')"
        expected = {
            "name": "greet",
            "type": "function",
            "start_line": 1,
            "end_line": 2,
            "arguments": [],
            "docstring": None,
            "source_code": code
        }
        results = parse_code(code)
        self.assertEqual(len(results), 1)
        self.assertDictEqual(results[0], expected)

    def test_function_definition_with_docstring(self):
        code = "def add(a, b):\n    \"\"\"Adds two numbers.\"\"\"\n    return a + b"
        expected = {
            "name": "add",
            "type": "function",
            "start_line": 1,
            "end_line": 3,
            "arguments": ["a", "b"],
            "docstring": "Adds two numbers.",
            "source_code": code
        }
        results = parse_code(code)
        self.assertEqual(len(results), 1)
        self.assertDictEqual(results[0], expected)

    def test_function_arguments(self):
        code = "def func(p1, p2='default', *args, p3_kw, p4_kw='dkw', **kwargs):\n    pass"
        # _parse_arguments in parser.py simplifies defaults to "..."
        # Keyword-only args without defaults should not get "=..."
        expected_args = ["p1", "p2=...", "*args", "p3_kw", "p4_kw=...", "**kwargs"]
        results = parse_code(code)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'func')
        self.assertListEqual(results[0]['arguments'], expected_args)

    def test_class_definition_simple_no_doc(self):
        code = "class MyClass:\n    pass"
        expected = {
            "name": "MyClass",
            "type": "class",
            "start_line": 1,
            "end_line": 2,
            "base_classes": [],
            "docstring": None,
            "source_code": code
        }
        results = parse_code(code)
        # parse_code might also pick up class variables if any, so filter for class
        class_results = [r for r in results if r['type'] == 'class']
        self.assertEqual(len(class_results), 1)
        self.assertDictEqual(class_results[0], expected)


    def test_class_definition_with_docstring_and_bases(self):
        code = "class ChildClass(Parent1, Parent2):\n    \"\"\"Inherits from Parent1 and Parent2.\"\"\"\n    attr = 1"
        expected_class = {
            "name": "ChildClass",
            "type": "class",
            "start_line": 1,
            "end_line": 3,
            "base_classes": ["Parent1", "Parent2"],
            "docstring": "Inherits from Parent1 and Parent2.",
            "source_code": code 
        }
        # The CLASS_VAR `attr = 1` will be captured by current logic as a global_variable if not handled
        # The current parser.py does not capture class variables as separate items, only their presence in source_code.
        # If it did, the test would need to account for it. Let's assume it doesn't for now.
        
        results = parse_code(code)
        class_result = next(item for item in results if item["type"] == "class")
        
        self.assertEqual(class_result["name"], expected_class["name"])
        self.assertEqual(class_result["type"], expected_class["type"])
        self.assertEqual(class_result["start_line"], expected_class["start_line"])
        self.assertEqual(class_result["end_line"], expected_class["end_line"])
        self.assertListEqual(class_result["base_classes"], expected_class["base_classes"])
        self.assertEqual(class_result["docstring"], expected_class["docstring"])
        self.assertEqual(class_result["source_code"], expected_class["source_code"])


    def test_class_with_method(self):
        code = "class Calculator:\n    def add(self, x, y):\n        \"\"\"Adds x and y.\"\"\"\n        return x + y"
        results = parse_code(code)
        self.assertEqual(len(results), 2) # Class and method

        class_res = next(r for r in results if r['type'] == 'class')
        method_res = next(r for r in results if r['type'] == 'method')

        expected_class = {
            "name": "Calculator", "type": "class", "start_line": 1, "end_line": 4,
            "base_classes": [], "docstring": None, "source_code": code
        }
        expected_method = {
            "name": "add", "type": "method", "class_name": "Calculator",
            "start_line": 2, "end_line": 4, "arguments": ["self", "x", "y"],
            "docstring": "Adds x and y.",
            "source_code": "    def add(self, x, y):\n        \"\"\"Adds x and y.\"\"\"\n        return x + y" # Source segment for method
        }
        
        self.assertDictEqual(class_res, expected_class)
        self.assertDictEqual(method_res, expected_method)


    def test_line_numbers_multiline_function(self):
        code = "\n\ndef my_func():\n    # comment\n    x = 1\n    y = 2\n    return x + y\n"
        # Expected: line 3 to 7 (inclusive by AST nodes)
        results = parse_code(code)
        self.assertEqual(len(results), 1)
        func_res = results[0]
        self.assertEqual(func_res['name'], 'my_func')
        self.assertEqual(func_res['start_line'], 3)
        self.assertEqual(func_res['end_line'], 7)
        self.assertEqual(func_res['source_code'], "def my_func():\n    # comment\n    x = 1\n    y = 2\n    return x + y")

    def test_complex_example(self):
        code = """
g_var = "global"
g_var_annotated: str = "global_annotated"

class MyClass:
    \"\"\"A sample class.\"\"\"
    cls_attr = 100

    def __init__(self, name):
        \"\"\"Constructor docstring.\"\"\"
        self.name = name

    def get_name(self):
        # A method comment
        \"\"\"Returns the name.\"\"\"
        return self.name

def another_func(param1, param2="val"):
    \"\"\"This is another function.\"\"\"
    local = param1
    return local
"""
        results = parse_code(code)
        # Expected: g_var, g_var_annotated, MyClass, __init__, get_name, another_func
        # Class attributes like cls_attr are not extracted as separate items by current parser.
        self.assertEqual(len(results), 6)

        # Line numbers based on the string starting with a newline, then content.
        # Line 1: (blank)
        # Line 2: g_var = "global"
        # Line 3: g_var_annotated: str = "global_annotated"
        # Line 4: (blank)
        # Line 5: class MyClass:
        # Line 9:     def __init__(self, name):
        # Line 11:        self.name = name
        # Line 13:    def get_name(self):
        # Line 16:        return self.name (method body ends here, node might include trailing blank line)
        # Line 17: (blank)
        # Line 18: def another_func(param1, param2="val"):
        # Line 21:    return local

        g_var_res = next(r for r in results if r['name'] == 'g_var')
        self.assertEqual(g_var_res['type'], 'global_variable')
        self.assertEqual(g_var_res['start_line'], 2) # Was 2
        self.assertEqual(g_var_res['end_line'], 2)   # Was 2

        g_var_annotated_res = next(r for r in results if r['name'] == 'g_var_annotated')
        self.assertEqual(g_var_annotated_res['type'], 'global_variable')
        self.assertEqual(g_var_annotated_res['start_line'], 3) # Was 3
        self.assertEqual(g_var_annotated_res['end_line'], 3)   # Was 3
        
        class_res = next(r for r in results if r['name'] == 'MyClass')
        self.assertEqual(class_res['type'], 'class')
        self.assertEqual(class_res['docstring'], "A sample class.")
        self.assertEqual(class_res['start_line'], 5) # Was 5
        self.assertEqual(class_res['end_line'], 16)  # Was 16 (correctly includes method up to its end)

        init_res = next(r for r in results if r['name'] == '__init__')
        self.assertEqual(init_res['type'], 'method')
        self.assertEqual(init_res['class_name'], 'MyClass')
        self.assertEqual(init_res['docstring'], "Constructor docstring.")
        self.assertEqual(init_res['start_line'], 9)  # Was 9
        self.assertEqual(init_res['end_line'], 11) # Was 11
        self.assertListEqual(init_res['arguments'], ['self', 'name'])

        get_name_res = next(r for r in results if r['name'] == 'get_name')
        self.assertEqual(get_name_res['type'], 'method')
        self.assertEqual(get_name_res['class_name'], 'MyClass')
        self.assertEqual(get_name_res['docstring'], "Returns the name.")
        self.assertEqual(get_name_res['start_line'], 13) # Was 13
        self.assertEqual(get_name_res['end_line'], 16)   # Was 16
        self.assertListEqual(get_name_res['arguments'], ['self'])

        another_func_res = next(r for r in results if r['name'] == 'another_func')
        self.assertEqual(another_func_res['type'], 'function')
        self.assertEqual(another_func_res['docstring'], "This is another function.")
        self.assertEqual(another_func_res['start_line'], 18) # Was 17, now 18
        self.assertEqual(another_func_res['end_line'], 21)   # Was 20, now 21
        self.assertListEqual(another_func_res['arguments'], ['param1', 'param2=...'])

    def test_docstrings_variations(self):
        code_no_doc = "def func_no_doc(): pass"
        code_with_doc = "def func_with_doc():\n    \"\"\"My doc.\"\"\"\n    pass"
        
        res_no_doc = parse_code(code_no_doc)[0]
        self.assertIsNone(res_no_doc['docstring'])

        res_with_doc = parse_code(code_with_doc)[0]
        self.assertEqual(res_with_doc['docstring'], "My doc.")

    def test_parse_code_with_imports(self):
        code = "import os\n\nfrom sys import argv\n\nx = 10"
        results = parse_code(code)
        # Imports should not be captured as knowledge units by the current parser logic
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'x')
        self.assertEqual(results[0]['type'], 'global_variable')

    def test_parse_code_with_comments_only(self):
        code = "# This is a comment\n# And another one"
        results = parse_code(code)
        self.assertEqual(results, [])

    def test_class_variable_not_extracted_separately(self):
        # Based on current parser.py, class variables are part of the class's source code
        # but not extracted as separate "global_variable" or "class_variable" types.
        code = "class MyData:\n    count = 0\n    data_list = []"
        results = parse_code(code)
        self.assertEqual(len(results), 1) # Only the class itself
        self.assertEqual(results[0]['type'], 'class')
        self.assertEqual(results[0]['name'], 'MyData')
        self.assertIn("count = 0", results[0]['source_code'])
        self.assertIn("data_list = []", results[0]['source_code'])

if __name__ == '__main__':
    unittest.main()
