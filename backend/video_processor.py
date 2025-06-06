import cv2
import numpy as np
import os
from typing import List, Tuple, Dict, Any
from PIL import Image
import logging

logger = logging.getLogger(__name__)

class VideoKeyframeExtractor:
    def __init__(self, config: Dict[str, Any] = None):
        """
        视频关键帧提取器
        Args:
            config: 配置参数
        """
        self.config = config or {
            "scene_change_threshold": 0.8,      # 场景变化阈值
            "min_frame_interval": 15,           # 最小帧间隔
            "time_sampling_interval": 5,        # 时间采样间隔(秒)
            "motion_threshold": 20,             # 运动检测阈值
            "max_duration_hours": 10,           # 最大处理时长(小时)
        }
    
    def extract_keyframes_high_recall(self, video_path: str, output_dir: str = None) -> List[Dict[str, Any]]:
        """
        高召回率关键帧提取 - 不生成缩略图文件
        Args:
            video_path: 视频文件路径
            output_dir: 输出目录（保留参数以兼容现有代码，但不使用）
        Returns:
            关键帧信息列表
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")
        
        # 获取视频信息
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = total_frames / fps if fps > 0 else 0
        
        logger.info(f"开始处理视频: {video_path}")
        logger.info(f"视频信息 - 总帧数: {total_frames}, FPS: {fps:.2f}, 时长: {duration:.2f}秒")
        
        # 检查视频时长限制
        if duration > self.config["max_duration_hours"] * 3600:
            logger.warning(f"视频时长超过限制 ({self.config['max_duration_hours']}小时)，将进行采样处理")
        
        # 多策略提取关键帧
        keyframes = []
        
        # 策略1: 场景变化检测
        scene_frames = self._detect_scene_changes(cap, video_path)
        logger.info(f"场景变化检测提取了 {len(scene_frames)} 个关键帧")
        
        # 策略2: 时间均匀采样
        time_frames = self._extract_time_based_frames(cap, video_path)
        logger.info(f"时间采样提取了 {len(time_frames)} 个关键帧")
        
        # 策略3: 运动检测
        motion_frames = self._detect_motion_keyframes(cap, video_path)
        logger.info(f"运动检测提取了 {len(motion_frames)} 个关键帧")
        
        # 合并并去重
        all_frames = scene_frames + time_frames + motion_frames
        unique_frames = self._remove_duplicate_frames(all_frames)
        
        logger.info(f"去重后共有 {len(unique_frames)} 个关键帧")
        
        # 生成结果（不保存缩略图文件）
        for i, (frame_idx, frame, method) in enumerate(unique_frames):
            timestamp = frame_idx / fps if fps > 0 else 0
            
            keyframes.append({
                "frame_index": frame_idx,
                "timestamp": timestamp,
                "thumbnail_path": "",  # 使用空字符串而不是None
                "extraction_method": method,
                "frame_data": frame  # 保持原始帧数据用于特征提取
            })
        
        cap.release()
        logger.info(f"视频处理完成，共提取 {len(keyframes)} 个关键帧")
        
        return keyframes
    
    def _detect_scene_changes(self, cap: cv2.VideoCapture, video_path: str) -> List[Tuple[int, np.ndarray, str]]:
        """场景变化检测"""
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        keyframes = []
        prev_hist = None
        frame_count = 0
        last_keyframe = -self.config["min_frame_interval"]
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 计算更细粒度的直方图
            hist = cv2.calcHist([frame], [0, 1, 2], None, [16, 16, 16], [0, 256, 0, 256, 0, 256])
            hist = cv2.normalize(hist, hist).flatten()
            
            if prev_hist is not None:
                similarity = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CORREL)
                if (similarity < self.config["scene_change_threshold"] and 
                    (frame_count - last_keyframe) >= self.config["min_frame_interval"]):
                    keyframes.append((frame_count, frame.copy(), "scene_change"))
                    last_keyframe = frame_count
            else:
                # 第一帧
                keyframes.append((frame_count, frame.copy(), "first_frame"))
                last_keyframe = frame_count
            
            prev_hist = hist
            frame_count += 1
        
        return keyframes
    
    def _extract_time_based_frames(self, cap: cv2.VideoCapture, video_path: str) -> List[Tuple[int, np.ndarray, str]]:
        """基于时间的均匀采样"""
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(fps * self.config["time_sampling_interval"]) if fps > 0 else 150
        
        keyframes = []
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % frame_interval == 0:
                keyframes.append((frame_count, frame.copy(), "time_sampling"))
            
            frame_count += 1
        
        return keyframes
    
    def _detect_motion_keyframes(self, cap: cv2.VideoCapture, video_path: str) -> List[Tuple[int, np.ndarray, str]]:
        """运动检测"""
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        keyframes = []
        prev_gray = None
        frame_count = 0
        last_motion_frame = -30  # 运动帧最小间隔
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            if prev_gray is not None:
                # 计算帧差
                diff = cv2.absdiff(prev_gray, gray)
                motion_score = np.mean(diff)
                
                if (motion_score > self.config["motion_threshold"] and 
                    (frame_count - last_motion_frame) >= 30):
                    keyframes.append((frame_count, frame.copy(), "motion_detection"))
                    last_motion_frame = frame_count
            
            prev_gray = gray
            frame_count += 1
        
        return keyframes
    
    def _remove_duplicate_frames(self, frames: List[Tuple[int, np.ndarray, str]], 
                               min_distance: int = 10) -> List[Tuple[int, np.ndarray, str]]:
        """去除重复和过于接近的帧"""
        if not frames:
            return []
        
        # 按帧索引排序
        frames.sort(key=lambda x: x[0])
        
        unique_frames = [frames[0]]
        
        for frame_idx, frame, method in frames[1:]:
            # 检查与最后一个关键帧的距离
            if frame_idx - unique_frames[-1][0] >= min_distance:
                unique_frames.append((frame_idx, frame, method))
        
        return unique_frames
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """获取视频基本信息"""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")
        
        info = {
            "total_frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            "fps": cap.get(cv2.CAP_PROP_FPS),
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "duration": 0
        }
        
        if info["fps"] > 0:
            info["duration"] = info["total_frames"] / info["fps"]
        
        cap.release()
        return info

class ImageProcessor:
    def __init__(self):
        """
        图像处理器 - 不再生成缩略图
        """
        pass
    
    def process_image(self, image_path: str, output_dir: str = None) -> Dict[str, Any]:
        """
        处理单张图像 - 不进行压缩和缩略图生成
        Args:
            image_path: 图像文件路径
            output_dir: 输出目录（保留参数以兼容现有代码，但不使用）
        Returns:
            图像信息
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图像文件不存在: {image_path}")
        
        # 读取图像获取基本信息
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"无法读取图像文件: {image_path}")
        
        height, width = image.shape[:2]
        
        return {
            "width": width,
            "height": height,
            "thumbnail_path": "",  # 使用空字符串而不是None
            "frame_data": image  # 用于特征提取，保持原始尺寸
        } 