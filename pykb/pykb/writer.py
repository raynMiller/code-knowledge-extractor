import json
import os # For testing

def write_knowledge_base(knowledge_data, output_filepath):
    """
    Writes the extracted knowledge data to a JSON file.

    Args:
        knowledge_data (list): A list of dictionaries, where each dictionary
                               represents an extracted knowledge unit.
        output_filepath (str): The path to the file where the JSON output
                               should be saved.
    """
    try:
        with open(output_filepath, 'w', encoding='utf-8') as f:
            json.dump(knowledge_data, f, indent=4, ensure_ascii=False)
        print(f"Knowledge base successfully written to {output_filepath}")
    except IOError as e:
        print(f"Error writing knowledge base to {output_filepath}: {e}")
    except TypeError as e:
        print(f"Error serializing knowledge data to JSON: {e}")


if __name__ == '__main__':
    # Example data (similar to what parser.py would produce)
    sample_data = [
        {
            "name": "my_function",
            "type": "function",
            "start_line": 1,
            "end_line": 3,
            "arguments": ["a", "b=None"],
            "docstring": "This is a test function.",
            "source_code": "def my_function(a, b=None):\n    pass"
        },
        {
            "name": "MyClass",
            "type": "class",
            "start_line": 5,
            "end_line": 8,
            "base_classes": [],
            "docstring": "This is a test class.",
            "source_code": "class MyClass:\n    def __init__(self):\n        pass"
        },
        {
            "name": "another_function",
            "type": "function",
            "start_line": 10,
            "end_line": 12,
            "arguments": [],
            "docstring": None, # Test case with None docstring
            "source_code": "def another_function():\n    return True"
        }
    ]
    
    test_output_dir = "test_writer_output"
    os.makedirs(test_output_dir, exist_ok=True)
    test_output_file = os.path.join(test_output_dir, "test_kb.json")
    
    print(f"Attempting to write to: {test_output_file}")
    write_knowledge_base(sample_data, test_output_file)
    
    # Verify content
    if os.path.exists(test_output_file):
        try:
            with open(test_output_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"\n--- Content of {test_output_file} ---")
                print(content)
                print("--- End of content ---")
            # Basic validation of JSON structure
            with open(test_output_file, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
                if isinstance(loaded_data, list) and len(loaded_data) == len(sample_data):
                    print("JSON structure seems valid.")
                else:
                    print("JSON structure validation failed.")

        except Exception as e:
            print(f"Error during verification: {e}")
        finally:
            # Clean up the test file and directory
            try:
                os.remove(test_output_file)
                os.rmdir(test_output_dir)
                print(f"Cleaned up {test_output_file} and {test_output_dir}")
            except OSError as e:
                print(f"Error during cleanup: {e}")
    else:
        print(f"Test output file {test_output_file} was not created.")

    # Test IOError
    print("\nTesting IOError (e.g., invalid path):")
    invalid_output_file = "/non_existent_dir/test_kb.json"
    write_knowledge_base(sample_data, invalid_output_file)

    # Test with empty data
    print("\nTesting with empty knowledge data:")
    empty_data_output_file = os.path.join(test_output_dir, "empty_kb.json")
    # Recreate dir for this test if it was removed or not created
    os.makedirs(test_output_dir, exist_ok=True) 
    write_knowledge_base([], empty_data_output_file)
    if os.path.exists(empty_data_output_file):
        with open(empty_data_output_file, 'r') as f:
            print(f"Content of empty_kb.json: {f.read()}")
        os.remove(empty_data_output_file)
        print(f"Cleaned up {empty_data_output_file}")
    
    # Final cleanup of the directory if it still exists
    if os.path.exists(test_output_dir):
        try:
            os.rmdir(test_output_dir)
            print(f"Cleaned up directory {test_output_dir} at the end.")
        except OSError as e:
            # This might happen if files are still in it due to an error
            print(f"Could not remove {test_output_dir} at the end: {e}")
