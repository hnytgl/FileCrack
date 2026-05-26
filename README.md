# FileCrack

FileCrack 是一个面向授权场景的常见加密文件密码恢复工具，支持导入字典路径、多线程尝试和多格式后端。适合找回自己遗忘的文件密码、企业内部合规恢复、取证实验环境验证等用途。

请只对你拥有所有权或明确授权的文件使用本工具。

## 支持格式

| 格式 | 支持方式 | 说明 |
| --- | --- | --- |
| zip | 内置支持 | 标准 ZipCrypto 可直接使用；AES ZIP 建议安装完整依赖 |
| rar | 可选依赖 | 需要 `rarfile`，部分系统还需要 unrar/bsdtar/unar |
| 7z | 可选依赖 | 需要 `py7zr` |
| doc/docx | 可选依赖 | 需要 `msoffcrypto-tool` |
| wps/wpt | 可选依赖 | 按 Office/WPS 加密容器尝试，需要 `msoffcrypto-tool` |
| xls/xlsx | 可选依赖 | 需要 `msoffcrypto-tool` |
| et/el | 可选依赖 | WPS 表格格式，按 Office/WPS 加密容器尝试 |
| ppt/pptx | 可选依赖 | 需要 `msoffcrypto-tool` |
| dps | 可选依赖 | WPS 演示格式，按 Office/WPS 加密容器尝试 |
| pdf | 可选依赖 | 需要 `pikepdf` |

## 安装

基础安装：

```bash
pip install -e .
```

完整格式支持：

```bash
pip install -e ".[full]"
```

如果只需要 ZIP，基础安装即可。RAR、7Z、PDF、Office/WPS 系列建议安装完整依赖。

## 快速使用

准备字典文件，每行一个候选密码：

```text
123456
password
my-secret
```

开始恢复：

```bash
filecrack ./locked.zip -w ./dict.txt
```

指定线程数：

```bash
filecrack ./locked.7z -w ./dict.txt -t 8
```

强制指定格式：

```bash
filecrack ./unknown.bin -w ./dict.txt --format zip
```

脚本中只输出密码：

```bash
filecrack ./locked.pdf -w ./dict.txt --quiet
```

Windows PowerShell 示例：

```powershell
filecrack .\locked.xlsx -w .\dict.txt -t 8
```

## 参数说明

| 参数 | 说明 |
| --- | --- |
| `target` | 需要恢复密码的文件路径 |
| `-w, --wordlist` | 字典路径，每行一个候选密码 |
| `-t, --threads` | 线程数，默认使用 CPU 核心数 |
| `--encoding` | 字典编码，默认 `utf-8` |
| `--format` | 强制指定格式，例如 `zip`、`rar`、`7z`、`pdf`、`docx` |
| `--chunk-size` | 每个线程任务批量尝试的密码数量，默认 `512` |
| `--quiet` | 只输出找到的密码 |

## 速度和准确率

- 工具使用多线程批量调度，适合 I/O 型和部分库释放 GIL 的格式后端。
- 准确率取决于格式后端能否正确验证密码，以及字典中是否包含正确密码。
- ZIP、7Z、RAR、PDF、Office/WPS 的加密算法差异很大，实际速度会明显不同。
- 未加密文件不会被误报为“第一个密码正确”。

## 退出码

- `0`：找到密码
- `1`：未找到密码
- `2`：依赖缺失或后端错误

## 开发测试

```bash
pip install -e ".[test]"
python -m pytest
```

## 合规声明

FileCrack 只用于授权文件密码恢复和安全测试。不要将它用于未授权访问、绕过他人数据保护或任何违法行为。作者不对滥用造成的后果负责。

## 许可证

MIT
