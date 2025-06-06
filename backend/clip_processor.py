import torch
import numpy as np
from PIL import Image
import clip
import cv2
from typing import List, Union, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CLIPFeatureExtractor:
    def __init__(self, model_name: str = "ViT-L/14", device: str = "cpu"):
        """
        初始化CLIP特征提取器
        Args:
            model_name: CLIP模型名称 (使用clip库的命名方式)
                       可选: ViT-B/32, ViT-B/16, ViT-L/14, ViT-L/14@336px
            device: 运行设备 (cpu/cuda)
        """
        self.device = device
        self.model_name = model_name
        
        logger.info(f"正在加载CLIP模型: {model_name}")
        try:
            # 使用clip库加载模型
            self.model, self.preprocess = clip.load(model_name, device=device)
            self.model.eval()
            logger.info(f"CLIP模型加载完成，运行在: {device}")
            
            # 获取模型特征维度
            self.feature_dim = self._get_model_feature_dim()
            logger.info(f"模型特征维度: {self.feature_dim}")
            
        except Exception as e:
            logger.error(f"无法加载CLIP模型: {e}")
            logger.info("尝试回退到ViT-B/16模型...")
            try:
                self.model_name = "ViT-B/16"
                self.model, self.preprocess = clip.load("ViT-B/16", device=device)
                self.model.eval()
                self.feature_dim = 512
                logger.info(f"成功加载回退模型: ViT-B/16")
            except Exception as fallback_e:
                logger.error(f"回退模型也加载失败: {fallback_e}")
                raise RuntimeError(f"无法加载任何CLIP模型: {e}")
    
    def _get_model_feature_dim(self) -> int:
        """获取模型的特征维度"""
        model_dims = {
            "ViT-B/32": 512,
            "ViT-B/16": 512,
            "ViT-L/14": 768,
            "ViT-L/14@336px": 768,
            "RN50": 1024,
            "RN101": 512,
            "RN50x4": 640,
            "RN50x16": 768,
            "RN50x64": 1024
        }
        return model_dims.get(self.model_name, 512)
    
    def extract_image_features(self, image: Union[Image.Image, np.ndarray, str]) -> np.ndarray:
        """
        提取图像特征向量
        Args:
            image: PIL图像、numpy数组或图像路径
        Returns:
            特征向量 (numpy数组)
        """
        try:
            # 处理不同输入格式
            if isinstance(image, str):
                image = Image.open(image).convert('RGB')
            elif isinstance(image, np.ndarray):
                if len(image.shape) == 3 and image.shape[2] == 3:
                    # BGR to RGB (OpenCV格式)
                    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(image)
            elif not isinstance(image, Image.Image):
                raise ValueError("不支持的图像格式")
            
            # 使用clip库的预处理
            image_input = self.preprocess(image).unsqueeze(0).to(self.device)
            
            # 提取特征
            with torch.no_grad():
                image_features = self.model.encode_image(image_input)
                # 归一化特征向量
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
            return image_features.cpu().numpy().flatten()
            
        except Exception as e:
            logger.error(f"图像特征提取失败: {e}")
            raise
    
    def extract_text_features(self, text: str) -> np.ndarray:
        """
        提取文本特征向量
        Args:
            text: 输入文本
        Returns:
            特征向量 (numpy数组)
        """
        try:
            # 使用clip库的文本tokenizer
            text_input = clip.tokenize([text]).to(self.device)
            
            # 提取特征
            with torch.no_grad():
                text_features = self.model.encode_text(text_input)
                # 归一化特征向量
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            
            return text_features.cpu().numpy().flatten()
            
        except Exception as e:
            logger.error(f"文本特征提取失败: {e}")
            raise
    
    def batch_extract_image_features(self, images: List[Union[Image.Image, np.ndarray]], 
                                   batch_size: int = 8) -> List[np.ndarray]:
        """
        批量提取图像特征
        Args:
            images: 图像列表
            batch_size: 批处理大小
        Returns:
            特征向量列表
        """
        features = []
        
        for i in range(0, len(images), batch_size):
            batch_images = images[i:i + batch_size]
            batch_features = []
            
            for image in batch_images:
                try:
                    feature = self.extract_image_features(image)
                    batch_features.append(feature)
                except Exception as e:
                    logger.warning(f"批处理中图像特征提取失败: {e}")
                    # 使用零向量作为占位符，使用动态特征维度
                    batch_features.append(np.zeros(self.feature_dim))
            
            features.extend(batch_features)
            logger.info(f"已处理 {min(i + batch_size, len(images))}/{len(images)} 张图像")
        
        return features
    
    def calculate_similarity(self, features1: np.ndarray, features2: np.ndarray) -> float:
        """
        计算两个特征向量的余弦相似度
        Args:
            features1: 特征向量1
            features2: 特征向量2
        Returns:
            相似度分数 (0-1)
        """
        # 确保向量已归一化
        features1 = features1 / np.linalg.norm(features1)
        features2 = features2 / np.linalg.norm(features2)
        
        # 计算余弦相似度
        similarity = np.dot(features1, features2)
        return float(similarity)
    
    def search_similar_images(self, query_text: str, image_features_db: List[Tuple[str, np.ndarray]], 
                            top_k: int = 10) -> List[Tuple[str, float]]:
        """
        根据文本查询搜索相似图像
        Args:
            query_text: 查询文本
            image_features_db: 图像特征数据库 [(image_id, features), ...]
            top_k: 返回前k个结果
        Returns:
            相似图像列表 [(image_id, similarity_score), ...]
        """
        # 提取查询文本特征
        query_features = self.extract_text_features(query_text)
        
        # 计算与所有图像的相似度
        similarities = []
        for image_id, image_features in image_features_db:
            similarity = self.calculate_similarity(query_features, image_features)
            similarities.append((image_id, similarity))
        
        # 按相似度排序并返回前k个
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def get_feature_dimension(self) -> int:
        """获取特征向量维度"""
        return self.feature_dim
    
    def enhance_query(self, query: str) -> List[str]:
        """
        增强查询文本，提高搜索效果
        Args:
            query: 原始查询
        Returns:
            增强后的查询列表
        """
        enhanced_queries = [query]
        
        # 中英文映射
        chinese_to_english = {
            "衣服": "clothes clothing garment",
            "黑色": "black dark",
            "白色": "white bright",
            "红色": "red",
            "蓝色": "blue",
            "绿色": "green",
            "黄色": "yellow",
            "紫色": "purple violet",
            "鼠": "mouse rat rodent",
            "猫": "cat kitten feline",
            "狗": "dog puppy canine",
            "人": "person people human",
            "人物": "person people human figure",
            "动物": "animal creature",
            "建筑": "building architecture structure",
            "风景": "landscape scenery nature view",
            "汽车": "car vehicle automobile",
            "食物": "food meal dish",
            "花": "flower blossom bloom",
            "树": "tree plant"
        }
        
        # 如果是中文查询，添加英文翻译
        for chinese, english in chinese_to_english.items():
            if chinese in query:
                enhanced_queries.append(f"{query} {english}")
                enhanced_queries.append(english)
        
        # 移除重复项
        return list(set(enhanced_queries))
    
    def extract_enhanced_text_features(self, query: str) -> np.ndarray:
        """
        提取增强的文本特征
        Args:
            query: 查询文本
        Returns:
            增强后的特征向量
        """
        enhanced_queries = self.enhance_query(query)
        
        if len(enhanced_queries) == 1:
            return self.extract_text_features(query)
        
        # 提取所有增强查询的特征
        features_list = []
        for enhanced_query in enhanced_queries:
            try:
                features = self.extract_text_features(enhanced_query)
                features_list.append(features)
            except Exception as e:
                logger.warning(f"增强查询特征提取失败: {enhanced_query}, 错误: {e}")
        
        if not features_list:
            return self.extract_text_features(query)
        
        # 计算加权平均特征
        weights = [1.0] + [0.7] * (len(features_list) - 1)  # 原查询权重更高
        weighted_features = np.average(features_list, axis=0, weights=weights[:len(features_list)])
        
        # 重新归一化
        weighted_features = weighted_features / np.linalg.norm(weighted_features)
        
        return weighted_features 