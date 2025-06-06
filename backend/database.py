import sqlite3
import os
import hashlib
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings

class DatabaseManager:
    def __init__(self, db_path: str = "media.db", chroma_path: str = "./chroma_db"):
        self.db_path = db_path
        self.chroma_path = chroma_path
        self.init_sqlite()
        self.init_chromadb()
    
    def init_sqlite(self):
        """初始化SQLite数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建媒体文件表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS media_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE NOT NULL,
                file_hash TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size INTEGER,
                duration REAL,
                fps REAL,
                width INTEGER,
                height INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建关键帧表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS keyframes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                media_file_id INTEGER NOT NULL,
                frame_index INTEGER NOT NULL,
                timestamp REAL NOT NULL,
                thumbnail_path TEXT NOT NULL,
                extraction_method TEXT,
                vector_id TEXT NOT NULL,
                similarity_score REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (media_file_id) REFERENCES media_files(id)
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_media_files_path ON media_files(file_path)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_keyframes_media_id ON keyframes(media_file_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_keyframes_vector_id ON keyframes(vector_id)')
        
        conn.commit()
        conn.close()
    
    def init_chromadb(self):
        """初始化ChromaDB向量数据库"""
        self.chroma_client = chromadb.PersistentClient(path=self.chroma_path)
        
        # 创建或获取集合
        try:
            self.collection = self.chroma_client.get_collection("media_embeddings")
        except:
            self.collection = self.chroma_client.create_collection(
                name="media_embeddings",
                metadata={"hnsw:space": "cosine"}  # 使用余弦相似度
            )
    
    def get_file_hash(self, file_path: str) -> str:
        """计算文件哈希值"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def add_media_file(self, file_path: str, file_type: str, **kwargs) -> int:
        """添加媒体文件记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        file_hash = self.get_file_hash(file_path)
        file_size = os.path.getsize(file_path)
        
        cursor.execute('''
            INSERT OR REPLACE INTO media_files 
            (file_path, file_hash, file_type, file_size, duration, fps, width, height)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            file_path, file_hash, file_type, file_size,
            kwargs.get('duration'), kwargs.get('fps'),
            kwargs.get('width'), kwargs.get('height')
        ))
        
        media_file_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return media_file_id
    
    def add_keyframe(self, media_file_id: int, frame_index: int, timestamp: float,
                     thumbnail_path: str, vector_id: str, extraction_method: str = "scene_change"):
        """添加关键帧记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO keyframes 
            (media_file_id, frame_index, timestamp, thumbnail_path, vector_id, extraction_method)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (media_file_id, frame_index, timestamp, thumbnail_path, vector_id, extraction_method))
        
        conn.commit()
        conn.close()
    
    def add_embeddings(self, embeddings: List[List[float]], metadatas: List[Dict], ids: List[str]):
        """批量添加向量嵌入"""
        self.collection.add(
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
    
    def search_similar(self, query_embedding: List[float], n_results: int = 50) -> Dict[str, Any]:
        """搜索相似向量"""
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=['metadatas', 'distances']
        )
        return results
    
    def get_media_file_by_path(self, file_path: str) -> Optional[Dict]:
        """根据路径获取媒体文件信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM media_files WHERE file_path = ?', (file_path,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            columns = ['id', 'file_path', 'file_hash', 'file_type', 'file_size', 
                      'duration', 'fps', 'width', 'height', 'created_at', 'updated_at']
            return dict(zip(columns, row))
        return None
    
    def get_keyframes_by_media_id(self, media_file_id: int) -> List[Dict]:
        """获取指定媒体文件的所有关键帧"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT k.*, m.file_path, m.file_type 
            FROM keyframes k 
            JOIN media_files m ON k.media_file_id = m.id 
            WHERE k.media_file_id = ?
            ORDER BY k.timestamp
        ''', (media_file_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'media_file_id', 'frame_index', 'timestamp', 'thumbnail_path',
                  'vector_id', 'similarity_score', 'extraction_method', 'created_at',
                  'file_path', 'file_type']
        
        return [dict(zip(columns, row)) for row in rows]
    
    def get_all_media_files(self) -> List[Dict]:
        """获取所有媒体文件"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM media_files ORDER BY created_at DESC')
        rows = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'file_path', 'file_hash', 'file_type', 'file_size',
                  'duration', 'fps', 'width', 'height', 'created_at', 'updated_at']
        
        return [dict(zip(columns, row)) for row in rows] 