from typing import List, Dict, Any, Tuple, Optional
import logging
from collections import defaultdict
import numpy as np

logger = logging.getLogger(__name__)

class SearchResultAggregator:
    def __init__(self):
        """搜索结果聚合器"""
        pass
    
    def aggregate_search_results(self, raw_results: Dict[str, Any], 
                                aggregation_strategy: str = "best_match",
                                similarity_threshold: float = 0.5) -> Dict[str, Any]:
        """
        聚合搜索结果
        Args:
            raw_results: ChromaDB返回的原始结果
            aggregation_strategy: 聚合策略 ("best_match", "multiple_scenes", "all_frames")
            similarity_threshold: 相似度阈值
        Returns:
            聚合后的结果
        """
        if not raw_results or not raw_results.get('metadatas'):
            return {'videos': [], 'images': [], 'total_results': 0}
        
        # 解析原始结果
        metadatas = raw_results['metadatas'][0]  # ChromaDB返回的是嵌套列表
        distances = raw_results['distances'][0]
        ids = raw_results['ids'][0]
        
        # 转换距离为相似度分数 (ChromaDB使用余弦距离)
        similarities = [1 - distance for distance in distances]
        
        # 过滤低相似度结果
        filtered_results = []
        for i, similarity in enumerate(similarities):
            if similarity >= similarity_threshold:
                filtered_results.append({
                    'id': ids[i],
                    'metadata': metadatas[i],
                    'similarity': similarity
                })
        
        logger.info(f"过滤后保留 {len(filtered_results)} 个结果 (阈值: {similarity_threshold})")
        
        # 按类型分组
        video_groups = defaultdict(list)
        image_results = []
        
        for result in filtered_results:
            metadata = result['metadata']
            if metadata.get('type') == 'video_frame':
                video_path = metadata['file_path']
                video_groups[video_path].append(result)
            elif metadata.get('type') == 'image':
                image_results.append(result)
        
        # 聚合视频结果
        aggregated_videos = self._aggregate_video_results(
            video_groups, aggregation_strategy
        )
        
        # 排序结果
        aggregated_videos.sort(key=lambda x: x['max_similarity'], reverse=True)
        image_results.sort(key=lambda x: x['similarity'], reverse=True)
        
        return {
            'videos': aggregated_videos,
            'images': image_results,
            'total_results': len(aggregated_videos) + len(image_results),
            'video_count': len(aggregated_videos),
            'image_count': len(image_results)
        }
    
    def _aggregate_video_results(self, video_groups: Dict[str, List[Dict]], 
                               strategy: str) -> List[Dict[str, Any]]:
        """
        聚合视频结果
        Args:
            video_groups: 按视频分组的结果
            strategy: 聚合策略
        Returns:
            聚合后的视频结果列表
        """
        aggregated_videos = []
        
        for video_path, frames in video_groups.items():
            if strategy == "best_match":
                # 选择最佳匹配帧作为代表
                best_frame = max(frames, key=lambda x: x['similarity'])
                aggregated_videos.append({
                    'type': 'video',
                    'file_path': video_path,
                    'best_frame': best_frame,
                    'representative_frames': [best_frame],
                    'all_frames': frames,
                    'match_count': len(frames),
                    'max_similarity': best_frame['similarity'],
                    'avg_similarity': np.mean([f['similarity'] for f in frames]),
                    'timestamps': [f['metadata']['timestamp'] for f in frames]
                })
                
            elif strategy == "multiple_scenes":
                # 选择多个高分帧展示
                top_frames = sorted(frames, key=lambda x: x['similarity'], reverse=True)[:5]
                best_frame = top_frames[0]
                aggregated_videos.append({
                    'type': 'video',
                    'file_path': video_path,
                    'best_frame': best_frame,
                    'representative_frames': top_frames,
                    'all_frames': frames,
                    'match_count': len(frames),
                    'max_similarity': best_frame['similarity'],
                    'avg_similarity': np.mean([f['similarity'] for f in frames]),
                    'timestamps': [f['metadata']['timestamp'] for f in top_frames]
                })
                
            elif strategy == "all_frames":
                # 显示所有匹配帧
                sorted_frames = sorted(frames, key=lambda x: x['similarity'], reverse=True)
                best_frame = sorted_frames[0]
                aggregated_videos.append({
                    'type': 'video',
                    'file_path': video_path,
                    'best_frame': best_frame,
                    'representative_frames': sorted_frames,
                    'all_frames': frames,
                    'match_count': len(frames),
                    'max_similarity': best_frame['similarity'],
                    'avg_similarity': np.mean([f['similarity'] for f in frames]),
                    'timestamps': [f['metadata']['timestamp'] for f in sorted_frames]
                })
        
        return aggregated_videos
    
    def get_context_frames(self, video_path: str, target_timestamp: float, 
                          context_seconds: int = 10, all_frames: List[Dict] = None) -> List[Dict]:
        """
        获取目标时间点前后的上下文帧
        Args:
            video_path: 视频路径
            target_timestamp: 目标时间戳
            context_seconds: 上下文时间范围(秒)
            all_frames: 该视频的所有帧信息
        Returns:
            上下文帧列表
        """
        if not all_frames:
            return []
        
        start_time = max(0, target_timestamp - context_seconds)
        end_time = target_timestamp + context_seconds
        
        context_frames = []
        for frame in all_frames:
            frame_timestamp = frame['metadata']['timestamp']
            if start_time <= frame_timestamp <= end_time:
                context_frames.append(frame)
        
        # 按时间戳排序
        context_frames.sort(key=lambda x: x['metadata']['timestamp'])
        
        return context_frames
    
    def filter_results_by_criteria(self, results: Dict[str, Any], 
                                 criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据条件过滤搜索结果
        Args:
            results: 搜索结果
            criteria: 过滤条件
        Returns:
            过滤后的结果
        """
        filtered_results = {
            'videos': [],
            'images': [],
            'total_results': 0,
            'video_count': 0,
            'image_count': 0
        }
        
        # 过滤视频结果
        for video in results.get('videos', []):
            if self._match_video_criteria(video, criteria):
                filtered_results['videos'].append(video)
        
        # 过滤图片结果
        for image in results.get('images', []):
            if self._match_image_criteria(image, criteria):
                filtered_results['images'].append(image)
        
        filtered_results['video_count'] = len(filtered_results['videos'])
        filtered_results['image_count'] = len(filtered_results['images'])
        filtered_results['total_results'] = filtered_results['video_count'] + filtered_results['image_count']
        
        return filtered_results
    
    def _match_video_criteria(self, video: Dict[str, Any], criteria: Dict[str, Any]) -> bool:
        """检查视频是否匹配过滤条件"""
        # 相似度阈值
        if 'min_similarity' in criteria:
            if video['max_similarity'] < criteria['min_similarity']:
                return False
        
        # 匹配帧数阈值
        if 'min_match_count' in criteria:
            if video['match_count'] < criteria['min_match_count']:
                return False
        
        # 文件路径包含
        if 'path_contains' in criteria:
            if criteria['path_contains'].lower() not in video['file_path'].lower():
                return False
        
        # 时长范围 (需要从metadata获取)
        if 'duration_range' in criteria:
            # 这里需要从数据库获取视频时长信息
            pass
        
        return True
    
    def _match_image_criteria(self, image: Dict[str, Any], criteria: Dict[str, Any]) -> bool:
        """检查图片是否匹配过滤条件"""
        # 相似度阈值
        if 'min_similarity' in criteria:
            if image['similarity'] < criteria['min_similarity']:
                return False
        
        # 文件路径包含
        if 'path_contains' in criteria:
            if criteria['path_contains'].lower() not in image['metadata']['file_path'].lower():
                return False
        
        return True

class SearchEngine:
    def __init__(self, database_manager, gemma_extractor):
        """
        搜索引擎
        Args:
            database_manager: 数据库管理器
            gemma_extractor: Gemma特征提取器
        """
        self.db = database_manager
        self.gemma = gemma_extractor
        self.aggregator = SearchResultAggregator()
    
    def search(self, query: str, max_results: int = 50, 
              aggregation_strategy: str = "multiple_scenes",
              similarity_threshold: float = 0.15,  # 降低默认阈值
              filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行搜索
        Args:
            query: 搜索查询文本
            max_results: 最大结果数
            aggregation_strategy: 聚合策略
            similarity_threshold: 相似度阈值
            filters: 过滤条件
        Returns:
            搜索结果
        """
        logger.info(f"执行搜索: '{query}' (最大结果: {max_results})")
        
        try:
            # 使用Gemma增强的查询特征提取（提供更好的语义理解）
            query_embedding = self.gemma.extract_text_features(query, use_gemma_enhancement=True)
            logger.debug(f"查询特征向量维度: {query_embedding.shape}")
            # 在向量数据库中搜索
            raw_results = self.db.search_similar(
                query_embedding.tolist(), 
                n_results=max_results
            )
            
            # 聚合结果
            aggregated_results = self.aggregator.aggregate_search_results(
                raw_results, 
                aggregation_strategy=aggregation_strategy,
                similarity_threshold=similarity_threshold
            )
            
            # 应用过滤条件
            if filters:
                aggregated_results = self.aggregator.filter_results_by_criteria(
                    aggregated_results, filters
                )
            
            logger.info(f"搜索完成 - 视频: {aggregated_results['video_count']} 个, "
                       f"图片: {aggregated_results['image_count']} 个")
            
            return aggregated_results
            
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            raise
    
    def get_similar_images(self, image_path: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        基于图片搜索相似图片
        Args:
            image_path: 参考图片路径
            max_results: 最大结果数
        Returns:
            相似图片列表
        """
        try:
            # 提取参考图片的特征向量（启用Gemma深度分析）
            image_embedding = self.gemma.extract_image_features(image_path, use_gemma_analysis=True)
            
            # 搜索相似向量
            raw_results = self.db.search_similar(
                image_embedding.tolist(),
                n_results=max_results
            )
            
            # 处理结果
            similar_images = []
            if raw_results and raw_results.get('metadatas'):
                metadatas = raw_results['metadatas'][0]
                distances = raw_results['distances'][0]
                ids = raw_results['ids'][0]
                
                for i, metadata in enumerate(metadatas):
                    similarity = 1 - distances[i]  # 转换距离为相似度
                    similar_images.append({
                        'id': ids[i],
                        'metadata': metadata,
                        'similarity': similarity
                    })
            
            return similar_images
            
        except Exception as e:
            logger.error(f"图片相似搜索失败: {e}")
            raise
    
    def get_video_details(self, video_path: str) -> Dict[str, Any]:
        """
        获取视频详细信息
        Args:
            video_path: 视频路径
        Returns:
            视频详细信息
        """
        try:
            # 从数据库获取视频信息
            media_info = self.db.get_media_file_by_path(video_path)
            if not media_info:
                raise ValueError(f"视频不存在于数据库中: {video_path}")
            
            # 获取所有关键帧
            keyframes = self.db.get_keyframes_by_media_id(media_info['id'])
            
            return {
                'media_info': media_info,
                'keyframes': keyframes,
                'keyframe_count': len(keyframes)
            }
            
        except Exception as e:
            logger.error(f"获取视频详情失败: {e}")
            raise 