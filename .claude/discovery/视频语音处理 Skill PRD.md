# PRD: 视频与语音处理 Skill 系统

## 一、需求理解（为什么）

### 目标
为 Claude Code 创建两个独立 Skill，使其能够自动处理视频和语音内容：
- **video-processor**: 视频下载、元数据提取、帧分析
- **audio-processor**: 语音转文字、说话人分离

### 交付物清单
- [ ] Skill 1: video-processor
  - [ ] A1: URL 解析与验证
  - [ ] A2: 平台适配（B站/YouTube/抖音）
  - [ ] A3: 视频下载（含分片、断点续传）
  - [ ] A4: 元数据提取
  - [ ] A5: 字幕/弹幕提取
  - [ ] B1: 音频轨道分离
  - [ ] B2: 关键帧提取
  - [ ] B3: 画面 OCR
  - [ ] B4: 场景切分检测
- [ ] Skill 2: audio-processor
  - [ ] C1: 音频格式标准化
  - [ ] C2: 语音转文字（STT）
  - [ ] C3: 说话人分离（Diarization）
  - [ ] C4: 时间戳对齐

### 用户动线（梳理实现路径）

#### 动线 1：视频下载流程
```
用户输入 URL
    ↓
URL 解析 → 平台识别（B站/YouTube/抖音/小红书）
    ↓
平台适配 → 选择对应 Extractor（yt-dlp）
    ↓
元数据提取 → 获取标题/描述/时长/可用格式
    ↓
用户确认下载参数（质量/格式）
    ↓
视频下载 → DASH/HLS 分片下载 → 合并
    ↓
字幕提取（如有）
    ↓
返回文件路径 + 元数据 JSON
```

#### 动线 2：视频内容理解流程
```
输入：视频文件路径
    ↓
场景切分检测（PySceneDetect）
    ↓
关键帧提取（每场景中间帧 + 质量评估）
    ↓
画面 OCR（PaddleOCR）
    ↓
音频轨道分离（ffmpeg）
    ↓
返回结构化结果（场景列表 + OCR 文本 + 音频路径）
```

#### 动线 3：语音处理流程
```
输入：音频文件路径
    ↓
音频格式标准化 → 转换为 16kHz WAV
    ↓
语音活动检测（VAD）→ 过滤静音
    ↓
语音转文字（Whisper small）
    ↓
说话人分离（pyannote.audio，可选）
    ↓
时间戳对齐
    ↓
返回：带时间戳的文本 + 说话人标签
```

### 边界条件
- **包含**：B站、YouTube、抖音、小红书、Twitter/X 的视频下载；中文/英文语音识别；本地文件处理
- **不包含**：实时直播流处理、视频编辑、语音合成（TTS）

---

## 二、调研结论（是什么）

### 市场现有 Skills 分析

通过 skills.sh 市场搜索，发现以下相关 skills：

| Skill | 安装量 | 功能覆盖 | 缺口分析 |
|-------|--------|---------|---------|
| **youtube-downloader** | 852 | YouTube 视频下载 | ❌ 仅支持 YouTube，不支持 B站/抖音/小红书 |
| **audio-transcriber** | 104 | Whisper 转录 + 说话人分离 + Markdown 输出 | ✅ 功能完善，但无视频相关功能 |
| **youtube-transcript** | 863 | YouTube 字幕获取 | ❌ 仅 YouTube，无下载功能 |
| **youtube-clipper** | 1.5K | YouTube 剪辑 | ❌ 与需求无关 |

**市场缺口总结**：
1. **多平台视频下载** - 没有支持 B站、抖音、小红书的 Skill
2. **视频内容理解** - 没有支持场景切分、画面 OCR 的 Skill
3. **视频-音频-文本一体化** - 现有 Skills 是分散的，没有整合方案

**决策**：采用**完全新建**方案，不扩展现有 skills。

---

### 2.1 视频下载模块（A2/A3）

#### 竞品/开源方案
| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| **yt-dlp** | 149k stars，支持1000+站点，活跃维护 | Python依赖较重 | **强烈推荐** |
| you-get | 56k stars，专注中文站点 | 更新慢，支持站点少 | 备选 |
| lux | 30k stars，Go高性能 | 功能相对简单 | 高性能场景 |

#### 平台反爬策略（深度调研）
- **YouTube**: PO Token 强制化（2024+），需多客户端轮换策略
- **B站**: WBI 签名算法，需动态密钥获取
- **TikTok/抖音**: JS挑战防护，需模拟或浏览器提取
- **小红书**: 数据在 INITIAL_STATE 中，反爬较宽松

#### 前瞻性趋势
- 平台加密持续升级，PO Token、设备指纹检测普及
- 应对策略：浏览器自动化降级、多客户端轮换、代理池

### 2.2 语音转文字模块（C2）

#### 方案对比
| 方案 | 参数量 | VRAM | 中文WER | 速度 | 结论 |
|------|--------|------|---------|------|------|
| Whisper tiny | 39M | ~1GB | ~20% | 10x | 测试用 |
| Whisper base | 74M | ~1GB | ~15% | 7x | 轻量 |
| **Whisper small** | **244M** | **~2GB** | **~10%** | **4x** | **推荐** |
| Whisper medium | 769M | ~5GB | ~8% | 2x | 高精度 |
| Whisper turbo | 809M | ~6GB | ~9% | 8x | 纯英文首选 |
| Paraformer-zh | 220M | ~2GB | ~6% | 5x | 中文专用首选 |

#### 前瞻性
- WhisperX 提供 4x 加速和批处理能力
- 端侧部署：whisper.cpp、Sherpa-ONNX 支持移动端

### 2.3 说话人分离（C3）

#### 方案对比
| 方案 | DER | 实时性 | 部署难度 | 结论 |
|------|-----|--------|----------|------|
| pyannote.audio 3.1 | 12-24% | 批处理 | 中 | **推荐** |
| WhisperX 集成 | 中等 | 批处理 | 低 | 快速集成 |
| AWS Transcribe | 低 | 流式 | 低 | 云服务备选 |

**关键限制**: 目前无真正的流式开源方案，实时场景需接受 trade-off

### 2.4 视频 OCR（B3）

#### 方案对比
| 方案 | 中文支持 | 速度 | 准确性 | 结论 |
|------|----------|------|--------|------|
| **PaddleOCR** | **极强** | **快** | **95%+** | **中文视频首选** |
| EasyOCR | 良好 | 中等 | 90% | 多语言快速原型 |
| Tesseract | 一般 | 慢 | 85% | 英文文档 |
| GPT-4V | 强 | 慢 | 高 | 复杂布局兜底 |

#### 前瞻性
- 多模态 LLM（GPT-4V、Qwen-VL）逐步替代传统 OCR
- 推荐混合策略：PaddleOCR 快速提取 + LLM 复杂场景兜底

### 2.5 场景切分（B4）

| 方案 | 原理 | 速度 | 准确性 | 结论 |
|------|------|------|--------|------|
| **PySceneDetect** | HSV直方图差异 | 快 | 高 | **推荐** |
| FFmpeg scene | 像素差异 | 快 | 中 | 简单场景 |
| 语义嵌入（CLIP） | 特征相似度 | 慢 | 高 | 语义场景分割 |

### 2.6 关键帧提取（B2）

| 策略 | 适用场景 | 实现方式 |
|------|----------|----------|
| 场景边界 | 内容分析 | PySceneDetect + 中间帧 |
| 固定间隔 | 快速预览 | 每 N 秒提取 |
| 质量评估 | 高质量归档 | 清晰度+对比度+人脸检测评分 |

---

## 三、实现方案（怎么办）

### 3.1 用户选择确认
- **架构**: 拆分为两个独立 Skill（video-processor + audio-processor）
- **Whisper 模型**: small（平衡速度与精度）
- **中文 OCR**: PaddleOCR
- **场景检测**: PySceneDetect

### 3.2 技术栈

#### video-processor
```
核心依赖:
- yt-dlp (视频下载)
- ffmpeg-python (音视频处理)
- scenedetect (场景切分)
- paddleocr (画面OCR)
- opencv-python (帧处理)
```

#### audio-processor
```
核心依赖:
- openai-whisper (STT)
- pyannote.audio (说话人分离)
- ffmpeg-python (音频处理)
- silero-vad (语音活动检测)
```

### 3.3 数据流设计

```
┌─────────────────────────────────────────────────────────────┐
│                      数据流架构                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  URL输入 → video-processor                                  │
│     │                                                       │
│     ├─→ yt-dlp 下载 ──→ 视频文件 + 元数据                    │
│     │                                                       │
│     ├─→ ffmpeg 分离音频 ──→ 音频文件 ──→ audio-processor    │
│     │                                    │                  │
│     │                                    ├─→ Whisper 转录   │
│     │                                    ├─→ pyannote 分离  │
│     │                                    └─→ 时间戳对齐     │
│     │                                                       │
│     ├─→ PySceneDetect 场景切分                              │
│     │            │                                          │
│     │            └─→ 关键帧提取 ──→ PaddleOCR 文字识别      │
│     │                                                       │
│     └─→ 结构化输出 (JSON/Markdown)                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.4 Skill 接口设计

#### video-processor
```python
# Skill 暴露的 Tools
def download_video(url: str, quality: str = "best") -> DownloadResult:
    """下载视频并返回文件路径和元数据"""
    ...

def extract_frames(video_path: str, method: str = "scene") -> List[FrameInfo]:
    """提取关键帧"""
    ...

def ocr_frames(frames: List[FrameInfo]) -> List[OCRResult]:
    """对关键帧进行 OCR"""
    ...

def extract_audio(video_path: str) -> str:
    """从视频提取音频轨道"""
    ...
```

#### audio-processor
```python
def transcribe(audio_path: str,
               language: str = "auto",
               model_size: str = "small") -> TranscriptionResult:
    """语音转文字"""
    ...

def diarize(audio_path: str,
            min_speakers: int = 1,
            max_speakers: int = 10) -> DiarizationResult:
    """说话人分离"""
    ...

def transcribe_with_diarization(audio_path: str) -> CombinedResult:
    """转录 + 说话人分离"""
    ...
```

---

## 四、验收标准

- [ ] video-processor 成功下载 B站、YouTube、抖音视频
- [ ] video-processor 正确提取视频元数据（标题、描述、时长）
- [ ] video-processor 准确识别视频画面中的文字（中文准确率>90%）
- [ ] video-processor 正确切分视频场景（边界误差<1秒）
- [ ] audio-processor 中文语音识别准确率>90%
- [ ] audio-processor 说话人分离 DER<20%
- [ ] 两个 Skill 可独立使用，也可协同工作
- [ ] 返回结果结构化，可被 Claude 直接理解和使用

---

## 五、下一步

进入 **Planning 阶段**，创建详细的文件契约和实现计划。
