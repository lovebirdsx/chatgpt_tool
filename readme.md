# Chatgpt工具

可以用来解释和审查代码的工具，支持大文件。

## 要求

- Windows
- Python 3.10

## 安装

- `pip install -r requirements.txt`

## 使用

### 配置chatgpt

在用户目录下，创建`.chatgpt_tool`文件夹，然后在里面创建`config.json`文件，内容类似于：

其中：

- `proxy`是代理，根据你的代理来设定，类似于：socks5h://localhost:38888
- `model`是模型，推荐`gpt-3.5-turbo`
- `access_token`是你的令牌，可以在[这里](https://chat.openai.com/api/auth/session)获得

```json
{
    "proxy": "your_proxy",
    "model": "gpt-3.5-turbo",
    "access_token": "your_access_token"
}
```

### 运行

代码解释：`python code_explain.py`
代码审查：`python code_reviewer.py`

执行后会有特定的命令行提示，按照提示操作即可。

## 其它

- [接入vscode](doc/vscode.md)
