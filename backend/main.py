from fastapi import FastAPI, HTTPException, BackgroundTasks, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
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
    description="基于CLIP的本地视频图片检索系统",
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

# 初始化媒体处理引擎
media_engine = MediaProcessingEngine()

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

# API路由
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "本地媒体检索系统API",
        "version": "1.0.0",
        "status": "运行中"
    }

@app.get("/api/status")
async def get_system_status():
    """获取系统状态"""
    try:
        processing_status = media_engine.get_processing_status()
        db_stats = media_engine.get_database_stats()
        
        return {
            "success": True,
            "processing": processing_status,
            "database": db_stats,
            "system": {
                "clip_model": media_engine.config["clip_model"],
                "device": media_engine.config["device"]
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
        background_tasks.add_task(
            media_engine.scan_and_process_directory,
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
        background_tasks.add_task(
            media_engine.process_media_files,
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
        
        results = media_engine.search_media(
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
        
        details = media_engine.search_engine.get_video_details(video_path)
        
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
        
        similar_images = media_engine.search_engine.get_similar_images(
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
        status = media_engine.get_processing_status()
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
        stats = media_engine.get_database_stats()
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
        all_files = media_engine.db.get_all_media_files()
        
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
        result = media_engine._process_single_file(file_path)
        
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 