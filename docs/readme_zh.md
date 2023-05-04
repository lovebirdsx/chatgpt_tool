# Chatgpt工具

[English](./readme.md)

- 可以用来解释和审查代码的工具，支持大文件
- ChatGPT命令行工具，可以通过命令行来调用ChatGPT

## 要求

- Windows
- Python 3.10

## 安装

- `pip install -r requirements.txt`

**注意**

由于通过access_token来调用网页版是非官方的做法，所以可能会出现访问不了的情况，一般可以通过如下方式来解决：
`python -m pip install --upgrade revChatGPT --isolated`
加入`--isolated`参数来解决可能出现的非官方软件源问题
具体请关注[这里](https://github.com/acheong08/ChatGPT)

## 使用

### 配置chatgpt

在用户目录下，创建`.chatgpt_tool`文件夹，然后在里面创建`config.json`文件，内容类似于：

```json
{
    "proxy": "your_proxy",
    "model": "gpt-3.5-turbo",
    "access_token": "your_access_token",
    "export_dir": "your_export_dir",
    "language": "chinese"
}
```

其中：

- `proxy`是代理，根据你的代理来设定，类似于：socks5h://localhost:38888
- `model`是模型，推荐`gpt-3.5-turbo`
- `access_token`是你的令牌，可以在[这里](https://chat.openai.com/api/auth/session)获得
- `export_dir`是导出对话的目录
- `language`是用来做代码审查和解释的语言


### 运行

- 代码解释：`python code_explainer.py -h`
- 代码审查：`python code_reviewer.py -h`
- 命令行工具：`python cli.py -h` 推荐使用Windows Terminal，可以输出更友好的界面和颜色

上面的指令在执行后会有特定的命令行提示，按照提示操作即可。

## 其它

- [接入vscode](./vscode_zh.md)
