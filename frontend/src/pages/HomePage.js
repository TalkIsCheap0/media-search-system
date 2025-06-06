import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Search,
  Scan,
  BarChart3,
  Play,
  Image,
  Database,
  Cpu,
} from 'lucide-react';
import api from '../utils/api';

const HomePage = () => {
  const [stats, setStats] = useState(null);
  const [systemStatus, setSystemStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSystemInfo();
  }, []);

  const fetchSystemInfo = async () => {
    try {
      const [statusResponse, statsResponse] = await Promise.all([
        api.get('/api/status'),
        api.get('/api/database-stats'),
      ]);

      if (statusResponse.data.success) {
        setSystemStatus(statusResponse.data);
      }
      if (statsResponse.data.success) {
        setStats(statsResponse.data.stats);
      }
    } catch (error) {
      console.error('获取系统信息失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const quickActions = [
    {
      title: '智能搜索',
      description: '使用自然语言搜索图片和视频',
      icon: Search,
      link: '/search',
      color: 'bg-blue-500',
      hoverColor: 'hover:bg-blue-600',
    },
    {
      title: '扫描文件',
      description: '扫描本地目录并建立索引',
      icon: Scan,
      link: '/scan',
      color: 'bg-green-500',
      hoverColor: 'hover:bg-green-600',
    },
    {
      title: '系统状态',
      description: '查看处理进度和系统信息',
      icon: BarChart3,
      link: '/status',
      color: 'bg-purple-500',
      hoverColor: 'hover:bg-purple-600',
    },
  ];

  const StatCard = ({ title, value, icon: Icon, color }) => (
    <div className='card'>
      <div className='flex items-center justify-between'>
        <div>
          <p className='text-sm font-medium text-gray-600'>{title}</p>
          <p className='text-2xl font-bold text-gray-900'>{value}</p>
        </div>
        <div className={`p-3 rounded-lg ${color}`}>
          <Icon className='w-6 h-6 text-white' />
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className='flex items-center justify-center min-h-96'>
        <div className='inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600'></div>
      </div>
    );
  }

  return (
    <div className='max-w-6xl mx-auto'>
      {/* 欢迎区域 */}
      <div className='text-center mb-12'>
        <h1 className='text-4xl font-bold text-gray-900 mb-4'>
          本地媒体检索系统
        </h1>
        <p className='text-xl text-gray-600 max-w-3xl mx-auto'>
          基于 CLIP 模型的智能图片视频检索系统，支持自然语言搜索，
          让您轻松找到本地存储的任何媒体内容
        </p>
      </div>

      {/* 统计卡片 */}
      {stats && (
        <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12'>
          <StatCard
            title='总文件数'
            value={stats.total_files.toLocaleString()}
            icon={Database}
            color='bg-blue-500'
          />
          <StatCard
            title='图片数量'
            value={stats.image_count.toLocaleString()}
            icon={Image}
            color='bg-green-500'
          />
          <StatCard
            title='视频数量'
            value={stats.video_count.toLocaleString()}
            icon={Play}
            color='bg-purple-500'
          />
          <StatCard
            title='关键帧数'
            value={stats.total_keyframes.toLocaleString()}
            icon={BarChart3}
            color='bg-orange-500'
          />
        </div>
      )}

      {/* 快速操作 */}
      <div className='mb-12'>
        <h2 className='text-2xl font-bold text-gray-900 mb-6'>快速操作</h2>
        <div className='grid grid-cols-1 md:grid-cols-3 gap-6'>
          {quickActions.map((action, index) => (
            <Link key={index} to={action.link} className='group block'>
              <div className='card hover:shadow-lg transition-all duration-200 group-hover:scale-105'>
                <div className='flex items-center space-x-4'>
                  <div
                    className={`p-3 rounded-lg ${action.color} ${action.hoverColor} transition-colors duration-200`}
                  >
                    <action.icon className='w-6 h-6 text-white' />
                  </div>
                  <div>
                    <h3 className='text-lg font-semibold text-gray-900 group-hover:text-primary-600 transition-colors duration-200'>
                      {action.title}
                    </h3>
                    <p className='text-gray-600'>{action.description}</p>
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* 系统信息 */}
      {systemStatus && (
        <div className='grid grid-cols-1 lg:grid-cols-2 gap-6 mb-12'>
          {/* 系统状态 */}
          <div className='card'>
            <h3 className='text-lg font-semibold text-gray-900 mb-4 flex items-center'>
              <Cpu className='w-5 h-5 mr-2' />
              系统状态
            </h3>
            <div className='space-y-3'>
              <div className='flex justify-between'>
                <span className='text-gray-600'>CLIP 模型</span>
                <span className='font-medium'>
                  {systemStatus.system.clip_model}
                </span>
              </div>
              <div className='flex justify-between'>
                <span className='text-gray-600'>运行设备</span>
                <span className='font-medium uppercase'>
                  {systemStatus.system.device}
                </span>
              </div>
              <div className='flex justify-between'>
                <span className='text-gray-600'>处理状态</span>
                <span
                  className={`font-medium ${
                    systemStatus.processing.is_processing
                      ? 'text-yellow-600'
                      : 'text-green-600'
                  }`}
                >
                  {systemStatus.processing.is_processing ? '处理中' : '空闲'}
                </span>
              </div>
            </div>
          </div>

          {/* 处理进度 */}
          <div className='card'>
            <h3 className='text-lg font-semibold text-gray-900 mb-4 flex items-center'>
              <BarChart3 className='w-5 h-5 mr-2' />
              处理进度
            </h3>
            {systemStatus.processing.is_processing ? (
              <div className='space-y-3'>
                <div className='flex justify-between text-sm'>
                  <span>进度</span>
                  <span>
                    {systemStatus.processing.processed_count} /{' '}
                    {systemStatus.processing.total_count}
                  </span>
                </div>
                <div className='w-full bg-gray-200 rounded-full h-2'>
                  <div
                    className='bg-primary-600 h-2 rounded-full transition-all duration-300'
                    style={{
                      width: `${
                        (systemStatus.processing.processed_count /
                          systemStatus.processing.total_count) *
                        100
                      }%`,
                    }}
                  ></div>
                </div>
                <p className='text-sm text-gray-600 truncate'>
                  当前文件: {systemStatus.processing.current_file}
                </p>
              </div>
            ) : (
              <p className='text-gray-600'>当前没有处理任务</p>
            )}
          </div>
        </div>
      )}

      {/* 功能特性 */}
      <div className='card'>
        <h2 className='text-2xl font-bold text-gray-900 mb-6'>功能特性</h2>
        <div className='grid grid-cols-1 md:grid-cols-2 gap-6'>
          <div>
            <h3 className='text-lg font-semibold text-gray-900 mb-3'>
              智能检索
            </h3>
            <ul className='space-y-2 text-gray-600'>
              <li>• 基于 CLIP 模型的语义理解</li>
              <li>• 支持自然语言描述搜索</li>
              <li>• 跨模态检索（文本搜图片/视频）</li>
              <li>• 智能结果聚合和排序</li>
            </ul>
          </div>
          <div>
            <h3 className='text-lg font-semibold text-gray-900 mb-3'>
              视频处理
            </h3>
            <ul className='space-y-2 text-gray-600'>
              <li>• 多策略关键帧提取</li>
              <li>• 场景变化自动检测</li>
              <li>• 高召回率时间采样</li>
              <li>• 精确时间戳定位</li>
            </ul>
          </div>
          <div>
            <h3 className='text-lg font-semibold text-gray-900 mb-3'>
              本地部署
            </h3>
            <ul className='space-y-2 text-gray-600'>
              <li>• 完全离线运行</li>
              <li>• 数据隐私保护</li>
              <li>• 无需网络连接</li>
              <li>• 支持大规模文件处理</li>
            </ul>
          </div>
          <div>
            <h3 className='text-lg font-semibold text-gray-900 mb-3'>
              用户体验
            </h3>
            <ul className='space-y-2 text-gray-600'>
              <li>• 现代化 Web 界面</li>
              <li>• 实时处理进度显示</li>
              <li>• 响应式设计</li>
              <li>• 直观的搜索结果展示</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage;
