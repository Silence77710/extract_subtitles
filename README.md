# YouTube 字幕提取器

这是一个基于 yt-dlp 的 YouTube 字幕下载工具，可以下载 YouTube 视频的英文字幕并发送到 Coze 工作流进行进一步处理。

## 功能特性

1. 通过 yt-dlp 下载 YouTube 字幕
2. 提供 RESTful API 接口接收 YouTube URL
3. 自动保存字幕文件到本地
4. 将字幕内容发送到 Coze 工作流
5. 支持身份验证（通过浏览器 cookies）
6. 字幕文本清洗功能（去除时间戳、元信息等）

## 安装依赖

在使用之前，请确保安装了所需的依赖项：

```bash
# 使用自动化安装脚本（推荐）
./install.sh

# 或者手动安装步骤：
# 1. 安装 yt-dlp
brew install yt-dlp

# 2. 创建虚拟环境
python3 -m venv venv

# 3. 激活虚拟环境
source venv/bin/activate

# 4. 安装 Python 依赖
pip install -r requirements.txt
```

## Coze 工作流配置

要将字幕内容发送到 Coze 工作流，需要配置工作流 ID 和访问令牌：

1. 复制配置文件模板：
   ```bash
   cp coze_config.json.example coze_config.json
   ```

2. 编辑 [coze_config.json](file:///Users/jackmac/Desktop/git_project/Python_dir/extract_subtitles/coze_config.json) 文件，填入您的 Coze 工作流信息：
   ```json
   {
     "workflow_id": "your_actual_workflow_id",
     "token": "your_actual_token",
     "api_base_url": "https://api.coze.cn/v1"
   }
   ```

或者，您也可以通过设置环境变量来配置：
```bash
export COZE_WORKFLOW_ID=your_workflow_id
export COZE_TOKEN=your_token
export COZE_API_BASE_URL=https://api.coze.cn/v1
```

## 测试 Coze 连接

如果遇到连接问题，可以使用测试脚本验证配置：

```bash
source venv/bin/activate
python test_coze.py
```

## 使用方法

### 方法一：使用启动脚本（推荐）

```bash
# 启动 Web 服务
./start_server.py

# 或者带参数运行（命令行模式）
./start_server.py https://www.youtube.com/watch?v=xxxxxxxxxxx en
```

### 方法二：手动激活环境后运行

```bash
# 激活虚拟环境
source venv/bin/activate

# 启动 Web 服务
python main.py

# 或者命令行模式
python main.py https://www.youtube.com/watch?v=xxxxxxxxxxx en
```

### 方法三：直接运行（需要确保依赖已安装）

```bash
python main.py
```

启动后可以通过以下 API 端点访问：

- `POST /download-subtitle` - 下载字幕
- `GET /health` - 健康检查

#### 下载字幕 API

发送 POST 请求到 `/download-subtitle`：

```json
{
  "url": "https://www.youtube.com/watch?v=xxxxxxxxxxx",
  "lang": "en",
  "browser": "chrome",
  "clean_text": true,
  "send_to_coze": true
}
```

参数说明：
- `url`: YouTube 视频地址（必需）
- `lang`: 字幕语言代码，默认为 "en"（可选）
- `browser`: 浏览器名称，用于获取 cookies，支持 "chrome", "firefox", "safari", "edge"（可选）
- `cookies_file`: cookies 文件路径（可选）
- `clean_text`: 是否清洗文本，默认为 true（可选）
- `send_to_coze`: 是否发送到 Coze 工作流，默认为 true（可选）
- `workflow_id`: Coze 工作流 ID（可选，优先级高于配置文件）
- `token`: Coze 访问令牌（可选，优先级高于配置文件）

## 字幕清洗规则

字幕清洗功能会按以下规则处理文本：

1. 删除所有时间戳行（如 00:00:00.000 --> 00:00:00.000）
2. 删除 WEBVTT、Kind、Language 等元信息
3. 删除空行
4. 删除字幕中的 HTML 实体（如 &nbsp;）
5. 保留原始英文内容，不会改写、总结或翻译
6. 将同一句被拆分在多行的字幕合并为自然句子
7. 最终输出为「纯英文连续文本」

## 解决身份验证问题

当遇到身份验证错误时，可以采用以下几种方法之一：

### 方法1：使用浏览器 cookies（推荐）

在请求中添加 `browser` 参数：
```json
{
  "url": "https://www.youtube.com/watch?v=xxxxxxxxxxx",
  "browser": "chrome"
}
```

支持的浏览器：
- Chrome: `"chrome"`
- Firefox: `"firefox"`
- Safari: `"safari"`
- Edge: `"edge"`

### 方法2：导出 cookies 文件

1. 使用浏览器扩展（如 "Get cookies.txt"）导出 YouTube 的 cookies
2. 将 cookies 文件保存到项目目录下的 [cookies](file:///Users/jackmac/Desktop/git_project/Python_dir/extract_subtitles/cookies) 文件夹中
3. 在请求中添加 `cookies_file` 参数：
```json
{
  "url": "https://www.youtube.com/watch?v=xxxxxxxxxxx",
  "cookies_file": "cookies/youtube_cookies.txt"
}
```

## 常见问题排查

### 1. 网络请求错误
如果出现 `Expecting value: line 1 column 1 (char 0)` 错误，可能是以下原因：
- Coze API 地址配置错误
- 网络连接问题
- 无效的工作流 ID 或令牌
- Coze API 服务暂时不可用

解决方法：
1. 检查 [coze_config.json](file:///Users/jackmac/Desktop/git_project/Python_dir/extract_subtitles/coze_config.json) 中的配置是否正确
2. 使用 [test_coze.py](file:///Users/jackmac/Desktop/git_project/Python_dir/extract_subtitles/test_coze.py) 脚本测试连接
3. 确保网络连接正常
4. 验证工作流 ID 和令牌是否有效

### 2. 身份验证错误
如果出现 YouTube 身份验证相关的错误：
- 尝试使用 `browser` 参数
- 导出 cookies 文件并使用 `cookies_file` 参数

## 关于使用注意事项

### 1. 关于 yt-dlp 依赖
每个使用此工具的人都需要安装 yt-dlp，有几种方式：
- 使用 Homebrew 安装（推荐）：`brew install yt-dlp`
- 使用 pip 安装：`pip install yt-dlp`

### 2. 关于网络访问
如果遇到网络问题可能需要：
- 确保可以正常访问 YouTube
- 必要时使用代理或 VPN

### 3. 关于登录验证
某些 YouTube 视频可能需要登录才能访问：
- 可以使用 `--cookies-from-browser` 参数从浏览器获取认证信息
- 或者手动导出 cookies 文件并使用 `--cookies` 参数

### 4. 如何简化用户使用
为了更方便地使用该工具，建议：
1. 编写脚本自动安装所有依赖
2. 提供图形界面版本
3. 支持批量处理多个视频
4. 添加配置文件支持常用选项

## 目录结构

- `main.py`: 主程序文件
- `config.py`: 配置文件
- `start_server.py`: 启动脚本（自动激活虚拟环境）
- `subtitles/`: 存储下载的字幕文件
- `cookies/`: 存储 cookies 文件
- `requirements.txt`: Python 依赖包列表
- `coze_config.json.example`: Coze 配置文件模板
- `test_coze.py`: Coze 连接测试脚本
- `install.sh`: 自动化安装脚本
- `README.md`: 说明文档

## 许可证

MIT License