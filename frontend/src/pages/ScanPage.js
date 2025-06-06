import React, { useState } from 'react';
import {
  Folder,
  Scan,
  AlertCircle,
  CheckCircle,
  FolderOpen,
} from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../utils/api';

const ScanPage = () => {
  const [directoryPath, setDirectoryPath] = useState('');
  const [recursive, setRecursive] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState(null);

  const handleScan = async (e) => {
    e.preventDefault();

    if (!directoryPath.trim()) {
      toast.error('请输入目录路径');
      return;
    }

    setScanning(true);
    setScanResult(null);

    try {
      const response = await api.post('/api/scan', {
        directory_path: directoryPath.trim(),
        recursive: recursive,
      });

      if (response.data.success) {
        toast.success('扫描任务已启动');
        setScanResult({
          success: true,
          message: response.data.message,
          directory: response.data.directory,
          recursive: response.data.recursive,
        });
      } else {
        toast.error('扫描失败');
      }
    } catch (error) {
      console.error('扫描错误:', error);
      const errorMessage = error.response?.data?.detail || error.message;
      toast.error('扫描失败: ' + errorMessage);
      setScanResult({
        success: false,
        error: errorMessage,
      });
    } finally {
      setScanning(false);
    }
  };

  const commonPaths = [
    { label: '图片文件夹', path: '~/Pictures', icon: '🖼️' },
    { label: '视频文件夹', path: '~/Videos', icon: '🎬' },
    { label: '下载文件夹', path: '~/Downloads', icon: '📥' },
    { label: '桌面', path: '~/Desktop', icon: '🖥️' },
    { label: '文档文件夹', path: '~/Documents', icon: '📁' },
  ];

  return (
    <div className='max-w-4xl mx-auto'>
      {/* 页面标题 */}
      <div className='mb-8'>
        <h1 className='text-3xl font-bold text-gray-900 mb-2'>扫描本地文件</h1>
        <p className='text-gray-600'>
          扫描指定目录下的图片和视频文件，建立搜索索引
        </p>
      </div>

      {/* 扫描表单 */}
      <div className='card mb-8'>
        <form onSubmit={handleScan}>
          <div className='mb-6'>
            <label className='block text-sm font-medium text-gray-700 mb-2'>
              目录路径
            </label>
            <div className='relative'>
              <FolderOpen className='absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5' />
              <input
                type='text'
                value={directoryPath}
                onChange={(e) => setDirectoryPath(e.target.value)}
                placeholder='例如: /Users/username/Pictures 或 C:\Users\username\Pictures'
                className='input-field pl-10'
                disabled={scanning}
              />
            </div>
            <p className='mt-2 text-sm text-gray-500'>
              请输入要扫描的目录的完整路径
            </p>
          </div>

          <div className='mb-6'>
            <label className='flex items-center'>
              <input
                type='checkbox'
                checked={recursive}
                onChange={(e) => setRecursive(e.target.checked)}
                className='rounded border-gray-300 text-primary-600 focus:ring-primary-500'
                disabled={scanning}
              />
              <span className='ml-2 text-sm text-gray-700'>递归扫描子目录</span>
            </label>
            <p className='mt-1 text-sm text-gray-500'>
              启用后将扫描指定目录下的所有子目录
            </p>
          </div>

          <button
            type='submit'
            disabled={scanning}
            className='btn-primary flex items-center space-x-2'
          >
            <Scan className='w-4 h-4' />
            <span>{scanning ? '扫描中...' : '开始扫描'}</span>
          </button>
        </form>
      </div>

      {/* 常用路径快捷选择 */}
      <div className='card mb-8'>
        <h3 className='text-lg font-semibold text-gray-900 mb-4'>常用目录</h3>
        <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3'>
          {commonPaths.map((item, index) => (
            <button
              key={index}
              onClick={() => setDirectoryPath(item.path)}
              className='flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors duration-200 text-left'
              disabled={scanning}
            >
              <span className='text-2xl'>{item.icon}</span>
              <div>
                <div className='font-medium text-gray-900'>{item.label}</div>
                <div className='text-sm text-gray-500'>{item.path}</div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* 扫描结果 */}
      {scanResult && (
        <div
          className={`card ${
            scanResult.success
              ? 'border-green-200 bg-green-50'
              : 'border-red-200 bg-red-50'
          }`}
        >
          <div className='flex items-start space-x-3'>
            {scanResult.success ? (
              <CheckCircle className='w-6 h-6 text-green-600 flex-shrink-0 mt-0.5' />
            ) : (
              <AlertCircle className='w-6 h-6 text-red-600 flex-shrink-0 mt-0.5' />
            )}
            <div className='flex-1'>
              <h3
                className={`font-medium ${
                  scanResult.success ? 'text-green-900' : 'text-red-900'
                }`}
              >
                {scanResult.success ? '扫描任务已启动' : '扫描失败'}
              </h3>
              {scanResult.success ? (
                <div className='mt-2 text-sm text-green-700'>
                  <p>目录: {scanResult.directory}</p>
                  <p>递归扫描: {scanResult.recursive ? '是' : '否'}</p>
                  <p className='mt-2'>
                    扫描任务已在后台启动，您可以在
                    <a
                      href='/status'
                      className='font-medium underline hover:no-underline'
                    >
                      状态页面
                    </a>
                    查看处理进度。
                  </p>
                </div>
              ) : (
                <p className='mt-2 text-sm text-red-700'>{scanResult.error}</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 使用说明 */}
      <div className='card'>
        <h3 className='text-lg font-semibold text-gray-900 mb-4'>使用说明</h3>
        <div className='space-y-4 text-sm text-gray-600'>
          <div>
            <h4 className='font-medium text-gray-900 mb-2'>支持的文件格式</h4>
            <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
              <div>
                <p className='font-medium'>图片格式:</p>
                <p>JPG, JPEG, PNG, GIF, BMP, TIFF, WebP, HEIC, HEIF</p>
              </div>
              <div>
                <p className='font-medium'>视频格式:</p>
                <p>MP4, AVI, MKV, MOV, WMV, FLV, WebM, M4V, 3GP</p>
              </div>
            </div>
          </div>

          <div>
            <h4 className='font-medium text-gray-900 mb-2'>扫描过程</h4>
            <ol className='list-decimal list-inside space-y-1'>
              <li>系统会递归扫描指定目录下的所有媒体文件</li>
              <li>对于图片，直接提取 CLIP 特征向量</li>
              <li>对于视频，会提取关键帧并生成特征向量</li>
              <li>所有特征向量存储到向量数据库中用于搜索</li>
              <li>生成缩略图以便在界面中预览</li>
            </ol>
          </div>

          <div>
            <h4 className='font-medium text-gray-900 mb-2'>注意事项</h4>
            <ul className='list-disc list-inside space-y-1'>
              <li>扫描大量文件可能需要较长时间，请耐心等待</li>
              <li>确保有足够的磁盘空间存储缩略图和数据库文件</li>
              <li>重复扫描相同文件会自动跳过，不会重复处理</li>
              <li>扫描过程中可以继续使用其他功能</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ScanPage;
