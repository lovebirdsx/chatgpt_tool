# Using the Tool with VS Code

## Running the Corresponding Script via Task

- In VS Code, press cmd+shift+p, and run `Tasks: Open User Tasks`.
- Add the following configuration and replace the corresponding path of the py file with your local path.

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

## Running Task via Shortcut

- In VS Code, press cmd+shift+p, and run `Preferences: Open Keyboard Shortcuts(JSON)`.
- Add shortcuts like the following, and you can run the corresponding Task via shortcuts.

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