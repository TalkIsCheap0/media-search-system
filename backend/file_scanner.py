import os
import hashlib
from typing import List, Dict, Set, Generator, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class MediaFileScanner:
    def __init__(self):
        """媒体文件扫描器"""
        # 支持的图片格式
        self.image_extensions = {
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif',
            '.webp', '.svg', '.ico', '.heic', '.heif'
        }
        
        # 支持的视频格式
        self.video_extensions = {
            '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm',
            '.m4v', '.3gp', '.3g2', '.mts', '.m2ts', '.ts', '.vob',
            '.asf', '.rm', '.rmvb', '.divx', '.xvid'
        }
        
        # 需要跳过的目录
        self.skip_directories = {
            '.git', '.svn', '.hg', '__pycache__', '.DS_Store',
            'node_modules', '.vscode', '.idea', 'thumbnails'
        }
    
    def scan_directory(self, directory_path: str, recursive: bool = True) -> Dict[str, List[str]]:
        """
        扫描目录中的媒体文件
        Args:
            directory_path: 要扫描的目录路径
            recursive: 是否递归扫描子目录
        Returns:
            包含图片和视频文件路径的字典
        """
        if not os.path.exists(directory_path):
            raise FileNotFoundError(f"目录不存在: {directory_path}")
        
        if not os.path.isdir(directory_path):
            raise ValueError(f"路径不是目录: {directory_path}")
        
        logger.info(f"开始扫描目录: {directory_path} (递归: {recursive})")
        
        media_files = {
            'images': [],
            'videos': []
        }
        
        total_files = 0
        
        for file_path in self._walk_directory(directory_path, recursive):
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext in self.image_extensions:
                media_files['images'].append(file_path)
                total_files += 1
            elif file_ext in self.video_extensions:
                media_files['videos'].append(file_path)
                total_files += 1
        
        logger.info(f"扫描完成 - 图片: {len(media_files['images'])} 个, "
                   f"视频: {len(media_files['videos'])} 个, 总计: {total_files} 个文件")
        
        return media_files
    
    def _walk_directory(self, directory_path: str, recursive: bool) -> Generator[str, None, None]:
        """
        遍历目录中的文件
        Args:
            directory_path: 目录路径
            recursive: 是否递归
        Yields:
            文件路径
        """
        try:
            if recursive:
                for root, dirs, files in os.walk(directory_path):
                    # 过滤掉需要跳过的目录
                    dirs[:] = [d for d in dirs if d not in self.skip_directories]
                    
                    for file in files:
                        if not file.startswith('.'):  # 跳过隐藏文件
                            yield os.path.join(root, file)
            else:
                # 只扫描当前目录
                for item in os.listdir(directory_path):
                    item_path = os.path.join(directory_path, item)
                    if os.path.isfile(item_path) and not item.startswith('.'):
                        yield item_path
        except PermissionError as e:
            logger.warning(f"权限不足，跳过目录: {directory_path} - {e}")
        except Exception as e:
            logger.error(f"扫描目录时出错: {directory_path} - {e}")
    
    def scan_multiple_directories(self, directories: List[str], recursive: bool = True) -> Dict[str, List[str]]:
        """
        扫描多个目录
        Args:
            directories: 目录路径列表
            recursive: 是否递归扫描
        Returns:
            合并后的媒体文件字典
        """
        combined_results = {
            'images': [],
            'videos': []
        }
        
        for directory in directories:
            try:
                results = self.scan_directory(directory, recursive)
                combined_results['images'].extend(results['images'])
                combined_results['videos'].extend(results['videos'])
            except Exception as e:
                logger.error(f"扫描目录失败: {directory} - {e}")
        
        # 去重
        combined_results['images'] = list(set(combined_results['images']))
        combined_results['videos'] = list(set(combined_results['videos']))
        
        return combined_results
    
    def get_file_info(self, file_path: str) -> Dict[str, any]:
        """
        获取文件基本信息
        Args:
            file_path: 文件路径
        Returns:
            文件信息字典
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        stat = os.stat(file_path)
        file_ext = Path(file_path).suffix.lower()
        
        # 判断文件类型
        if file_ext in self.image_extensions:
            file_type = 'image'
        elif file_ext in self.video_extensions:
            file_type = 'video'
        else:
            file_type = 'unknown'
        
        return {
            'file_path': file_path,
            'file_name': os.path.basename(file_path),
            'file_type': file_type,
            'file_extension': file_ext,
            'file_size': stat.st_size,
            'created_time': stat.st_ctime,
            'modified_time': stat.st_mtime,
            'accessed_time': stat.st_atime
        }
    
    def filter_existing_files(self, file_paths: List[str]) -> List[str]:
        """
        过滤出存在的文件
        Args:
            file_paths: 文件路径列表
        Returns:
            存在的文件路径列表
        """
        existing_files = []
        for file_path in file_paths:
            if os.path.exists(file_path) and os.path.isfile(file_path):
                existing_files.append(file_path)
            else:
                logger.warning(f"文件不存在或不是文件: {file_path}")
        
        return existing_files
    
    def get_directory_stats(self, directory_path: str, recursive: bool = True) -> Dict[str, any]:
        """
        获取目录统计信息
        Args:
            directory_path: 目录路径
            recursive: 是否递归统计
        Returns:
            统计信息字典
        """
        if not os.path.exists(directory_path):
            raise FileNotFoundError(f"目录不存在: {directory_path}")
        
        stats = {
            'total_files': 0,
            'image_count': 0,
            'video_count': 0,
            'total_size': 0,
            'image_size': 0,
            'video_size': 0,
            'image_extensions': set(),
            'video_extensions': set()
        }
        
        for file_path in self._walk_directory(directory_path, recursive):
            try:
                file_info = self.get_file_info(file_path)
                file_size = file_info['file_size']
                file_ext = file_info['file_extension']
                
                stats['total_files'] += 1
                stats['total_size'] += file_size
                
                if file_info['file_type'] == 'image':
                    stats['image_count'] += 1
                    stats['image_size'] += file_size
                    stats['image_extensions'].add(file_ext)
                elif file_info['file_type'] == 'video':
                    stats['video_count'] += 1
                    stats['video_size'] += file_size
                    stats['video_extensions'].add(file_ext)
                    
            except Exception as e:
                logger.warning(f"获取文件信息失败: {file_path} - {e}")
        
        # 转换集合为列表以便JSON序列化
        stats['image_extensions'] = list(stats['image_extensions'])
        stats['video_extensions'] = list(stats['video_extensions'])
        
        return stats
    
    def is_supported_file(self, file_path: str) -> Tuple[bool, str]:
        """
        检查文件是否为支持的媒体文件
        Args:
            file_path: 文件路径
        Returns:
            (是否支持, 文件类型)
        """
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext in self.image_extensions:
            return True, 'image'
        elif file_ext in self.video_extensions:
            return True, 'video'
        else:
            return False, 'unknown'
    
    def batch_scan_files(self, file_paths: List[str]) -> Dict[str, List[str]]:
        """
        批量扫描指定的文件列表
        Args:
            file_paths: 文件路径列表
        Returns:
            分类后的媒体文件字典
        """
        media_files = {
            'images': [],
            'videos': []
        }
        
        for file_path in file_paths:
            if os.path.exists(file_path) and os.path.isfile(file_path):
                is_supported, file_type = self.is_supported_file(file_path)
                if is_supported:
                    if file_type == 'image':
                        media_files['images'].append(file_path)
                    elif file_type == 'video':
                        media_files['videos'].append(file_path)
        
        return media_files 