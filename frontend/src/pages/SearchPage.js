import React, { useState, useEffect } from 'react';
import { Search, Filter, Play, Image, Clock, Star } from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../utils/api';

const SearchPage = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    aggregation_strategy: 'multiple_scenes',
    similarity_threshold: 0.15,
    max_results: 50,
  });
  const [showFilters, setShowFilters] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) {
      toast.error('请输入搜索内容');
      return;
    }

    setLoading(true);
    try {
      const response = await api.post('/api/search', {
        query: query.trim(),
        ...filters,
      });

      if (response.data.success) {
        setResults(response.data.results);
        toast.success(`找到 ${response.data.results.total_results} 个结果`);
      } else {
        toast.error('搜索失败');
      }
    } catch (error) {
      console.error('搜索错误:', error);
      toast.error(
        '搜索失败: ' + (error.response?.data?.detail || error.message),
      );
    } finally {
      setLoading(false);
    }
  };

  const formatTimestamp = (timestamp) => {
    const minutes = Math.floor(timestamp / 60);
    const seconds = Math.floor(timestamp % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const formatSimilarity = (similarity) => {
    return (similarity * 100).toFixed(1) + '%';
  };

  const VideoResult = ({ video }) => {
    return (
      <div className='search-result-card'>
        {/* 视频关键帧网格 */}
        <div className='grid grid-cols-3 gap-2 p-4'>
          {video.representative_frames.slice(0, 3).map((frame, index) => (
            <div key={index} className='relative'>
              <img
                src={`/api/media/${encodeURIComponent(
                  frame.metadata.file_path,
                )}`}
                alt={`关键帧 ${index + 1}`}
                className='thumbnail video-thumbnail'
              />
              <div className='absolute bottom-2 left-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded'>
                {formatTimestamp(frame.metadata.timestamp)}
              </div>
              <div className='absolute top-2 right-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded'>
                {formatSimilarity(frame.similarity)}
              </div>
            </div>
          ))}
        </div>

        {/* 视频信息 */}
        <div className='p-4'>
          <div className='flex items-center justify-between mb-2'>
            <h3 className='font-medium text-gray-900 truncate'>
              {video.file_path.split('/').pop()}
            </h3>
            <div className='flex items-center space-x-1 text-sm text-gray-500'>
              <Play className='w-4 h-4' />
              <span>视频</span>
            </div>
          </div>
          <div className='flex items-center justify-between text-sm text-gray-600'>
            <div className='flex items-center space-x-1'>
              <Star className='w-4 h-4 text-yellow-500' />
              <span>{formatSimilarity(video.max_similarity)}</span>
            </div>
            <span>{video.match_count} 个匹配帧</span>
          </div>
          <div className='mt-2 text-xs text-gray-500'>{video.file_path}</div>
        </div>
      </div>
    );
  };

  const ImageResult = ({ image }) => {
    return (
      <div className='search-result-card'>
        <img
          src={`/api/media/${encodeURIComponent(image.metadata.file_path)}`}
          alt='搜索结果'
          className='thumbnail'
        />
        <div className='p-4'>
          <div className='flex items-center justify-between mb-2'>
            <h3 className='font-medium text-gray-900 truncate'>
              {image.metadata.file_path.split('/').pop()}
            </h3>
            <div className='flex items-center space-x-1 text-sm text-gray-500'>
              <Image className='w-4 h-4' />
              <span>图片</span>
            </div>
          </div>
          <div className='flex items-center space-x-1 text-sm text-gray-600'>
            <Star className='w-4 h-4 text-yellow-500' />
            <span>{formatSimilarity(image.similarity)}</span>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className='max-w-6xl mx-auto'>
      {/* 页面标题 */}
      <div className='mb-8'>
        <h1 className='text-3xl font-bold text-gray-900 mb-2'>智能搜索</h1>
        <p className='text-gray-600'>使用自然语言描述来搜索你的图片和视频</p>
      </div>

      {/* 搜索表单 */}
      <form onSubmit={handleSearch} className='mb-8'>
        <div className='flex space-x-4'>
          <div className='flex-1 relative'>
            <Search className='absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5' />
            <input
              type='text'
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder='例如：海边的日落、猫咪在玩耍、生日聚会...'
              className='input-field pl-10'
              disabled={loading}
            />
          </div>
          <button
            type='button'
            onClick={() => setShowFilters(!showFilters)}
            className='btn-secondary flex items-center space-x-2'
          >
            <Filter className='w-4 h-4' />
            <span>筛选</span>
          </button>
          <button
            type='submit'
            disabled={loading}
            className='btn-primary flex items-center space-x-2'
          >
            <Search className='w-4 h-4' />
            <span>{loading ? '搜索中...' : '搜索'}</span>
          </button>
        </div>

        {/* 高级筛选 */}
        {showFilters && (
          <div className='mt-4 p-4 bg-gray-50 rounded-lg'>
            <div className='grid grid-cols-1 md:grid-cols-3 gap-4'>
              <div>
                <label className='block text-sm font-medium text-gray-700 mb-2'>
                  聚合策略
                </label>
                <select
                  value={filters.aggregation_strategy}
                  onChange={(e) =>
                    setFilters({
                      ...filters,
                      aggregation_strategy: e.target.value,
                    })
                  }
                  className='input-field'
                >
                  <option value='best_match'>最佳匹配</option>
                  <option value='multiple_scenes'>多个场景</option>
                  <option value='all_frames'>所有帧</option>
                </select>
              </div>
              <div>
                <label className='block text-sm font-medium text-gray-700 mb-2'>
                  相似度阈值
                </label>
                <div className='space-y-2'>
                  <input
                    type='range'
                    min='0'
                    max='1'
                    step='0.05'
                    value={filters.similarity_threshold}
                    onChange={(e) =>
                      setFilters({
                        ...filters,
                        similarity_threshold: parseFloat(e.target.value),
                      })
                    }
                    className='w-full'
                  />
                  <div className='flex justify-between text-xs text-gray-500'>
                    <span>宽松 (0.0)</span>
                    <span className='font-medium'>
                      {formatSimilarity(filters.similarity_threshold)}
                    </span>
                    <span>严格 (1.0)</span>
                  </div>
                  <div className='flex space-x-2 mt-2'>
                    <button
                      type='button'
                      onClick={() =>
                        setFilters({ ...filters, similarity_threshold: 0.1 })
                      }
                      className={`px-2 py-1 text-xs rounded ${
                        Math.abs(filters.similarity_threshold - 0.1) < 0.01
                          ? 'bg-blue-500 text-white'
                          : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      }`}
                    >
                      宽松
                    </button>
                    <button
                      type='button'
                      onClick={() =>
                        setFilters({ ...filters, similarity_threshold: 0.15 })
                      }
                      className={`px-2 py-1 text-xs rounded ${
                        Math.abs(filters.similarity_threshold - 0.15) < 0.01
                          ? 'bg-blue-500 text-white'
                          : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      }`}
                    >
                      标准
                    </button>
                    <button
                      type='button'
                      onClick={() =>
                        setFilters({ ...filters, similarity_threshold: 0.25 })
                      }
                      className={`px-2 py-1 text-xs rounded ${
                        Math.abs(filters.similarity_threshold - 0.25) < 0.01
                          ? 'bg-blue-500 text-white'
                          : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      }`}
                    >
                      严格
                    </button>
                  </div>
                </div>
              </div>
              <div>
                <label className='block text-sm font-medium text-gray-700 mb-2'>
                  最大结果数
                </label>
                <input
                  type='number'
                  min='10'
                  max='200'
                  value={filters.max_results}
                  onChange={(e) =>
                    setFilters({
                      ...filters,
                      max_results: parseInt(e.target.value),
                    })
                  }
                  className='input-field'
                />
              </div>
            </div>
          </div>
        )}
      </form>

      {/* 搜索结果 */}
      {loading && (
        <div className='text-center py-12'>
          <div className='inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600'></div>
          <p className='mt-2 text-gray-600'>正在搜索...</p>
        </div>
      )}

      {results && !loading && (
        <div>
          {/* 结果统计 */}
          <div className='mb-6 p-4 bg-white rounded-lg border border-gray-200'>
            <div className='flex items-center justify-between'>
              <div>
                <h2 className='text-lg font-medium text-gray-900'>搜索结果</h2>
                <p className='text-sm text-gray-600'>
                  找到 {results.total_results} 个结果 ({results.video_count}{' '}
                  个视频, {results.image_count} 张图片)
                </p>
              </div>
              <div className='text-sm text-gray-500'>查询: "{query}"</div>
            </div>
          </div>

          {/* 视频结果 */}
          {results.videos.length > 0 && (
            <div className='mb-8'>
              <h3 className='text-xl font-semibold text-gray-900 mb-4 flex items-center'>
                <Play className='w-5 h-5 mr-2' />
                视频结果 ({results.videos.length})
              </h3>
              <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6'>
                {results.videos.map((video, index) => (
                  <VideoResult key={index} video={video} />
                ))}
              </div>
            </div>
          )}

          {/* 图片结果 */}
          {results.images.length > 0 && (
            <div>
              <h3 className='text-xl font-semibold text-gray-900 mb-4 flex items-center'>
                <Image className='w-5 h-5 mr-2' />
                图片结果 ({results.images.length})
              </h3>
              <div className='grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4'>
                {results.images.map((image, index) => (
                  <ImageResult key={index} image={image} />
                ))}
              </div>
            </div>
          )}

          {/* 无结果 */}
          {results.total_results === 0 && (
            <div className='text-center py-12'>
              <Search className='w-16 h-16 text-gray-300 mx-auto mb-4' />
              <h3 className='text-lg font-medium text-gray-900 mb-2'>
                没有找到相关结果
              </h3>
              <p className='text-gray-600'>
                尝试使用不同的关键词或降低相似度阈值
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SearchPage;
