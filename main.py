#!/usr/bin/env python3
"""
YouTube 字幕提取器
功能：
1. 通过 yt-dlp 下载 YouTube 字幕
2. 提供 RESTful API 接口接收 YouTube URL
3. 自动保存字幕文件到本地
4. 将字幕内容发送到 Coze 工作流
"""

import os
import subprocess
import sys
import json
import re
import requests
import traceback

try:
    from flask import Flask, request, jsonify, send_file, Response
    from flask_cors import CORS
except ImportError:
    print("错误: 找不到 Flask 模块。请确保已安装依赖:")
    print("1. 运行 ./install.sh 脚本，或")
    print("2. 手动安装: pip install flask flask-cors")
    sys.exit(1)

# 导入配置
from config import Config

app = Flask(__name__)
# 启用 CORS 支持，允许所有来源
CORS(app, resources={r"/*": {"origins": "*"}})

# 创建存储字幕的目录
SUBTITLES_DIR = Config.SUBTITLES_DIR
os.makedirs(SUBTITLES_DIR, exist_ok=True)

# 创建存储 cookies 的目录
COOKIES_DIR = Config.COOKIES_DIR
os.makedirs(COOKIES_DIR, exist_ok=True)

def clean_subtitle_content(content):
    """
    清洗字幕内容，按要求处理文本
    
    Args:
        content (str): 原始字幕内容
    
    Returns:
        str: 清洗后的文本
    """
    lines = content.split('\n')
    cleaned_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # 跳过空行
        if not line:
            i += 1
            continue
            
        # 跳过 WEBVTT 行
        if line.upper() == "WEBVTT":
            i += 1
            continue
            
        # 跳过 Kind, Language 等元信息行
        if re.match(r'^(Kind|Language):', line, re.IGNORECASE):
            i += 1
            continue
            
        # 跳过时间戳行
        if re.match(r'^\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}', line):
            i += 1
            continue
            
        # 处理字幕文本行
        # 收集连续的字幕文本行
        subtitle_text_lines = []
        while i < len(lines) and lines[i].strip() and not (
            lines[i].strip().upper() == "WEBVTT" or
            re.match(r'^(Kind|Language):', lines[i].strip(), re.IGNORECASE) or
            re.match(r'^\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}', lines[i].strip())
        ):
            # 处理当前行的HTML实体
            cleaned_line = lines[i].replace('&nbsp;', ' ')
            # 可以在这里添加更多HTML实体的处理
            subtitle_text_lines.append(cleaned_line.strip())
            i += 1
        
        # 合并收集到的字幕行
        if subtitle_text_lines:
            # 合并行并处理多余的空格
            merged_line = ' '.join(subtitle_text_lines)
            merged_line = re.sub(r'\s+', ' ', merged_line).strip()
            if merged_line:
                cleaned_lines.append(merged_line)
        
        # 不增加 i，因为内部循环已经处理过了
    
    # 用空格连接所有清洗后的行，形成最终的连续文本
    cleaned_text = ' '.join(cleaned_lines)
    
    # 最终清理多余的空格
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    
    return cleaned_text

def download_subtitle(url, lang='en', browser=None, cookies_file=None):
    """
    使用 yt-dlp 下载指定语言的字幕
    
    Args:
        url (str): YouTube 视频链接
        lang (str): 字幕语言，默认为 'en'
        browser (str): 浏览器名称，用于获取 cookies (如 'chrome', 'firefox', 'safari')
        cookies_file (str): cookies 文件路径
    
    Returns:
        str: 下载的字幕文件路径
    """
    try:
        # 构建 yt-dlp 命令基础部分
        cmd = [
            "yt-dlp",
            "--write-auto-sub",      # 写入自动翻译的字幕
            "--write-sub",           # 写入手动添加的字幕
            f"--sub-lang={lang}",    # 指定语言
            "--skip-download",       # 跳过视频下载
            "--sub-format=vtt",      # 指定字幕格式
            "-o", f"{SUBTITLES_DIR}/%(title)s.%(ext)s",  # 输出路径
        ]
        
        # 添加浏览器 cookies 参数
        if browser:
            cmd.extend(["--cookies-from-browser", browser])
        elif cookies_file and os.path.exists(cookies_file):
            cmd.extend(["--cookies", cookies_file])
        else:
            # 如果没有指定浏览器或 cookies 文件，则尝试默认浏览器
            # 注意：这可能会导致某些视频无法访问
            pass
            
        # 添加 URL
        cmd.append(url)
        
        print(f"执行命令: {' '.join(cmd)}")
        
        # 执行命令
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            error_msg = result.stderr.strip()
            # 检查是否是身份验证错误
            if "Sign in to confirm you're not a bot" in error_msg:
                raise Exception(
                    "需要身份验证才能访问此视频。\n"
                    "请提供浏览器信息或 cookies 文件。\n"
                    "支持的浏览器: chrome, firefox, safari, edge\n"
                    "或者导出 cookies 文件并提供路径。"
                )
            # 检查是否是浏览器 cookies 数据库未找到的错误
            if "could not find" in error_msg.lower() and "cookies database" in error_msg.lower():
                if browser:
                    raise Exception(
                        f"无法从浏览器 '{browser}' 获取 cookies。\n"
                        "浏览器 cookies 数据库未找到或无法访问。\n"
                        "建议解决方案：\n"
                        "1. 使用浏览器扩展（如 'Get cookies.txt'）导出 YouTube 的 cookies\n"
                        "2. 将 cookies 文件保存到项目的 cookies/ 目录\n"
                        "3. 在请求中使用 'cookies_file' 参数而不是 'browser' 参数\n"
                        f"原始错误: {error_msg}"
                    )
            raise Exception(f"下载失败: {error_msg}")
        
        # 查找下载的文件
        downloaded_files = []
        for file in os.listdir(SUBTITLES_DIR):
            if file.endswith(".vtt"):
                downloaded_files.append(os.path.join(SUBTITLES_DIR, file))
        
        if not downloaded_files:
            raise Exception("未找到下载的字幕文件")
        
        # 返回最新下载的文件
        latest_file = max(downloaded_files, key=os.path.getctime)
        return latest_file
        
    except Exception as e:
        raise Exception(f"下载字幕时出错: {str(e)}")

def send_to_coze_workflow(workflow_id, token, cleaned_text, file_name):
    """
    发送清洗后的文本到 Coze 工作流
    
    Args:
        workflow_id (str): Coze 工作流 ID
        token (str): Coze API Token
        cleaned_text (str): 清洗后的文本内容
        file_name (str): 字幕文件名
    
    Returns:
        dict: 工作流响应
    """
    try:
        # Coze API URL
        api_url = f"{Config.COZE_API_BASE_URL}"
        
        # 请求头
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 请求数据 - 根据您提供的格式调整
        payload = {
            "workflow_id": int(workflow_id),  # 确保是整数类型
            "parameters": {
                "subtitle": cleaned_text
            }
        }
        
        print(f"正在发送请求到 Coze API: {api_url}")
        print(f"请求头: {headers}")
        # 打印完整请求数据
        print(f"请求数据: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        
        # 发送 POST 请求到 Coze API
        response = requests.post(api_url, headers=headers, json=payload, timeout=200)
        
        print(f"Coze API 响应状态码: {response.status_code}")
        print(f"Coze API 响应头: {dict(response.headers)}")
        
        # 检查响应内容是否为空
        if not response.content:
            raise Exception("Coze API 返回空响应")
        
        # 尝试解析 JSON
        try:
            response_text = response.text
            print(f"Coze API 响应内容长度: {len(response_text)} 字符")
            
            # 检查响应是否为 JSON 格式
            if response.headers.get('Content-Type', '').startswith('application/json'):
                result = response.json()
                print(f"成功解析 JSON 响应，响应码: {result.get('code', 'N/A')}")
                return result
            else:
                raise Exception(f"Coze API 返回非 JSON 响应: {response_text[:200]}")
        except json.JSONDecodeError as je:
            raise Exception(f"Coze API 返回无效 JSON: {je}. 原始响应: {response.text[:200]}")
            
    except requests.exceptions.Timeout:
        raise Exception("Coze API 请求超时")
    except requests.exceptions.ConnectionError:
        raise Exception("Coze API 连接错误，请检查网络连接")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Coze API 网络请求错误: {str(e)}")
    except Exception as e:
        raise Exception(f"发送到 Coze 工作流出错: {str(e)}")

@app.route('/download-subtitle', methods=['POST'])
def handle_download_request():
    """
    处理下载字幕的请求
    """
    try:
        # 打印请求信息以便调试
        print(f"\n收到 /download-subtitle 请求")
        print(f"请求方法: {request.method}")
        print(f"Content-Type: {request.content_type}")
        
        data = request.json
        if data is None:
            print("警告: request.json 为 None，尝试解析原始数据")
            if request.data:
                try:
                    data = json.loads(request.data)
                except json.JSONDecodeError as e:
                    print(f"无法解析 JSON 数据: {e}")
                    return jsonify({"error": f"无效的 JSON 数据: {str(e)}"}), 400
            else:
                return jsonify({"error": "请求体为空"}), 400
        
        print(f"请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        url = data.get('url')
        lang = data.get('lang', 'en')
        browser = data.get('browser')  # 浏览器名称，如 'chrome', 'firefox'
        cookies_file = data.get('cookies_file')  # cookies 文件路径
        clean_text = data.get('clean_text', True)  # 是否清洗文本
        # Coze 配置（如果未在配置文件中设置）
        workflow_id = data.get('workflow_id', Config.COZE_WORKFLOW_ID)
        token = data.get('token', Config.COZE_TOKEN)
        send_to_coze = data.get('send_to_coze', True)  # 是否发送到 Coze
        
        if not url:
            return jsonify({"error": "缺少视频 URL"}), 400
        
        # 检查是否需要发送到 Coze 但没有配置信息
        if send_to_coze and not (workflow_id and token):
            return jsonify({
                "error": "未配置 Coze 工作流信息",
                "message": "请在配置文件中设置 Coze 工作流 ID 和 Token，或在请求中提供"
            }), 400
        
        # 下载字幕
        subtitle_file = download_subtitle(url, lang, browser, cookies_file)
        
        # 读取原始字幕内容
        with open(subtitle_file, 'r', encoding='utf-8') as f:
            subtitle_content = f.read()
        
        # 默认进行文本清洗
        cleaned_text = None
        if clean_text:
            cleaned_text = clean_subtitle_content(subtitle_content)
        
        result = {
            "status": "success",
            "subtitle_file": subtitle_file,
            "original_content": subtitle_content
        }
        
        if clean_text:
            result["cleaned_text"] = cleaned_text
        
        # 发送到 Coze 工作流
        coze_result = None
        markdown_file = None
        if send_to_coze:
            coze_response = send_to_coze_workflow(
                workflow_id, 
                token, 
                cleaned_text if clean_text else subtitle_content, 
                os.path.basename(subtitle_file)
            )
            
            # 生成 Markdown 文件
            if coze_response and 'data' in coze_response:
                coze_data = coze_response['data']
                # 提取 summary 字段
                summary_content = None
                if isinstance(coze_data, dict) and 'summary' in coze_data:
                    summary_content = coze_data['summary']
                elif isinstance(coze_data, str):
                    try:
                        coze_data_dict = json.loads(coze_data)
                        if isinstance(coze_data_dict, dict) and 'summary' in coze_data_dict:
                            summary_content = coze_data_dict['summary']
                    except json.JSONDecodeError:
                        # 如果不是JSON格式，保持原样
                        summary_content = coze_data
                else:
                    summary_content = str(coze_data)
                
                # 创建 Markdown 文件
                md_filename = os.path.splitext(subtitle_file)[0] + '_coze_result.md'
                with open(md_filename, 'w', encoding='utf-8') as f:
                    # 写入 summary 内容到 Markdown 文件
                    if summary_content:
                        f.write(summary_content)
                    else:
                        f.write(str(coze_data))
                markdown_file = md_filename
            
            result["coze_response"] = coze_response
            
        if markdown_file:
            # 直接返回 Markdown 文件供下载
            try:
                return send_file(
                    markdown_file, 
                    as_attachment=True, 
                    download_name=os.path.basename(markdown_file),
                    mimetype='text/markdown'
                )
            except Exception as e:
                # 如果发送文件失败，尝试读取并返回
                try:
                    with open(markdown_file, 'rb') as f:
                        content = f.read()
                    response = Response(content, mimetype='text/markdown')
                    response.headers['Content-Disposition'] = f'attachment; filename={os.path.basename(markdown_file)}'
                    return response
                except Exception as inner_e:
                    return jsonify({"error": f"无法返回文件: {str(inner_e)}"}), 500
        
        # 如果没有生成 Markdown 文件，返回 JSON 结果
        return jsonify(result)
        
    except Exception as e:
        # 打印异常信息以便调试
        print(f"\n{'='*60}")
        print(f"异常发生在 /download-subtitle 端点:")
        print(f"异常类型: {type(e).__name__}")
        print(f"异常信息: {str(e)}")
        print(f"\n完整堆栈跟踪:")
        traceback.print_exc()
        print(f"{'='*60}\n")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """
    健康检查端点
    """
    return jsonify({
        "status": "healthy",
        "coze_configured": Config.is_coze_configured()
    })

@app.route('/download-markdown', methods=['GET'])
def download_markdown():
    """
    下载 Markdown 文件
    """
    filename = request.args.get('file')
    if not filename:
        return jsonify({"error": "缺少文件名参数"}), 400
    
    filepath = os.path.join(Config.SUBTITLES_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "文件不存在"}), 404
    
    try:
        return send_file(filepath, as_attachment=True, download_name=filename)
    except Exception as e:
        # 即使在文件传输过程中出现错误也尽量返回文件
        try:
            with open(filepath, 'rb') as f:
                content = f.read()
            response = Response(content, mimetype='text/markdown')
            response.headers['Content-Disposition'] = f'attachment; filename={filename}'
            return response
        except Exception as inner_e:
            return jsonify({"error": f"无法读取或发送文件: {str(inner_e)}"}), 500

def main(url=None, lang='en', return_result=False):
    """
    主函数 - 可以直接运行或通过 API 调用
    
    Args:
        url (str): YouTube 视频链接（可选，用于程序化调用）
        lang (str): 字幕语言，默认为 'en'
        return_result (bool): 是否返回结果字典（默认 False）
    
    Returns:
        dict: 如果 return_result=True，返回包含 markdown_file 等信息的字典
    """
    # 尝试从文件加载 Coze 配置
    Config.load_from_file()
    
    # 如果直接传入了 URL 参数，使用程序化调用模式
    if url:
        try:
            print(f"正在下载字幕: {url}")
            subtitle_file = download_subtitle(url, lang)
            print(f"字幕下载完成: {subtitle_file}")
            
            # 读取并清洗字幕内容
            with open(subtitle_file, 'r', encoding='utf-8') as f:
                content = f.read()
                cleaned_content = clean_subtitle_content(content)
                
            print("\n清洗后的文本:")
            print("=" * 50)
            print(cleaned_content)
            print("=" * 50)
            
            result = {
                "status": "success",
                "subtitle_file": subtitle_file,
                "cleaned_text": cleaned_content
            }
            
            # 如果配置了 Coze，则发送到工作流
            if Config.is_coze_configured():
                print("\n正在发送到 Coze 工作流...")
                coze_response = send_to_coze_workflow(
                    Config.COZE_WORKFLOW_ID,
                    Config.COZE_TOKEN,
                    cleaned_content,
                    os.path.basename(subtitle_file)
                )
                print("Coze 工作流响应:")
                print(json.dumps(coze_response, indent=2, ensure_ascii=False))
                
                result["coze_response"] = coze_response
                
                # 生成 Markdown 文件
                if coze_response and 'data' in coze_response:
                    coze_data = coze_response['data']
                    # 提取 summary 字段
                    summary_content = None
                    if isinstance(coze_data, dict) and 'summary' in coze_data:
                        summary_content = coze_data['summary']
                    elif isinstance(coze_data, str):
                        try:
                            coze_data_dict = json.loads(coze_data)
                            if isinstance(coze_data_dict, dict) and 'summary' in coze_data_dict:
                                summary_content = coze_data_dict['summary']
                        except json.JSONDecodeError:
                            # 如果不是JSON格式，保持原样
                            summary_content = coze_data
                    else:
                        summary_content = str(coze_data)
                    
                    # 创建 Markdown 文件
                    md_filename = os.path.splitext(subtitle_file)[0] + '_coze_result.md'
                    with open(md_filename, 'w', encoding='utf-8') as f:
                        # 写入 summary 内容到 Markdown 文件
                        if summary_content:
                            f.write(summary_content)
                        else:
                            f.write(str(coze_data))
                    print(f"\nCoze 结果已保存到 Markdown 文件: {md_filename}")
                    result["markdown_file"] = md_filename
            else:
                print("\n提示: 如需发送到 Coze 工作流，请配置 workflow_id 和 token")
            
            # 如果需要返回结果，返回字典
            if return_result:
                return result
            
        except Exception as e:
            print(f"错误: {e}")
            if return_result:
                return {"status": "error", "error": str(e)}
            sys.exit(1)
    
    elif len(sys.argv) > 1:
        # 命令行模式
        url = sys.argv[1]
        lang = sys.argv[2] if len(sys.argv) > 2 else 'en'
        
        try:
            print(f"正在下载字幕: {url}")
            subtitle_file = download_subtitle(url, lang)
            print(f"字幕下载完成: {subtitle_file}")
            
            # 读取并清洗字幕内容
            with open(subtitle_file, 'r', encoding='utf-8') as f:
                content = f.read()
                cleaned_content = clean_subtitle_content(content)
                
            print("\n清洗后的文本:")
            print("=" * 50)
            print(cleaned_content)
            print("=" * 50)
            
            # 如果配置了 Coze，则发送到工作流
            if Config.is_coze_configured():
                print("\n正在发送到 Coze 工作流...")
                coze_response = send_to_coze_workflow(
                    Config.COZE_WORKFLOW_ID,
                    Config.COZE_TOKEN,
                    cleaned_content,
                    os.path.basename(subtitle_file)
                )
                print("Coze 工作流响应:")
                print(json.dumps(coze_response, indent=2, ensure_ascii=False))
                
                # 生成 Markdown 文件
                if coze_response and 'data' in coze_response:
                    coze_data = coze_response['data']
                    # 提取 summary 字段
                    summary_content = None
                    if isinstance(coze_data, dict) and 'summary' in coze_data:
                        summary_content = coze_data['summary']
                    elif isinstance(coze_data, str):
                        try:
                            coze_data_dict = json.loads(coze_data)
                            if isinstance(coze_data_dict, dict) and 'summary' in coze_data_dict:
                                summary_content = coze_data_dict['summary']
                        except json.JSONDecodeError:
                            # 如果不是JSON格式，保持原样
                            summary_content = coze_data
                    else:
                        summary_content = str(coze_data)
                    
                    # 创建 Markdown 文件
                    md_filename = os.path.splitext(subtitle_file)[0] + '_coze_result.md'
                    with open(md_filename, 'w', encoding='utf-8') as f:
                        # 写入 summary 内容到 Markdown 文件
                        if summary_content:
                            f.write(summary_content)
                        else:
                            f.write(str(coze_data))
                    print(f"\nCoze 结果已保存到 Markdown 文件: {md_filename}")
            else:
                print("\n提示: 如需发送到 Coze 工作流，请配置 workflow_id 和 token")
                
        except Exception as e:
            print(f"错误: {e}")
            sys.exit(1)
    else:
        # 启动 Web 服务模式
        print("启动 Web 服务...")
        print("API 端点:")
        print("  POST /download-subtitle - 下载字幕")
        print("  GET  /health           - 健康检查")
        if Config.is_coze_configured():
            print(f"  Coze 工作流已配置 (ID: {Config.COZE_WORKFLOW_ID[:10]}...)")
        else:
            print("  Coze 工作流未配置")
        # 根据环境变量决定是否启用 debug 模式
        debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
        app.run(host='0.0.0.0', port=5001, debug=debug_mode)

if __name__ == '__main__':
    main()