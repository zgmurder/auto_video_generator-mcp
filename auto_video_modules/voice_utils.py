"""
语音工具模块
负责语音音色的管理和选择
"""

from mcp.server.fastmcp import FastMCP

# 创建MCP实例
mcp = FastMCP("voice-utils", log_level="ERROR")

def get_voice_by_index(idx):
    """根据索引获取语音音色
    
    Args:
        idx: 语音音色索引 (0-4)
        
    Returns:
        str: 语音音色名称
    """
    voices = [
        "zh-CN-XiaoxiaoNeural",  # 0 女
        "zh-CN-YunyangNeural",   # 1 男
        "zh-CN-XiaoyiNeural",    # 2 女
        "zh-CN-YunxiNeural",     # 3 女
        "zh-CN-YunjianNeural"    # 4 男
    ]
    
    if idx < 0 or idx >= len(voices):
        print(f"activeTimbre超出范围，使用默认音色: {voices[0]}")
        return voices[0]
    return voices[idx]

def get_voice_list():
    """获取所有可用的语音音色列表
    
    Returns:
        list: 语音音色列表
    """
    return [
        "zh-CN-XiaoxiaoNeural",  # 0 女
        "zh-CN-YunyangNeural",   # 1 男
        "zh-CN-XiaoyiNeural",    # 2 女
        "zh-CN-YunxiNeural",     # 3 女
        "zh-CN-YunjianNeural"    # 4 男
    ]

def get_voice_info():
    """获取语音音色的详细信息
    
    Returns:
        list: 包含索引、名称和描述的语音信息列表
    """
    return [
        {"index": 0, "name": "zh-CN-XiaoxiaoNeural", "description": "女声小晓"},
        {"index": 1, "name": "zh-CN-YunyangNeural", "description": "男声云扬"},
        {"index": 2, "name": "zh-CN-XiaoyiNeural", "description": "女声小艺"},
        {"index": 3, "name": "zh-CN-YunxiNeural", "description": "女声云希"},
        {"index": 4, "name": "zh-CN-YunjianNeural", "description": "男声云健"}
    ]

def validate_voice_index(idx):
    """验证语音音色索引是否有效
    
    Args:
        idx: 语音音色索引
        
    Returns:
        bool: 是否有效
    """
    return 0 <= idx <= 4

@mcp.tool()
async def get_available_voices() -> str:
    """获取可用的语音音色列表
    
    Returns:
        可用的语音音色信息
    """
    voice_info = get_voice_info()
    voices = []
    for info in voice_info:
        voices.append(f"{info['index']}: {info['name']} ({info['description']})")
    return "可用的语音音色:\n" + "\n".join(voices)

@mcp.tool()
async def get_voice_by_index_tool(voice_index: int) -> str:
    """根据索引获取语音音色
    
    Args:
        voice_index: 语音音色索引 (0-4)
        
    Returns:
        语音音色信息
    """
    if not validate_voice_index(voice_index):
        return f"错误：语音音色索引 {voice_index} 无效，有效范围为 0-4"
    
    voice_name = get_voice_by_index(voice_index)
    voice_info = get_voice_info()[voice_index]
    return f"语音音色: {voice_name}\n描述: {voice_info['description']}"

@mcp.tool()
async def validate_voice_index_tool(voice_index: int) -> str:
    """验证语音音色索引
    
    Args:
        voice_index: 语音音色索引
        
    Returns:
        验证结果
    """
    if validate_voice_index(voice_index):
        voice_info = get_voice_info()[voice_index]
        return f"语音音色索引 {voice_index} 有效\n名称: {voice_info['name']}\n描述: {voice_info['description']}"
    else:
        return f"语音音色索引 {voice_index} 无效，有效范围为 0-4"

@mcp.tool()
async def get_voice_statistics() -> str:
    """获取语音音色统计信息
    
    Returns:
        语音音色统计信息
    """
    voice_info = get_voice_info()
    total_voices = len(voice_info)
    male_voices = len([v for v in voice_info if "男" in v['description']])
    female_voices = total_voices - male_voices
    
    stats = f"""语音音色统计信息:
总数量: {total_voices}
男声: {male_voices}
女声: {female_voices}

详细列表:"""
    
    for info in voice_info:
        stats += f"\n{info['index']}: {info['name']} ({info['description']})"
    
    return stats

def get_mcp_instance():
    """获取MCP实例
    
    Returns:
        FastMCP: MCP实例
    """
    return mcp 