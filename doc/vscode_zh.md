# VS Code下结合该工具的使用

## 通过Task来运行对应的脚本

- vscode中cmd+shift+p，运行`Tasks: Open User Tasks`
- 加入下面的配置，将对应的py文件路径改为本地的路径

``` json
{
    // See https://go.microsoft.com/fwlink/?LinkId=733558
    // for the documentation about the tasks.json format
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Explain Code",
            "command": "python",
            "args": ["your_path/src/code_explainer.py", "-c", "-f", "${file}"],
            "type": "process",
            "presentation": {
                "clear": true,
                "showReuseMessage": false
            }
        },
        {
            "label": "Review Code",
            "type": "process",
            "command": "python",
            "args": ["your_path/src/code_reviewer.py", "-f", "${file}"],
            "presentation": {
                "clear": true,
                "showReuseMessage": false
            }
        }
    ]
}
```

## Task通过快捷键运行

- vscode中cmd+shift+p，运行`Preferences: Open Keyboard Shortcuts(JSON)`
- 加入类似下面的快捷键，即可通过快捷键运行对应的Task

``` json
[
    {
        "key": "ctrl+alt+i",
        "command": "workbench.action.tasks.runTask",
        "args": "Explain Code"
    },
    {
        "key": "ctrl+alt+u",
        "command": "workbench.action.tasks.runTask",
        "args": "Review Code"
    }
]
```
