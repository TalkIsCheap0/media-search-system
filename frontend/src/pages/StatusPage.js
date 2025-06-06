import React, { useState, useEffect } from 'react';
import {
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Clock,
  Database,
  Cpu,
  HardDrive,
} from 'lucide-react';
import api from '../utils/api';

const StatusPage = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    fetchStatus();

    let interval;
    if (autoRefresh) {
      interval = setInterval(fetchStatus, 2000); // 每2秒刷新一次
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  const fetchStatus = async () => {
    try {
      const response = await api.get('/api/status');
      if (response.data.success) {
        setStatus(response.data);
      }
    } catch (error) {
      console.error('获取状态失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDuration = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs
        .toString()
        .padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  if (loading) {
    return (
      <div className='flex items-center justify-center min-h-96'>
        <div className='inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600'></div>
      </div>
    );
  }

  if (!status) {
    return (
      <div className='text-center py-12'>
        <AlertCircle className='w-16 h-16 text-red-300 mx-auto mb-4' />
        <h3 className='text-lg font-medium text-gray-900 mb-2'>
          无法获取系统状态
        </h3>
        <button onClick={fetchStatus} className='btn-primary'>
          重试
        </button>
      </div>
    );
  }

  const { processing, database, system } = status;

  return (
    <div className='max-w-6xl mx-auto'>
      {/* 页面标题 */}
      <div className='flex items-center justify-between mb-8'>
        <div>
          <h1 className='text-3xl font-bold text-gray-900 mb-2'>系统状态</h1>
          <p className='text-gray-600'>实时监控系统运行状态和处理进度</p>
        </div>
        <div className='flex items-center space-x-4'>
          <label className='flex items-center'>
            <input
              type='checkbox'
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className='rounded border-gray-300 text-primary-600 focus:ring-primary-500'
            />
            <span className='ml-2 text-sm text-gray-700'>自动刷新</span>
          </label>
          <button
            onClick={fetchStatus}
            className='btn-secondary flex items-center space-x-2'
          >
            <RefreshCw className='w-4 h-4' />
            <span>刷新</span>
          </button>
        </div>
      </div>

      {/* 处理状态卡片 */}
      <div className='grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8'>
        {/* 当前处理状态 */}
        <div className='card'>
          <h3 className='text-lg font-semibold text-gray-900 mb-4 flex items-center'>
            <Clock className='w-5 h-5 mr-2' />
            处理状态
          </h3>

          {processing.is_processing ? (
            <div className='space-y-4'>
              <div className='flex items-center space-x-2'>
                <div className='w-3 h-3 bg-yellow-500 rounded-full animate-pulse'></div>
                <span className='font-medium text-yellow-700'>正在处理</span>
              </div>

              <div>
                <div className='flex justify-between text-sm mb-2'>
                  <span>进度</span>
                  <span>
                    {processing.processed_count} / {processing.total_count}
                  </span>
                </div>
                <div className='w-full bg-gray-200 rounded-full h-3'>
                  <div
                    className='bg-primary-600 h-3 rounded-full transition-all duration-300'
                    style={{
                      width: `${
                        (processing.processed_count / processing.total_count) *
                        100
                      }%`,
                    }}
                  ></div>
                </div>
                <div className='text-sm text-gray-600 mt-2'>
                  {(
                    (processing.processed_count / processing.total_count) *
                    100
                  ).toFixed(1)}
                  % 完成
                </div>
              </div>

              <div>
                <p className='text-sm font-medium text-gray-700 mb-1'>
                  当前文件:
                </p>
                <p className='text-sm text-gray-600 break-all'>
                  {processing.current_file || '准备中...'}
                </p>
              </div>
            </div>
          ) : (
            <div className='flex items-center space-x-2'>
              <CheckCircle className='w-5 h-5 text-green-500' />
              <span className='font-medium text-green-700'>空闲状态</span>
            </div>
          )}
        </div>

        {/* 系统信息 */}
        <div className='card'>
          <h3 className='text-lg font-semibold text-gray-900 mb-4 flex items-center'>
            <Cpu className='w-5 h-5 mr-2' />
            系统信息
          </h3>
          <div className='space-y-3'>
            <div className='flex justify-between'>
              <span className='text-gray-600'>CLIP 模型</span>
              <span className='font-medium text-sm'>{system.clip_model}</span>
            </div>
            <div className='flex justify-between'>
              <span className='text-gray-600'>运行设备</span>
              <span className='font-medium uppercase'>{system.device}</span>
            </div>
            <div className='flex justify-between'>
              <span className='text-gray-600'>系统状态</span>
              <span className='font-medium text-green-600'>运行中</span>
            </div>
          </div>
        </div>
      </div>

      {/* 数据库统计 */}
      <div className='card mb-8'>
        <h3 className='text-lg font-semibold text-gray-900 mb-6 flex items-center'>
          <Database className='w-5 h-5 mr-2' />
          数据库统计
        </h3>

        <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6'>
          <div className='text-center'>
            <div className='text-3xl font-bold text-primary-600 mb-2'>
              {database.total_files.toLocaleString()}
            </div>
            <div className='text-sm text-gray-600'>总文件数</div>
          </div>

          <div className='text-center'>
            <div className='text-3xl font-bold text-green-600 mb-2'>
              {database.image_count.toLocaleString()}
            </div>
            <div className='text-sm text-gray-600'>图片数量</div>
          </div>

          <div className='text-center'>
            <div className='text-3xl font-bold text-purple-600 mb-2'>
              {database.video_count.toLocaleString()}
            </div>
            <div className='text-sm text-gray-600'>视频数量</div>
          </div>

          <div className='text-center'>
            <div className='text-3xl font-bold text-orange-600 mb-2'>
              {database.total_keyframes.toLocaleString()}
            </div>
            <div className='text-sm text-gray-600'>关键帧数</div>
          </div>
        </div>
      </div>

      {/* 错误日志 */}
      {processing.errors && processing.errors.length > 0 && (
        <div className='card'>
          <h3 className='text-lg font-semibold text-gray-900 mb-4 flex items-center'>
            <AlertCircle className='w-5 h-5 mr-2 text-red-500' />
            处理错误 ({processing.errors.length})
          </h3>

          <div className='space-y-3 max-h-96 overflow-y-auto'>
            {processing.errors.map((error, index) => (
              <div
                key={index}
                className='p-3 bg-red-50 border border-red-200 rounded-lg'
              >
                <div className='font-medium text-red-900 text-sm mb-1'>
                  {error.file}
                </div>
                <div className='text-red-700 text-sm'>{error.error}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 性能指标 */}
      <div className='grid grid-cols-1 lg:grid-cols-3 gap-6 mt-8'>
        <div className='card text-center'>
          <HardDrive className='w-8 h-8 text-gray-400 mx-auto mb-3' />
          <div className='text-2xl font-bold text-gray-900 mb-1'>
            {database.total_files > 0
              ? (database.total_keyframes / database.total_files).toFixed(1)
              : '0'}
          </div>
          <div className='text-sm text-gray-600'>平均关键帧/文件</div>
        </div>

        <div className='card text-center'>
          <Database className='w-8 h-8 text-gray-400 mx-auto mb-3' />
          <div className='text-2xl font-bold text-gray-900 mb-1'>
            {database.video_count > 0
              ? (database.total_keyframes / database.video_count).toFixed(1)
              : '0'}
          </div>
          <div className='text-sm text-gray-600'>平均关键帧/视频</div>
        </div>

        <div className='card text-center'>
          <CheckCircle className='w-8 h-8 text-gray-400 mx-auto mb-3' />
          <div className='text-2xl font-bold text-gray-900 mb-1'>
            {processing.total_count > 0
              ? (
                  ((processing.total_count - processing.errors.length) /
                    processing.total_count) *
                  100
                ).toFixed(1)
              : '100'}
            %
          </div>
          <div className='text-sm text-gray-600'>处理成功率</div>
        </div>
      </div>
    </div>
  );
};

export default StatusPage;
