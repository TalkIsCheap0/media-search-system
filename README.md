# 本地媒体检索系统

基于 CLIP 模型的智能本地图片视频检索系统，支持自然语言搜索，完全离线运行。

## 功能特性

### 🔍 智能检索

- 基于 CLIP 模型的语义理解
- 支持自然语言描述搜索
- 跨模态检索（文本搜图片/视频）
- 智能结果聚合和排序

### 🎬 视频处理

- 多策略关键帧提取
- 场景变化自动检测
- 高召回率时间采样
- 精确时间戳定位

### 🔒 本地部署

- 完全离线运行
- 数据隐私保护
- 无需网络连接
- 支持大规模文件处理

### 💻 用户体验

- 现代化 Web 界面
- 实时处理进度显示
- 响应式设计
- 直观的搜索结果展示

## 技术架构

### 后端

- **FastAPI**: 高性能 Web 框架
- **CLIP**: OpenAI 的视觉语言模型
- **ChromaDB**: 向量数据库
- **SQLite**: 元数据存储
- **OpenCV**: 视频处理

### 前端

- **React**: 用户界面框架
- **Tailwind CSS**: 样式框架
- **Axios**: HTTP 客户端

## 安装部署

### 环境要求

- Python 3.8+
- Node.js 16+
- 至少 4GB 内存
- 足够的磁盘空间存储缩略图和数据库

### 1. 克隆项目

```bash
git clone <repository-url>
cd local-nas
```

### 2. 安装后端依赖

```bash
pip install -r requirements.txt
```

### 3. 安装前端依赖

```bash
cd frontend
npm install
cd ..
```

### 4. 启动后端服务

```bash
python start_backend.py
```

后端服务将在 http://localhost:8000 启动

### 5. 启动前端服务

```bash
cd frontend
npm start
```

前端服务将在 http://localhost:3000 启动

## 使用指南

### 1. 扫描文件

1. 访问 http://localhost:3000
2. 点击"扫描文件"
3. 输入要扫描的目录路径
4. 选择是否递归扫描子目录
5. 点击"开始扫描"

### 2. 搜索媒体

1. 点击"智能搜索"
2. 输入自然语言描述，例如：
   - "海边的日落"
   - "猫咪在玩耍"
   - "生日聚会"
   - "雪山风景"
3. 调整搜索参数（可选）
4. 查看搜索结果

### 3. 查看状态

- 点击"系统状态"查看处理进度
- 监控数据库统计信息
- 查看错误日志

## 支持的文件格式

### 图片格式

- JPG, JPEG, PNG, GIF, BMP
- TIFF, TIF, WebP, SVG, ICO
- HEIC, HEIF

### 视频格式

- MP4, AVI, MKV, MOV, WMV
- FLV, WebM, M4V, 3GP, 3G2
- MTS, M2TS, TS, VOB, ASF
- RM, RMVB, DivX, XviD

## 配置说明

### 后端配置

在 `backend/media_processor.py` 中可以调整以下配置：

```python
config = {
    "thumbnails_dir": "./thumbnails",      # 缩略图存储目录
    "db_path": "./media.db",               # SQLite数据库路径
    "chroma_path": "./chroma_db",          # ChromaDB存储路径
    "clip_model": "openai/clip-vit-base-patch32",  # CLIP模型
    "device": "cpu",                       # 运行设备 (cpu/cuda)
    "batch_size": 8,                       # 批处理大小
    "max_workers": 2,                      # 最大并行工作线程
    "keyframe_config": {
        "scene_change_threshold": 0.8,     # 场景变化阈值
        "min_frame_interval": 15,          # 最小帧间隔
        "time_sampling_interval": 5,       # 时间采样间隔(秒)
        "motion_threshold": 20,            # 运动检测阈值
        "thumbnail_size": (224, 224),      # 缩略图尺寸
        "max_duration_hours": 10,          # 最大处理时长(小时)
    }
}
```

## 性能优化

### 硬件建议

- **CPU**: 多核处理器，推荐 8 核以上
- **内存**: 8GB 以上，处理大量文件时建议 16GB+
- **存储**: SSD 硬盘，提高文件读取速度
- **GPU**: 可选，设置 `device: "cuda"` 启用 GPU 加速

### 处理优化

- 调整 `batch_size` 和 `max_workers` 参数
- 根据硬件配置调整关键帧提取参数
- 定期清理不需要的缩略图文件

## 故障排除

### 常见问题

1. **CLIP 模型下载失败**

   - 检查网络连接
   - 手动下载模型文件到缓存目录

2. **内存不足**

   - 减少 `batch_size` 参数
   - 减少 `max_workers` 参数
   - 增加系统内存

3. **处理速度慢**

   - 启用 GPU 加速（如果有 NVIDIA GPU）
   - 调整关键帧提取参数
   - 使用 SSD 存储

4. **搜索结果不准确**
   - 降低相似度阈值
   - 尝试不同的搜索关键词
   - 检查文件是否正确处理

### 日志查看

- 后端日志：`media_search.log`
- 浏览器控制台：F12 查看前端错误

## 开发说明

### 项目结构

```
local-nas/
├── backend/                 # 后端代码
│   ├── main.py             # FastAPI 主应用
│   ├── database.py         # 数据库管理
│   ├── clip_processor.py   # CLIP 模型处理
│   ├── video_processor.py  # 视频处理
│   ├── file_scanner.py     # 文件扫描
│   ├── search_engine.py    # 搜索引擎
│   └── media_processor.py  # 媒体处理引擎
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── components/     # React 组件
│   │   ├── pages/          # 页面组件
│   │   └── App.js          # 主应用
│   └── public/
├── requirements.txt        # Python 依赖
├── start_backend.py       # 后端启动脚本
└── README.md              # 项目说明
```

### 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 发起 Pull Request

## 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。

## 致谢

- [OpenAI CLIP](https://github.com/openai/CLIP) - 视觉语言模型
- [ChromaDB](https://github.com/chroma-core/chroma) - 向量数据库
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架
- [React](https://reactjs.org/) - 前端框架
