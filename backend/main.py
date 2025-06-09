from fastapi import FastAPI, HTTPException, BackgroundTasks, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import os
import asyncio
from pathlib import Path

from media_processor import MediaProcessingEngine

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="本地媒体检索系统",
    description="基于Gemma的本地视频图片检索系统",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载前端静态文件
frontend_build_path = Path(__file__).parent.parent / "frontend" / "build"
if frontend_build_path.exists():
    # 挂载前端构建产物中的静态资源（CSS、JS等）
    app.mount("/static", StaticFiles(directory=str(frontend_build_path / "static")), name="static")
    
    # 挂载其他前端资源（如favicon、manifest等）
    app.mount("/assets", StaticFiles(directory=str(frontend_build_path)), name="assets")
    
    logger.info(f"前端静态文件已挂载: {frontend_build_path}")
else:
    logger.warning("前端构建目录不存在，请先构建前端应用")

# 媒体处理引擎实例（延迟初始化以支持多worker）
media_engine = None

def get_media_engine():
    """获取媒体处理引擎实例（单例模式）"""
    global media_engine
    if media_engine is None:
        media_engine = MediaProcessingEngine()
    return media_engine

# 不再挂载缩略图静态文件服务

# Pydantic模型
class ScanRequest(BaseModel):
    directory_path: str
    recursive: bool = True

class SearchRequest(BaseModel):
    query: str
    max_results: int = 50
    aggregation_strategy: str = "multiple_scenes"
    similarity_threshold: float = 0.1
    filters: Optional[Dict[str, Any]] = None

class ProcessFilesRequest(BaseModel):
    file_paths: List[str]

# 根路径处理 - 返回前端应用
@app.get("/")
async def root():
    """根路径 - 返回前端应用"""
    frontend_build_path = Path(__file__).parent.parent / "frontend" / "build"
    index_path = frontend_build_path / "index.html"
    
    if index_path.exists():
        return FileResponse(index_path, media_type="text/html")
    else:
        # 如果前端未构建，返回API信息
        return {
            "message": "本地媒体检索系统API",
            "version": "1.0.0",
            "status": "运行中",
            "note": "前端应用未构建，请运行 'tnpm run build' 构建前端"
        }

@app.get("/api/status")
async def get_system_status():
    """获取系统状态"""
    try:
        engine = get_media_engine()
        processing_status = engine.get_processing_status()
        db_stats = engine.get_database_stats()
        
        # 检查前端构建状态
        frontend_build_path = Path(__file__).parent.parent / "frontend" / "build"
        frontend_status = {
            "built": frontend_build_path.exists(),
            "build_path": str(frontend_build_path),
            "index_exists": (frontend_build_path / "index.html").exists() if frontend_build_path.exists() else False
        }
        
        return {
            "success": True,
            "processing": processing_status,
            "database": db_stats,
            "frontend": frontend_status,
            "system": {
                "gemma_model": engine.config["gemma_model"],
                "ollama_host": engine.config["ollama_host"]
            }
        }
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scan")
async def scan_directory(request: ScanRequest, background_tasks: BackgroundTasks):
    """扫描目录"""
    print(request)
    try:
        # 验证目录路径
        if not os.path.exists(request.directory_path):
            raise HTTPException(status_code=400, detail="目录不存在")
        
        if not os.path.isdir(request.directory_path):
            raise HTTPException(status_code=400, detail="路径不是目录")
        
        # 在后台任务中执行扫描
        engine = get_media_engine()
        background_tasks.add_task(
            engine.scan_and_process_directory,
            request.directory_path,
            request.recursive
        )
        
        return {
            "success": True,
            "message": "扫描任务已启动",
            "directory": request.directory_path,
            "recursive": request.recursive
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"扫描目录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/process-files")
async def process_files(request: ProcessFilesRequest, background_tasks: BackgroundTasks):
    """处理指定文件列表"""
    try:
        # 验证文件路径
        valid_files = []
        for file_path in request.file_paths:
            if os.path.exists(file_path) and os.path.isfile(file_path):
                valid_files.append(file_path)
        
        if not valid_files:
            raise HTTPException(status_code=400, detail="没有有效的文件路径")
        
        # 在后台任务中执行处理
        engine = get_media_engine()
        background_tasks.add_task(
            engine.process_media_files,
            valid_files
        )
        
        return {
            "success": True,
            "message": "文件处理任务已启动",
            "valid_files": len(valid_files),
            "total_files": len(request.file_paths)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"处理文件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search")
async def search_media(request: SearchRequest):
    """搜索媒体文件"""
    try:
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="搜索查询不能为空")
        
        engine = get_media_engine()
        results = engine.search_media(
            query=request.query,
            max_results=request.max_results,
            aggregation_strategy=request.aggregation_strategy,
            similarity_threshold=request.similarity_threshold,
            filters=request.filters
        )
        
        return {
            "success": True,
            "query": request.query,
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"搜索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/video/{video_id}/details")
async def get_video_details(video_id: str):
    """获取视频详细信息"""
    try:
        # 这里需要根据video_id获取视频路径
        # 简化实现：假设video_id就是base64编码的文件路径
        import base64
        try:
            video_path = base64.b64decode(video_id).decode('utf-8')
        except:
            raise HTTPException(status_code=400, detail="无效的视频ID")
        
        engine = get_media_engine()
        details = engine.search_engine.get_video_details(video_path)
        
        return {
            "success": True,
            "video_details": details
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取视频详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/similar-images")
async def get_similar_images(image_path: str, max_results: int = 20):
    """获取相似图片"""
    try:
        if not os.path.exists(image_path):
            raise HTTPException(status_code=400, detail="图片文件不存在")
        
        engine = get_media_engine()
        similar_images = engine.search_engine.get_similar_images(
            image_path, max_results
        )
        
        return {
            "success": True,
            "reference_image": image_path,
            "similar_images": similar_images
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取相似图片失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/processing-status")
async def get_processing_status():
    """获取处理状态"""
    try:
        engine = get_media_engine()
        status = engine.get_processing_status()
        return {
            "success": True,
            "status": status
        }
    except Exception as e:
        logger.error(f"获取处理状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/database-stats")
async def get_database_stats():
    """获取数据库统计"""
    try:
        engine = get_media_engine()
        stats = engine.get_database_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"获取数据库统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/media-files")
async def get_media_files(skip: int = 0, limit: int = 100):
    """获取媒体文件列表"""
    try:
        engine = get_media_engine()
        all_files = engine.db.get_all_media_files()
        
        # 简单分页
        paginated_files = all_files[skip:skip + limit]
        
        return {
            "success": True,
            "files": paginated_files,
            "total": len(all_files),
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"获取媒体文件列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传文件并处理"""
    try:
        # 创建上传目录
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # 保存文件
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 处理文件
        engine = get_media_engine()
        result = engine._process_single_file(file_path)
        
        return {
            "success": True,
            "filename": file.filename,
            "file_path": file_path,
            "processing_result": result
        }
        
    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 缩略图API已移除 - 现在直接使用原始媒体文件

@app.delete("/api/media/{media_id}")
async def delete_media(media_id: int):
    """删除媒体文件记录"""
    try:
        # 这里应该实现删除逻辑
        # 包括删除数据库记录、向量数据、缩略图等
        return {
            "success": True,
            "message": f"媒体文件 {media_id} 已删除"
        }
        
    except Exception as e:
        logger.error(f"删除媒体文件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/media/{file_path:path}")
async def get_media_file(file_path: str):
    """获取原始媒体文件"""
    try:
        # 解码文件路径
        import urllib.parse
        decoded_path = urllib.parse.unquote(file_path)
        
        if not os.path.exists(decoded_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return FileResponse(decoded_path)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取媒体文件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 健康检查
@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z"
    }

# 前端路由处理 - 必须放在最后，作为fallback
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """托管前端应用"""
    frontend_build_path = Path(__file__).parent.parent / "frontend" / "build"
    
    # 如果前端构建目录不存在，返回404
    if not frontend_build_path.exists():
        raise HTTPException(status_code=404, detail="Frontend not built")
    
    # 跳过API路由
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    # 尝试返回请求的文件
    file_path = frontend_build_path / full_path
    if file_path.exists() and file_path.is_file():
        # 根据文件扩展名设置正确的Content-Type
        import mimetypes
        content_type, _ = mimetypes.guess_type(str(file_path))
        return FileResponse(file_path, media_type=content_type)
    
    # 对于SPA路由（React Router等），返回index.html
    index_path = frontend_build_path / "index.html"
    if index_path.exists():
        return FileResponse(index_path, media_type="text/html")
    
    raise HTTPException(status_code=404, detail="Frontend resource not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 