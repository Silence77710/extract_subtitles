#!/usr/bin/env python3
"""
测试字幕清洗功能
"""

import re

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

# 测试用的字幕内容
test_content = """WEBVTT
Kind: captions
Language: en

00:00:00.360 --> 00:00:06.040
Hey guys! It's Ariannita la Gringa and welcome&nbsp;
back to my YouTube channel. Can you guys guess&nbsp;&nbsp;

00:00:06.040 --> 00:00:13.400
where I am? Well, I'm still in New York City (the&nbsp;
city that never sleeps) and in my last video I&nbsp;&nbsp;

00:00:13.400 --> 00:00:18.680
explored Manhattan and today I'm going to be exploring&nbsp;
different modes of transportation that are&nbsp;&nbsp;
"""

def main():
    print("原始字幕内容:")
    print("-" * 50)
    print(test_content)
    print("-" * 50)
    
    cleaned = clean_subtitle_content(test_content)
    
    print("\n清洗后的文本:")
    print("-" * 50)
    print(cleaned)
    print("-" * 50)
    
    print("\n验证清洗结果:")
    print("1. 是否删除了时间戳？", "00:00:00.360 -->" not in cleaned)
    print("2. 是否删除了WEBVTT？", "WEBVTT" not in cleaned)
    print("3. 是否删除了Kind/Language？", "Kind:" not in cleaned and "Language:" not in cleaned)
    print("4. 是否替换了&nbsp;？", "&nbsp;" not in cleaned)
    print("5. 是否删除了空行？", "\n\n" not in cleaned)

if __name__ == "__main__":
    main()