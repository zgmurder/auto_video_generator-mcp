#!/usr/bin/env python3
"""
测试模块化自动视频生成MCP服务器
测试所有模块的功能
"""

import asyncio
import os
import time
import json
from typing import Dict, List, Any
from auto_generate_video_mcp_modular import mcp
from auto_video_modules.mcp_tools import get_mcp_instance

class TestResult:
    """测试结果类"""
    def __init__(self, name: str):
        self.name = name
        self.success = False
        self.error: str | None = None
        self.duration = 0.0
        self.result = None

class TestRunner:
    """测试运行器"""
    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = 0.0
        
    async def run_test(self, test_func, test_name: str) -> TestResult:
        """运行单个测试"""
        result = TestResult(test_name)
        start_time = time.time()
        
        try:
            result.result = await test_func()
            result.success = True
        except Exception as e:
            result.error = str(e)
            result.success = False
        
        result.duration = time.time() - start_time
        self.results.append(result)
        
        # 打印测试结果
        status = "✓" if result.success else "✗"
        print(f"{status} {test_name} ({result.duration:.2f}s)")
        if not result.success and result.error:
            print(f"  错误: {result.error}")
        
        return result
    
    def print_summary(self):
        """打印测试总结"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.success)
        failed = total - passed
        total_time = sum(r.duration for r in self.results)
        
        print(f"\n{'='*50}")
        print(f"测试总结:")
        print(f"总计: {total} 个测试")
        print(f"通过: {passed} 个")
        print(f"失败: {failed} 个")
        print(f"成功率: {passed/total*100:.1f}%")
        print(f"总耗时: {total_time:.2f}秒")
        print(f"{'='*50}")
        
        if failed > 0:
            print("\n失败的测试:")
            for result in self.results:
                if not result.success:
                    print(f"  - {result.name}: {result.error}")

# 创建测试运行器
test_runner = TestRunner()

async def test_ffmpeg_tools():
    """测试FFmpeg工具"""
    print("\n=== 测试FFmpeg工具 ===")
    
    # 测试FFmpeg状态检查
    await test_runner.run_test(
        lambda: mcp.call_tool("check_ffmpeg_status_mcp", {}),
        "FFmpeg状态检查"
    )
    
    # 测试FFmpeg功能测试
    await test_runner.run_test(
        lambda: mcp.call_tool("test_ffmpeg_functionality_mcp", {}),
        "FFmpeg功能测试"
    )
    
    # 测试获取FFmpeg版本
    await test_runner.run_test(
        lambda: mcp.call_tool("get_ffmpeg_version_mcp", {}),
        "获取FFmpeg版本"
    )

async def test_voice_tools():
    """测试语音工具"""
    print("\n=== 测试语音工具 ===")
    
    # 测试获取可用语音列表
    await test_runner.run_test(
        lambda: mcp.call_tool("get_available_voices_mcp", {}),
        "获取可用语音列表"
    )
    
    # 测试根据索引获取语音
    await test_runner.run_test(
        lambda: mcp.call_tool("get_voice_by_index_tool_mcp", {"voice_index": 0}),
        "获取语音索引0"
    )
    
    # 测试验证语音索引
    await test_runner.run_test(
        lambda: mcp.call_tool("validate_voice_index_tool_mcp", {"voice_index": 2}),
        "验证语音索引2"
    )
    
    # 测试语音统计信息
    await test_runner.run_test(
        lambda: mcp.call_tool("get_voice_statistics_mcp", {}),
        "获取语音统计信息"
    )

async def test_audio_tools():
    """测试音频工具"""
    print("\n=== 测试音频工具 ===")
    
    # 测试获取可用语音列表（音频模块）
    await test_runner.run_test(
        lambda: mcp.call_tool("list_available_voices_audio_mcp", {}),
        "音频模块语音列表"
    )
    
    # 测试文本转语音（如果有测试音频文件）
    test_text = "这是一个测试音频。"
    test_voice = "zh-CN-XiaoxiaoNeural"
    test_output = "test_audio.mp3"
    
    result = await test_runner.run_test(
        lambda: mcp.call_tool("convert_text_to_speech_mcp", {
            "text": test_text, 
            "voice": test_voice, 
            "output_file": test_output
        }),
        "文本转语音测试"
    )
    
    # 如果生成了音频文件，测试音频信息
    if result.success and os.path.exists(test_output):
        await test_runner.run_test(
            lambda: mcp.call_tool("get_audio_file_info_mcp", {"audio_file": test_output}),
            "获取音频文件信息"
        )
        
        await test_runner.run_test(
            lambda: mcp.call_tool("validate_audio_file_tool_mcp", {"audio_file": test_output}),
            "验证音频文件"
        )
        
        await test_runner.run_test(
            lambda: mcp.call_tool("get_audio_duration_tool_mcp", {"audio_file": test_output}),
            "获取音频时长"
        )
        
        # 清理测试文件
        try:
            os.remove(test_output)
            print("  清理测试音频文件")
        except Exception as e:
            print(f"  清理文件失败: {e}")

async def test_subtitle_tools():
    """测试字幕工具"""
    print("\n=== 测试字幕工具 ===")
    
    test_text = "这是一个测试文本，用于测试字幕分割功能。这个文本比较长，应该会被分割成多个片段。"
    
    # 测试文本分割
    await test_runner.run_test(
        lambda: mcp.call_tool("split_text_for_subtitles_mcp", {"text": test_text, "max_length": 30}),
        "文本分割测试"
    )
    
    # 测试文本清理
    dirty_text = "  这是一个  有  多余空格的  文本  "
    await test_runner.run_test(
        lambda: mcp.call_tool("clean_subtitle_text_mcp", {"text": dirty_text}),
        "文本清理测试"
    )
    
    # 测试字幕文本验证
    await test_runner.run_test(
        lambda: mcp.call_tool("validate_subtitle_text_tool_mcp", {"text": test_text}),
        "字幕文本验证"
    )
    
    # 测试字幕统计信息
    await test_runner.run_test(
        lambda: mcp.call_tool("get_subtitle_statistics_tool_mcp", {"text": test_text}),
        "字幕统计信息"
    )
    
    # 测试字幕长度优化
    await test_runner.run_test(
        lambda: mcp.call_tool("optimize_subtitle_length_mcp", {"text": test_text, "target_length": 25}),
        "字幕长度优化"
    )

async def test_video_tools():
    """测试视频工具"""
    print("\n=== 测试视频工具 ===")
    
    # 测试视频格式信息
    await test_runner.run_test(
        lambda: mcp.call_tool("get_video_formats_mcp", {}),
        "获取支持的视频格式"
    )
    
    # 测试视频文件验证（如果存在测试视频）
    test_video = "test_video.mp4"
    if os.path.exists(test_video):
        await test_runner.run_test(
            lambda: mcp.call_tool("validate_video_file_tool_mcp", {"video_path": test_video}),
            "验证视频文件"
        )
        
        await test_runner.run_test(
            lambda: mcp.call_tool("get_video_info_tool_mcp", {"video_path": test_video}),
            "获取视频文件信息"
        )
    else:
        print(f"⚠ 测试视频文件不存在: {test_video}")

async def test_main_tools():
    """测试主要功能工具"""
    print("\n=== 测试主要功能工具 ===")
    
    # 测试系统状态
    await test_runner.run_test(
        lambda: mcp.call_tool("get_system_status_mcp", {}),
        "获取系统状态"
    )
    
    # 测试获取语音选项
    await test_runner.run_test(
        lambda: mcp.call_tool("get_available_voice_options_mcp", {}),
        "获取语音选项"
    )
    
    # 测试参数验证
    test_text = "这是一个测试文本。"
    test_video = "test_video.mp4"
    
    if os.path.exists(test_video):
        await test_runner.run_test(
            lambda: mcp.call_tool("validate_input_parameters_mcp", {
                "text": test_text, 
                "video_path": test_video, 
                "voice_index": 0
            }),
            "参数验证"
        )
        
        await test_runner.run_test(
            lambda: mcp.call_tool("get_generation_estimate_mcp", {
                "text": test_text, 
                "video_path": test_video
            }),
            "生成时间估算"
        )
    else:
        print(f"⚠ 测试视频文件不存在，跳过相关测试: {test_video}")
    
    # 测试获取所有工具列表
    await test_runner.run_test(
        lambda: mcp.call_tool("get_all_available_tools", {}),
        "获取所有可用工具"
    )

async def test_full_video_generation():
    """测试完整的视频生成功能"""
    print("\n=== 测试完整视频生成功能 ===")
    
    test_text = "这是一个完整的视频生成测试。我们将使用这个文本来测试整个流程。"
    test_video = "test_video.mp4"
    
    if os.path.exists(test_video):
        print("开始测试完整视频生成...")
        result = await test_runner.run_test(
            lambda: mcp.call_tool("generate_auto_video_mcp", {
                "text": test_text, 
                "video_path": test_video, 
                "voice_index": 0, 
                "output_path": "test_output.mp4"
            }),
            "完整视频生成测试"
        )
        
        # 检查输出文件
        if result.success and os.path.exists("test_output.mp4"):
            print("  ✓ 输出视频文件生成成功")
            # 清理测试文件
            try:
                os.remove("test_output.mp4")
                print("  清理测试输出文件")
            except Exception as e:
                print(f"  清理文件失败: {e}")
        else:
            print("  ✗ 输出视频文件未生成")
    else:
        print(f"⚠ 测试视频文件不存在，跳过完整视频生成测试: {test_video}")

async def test_generate_auto_video_with_configs():
    """测试带配置参数的视频生成"""
    print("=== 测试带配置参数的视频生成 ===")
    
    mcp = get_mcp_instance()
    
    # 测试文本
    text = "这是一个测试视频。我们将演示各种配置参数的效果。包括视频片段剪辑、字幕样式设置和智能分割功能。"
    
    # 测试视频文件
    video_path = "test_video.mp4"
    if not os.path.exists(video_path):
        print(f"警告：测试视频文件 {video_path} 不存在，跳过测试")
        return
    
    # 测试配置1：基本配置
    print("\n1. 测试基本配置...")
    result1 = await mcp.call_tool("generate_auto_video", {
        "text": text,
        "video_path": video_path,
        "voice_index": 0,
        "output_path": "output_basic.mp4"
    })
    print(f"基本配置结果: {result1[:200]}...")
    
    # 测试配置2：视频片段剪辑
    print("\n2. 测试视频片段剪辑...")
    segments_config = json.dumps([
        {"start": "00:00:05", "end": "00:00:15"},
        {"start": "00:00:25", "end": "00:00:35"}
    ])
    result2 = await mcp.call_tool("generate_auto_video", {
        "text": text,
        "video_path": video_path,
        "voice_index": 0,
        "output_path": "output_segments_keep.mp4",
        "segments_mode": "keep",
        "segments": segments_config
    })
    print(f"视频片段保留模式结果: {result2[:200]}...")
    
    # 测试配置3：字幕样式
    print("\n3. 测试字幕样式...")
    subtitle_style_config = json.dumps({
        "fontSize": 50,
        "color": "yellow",
        "bgColor": [0, 0, 0, 128],
        "marginX": 150,
        "marginBottom": 80
    })
    result3 = await mcp.call_tool("generate_auto_video", {
        "text": text,
        "video_path": video_path,
        "voice_index": 0,
        "output_path": "output_subtitle_style.mp4",
        "subtitle_style": subtitle_style_config
    })
    print(f"字幕样式配置结果: {result3[:200]}...")
    
    # 测试配置4：智能分割
    print("\n4. 测试智能分割...")
    auto_split_config = json.dumps({
        "enable": True,
        "strategy": "smart",
        "maxChars": 15
    })
    result4 = await mcp.call_tool("generate_auto_video", {
        "text": text,
        "video_path": video_path,
        "voice_index": 0,
        "output_path": "output_auto_split.mp4",
        "auto_split_config": auto_split_config
    })
    print(f"智能分割配置结果: {result4[:200]}...")
    
    # 测试配置5：完整配置
    print("\n5. 测试完整配置...")
    result5 = await mcp.call_tool("generate_auto_video", {
        "text": text,
        "video_path": video_path,
        "voice_index": 1,
        "output_path": "output_full_config.mp4",
        "segments_mode": "cut",
        "segments": json.dumps([{"start": "00:00:10", "end": "00:00:20"}]),
        "subtitle_style": json.dumps({
            "fontSize": 45,
            "color": "red",
            "bgColor": [255, 255, 255, 100]
        }),
        "auto_split_config": json.dumps({
            "enable": True,
            "strategy": "duration",
            "targetDuration": 2.0
        })
    })
    print(f"完整配置结果: {result5[:200]}...")

async def test_system_tools():
    """测试系统工具"""
    print("\n=== 测试系统工具 ===")
    
    mcp = get_mcp_instance()
    
    # 测试系统状态
    print("\n1. 测试系统状态...")
    status = await mcp.call_tool("get_system_status", {})
    print(f"系统状态: {status[:200]}...")
    
    # 测试语音选项
    print("\n2. 测试语音选项...")
    voices = await mcp.call_tool("get_available_voice_options", {})
    print(f"语音选项: {voices[:200]}...")
    
    # 测试参数验证
    print("\n3. 测试参数验证...")
    validation = await mcp.call_tool("validate_input_parameters", {
        "text": "测试文本",
        "video_path": "test_video.mp4",
        "voice_index": 0
    })
    print(f"参数验证: {validation}")
    
    # 测试时间估算
    print("\n4. 测试时间估算...")
    estimate = await mcp.call_tool("get_generation_estimate", {
        "text": "这是一个较长的测试文本，用于测试时间估算功能。",
        "video_path": "test_video.mp4"
    })
    print(f"时间估算: {estimate[:200]}...")

async def test_config_examples():
    """测试配置示例"""
    print("\n=== 测试配置示例 ===")
    
    # 配置示例
    examples = {
        "基本使用": {
            "text": "简单的测试文本",
            "video_path": "test_video.mp4",
            "voice_index": 0,
            "output_path": "output_basic.mp4"
        },
        "视频片段保留": {
            "text": "保留指定片段的视频",
            "video_path": "test_video.mp4",
            "voice_index": 0,
            "output_path": "output_keep.mp4",
            "segments_mode": "keep",
            "segments": json.dumps([{"start": "00:00:05", "end": "00:00:15"}])
        },
        "视频片段剪掉": {
            "text": "剪掉指定片段的视频",
            "video_path": "test_video.mp4",
            "voice_index": 0,
            "output_path": "output_cut.mp4",
            "segments_mode": "cut",
            "segments": json.dumps([{"start": "00:00:10", "end": "00:00:20"}])
        },
        "自定义字幕样式": {
            "text": "自定义字幕样式的视频",
            "video_path": "test_video.mp4",
            "voice_index": 0,
            "output_path": "output_style.mp4",
            "subtitle_style": json.dumps({
                "fontSize": 50,
                "color": "yellow",
                "bgColor": [0, 0, 0, 128],
                "marginX": 150,
                "marginBottom": 80
            })
        },
        "智能分割": {
            "text": "使用智能分割的文本处理",
            "video_path": "test_video.mp4",
            "voice_index": 0,
            "output_path": "output_split.mp4",
            "auto_split_config": json.dumps({
                "enable": True,
                "strategy": "smart",
                "maxChars": 15
            })
        },
        "按时长分割": {
            "text": "按时长分割的文本处理",
            "video_path": "test_video.mp4",
            "voice_index": 0,
            "output_path": "output_duration.mp4",
            "auto_split_config": json.dumps({
                "enable": True,
                "strategy": "duration",
                "targetDuration": 2.0
            })
        }
    }
    
    for name, config in examples.items():
        print(f"\n{name}配置示例:")
        print(json.dumps(config, ensure_ascii=False, indent=2))

async def main():
    """主测试函数"""
    print("开始测试模块化自动视频生成MCP服务器...")
    test_runner.start_time = time.time()
    
    try:
        # 测试各个模块
        await test_ffmpeg_tools()
        await test_voice_tools()
        await test_audio_tools()
        await test_subtitle_tools()
        await test_video_tools()
        await test_main_tools()
        await test_full_video_generation()
        
        # 测试带配置参数的视频生成
        await test_generate_auto_video_with_configs()
        
        # 测试系统工具
        await test_system_tools()
        
        # 测试配置示例
        await test_config_examples()
        
        # 打印测试总结
        test_runner.print_summary()
        
    except Exception as e:
        print(f"\n✗ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 