---
name: open-vscode
description: Open files or directories in VSCode from Claude Code
---

# Open in VSCode Skill

Opens specified files or directories in Visual Studio Code.

## Usage

When the user asks to:
- "用 VSCode 開啟 X"
- "在 VSCode 中打開 X"
- "open X in VSCode"
- "vscode X"

Execute the VSCode command to open the specified file(s) or directory.

## Implementation

Use the Bash tool to execute:

```bash
code <file_or_directory_path>
```

### Options

- `code <path>` - Open file/directory in the most recently used window
- `code -n <path>` - Open in a new window
- `code -r <path>` - Reuse the current window
- `code -a <path>` - Add folder to the last active window

### Multiple Files

To open multiple files:
```bash
code file1.md file2.json file3.txt
```

### Open Current Directory

```bash
code .
```

## Examples

User: "用 VSCode 開啟 package.json"
Assistant: 執行 `code package.json`

User: "在 VSCode 中打開當前目錄"
Assistant: 執行 `code .`

User: "用 VSCode 開啟 src/ 資料夾"
Assistant: 執行 `code src/`

## Notes

- Always use absolute paths or verify the current working directory
- Confirm the file exists before attempting to open
- VSCode must be installed with the `code` command-line tool
