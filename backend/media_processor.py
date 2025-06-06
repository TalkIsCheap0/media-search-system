import os
import hashlib
from typing import List, Dict, Any, Optional
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from pathlib import Path

from database import DatabaseManager
from clip_processor import CLIPFeatureExtractor
from video_processor import VideoKeyframeExtractor, ImageProcessor
from file_scanner import MediaFileScanner
from search_engine import SearchEngine

logger = logging.getLogger(__name__)

class MediaProcessingEngine:
    def __init__(self, config: Dict[str, Any] = None):
        """
        媒体处理引擎
        Args:
            config: 配置参数
        """
        self.config = config or {
            "db_path": "./media.db",
            "chroma_path": "./chroma_db",
            "clip_model": "ViT-L/14",
            "device": "cpu",
            "batch_size": 4,
            "max_workers": 2,
            "keyframe_config": {
                "scene_change_threshold": 0.8,
                "min_frame_interval": 15,
                "time_sampling_interval": 5,
                "motion_threshold": 20,
                "max_duration_hours": 10,
            }
        }
        
        # 初始化组件
        self._init_components()
        
        # 处理状态
        self.processing_status = {
            "is_processing": False,
            "current_file": "",
            "processed_count": 0,
            "total_count": 0,
            "errors": []
        }
        self._status_lock = threading.Lock()
    
    def _init_components(self):
        """初始化所有组件"""
        logger.info("初始化媒体处理引擎...")
        
        # 不再创建缩略图目录
        
        # 初始化数据库
        self.db = DatabaseManager(
            db_path=self.config["db_path"],
            chroma_path=self.config["chroma_path"]
        )
        
        # 初始化CLIP模型
        self.clip = CLIPFeatureExtractor(
            model_name=self.config["clip_model"],
            device=self.config["device"]
        )
        
        # 初始化处理器
        self.video_processor = VideoKeyframeExtractor(self.config["keyframe_config"])
        self.image_processor = ImageProcessor()
        self.file_scanner = MediaFileScanner()
        
        # 初始化搜索引擎
        self.search_engine = SearchEngine(self.db, self.clip)
        
        logger.info("媒体处理引擎初始化完成")
    
    def scan_and_process_directory(self, directory_path: str, recursive: bool = True) -> Dict[str, Any]:
        """
        扫描并处理目录中的所有媒体文件
        Args:
            directory_path: 目录路径
            recursive: 是否递归扫描
        Returns:
            处理结果统计
        """
        logger.info(f"开始扫描并处理目录: {directory_path}")
        
        try:
            # 扫描文件
            media_files = self.file_scanner.scan_directory(directory_path, recursive)
            
            # 处理文件
            results = self.process_media_files(
                media_files['images'] + media_files['videos']
            )
            
            return {
                "success": True,
                "scanned_images": len(media_files['images']),
                "scanned_videos": len(media_files['videos']),
                "processed_files": results['processed_count'],
                "failed_files": results['failed_count'],
                "errors": results['errors']
            }
            
        except Exception as e:
            logger.error(f"目录处理失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "processed_files": 0,
                "failed_files": 0
            }
    
    def process_media_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        批量处理媒体文件
        Args:
            file_paths: 文件路径列表
        Returns:
            处理结果
        """
        with self._status_lock:
            self.processing_status.update({
                "is_processing": True,
                "processed_count": 0,
                "total_count": len(file_paths),
                "errors": []
            })
        
        processed_count = 0
        failed_count = 0
        errors = []
        
        try:
            # 使用线程池并行处理
            with ThreadPoolExecutor(max_workers=self.config["max_workers"]) as executor:
                # 提交所有任务
                future_to_file = {
                    executor.submit(self._process_single_file, file_path): file_path
                    for file_path in file_paths
                }
                
                # 收集结果
                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
                    
                    with self._status_lock:
                        self.processing_status["current_file"] = file_path
                    
                    try:
                        result = future.result()
                        if result["success"]:
                            processed_count += 1
                        else:
                            failed_count += 1
                            errors.append({
                                "file": file_path,
                                "error": result["error"]
                            })
                    except Exception as e:
                        failed_count += 1
                        errors.append({
                            "file": file_path,
                            "error": str(e)
                        })
                    
                    with self._status_lock:
                        self.processing_status["processed_count"] = processed_count + failed_count
                        self.processing_status["errors"] = errors
                    
                    logger.info(f"处理进度: {processed_count + failed_count}/{len(file_paths)}")
        
        finally:
            with self._status_lock:
                self.processing_status["is_processing"] = False
        
        return {
            "processed_count": processed_count,
            "failed_count": failed_count,
            "errors": errors
        }
    
    def _process_single_file(self, file_path: str) -> Dict[str, Any]:
        """
        处理单个文件
        Args:
            file_path: 文件路径
        Returns:
            处理结果
        """
        try:
            # 检查文件是否已存在
            existing_file = self.db.get_media_file_by_path(file_path)
            if existing_file:
                logger.info(f"文件已存在，跳过: {file_path}")
                return {"success": True, "message": "文件已存在"}
            
            # 判断文件类型
            is_supported, file_type = self.file_scanner.is_supported_file(file_path)
            if not is_supported:
                return {"success": False, "error": "不支持的文件格式"}
            
            if file_type == "video":
                return self._process_video_file(file_path)
            elif file_type == "image":
                return self._process_image_file(file_path)
            else:
                return {"success": False, "error": "未知文件类型"}
                
        except Exception as e:
            logger.error(f"处理文件失败 {file_path}: {e}")
            return {"success": False, "error": str(e)}
    
    def _process_video_file(self, video_path: str) -> Dict[str, Any]:
        """处理视频文件"""
        logger.info(f"开始处理视频: {video_path}")
        
        # 获取视频信息
        video_info = self.video_processor.get_video_info(video_path)
        
        # 提取关键帧
        keyframes = self.video_processor.extract_keyframes_high_recall(
            video_path
        )
        
        # 添加视频文件记录
        media_file_id = self.db.add_media_file(
            file_path=video_path,
            file_type="video",
            duration=video_info["duration"],
            fps=video_info["fps"],
            width=video_info["width"],
            height=video_info["height"]
        )
        
        # 批量提取CLIP特征
        frame_images = [kf["frame_data"] for kf in keyframes]
        embeddings = self.clip.batch_extract_image_features(
            frame_images, batch_size=self.config["batch_size"]
        )
        
        # 准备向量数据库数据
        vector_embeddings = []
        vector_metadatas = []
        vector_ids = []
        
        # 生成视频hash用于向量ID
        video_hash = hashlib.md5(video_path.encode()).hexdigest()[:12]
        
        for i, (keyframe, embedding) in enumerate(zip(keyframes, embeddings)):
            vector_id = f"{video_hash}_{keyframe['frame_index']}"
            
            # 添加关键帧记录
            self.db.add_keyframe(
                media_file_id=media_file_id,
                frame_index=keyframe["frame_index"],
                timestamp=keyframe["timestamp"],
                thumbnail_path="",  # 使用空字符串而不是None
                vector_id=vector_id,
                extraction_method=keyframe["extraction_method"]
            )
            
            # 准备向量数据
            vector_embeddings.append(embedding.tolist())
            vector_metadatas.append({
                "file_path": video_path,
                "type": "video_frame",
                "frame_index": keyframe["frame_index"],
                "timestamp": keyframe["timestamp"],
                "extraction_method": keyframe["extraction_method"]
            })
            vector_ids.append(vector_id)
        
        # 批量添加到向量数据库
        self.db.add_embeddings(vector_embeddings, vector_metadatas, vector_ids)
        
        logger.info(f"视频处理完成: {video_path} (提取 {len(keyframes)} 个关键帧)")
        
        return {
            "success": True,
            "keyframe_count": len(keyframes),
            "duration": video_info["duration"]
        }
    
    def _process_image_file(self, image_path: str) -> Dict[str, Any]:
        """处理图片文件"""
        logger.info(f"开始处理图片: {image_path}")
        
        # 处理图片
        image_info = self.image_processor.process_image(image_path)
        
        # 添加图片文件记录
        media_file_id = self.db.add_media_file(
            file_path=image_path,
            file_type="image",
            width=image_info["width"],
            height=image_info["height"]
        )
        
        # 提取CLIP特征
        embedding = self.clip.extract_image_features(image_info["frame_data"])
        
        # 生成向量ID
        image_hash = hashlib.md5(image_path.encode()).hexdigest()[:12]
        vector_id = f"img_{image_hash}"
        
        # 添加到向量数据库
        self.db.add_embeddings(
            embeddings=[embedding.tolist()],
            metadatas=[{
                "file_path": image_path,
                "type": "image",
                "width": image_info["width"],
                "height": image_info["height"]
            }],
            ids=[vector_id]
        )
        
        logger.info(f"图片处理完成: {image_path}")
        
        return {
            "success": True,
            "width": image_info["width"],
            "height": image_info["height"]
        }
    
    def search_media(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        搜索媒体文件
        Args:
            query: 搜索查询
            **kwargs: 其他搜索参数
        Returns:
            搜索结果
        """
        return self.search_engine.search(query, **kwargs)
    
    def get_processing_status(self) -> Dict[str, Any]:
        """获取处理状态"""
        with self._status_lock:
            return self.processing_status.copy()
    
    def get_database_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        try:
            media_files = self.db.get_all_media_files()
            
            stats = {
                "total_files": len(media_files),
                "image_count": 0,
                "video_count": 0,
                "total_keyframes": 0
            }
            
            for file_info in media_files:
                if file_info["file_type"] == "image":
                    stats["image_count"] += 1
                elif file_info["file_type"] == "video":
                    stats["video_count"] += 1
                    # 获取该视频的关键帧数量
                    keyframes = self.db.get_keyframes_by_media_id(file_info["id"])
                    stats["total_keyframes"] += len(keyframes)
            
            return stats
            
        except Exception as e:
            logger.error(f"获取数据库统计失败: {e}")
            return {
                "total_files": 0,
                "image_count": 0,
                "video_count": 0,
                "total_keyframes": 0,
                "error": str(e)
            } 