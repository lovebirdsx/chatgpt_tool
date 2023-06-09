# ChatGPT Tool

[中文](./readme_zh.md)

- A tool for explaining and reviewing code, which supports large files.
- ChatGPT command-line tool, which can be called via command-line to utilize ChatGPT.

## Requirements

- Windows
- Python 3.10

## Installation

- `pip install -r requirements.txt`

## Usage

### Configuring ChatGPT

Create a `.chatgpt_tool` folder in your user directory and create a `config.json` file inside it with content like this:

```json
{
    "model": "text-davinci-002-render-sha",
    "access_token": "your_access_token",
    "export_dir": "your_export_dir",
    "language": "chinese"
}
```

where:

- `model` is the model to use, default to `text-davinci-002-render-sha`.
- `access_token` is your token, which can be obtained from [here](https://chat.openai.com/api/auth/session).
- `export_dir` is the directory to export the conversations.
- `language` is the language to do code review and explanation

Additionally, environment variables can be supported, like: `"export_dir": ${CHATGPT_EXPORT_DIR}`

### Running

- Code explanation: `python code_explainer.py -h`
- Code review: `python code_reviewer.py -h`
- Command-line tool: `python cli.py -h` We recommend using the Windows Terminal, which can output more user-friendly interfaces and colors.

After executing the above commands, you will see specific command-line prompts, which can be followed to continue.

## Others

- [Integration with VS Code](./vscode.md)