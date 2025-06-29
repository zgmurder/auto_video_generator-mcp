"""
字幕工具模块
负责字幕图片生成、智能分割和文本处理
"""

import numpy as np
import opencc
from PIL import Image, ImageDraw, ImageFont
import re
from mcp.server.fastmcp import FastMCP

# 创建MCP实例
mcp = FastMCP("subtitle-utils", log_level="ERROR")

def create_subtitle_image(text, width, height, font_path, fontsize=40, color='white', bg_color=(0,0,0,0), margin_x=100, margin_bottom=50):
    """创建字幕图片
    
    Args:
        text: 字幕文本
        width: 图片宽度
        height: 图片高度
        font_path: 字体文件路径
        fontsize: 字体大小
        color: 字体颜色 (支持颜色名称如'yellow'或RGB元组如(255,255,0))
        bg_color: 背景颜色 (RGBA元组)
        margin_x: 左右边距
        margin_bottom: 底部边距
        
    Returns:
        numpy.ndarray: 字幕图片数组
    """
    # 繁体转简体
    converter = opencc.OpenCC('t2s')
    text = converter.convert(text)
    
    # 处理颜色格式
    def parse_color(color_input):
        """解析颜色格式"""
        if isinstance(color_input, str):
            # 颜色名称映射
            color_map = {
                'white': (255, 255, 255),
                'black': (0, 0, 0),
                'red': (255, 0, 0),
                'green': (0, 255, 0),
                'blue': (0, 0, 255),
                'yellow': (255, 255, 0),
                'cyan': (0, 255, 255),
                'magenta': (255, 0, 255),
                'orange': (255, 165, 0),
                'purple': (128, 0, 128),
                'pink': (255, 192, 203),
                'brown': (165, 42, 42),
                'gray': (128, 128, 128),
                'grey': (128, 128, 128)
            }
            return color_map.get(color_input.lower(), (255, 255, 255))  # 默认白色
        elif isinstance(color_input, (list, tuple)):
            if len(color_input) == 3:
                return tuple(color_input)  # RGB
            elif len(color_input) == 4:
                return tuple(color_input)  # RGBA
            else:
                return (255, 255, 255)  # 默认白色
        else:
            return (255, 255, 255)  # 默认白色
    
    # 解析颜色
    text_color = parse_color(color)
    background_color = bg_color if isinstance(bg_color, (list, tuple)) and len(bg_color) == 4 else (0, 0, 0, 0)
    
    # 创建图片
    img = Image.new('RGBA', (width, height), background_color)
    draw = ImageDraw.Draw(img)
    
    # 尝试加载字体，如果失败则使用默认字体
    try:
        font = ImageFont.truetype(font_path, fontsize)
    except:
        print(f"警告：无法加载字体 {font_path}，使用默认字体")
        font = ImageFont.load_default()
    
    # 计算文本布局
    max_text_width = width - 2 * margin_x
    avg_char_width = font.getlength('测')
    max_chars_per_line = max(int(max_text_width // avg_char_width), 1)
    
    # 只取第一行，超长截断
    if len(text) > max_chars_per_line:
        text = text[:max_chars_per_line] + '...'
    
    # 计算文本位置
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (width - w) // 2
    y = height - h - margin_bottom
    
    # 绘制文本
    draw.text((x, y), text, font=font, fill=text_color)
    
    return np.array(img)

def split_timings(timing, max_chars=20):
    """智能分割timing，支持时间标记作为静默间隔
    
    Args:
        timing: 字幕时间列表
        max_chars: 每行最大字符数
        
    Returns:
        list: 分割后的字幕时间列表
    """
    new_timings = []
    
    for t in timing:
        txt = t['text'].strip()
        duration = t.get('duration', 0)
        delay = t.get('delay', 0)
        
        # 处理空白静默
        if txt == "" and (delay > 0 or duration > 0):
            new_timings.append({'text': txt, 'duration': duration, 'delay': delay})
            continue
            
        # 如果文本为空，跳过
        if not txt:
            continue
        
        # 检查是否包含时间标记
        time_pattern = r'\{(\d+(?:\.\d+)?)(s|ms)\}'
        time_matches = list(re.finditer(time_pattern, txt))
        
        if time_matches:
            # 包含时间标记，按时间标记分割文本并添加静默
            segments = []
            last_end = 0
            
            for i, match in enumerate(time_matches):
                start_pos = match.start()
                end_pos = match.end()
                
                # 提取时间标记前的文本
                if start_pos > last_end:
                    segment_text = txt[last_end:start_pos].strip()
                    if segment_text:
                        segments.append({'text': segment_text, 'delay': 0})
                
                # 解析时间标记
                time_value = float(match.group(1))
                time_unit = match.group(2)
                
                # 转换为毫秒
                if time_unit == 's':
                    delay_ms = int(time_value * 1000)
                else:  # ms
                    delay_ms = int(time_value)
                
                # 添加静默片段
                segments.append({'text': '', 'delay': delay_ms})
                
                last_end = end_pos
            
            # 添加最后一个时间标记后的文本
            if last_end < len(txt):
                segment_text = txt[last_end:].strip()
                if segment_text:
                    segments.append({'text': segment_text, 'delay': 0})
            
            # 处理分割后的片段
            for segment in segments:
                if segment['text']:
                    # 有文本的片段，进行智能分割
                    sub_segments = _smart_split_text(segment['text'], max_chars, duration / len([s for s in segments if s['text']]))
                    new_timings.extend(sub_segments)
                else:
                    # 纯静默片段
                    new_timings.append({'text': '', 'duration': 0, 'delay': segment['delay']})
        else:
            # 不包含时间标记，使用原有逻辑
            sub_segments = _smart_split_text(txt, max_chars, duration)
            new_timings.extend(sub_segments)
    
    return new_timings

def _smart_split_text(text, max_chars, total_duration):
    """智能分割文本的内部函数
    
    Args:
        text: 要分割的文本
        max_chars: 每行最大字符数
        total_duration: 总时长
        
    Returns:
        list: 分割后的片段列表
    """
    # 策略1：按句子分割（句号、问号、感叹号）
    sentences = []
    current_sentence = ""
    for char in text:
        current_sentence += char
        if char in '。？！.!?':
            sentences.append(current_sentence.strip())
            current_sentence = ""
    if current_sentence.strip():
        sentences.append(current_sentence.strip())
        
    # 如果按句子分割后只有一句，尝试按逗号分割
    if len(sentences) <= 1:
        sentences = []
        current_sentence = ""
        for char in text:
            current_sentence += char
            if char in '，,；;':
                sentences.append(current_sentence.strip())
                current_sentence = ""
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
            
    # 如果按逗号分割后只有一句，按字符数分割
    if len(sentences) <= 1:
        sentences = [text[i:i+max_chars] for i in range(0, len(text), max_chars)]
        
    # 智能时长分配
    if len(sentences) == 1:
        return [{'text': text, 'duration': total_duration, 'delay': 0}]
    else:
        # 根据句子长度比例分配时长
        total_chars = sum(len(s) for s in sentences)
        result = []
        for sentence in sentences:
            if total_chars > 0:
                sentence_duration = (len(sentence) / total_chars) * total_duration
            else:
                sentence_duration = total_duration / len(sentences)
            result.append({
                'text': sentence, 
                'duration': sentence_duration,
                'delay': 0
            })
        return result

def auto_split_timing_by_duration(timing, target_duration_per_segment=3.0):
    """根据目标时长自动分割timing
    
    Args:
        timing: 字幕时间列表
        target_duration_per_segment: 每个片段的目标时长（秒）
        
    Returns:
        list: 分割后的字幕时间列表
    """
    new_timings = []
    current_segment = []
    current_duration = 0
    
    for t in timing:
        txt = t['text'].strip()
        duration = t.get('duration', 0)
        delay = t.get('delay', 0)
        
        # 处理空白静默
        if txt == "" and (delay > 0 or duration > 0):
            # 如果当前片段不为空，先保存当前片段
            if current_segment:
                new_timings.append({
                    'text': ' '.join([item['text'] for item in current_segment]),
                    'duration': current_duration,
                    'delay': 0
                })
                current_segment = []
                current_duration = 0
            # 添加静默
            new_timings.append({'text': txt, 'duration': duration, 'delay': delay})
            continue
            
        # 如果文本为空，跳过
        if not txt:
            continue
            
        # 检查是否需要开始新片段
        if current_duration + duration > target_duration_per_segment and current_segment:
            # 保存当前片段
            new_timings.append({
                'text': ' '.join([item['text'] for item in current_segment]),
                'duration': current_duration,
                'delay': 0
            })
            current_segment = []
            current_duration = 0
            
        # 添加到当前片段
        current_segment.append({'text': txt, 'duration': duration})
        current_duration += duration
    
    # 保存最后一个片段
    if current_segment:
        new_timings.append({
            'text': ' '.join([item['text'] for item in current_segment]),
            'duration': current_duration,
            'delay': 0
        })
    
    return new_timings

def convert_traditional_to_simplified(text):
    """繁体转简体
    
    Args:
        text: 繁体文本
        
    Returns:
        str: 简体文本
    """
    converter = opencc.OpenCC('t2s')
    return converter.convert(text)

def truncate_text(text, max_length, suffix='...'):
    """截断文本
    
    Args:
        text: 原文本
        max_length: 最大长度
        suffix: 截断后缀
        
    Returns:
        str: 截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + suffix

def split_text(text, max_length=50):
    """智能分割文本为字幕片段
    
    Args:
        text: 要分割的文本
        max_length: 每段最大字符数
        
    Returns:
        list: 分割后的文本片段列表
    """
    if len(text) <= max_length:
        return [text]
    
    # 按句号分割
    sentences = re.split(r'[。！？]', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    result = []
    current_segment = ""
    
    for sentence in sentences:
        # 如果当前句子加上标点符号超过最大长度，需要进一步分割
        if len(sentence) > max_length:
            # 按逗号分割
            parts = re.split(r'[，,]', sentence)
            parts = [p.strip() for p in parts if p.strip()]
            
            for part in parts:
                if len(part) > max_length:
                    # 按空格分割（如果有的话）
                    words = part.split()
                    if len(words) > 1:
                        temp = ""
                        for word in words:
                            if len(temp + word) <= max_length:
                                temp += word + " "
                            else:
                                if temp:
                                    result.append(temp.strip())
                                temp = word + " "
                        if temp:
                            current_segment += temp.strip()
                    else:
                        # 如果还是太长，强制分割
                        for i in range(0, len(part), max_length):
                            segment = part[i:i + max_length]
                            if current_segment:
                                result.append(current_segment)
                                current_segment = ""
                            result.append(segment)
                else:
                    if len(current_segment + part) <= max_length:
                        current_segment += part + "，"
                    else:
                        if current_segment:
                            result.append(current_segment.rstrip("，"))
                        current_segment = part + "，"
        else:
            if len(current_segment + sentence) <= max_length:
                current_segment += sentence + "。"
            else:
                if current_segment:
                    result.append(current_segment.rstrip("。"))
                current_segment = sentence + "。"
    
    if current_segment:
        result.append(current_segment.rstrip("。"))
    
    return result

def clean_text(text):
    """清理文本，移除多余的空白字符
    
    Args:
        text: 要清理的文本
        
    Returns:
        str: 清理后的文本
    """
    # 移除多余的空白字符
    text = re.sub(r'\s+', ' ', text)
    # 移除开头和结尾的空白字符
    text = text.strip()
    return text

def validate_subtitle_text(text):
    """验证字幕文本是否有效
    
    Args:
        text: 字幕文本
        
    Returns:
        bool: 是否有效
    """
    if not text or not text.strip():
        return False
    
    # 检查是否包含有效字符
    if not re.search(r'[\u4e00-\u9fff\w]', text):
        return False
    
    return True

def get_subtitle_statistics(text):
    """获取字幕文本统计信息
    
    Args:
        text: 字幕文本
        
    Returns:
        dict: 统计信息
    """
    if not text:
        return {"error": "文本为空"}
    
    # 字符统计
    total_chars = len(text)
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    english_chars = len(re.findall(r'[a-zA-Z]', text))
    digit_chars = len(re.findall(r'\d', text))
    punctuation_chars = len(re.findall(r'[^\w\s\u4e00-\u9fff]', text))
    
    # 句子统计
    sentences = re.split(r'[。！？.!?]', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # 段落统计
    paragraphs = text.split('\n')
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    
    return {
        "total_chars": total_chars,
        "chinese_chars": chinese_chars,
        "english_chars": english_chars,
        "digit_chars": digit_chars,
        "punctuation_chars": punctuation_chars,
        "sentences": len(sentences),
        "paragraphs": len(paragraphs)
    }

@mcp.tool()
async def split_text_for_subtitles(text: str, max_length: int = 50) -> str:
    """智能分割文本为字幕片段
    
    Args:
        text: 要分割的文本
        max_length: 每段最大字符数
        
    Returns:
        分割后的字幕片段
    """
    try:
        cleaned_text = clean_text(text)
        if not validate_subtitle_text(cleaned_text):
            return "错误：文本无效或为空"
        
        segments = split_text(cleaned_text, max_length)
        
        result = f"文本分割完成，共 {len(segments)} 个片段:\n\n"
        for i, segment in enumerate(segments, 1):
            result += f"片段 {i}: {segment}\n"
        
        return result
    except Exception as e:
        return f"文本分割失败: {str(e)}"

@mcp.tool()
async def clean_subtitle_text(text: str) -> str:
    """清理字幕文本
    
    Args:
        text: 要清理的文本
        
    Returns:
        清理后的文本
    """
    try:
        cleaned = clean_text(text)
        return f"文本清理完成:\n\n原始文本: {text}\n\n清理后文本: {cleaned}"
    except Exception as e:
        return f"文本清理失败: {str(e)}"

@mcp.tool()
async def validate_subtitle_text_tool(text: str) -> str:
    """验证字幕文本
    
    Args:
        text: 字幕文本
        
    Returns:
        验证结果
    """
    try:
        if validate_subtitle_text(text):
            stats = get_subtitle_statistics(text)
            return f"""字幕文本验证通过

统计信息:
总字符数: {stats['total_chars']}
中文字符: {stats['chinese_chars']}
英文字符: {stats['english_chars']}
数字字符: {stats['digit_chars']}
标点符号: {stats['punctuation_chars']}
句子数量: {stats['sentences']}
段落数量: {stats['paragraphs']}"""
        else:
            return "字幕文本验证失败：文本无效或为空"
    except Exception as e:
        return f"字幕文本验证出错: {str(e)}"

@mcp.tool()
async def get_subtitle_statistics_tool(text: str) -> str:
    """获取字幕文本统计信息
    
    Args:
        text: 字幕文本
        
    Returns:
        统计信息
    """
    try:
        if not text:
            return "错误：文本为空"
        
        stats = get_subtitle_statistics(text)
        if "error" in stats:
            return f"获取统计信息失败: {stats['error']}"
        
        return f"""字幕文本统计信息:

字符统计:
- 总字符数: {stats['total_chars']}
- 中文字符: {stats['chinese_chars']}
- 英文字符: {stats['english_chars']}
- 数字字符: {stats['digit_chars']}
- 标点符号: {stats['punctuation_chars']}

结构统计:
- 句子数量: {stats['sentences']}
- 段落数量: {stats['paragraphs']}

建议:
- 每段字幕建议不超过50个字符
- 当前文本可分割为约 {max(1, stats['total_chars'] // 50)} 个字幕片段"""
    except Exception as e:
        return f"获取统计信息失败: {str(e)}"

@mcp.tool()
async def optimize_subtitle_length(text: str, target_length: int = 50) -> str:
    """优化字幕长度
    
    Args:
        text: 字幕文本
        target_length: 目标长度
        
    Returns:
        优化建议
    """
    try:
        cleaned_text = clean_text(text)
        if not validate_subtitle_text(cleaned_text):
            return "错误：文本无效或为空"
        
        current_length = len(cleaned_text)
        
        if current_length <= target_length:
            return f"文本长度合适 ({current_length} 字符)，无需优化"
        
        # 分割文本
        segments = split_text(cleaned_text, target_length)
        
        result = f"""字幕长度优化建议:

当前长度: {current_length} 字符
目标长度: {target_length} 字符
建议分割为: {len(segments)} 个片段

分割结果:"""
        
        for i, segment in enumerate(segments, 1):
            result += f"\n片段 {i} ({len(segment)} 字符): {segment}"
        
        return result
    except Exception as e:
        return f"字幕长度优化失败: {str(e)}"

def get_mcp_instance():
    """获取MCP实例
    
    Returns:
        FastMCP: MCP实例
    """
    return mcp 