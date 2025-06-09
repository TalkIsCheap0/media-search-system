# 本地媒体检索系统

基于 Gemma 的本地视频图片智能检索系统，支持自然语言搜索本地媒体文件。

## 功能特性

- 🔍 **智能搜索**: 使用 Gemma 大语言模型进行图像理解和文本搜索
- 🎥 **视频支持**: 自动提取视频关键帧进行索引
- 🖼️ **图片检索**: 支持各种图片格式的智能检索
- 🚀 **统一启动**: 一个脚本启动前后端，支持热更新
- 📱 **现代界面**: React 前端，响应式设计
- 🌐 **前端集成**: 生产模式下前端构建产物完全集成到后端服务

## 系统要求

- Python 3.8+
- Node.js 16+
- Ollama (用于运行 Gemma 模型)

## 快速开始

### 1. 安装 Ollama 和 Gemma 模型

```bash
# 安装Ollama (macOS)
brew install ollama

# 启动Ollama服务
ollama serve

# 在新终端中拉取Gemma模型
ollama pull gemma2:27b
```

### 2. 启动系统

```bash
# 开发模式 (前端热更新)
python start.py --dev

# 生产模式 (构建前端)
python start.py --prod

# 默认开发模式
python start.py
```

### 3. 访问系统

**开发模式**：

- 前端界面: http://localhost:3000 (支持热更新)
- 后端 API: http://localhost:8000

**生产模式**：

- 完整应用: http://localhost:8000 (前端构建产物已集成到后端)
- API 文档: http://localhost:8000/docs

## 使用说明

### 扫描媒体文件

1. 在前端界面中点击"扫描目录"
2. 选择包含图片/视频的文件夹
3. 系统会自动分析并建立索引

### 智能搜索

- 支持中文自然语言搜索
- 例如: "红色的汽车", "海边的风景", "可爱的小猫"
- Gemma 会理解查询内容并匹配相关图片

### 配置选项

系统配置在 `backend/media_processor.py` 中：

```python
config = {
    "gemma_model": "gemma2:27b",        # Gemma模型名称
    "ollama_host": "http://localhost:11434",  # Ollama服务地址
    "batch_size": 2,                    # 批处理大小
    "max_workers": 1,                   # 并发工作数
}
```

## 项目结构

```
local-nas/
├── start.py              # 统一启动脚本
├── backend/              # 后端代码
│   ├── main.py          # FastAPI应用
│   ├── gemma_processor.py # Gemma特征提取器
│   ├── media_processor.py # 媒体处理引擎
│   ├── search_engine.py  # 搜索引擎
│   └── ...
├── frontend/             # React前端
│   ├── src/
│   ├── public/
│   └── package.json
└── requirements.txt      # Python依赖
```

## 开发说明

### 启动脚本功能

- **依赖检查**: 自动检查并安装 Python 和 Node.js 依赖
- **前端热更新**: 开发模式下支持前端代码热更新
- **静态文件托管**: 生产模式下后端直接托管前端构建产物
- **进程管理**: 统一管理前后端进程，Ctrl+C 优雅退出

### 前端集成特性

- **单端口访问**: 生产模式下通过一个端口访问完整应用
- **SPA 路由支持**: 支持 React Router 等前端路由，自动 fallback 到 index.html
- **静态资源优化**: 正确设置 MIME 类型和缓存头部
- **API 路由保护**: 确保/api/\*路径不被前端路由覆盖

### Gemma 集成

- 使用 Ollama API 调用本地 Gemma 模型
- 支持图像分析和文本理解
- 自动生成语义特征向量
- 支持查询增强和关键词提取

## 故障排除

### Ollama 连接失败

```bash
# 检查Ollama是否运行
ollama list

# 重启Ollama服务
ollama serve
```

### 模型未找到

```bash
# 确认模型已安装
ollama list

# 重新拉取模型
ollama pull gemma2:27b
```

### 前端依赖问题

```bash
# 清理并重新安装
cd frontend
rm -rf node_modules package-lock.json
tnpm install
```

## 部署说明

### 生产环境部署

1. **构建前端应用**：

   ```bash
   cd frontend
   tnpm run build
   ```

2. **启动生产服务**：

   ```bash
   python start.py --prod
   ```

3. **多 worker 部署**：
   ```bash
   python start.py --prod --workers 4
   ```

### 前端构建产物结构

```
frontend/build/
├── index.html          # 主页面
├── static/            # 静态资源
│   ├── css/          # 样式文件
│   └── js/           # JavaScript文件
└── asset-manifest.json # 资源清单
```

### 服务端路由映射

- `/` → 前端应用首页 (index.html)
- `/static/*` → 前端静态资源 (CSS、JS 等)
- `/assets/*` → 前端资源文件 (favicon、manifest 等)
- `/api/*` → 后端 API 接口
- `/{path}` → SPA 路由 fallback 到 index.html

## 性能优化

- Gemma 处理速度较慢，建议使用较小的批次大小
- 可以考虑使用更小的模型如 `gemma2:9b` 提升速度
- 大量文件处理时建议分批进行
- 生产模式下使用多 worker 提升并发处理能力

## 许可证

MIT License
