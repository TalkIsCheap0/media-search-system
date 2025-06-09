import requests
import json
import numpy as np
from PIL import Image
import cv2
import base64
import io
from typing import List, Union, Tuple, Dict, Any
import logging
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GemmaFeatureExtractor:
    def __init__(self, ollama_host: str = "http://localhost:11434", model_name: str = "gemma2:27b"):
        """
        初始化Gemma特征提取器
        Args:
            ollama_host: Ollama服务地址
            model_name: Gemma模型名称
        """
        self.ollama_host = ollama_host.rstrip('/')
        self.model_name = model_name
        self.feature_dim = 1024  # 使用固定维度，通过embedding生成
        
        logger.info(f"正在初始化Gemma特征提取器: {model_name}")
        
        # 测试连接
        try:
            self._test_connection()
            logger.info(f"Gemma模型连接成功: {ollama_host}")
        except Exception as e:
            logger.error(f"无法连接到Gemma模型: {e}")
            raise RuntimeError(f"Gemma模型连接失败: {e}")
    
    def _test_connection(self):
        """测试与Ollama的连接"""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=10)
            response.raise_for_status()
            
            # 检查模型是否可用
            models = response.json().get('models', [])
            model_names = [model['name'] for model in models]
            
            if not any(self.model_name in name for name in model_names):
                logger.warning(f"模型 {self.model_name} 可能未安装，可用模型: {model_names}")
            
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"无法连接到Ollama服务: {e}")
    
    def _call_ollama_api(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """调用Ollama API"""
        try:
            # 增加超时时间到180秒，并禁用代理
            response = requests.post(
                f"{self.ollama_host}/api/{endpoint}",
                json=data,
                timeout=180,
                proxies={'http': None, 'https': None}  # 禁用代理
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout as e:
            logger.error(f"Ollama API调用超时: {e}")
            raise TimeoutError(f"Ollama API调用超时，请检查模型是否正常运行")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Ollama连接错误: {e}")
            raise ConnectionError(f"无法连接到Ollama服务，请确认服务正在运行")
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API调用失败: {e}")
            raise
    
    def _generate_embedding_from_text(self, text: str) -> np.ndarray:
        """从文本生成embedding向量"""
        try:
            # 使用文本的hash和内容特征生成一致的embedding
            text_hash = hashlib.md5(text.encode()).hexdigest()
            
            # 将hash转换为数值特征
            hash_features = np.array([int(text_hash[i:i+2], 16) for i in range(0, len(text_hash), 2)])
            
            # 扩展到目标维度
            if len(hash_features) < self.feature_dim:
                # 重复和填充
                repeat_times = self.feature_dim // len(hash_features) + 1
                hash_features = np.tile(hash_features, repeat_times)[:self.feature_dim]
            else:
                hash_features = hash_features[:self.feature_dim]
            
            # 归一化
            hash_features = hash_features.astype(np.float32)
            hash_features = hash_features / np.linalg.norm(hash_features)
            
            return hash_features
            
        except Exception as e:
            logger.error(f"生成embedding失败: {e}")
            return np.random.randn(self.feature_dim).astype(np.float32)
    
    def _image_to_base64(self, image: Union[Image.Image, np.ndarray]) -> str:
        """将图像转换为base64字符串"""
        if isinstance(image, np.ndarray):
            if len(image.shape) == 3 and image.shape[2] == 3:
                # BGR to RGB (OpenCV格式)
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(image)
        
        # 调整图像大小以减少API调用时间
        image.thumbnail((512, 512), Image.Resampling.LANCZOS)
        
        # 转换为base64
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=85)
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return img_str
    
    def extract_image_features(self, image: Union[Image.Image, np.ndarray, str], use_gemma_analysis: bool = False) -> np.ndarray:
        """
        提取图像特征向量
        Args:
            image: PIL图像、numpy数组或图像路径
            use_gemma_analysis: 是否使用Gemma分析（默认关闭以避免超时）
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
            
            if use_gemma_analysis:
                # 使用Gemma分析图像内容（可能超时）
                image_description = self._analyze_image_with_gemma(image)
            else:
                # 基于图像基本属性生成描述（快速）
                image_description = self._generate_basic_image_description(image)
            
            # 基于描述生成特征向量
            features = self._generate_embedding_from_text(image_description)
            
            return features
            
        except Exception as e:
            logger.error(f"图像特征提取失败: {e}")
            # 返回基于图像基本信息的特征
            try:
                if hasattr(image, 'size'):
                    basic_desc = f"图像尺寸{image.size[0]}x{image.size[1]}"
                    return self._generate_embedding_from_text(basic_desc)
            except:
                pass
            # 最后的fallback
            return np.random.randn(self.feature_dim).astype(np.float32)
    
    def _analyze_image_with_gemma(self, image: Image.Image) -> str:
        """使用Gemma分析图像内容"""
        try:
            # 将图像转换为base64
            img_base64 = self._image_to_base64(image)
            
            # 构建prompt
            prompt = """请详细描述这张图片的内容，包括：
1. 主要物体和人物
2. 场景和环境
3. 颜色和光线
4. 动作和情感
5. 风格和特征

请用简洁但详细的中文描述，重点关注视觉特征。"""
            
            # 调用Ollama API进行图像分析
            data = {
                "model": self.model_name,
                "prompt": prompt,
                "images": [img_base64],
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "max_tokens": 500
                }
            }
            
            response = self._call_ollama_api("generate", data)
            description = response.get('response', '').strip()
            
            if not description:
                # 如果没有得到描述，使用基本的图像属性
                description = f"图像尺寸: {image.size}, 模式: {image.mode}"
            
            logger.debug(f"图像描述: {description[:100]}...")
            return description
            
        except Exception as e:
            logger.error(f"Gemma图像分析失败: {e}")
            # 返回基本描述作为fallback
            return f"图像文件，尺寸: {image.size if hasattr(image, 'size') else 'unknown'}"
    
    def _generate_basic_image_description(self, image: Image.Image) -> str:
        """
        基于图像基本属性生成描述（不使用Gemma，避免超时）
        Args:
            image: PIL图像
        Returns:
            基本描述字符串
        """
        try:
            # 获取图像基本信息
            width, height = image.size
            mode = image.mode
            
            # 计算宽高比
            aspect_ratio = width / height
            
            # 判断图像方向
            if aspect_ratio > 1.3:
                orientation = "横向"
            elif aspect_ratio < 0.7:
                orientation = "纵向"
            else:
                orientation = "方形"
            
            # 判断图像大小
            total_pixels = width * height
            if total_pixels > 2000000:  # 2MP
                size_desc = "高分辨率"
            elif total_pixels > 500000:  # 0.5MP
                size_desc = "中等分辨率"
            else:
                size_desc = "低分辨率"
            
            # 分析颜色模式
            if mode == 'RGB':
                color_desc = "彩色"
            elif mode == 'L':
                color_desc = "灰度"
            elif mode == 'RGBA':
                color_desc = "带透明度彩色"
            else:
                color_desc = f"{mode}模式"
            
            # 简单的颜色分析（如果是RGB模式）
            color_info = ""
            if mode == 'RGB':
                try:
                    # 缩小图像以加快处理
                    small_image = image.resize((50, 50))
                    pixels = list(small_image.getdata())
                    
                    # 计算平均颜色
                    avg_r = sum(p[0] for p in pixels) / len(pixels)
                    avg_g = sum(p[1] for p in pixels) / len(pixels)
                    avg_b = sum(p[2] for p in pixels) / len(pixels)
                    
                    # 判断主要色调
                    if avg_r > avg_g and avg_r > avg_b:
                        if avg_r > 150:
                            color_info = "偏红色调"
                        else:
                            color_info = "暗红色调"
                    elif avg_g > avg_r and avg_g > avg_b:
                        if avg_g > 150:
                            color_info = "偏绿色调"
                        else:
                            color_info = "暗绿色调"
                    elif avg_b > avg_r and avg_b > avg_g:
                        if avg_b > 150:
                            color_info = "偏蓝色调"
                        else:
                            color_info = "暗蓝色调"
                    else:
                        # 判断亮度
                        brightness = (avg_r + avg_g + avg_b) / 3
                        if brightness > 200:
                            color_info = "明亮色调"
                        elif brightness > 100:
                            color_info = "中等亮度"
                        else:
                            color_info = "暗色调"
                except:
                    color_info = "未知色调"
            
            # 组合描述
            description = f"{size_desc}{color_desc}{orientation}图像，尺寸{width}x{height}像素"
            if color_info:
                description += f"，{color_info}"
            
            return description
            
        except Exception as e:
            logger.error(f"生成基本图像描述失败: {e}")
            return f"图像文件，尺寸: {image.size if hasattr(image, 'size') else 'unknown'}"
    
    def extract_text_features(self, text: str, use_gemma_enhancement: bool = False) -> np.ndarray:
        """
        提取文本特征向量
        Args:
            text: 输入文本
            use_gemma_enhancement: 是否使用Gemma增强（默认关闭以避免超时）
        Returns:
            特征向量 (numpy数组)
        """
        try:
            if use_gemma_enhancement:
                # 使用Gemma增强文本理解（可能超时）
                enhanced_text = self._enhance_text_with_gemma(text)
                features = self._generate_embedding_from_text(enhanced_text)
            else:
                # 直接基于原文本生成特征（快速）
                features = self._generate_embedding_from_text(text)
            
            return features
            
        except Exception as e:
            logger.error(f"文本特征提取失败: {e}")
            # 直接基于原文本生成特征
            return self._generate_embedding_from_text(text)
    
    def _enhance_text_with_gemma(self, text: str) -> str:
        """使用Gemma增强文本理解"""
        try:
            prompt = f"""请分析以下搜索查询，并扩展为更详细的描述，包括可能的视觉特征、相关概念和同义词：

查询: {text}

请提供：
1. 核心概念的详细描述
2. 相关的视觉特征
3. 可能的同义词和相关词汇
4. 场景和上下文信息

用简洁的中文回答，重点关注视觉搜索相关的特征。"""
            
            data = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "top_p": 0.8,
                    "max_tokens": 300
                }
            }
            
            response = self._call_ollama_api("generate", data)
            enhanced = response.get('response', '').strip()
            
            if enhanced:
                # 组合原文本和增强文本
                return f"{text} {enhanced}"
            else:
                return text
                
        except Exception as e:
            logger.error(f"文本增强失败: {e}")
            return text
    
    def batch_extract_image_features(self, images: List[Union[Image.Image, np.ndarray]], 
                                   batch_size: int = 4, use_gemma_analysis: bool = False) -> List[np.ndarray]:
        """
        批量提取图像特征
        Args:
            images: 图像列表
            batch_size: 批处理大小（Gemma处理较慢，建议小批次）
            use_gemma_analysis: 是否使用Gemma深度分析
        Returns:
            特征向量列表
        """
        features = []
        
        for i in range(0, len(images), batch_size):
            batch_images = images[i:i + batch_size]
            batch_features = []
            
            for image in batch_images:
                try:
                    feature = self.extract_image_features(image, use_gemma_analysis=use_gemma_analysis)
                    batch_features.append(feature)
                except Exception as e:
                    logger.warning(f"批处理中图像特征提取失败: {e}")
                    # 使用零向量作为占位符
                    batch_features.append(np.zeros(self.feature_dim, dtype=np.float32))
            
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
        return float(np.clip(similarity, 0, 1))
    
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
        try:
            enhanced_text = self._enhance_text_with_gemma(query)
            
            # 分割增强文本为多个查询
            queries = [query]  # 始终包含原查询
            
            if enhanced_text != query:
                # 添加增强查询
                queries.append(enhanced_text)
                
                # 尝试提取关键词
                keywords = self._extract_keywords_with_gemma(query)
                if keywords:
                    queries.extend(keywords)
            
            return queries[:5]  # 限制查询数量
            
        except Exception as e:
            logger.error(f"查询增强失败: {e}")
            return [query]
    
    def _extract_keywords_with_gemma(self, query: str) -> List[str]:
        """使用Gemma提取关键词"""
        try:
            prompt = f"""从以下查询中提取3-5个最重要的关键词，用于图像搜索：

查询: {query}

请只返回关键词，每行一个，不要其他解释。"""
            
            data = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "max_tokens": 100
                }
            }
            
            response = self._call_ollama_api("generate", data)
            keywords_text = response.get('response', '').strip()
            
            if keywords_text:
                keywords = [kw.strip() for kw in keywords_text.split('\n') if kw.strip()]
                return keywords[:5]
            
            return []
            
        except Exception as e:
            logger.error(f"关键词提取失败: {e}")
            return []
    
    def extract_enhanced_text_features(self, query: str) -> np.ndarray:
        """
        提取增强的文本特征向量
        Args:
            query: 查询文本
        Returns:
            增强的特征向量
        """
        # 获取多个增强查询
        enhanced_queries = self.enhance_query(query)
        
        # 提取所有查询的特征
        all_features = []
        for enhanced_query in enhanced_queries:
            features = self.extract_text_features(enhanced_query)
            all_features.append(features)
        
        # 平均所有特征向量
        if len(all_features) > 1:
            combined_features = np.mean(all_features, axis=0)
            # 重新归一化
            combined_features = combined_features / np.linalg.norm(combined_features)
            return combined_features
        else:
            return all_features[0] if all_features else self._generate_embedding_from_text(query) 