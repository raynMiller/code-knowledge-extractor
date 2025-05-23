# pykb: Python 知识库提取器

## 描述

`pykb` 是一个命令行工具，用于从 Python 项目中提取结构化信息。它解析 Python 源代码以识别全局变量、函数、类和方法，然后将这些数据输出到 JSON 文件中。这个结构化的知识库可用于代码分析、文档生成或其他 AI 驱动的开发任务。

## 功能特性

*   使用内置的 `ast` 模块解析 Python 源代码。
*   识别全局变量、函数、类和方法。
*   为每个识别出的单元提取关键详细信息：
    *   名称
    *   类型 (例如, "function", "class")
    *   起始和结束行号
    *   文档字符串
    *   函数/方法参数
    *   源代码片段
    *   相对文件路径
    *   基类 (对于类)
    *   所属类名 (对于方法)
*   将提取的信息输出到结构化的 JSON 文件中。
*   提供命令行界面 (CLI)，方便集成到工作流程中。
*   支持使用 glob 模式进行可定制的文件匹配。
*   允许排除特定的目录和文件模式。

## 安装

1.  **先决条件**:
    *   Python 3.7 或更高版本。

2.  **从源代码安装**:
    如果您有源代码 (例如，通过克隆仓库或下载存档文件)：
    ```bash
    # 导航到项目的根目录 (setup.py 所在的目录)
    # 例如，如果您克隆了它：
    # git clone https://your-repository-url/pykb.git
    # cd pykb
    
    pip install .
    ```
    这将安装 `pykb` 包，并使 `pykb` 命令行工具在您的环境中可用。

## 使用方法

`pykb` 工具从命令行运行。

### 基本语法

```bash
pykb <project_path> [options]
```

### 参数和选项

*   **`project_path`**: (必需) 您要分析的 Python 项目的目录路径。
*   **`-o OUTPUT_FILE`, `--output OUTPUT_FILE`**:
    保存生成的 JSON 知识库的路径。
    默认值：当前工作目录下的 `knowledge_base.json`。
*   **`-g GLOB_PATTERN`, `--glob GLOB_PATTERN`**:
    用于匹配 `project_path` 中要处理的文件的 glob 模式。
    默认值：`*.py` (处理所有 Python 文件)。
*   **`-e EXCLUDE_PATTERNS`, `--exclude EXCLUDE_PATTERNS`**:
    一个逗号分隔的目录名或文件模式字符串，用于从分析中排除。
    默认值：`venv,.env,.git,__pycache__,build,dist,docs,examples,tests,node_modules,*.egg-info`

### 示例

1.  **分析项目并将结果保存到默认的 `knowledge_base.json`**:
    此命令分析 `./my_python_project` 目录中的 Python 文件。
    ```bash
    pykb ./my_python_project
    ```

2.  **指定自定义输出文件名**:
    此命令分析项目并将输出保存到 `custom_kb.json`。
    ```bash
    pykb ./my_python_project -o custom_kb.json
    ```

3.  **仅分析特定文件并排除一个目录**:
    此命令仅分析 `utils` 子目录下的 Python 文件，并排除 `legacy_code` 目录。
    ```bash
    pykb ./my_awesome_lib -g "utils/*.py" -e "legacy_code,*.log"
    ```

## 输出格式

`pykb` 生成一个包含对象数组的 JSON 文件。每个对象代表一个提取出的知识单元 (例如，函数、类、方法或全局变量)。

每个单元的字段如下：

*   **`name`** (字符串): 变量、函数、类或方法的名称。
*   **`type`** (字符串): 单元的类型。可能的值包括：
    *   `"global_variable"`
    *   `"function"`
    *   `"class"`
    *   `"method"`
*   **`start_line`** (整数): 单元定义在其源文件中开始的行号。
*   **`end_line`** (整数): 单元定义在其源文件中结束的行号。
*   **`filepath`** (字符串): 包含此单元的源文件的相对路径，使用 `/`作为路径分隔符。
*   **`docstring`** (字符串 | null): 与单元关联的文档字符串 (如果有)。如果不存在文档字符串，则为 `null`。
*   **`source_code`** (字符串): 单元的原始源代码片段。
*   **`arguments`** (字符串数组, 可选): 对于函数和方法，这是其参数列表。默认值用 `...` 表示 (例如, `arg_name=...`)。示例: `["param1", "param2=...", "*args", "**kwargs"]`。
*   **`base_classes`** (字符串数组, 可选): 对于类，此列表显示其基类的名称。
*   **`class_name`** (字符串, 可选): 对于方法，此字段指示它们所属的类的名称。

### JSON 输出片段示例

输出是这些单元的扁平列表。在 JSON 中，方法不会嵌套在其类对象内，而是作为单独的条目列出，并通过 `class_name` 字段链接到其父类。

```json
[
  {
    "name": "MY_GLOBAL_VAR",
    "type": "global_variable",
    "start_line": 5,
    "end_line": 5,
    "filepath": "config/settings.py",
    "docstring": null,
    "source_code": "MY_GLOBAL_VAR = \"some_value\"",
  },
  {
    "name": "helper_function",
    "type": "function",
    "start_line": 10,
    "end_line": 25,
    "filepath": "utils/helpers.py",
    "arguments": ["item", "options=..."],
    "docstring": "此函数有助于执行特定任务。\n\n它有一个多行文档字符串。",
    "source_code": "def helper_function(item, options=None):\n    \"\"\"此函数有助于执行特定任务。\n\n    它有一个多行文档字符串。\"\"\"\n    # ... 函数体 ...\n    return result"
  },
  {
    "name": "AdvancedService",
    "type": "class",
    "start_line": 15,
    "end_line": 50,
    "filepath": "services/advanced.py",
    "base_classes": ["BaseService", "Mixins.Auth"],
    "docstring": "一个提供高级服务的类。",
    "source_code": "class AdvancedService(BaseService, Mixins.Auth):\n    \"\"\"一个提供高级服务的类。\"\"\"\n    # ... 类主体 ...\n"
  },
  {
    "name": "__init__",
    "type": "method",
    "start_line": 18,
    "end_line": 22,
    "filepath": "services/advanced.py",
    "arguments": ["self", "config_path"],
    "docstring": "初始化 AdvancedService。",
    "source_code": "    def __init__(self, config_path):\n        \"\"\"初始化 AdvancedService。\"\"\"\n        self.config = load_config(config_path)",
    "class_name": "AdvancedService"
  },
  {
    "name": "process_data",
    "type": "method",
    "start_line": 25,
    "end_line": 48,
    "filepath": "services/advanced.py",
    "arguments": ["self", "data", "force_recompute=..."],
    "docstring": "使用高级逻辑处理给定数据。",
    "source_code": "    def process_data(self, data, force_recompute=False):\n        \"\"\"使用高级逻辑处理给定数据。\"\"\"\n        # ... 方法体 ...\n        return processed_output",
    "class_name": "AdvancedService"
  }
]
```

## 许可证

本项目根据 MIT 许可证授权。有关详细信息，请参阅 `setup.py` 文件 (或可用的单独 `LICENSE` 文件)。

## 贡献

欢迎贡献！请随时提交拉取请求或针对错误、功能请求或改进提出问题。
(此处可添加更多详细信息，例如，开发设置、运行测试)
