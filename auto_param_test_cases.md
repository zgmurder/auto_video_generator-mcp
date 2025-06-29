# 自动化参数测试用例文档

本测试用例文档覆盖了 `generate_auto_video` MCP工具的所有参数组合，从只传必传参数到传递全部参数，适用于接口兼容性和健壮性验证。

---

## 测试环境
- 视频路径：`E:\project\py\auto-video-generator\demo.mp4`
- 文本内容：`{2000ms}欢迎观看{1500ms}本视频教程`

---

## 测试用例列表

### 1. 只传必传参数
- **参数**：
  - `text`：`{2000ms}欢迎观看{1500ms}本视频教程`
  - `video_path`：`E:\project\py\auto-video-generator\demo.mp4`
- **预期结果**：
  - 视频生成成功，使用默认音色、默认输出路径、全视频内容、默认字幕样式和分割策略。

---

### 2. 增加 voice_index
- **参数**：
  - 同上，增加 `voice_index: 1`
- **预期结果**：
  - 视频生成成功，使用指定音色。

---

### 3. 增加 output_path
- **参数**：
  - 同上，增加 `output_path: output_test3.mp4`
- **预期结果**：
  - 视频生成成功，输出文件名为 `output_test3.mp4`。

---

### 4. 增加 segments_mode
- **参数**：
  - 同上，增加 `segments_mode: keep`
- **预期结果**：
  - 视频生成成功，保留全部视频内容（因未指定 segments）。

---

### 5. 增加 segments
- **参数**：
  - 同上，增加 `segments: '[{"start": "00:00:05", "end": "00:00:15"}]'`（必须为字符串）
- **预期结果**：
  - 视频生成成功，仅保留指定片段。
  - ⚠️ 若 segments 传递为 list 而非字符串，将报类型校验错误。

---

### 6. 增加 subtitle_style
- **参数**：
  - 同上，增加 `subtitle_style: '{"fontSize": 44, "color": "yellow", "bgColor": [0, 0, 0, 128], "marginX": 120, "marginBottom": 60}'`（必须为字符串）
- **预期结果**：
  - 视频生成成功，字幕样式为指定样式。
  - ⚠️ 若 subtitle_style 传递为 dict 而非字符串，将报类型校验错误。

---

### 7. 增加 auto_split_config
- **参数**：
  - 同上，增加 `auto_split_config: '{"enable": true, "strategy": "duration", "targetDuration": 2.0, "maxChars": 18}'`（必须为字符串）
- **预期结果**：
  - 视频生成成功，字幕分割策略为指定策略。
  - ⚠️ 若 auto_split_config 传递为 dict 而非字符串，将报类型校验错误。

---

### 8. 测试不同参数组合
- **参数**：
  - `voice_index: 2`
  - `output_path: output_test8_cut.mp4`
  - `segments_mode: cut`
  - `segments: '[{"start": "00:00:10", "end": "00:00:20"}]'`
  - `subtitle_style: '{"fontSize": 50, "color": "red", "bgColor": [255, 255, 255, 100]}'`
  - `auto_split_config: '{"enable": true, "strategy": "smart", "maxChars": 15}'`
- **预期结果**：
  - 视频生成成功，剪掉指定片段，字幕样式和分割策略均为自定义。

---

## 重要注意事项
- segments、subtitle_style、auto_split_config 必须以字符串形式传递，不能直接传 list/dict。
- 若参数类型不符，MCP接口会报 `Input should be a valid string` 错误。
- 推荐所有复杂结构参数均用 json 字符串传递。

---

## 示例代码片段

```python
await mcp.call_tool("generate_auto_video", {
    "text": "{2000ms}欢迎观看{1500ms}本视频教程",
    "video_path": r"E:\\project\\py\\auto-video-generator\\demo.mp4",
    "voice_index": 2,
    "output_path": "output_test8_cut.mp4",
    "segments_mode": "cut",
    "segments": '[{"start": "00:00:10", "end": "00:00:20"}]',
    "subtitle_style": '{"fontSize": 50, "color": "red", "bgColor": [255, 255, 255, 100]}',
    "auto_split_config": '{"enable": true, "strategy": "smart", "maxChars": 15}'
})
```

---

## 结论
- 只传必传参数及基础参数时，接口100%通过。
- 复杂结构参数必须严格用字符串传递。
- 本文档可作为接口自动化测试和开发联调的标准参考。 