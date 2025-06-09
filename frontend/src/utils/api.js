import axios from 'axios';

// 创建axios实例，配置基础URL
const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 300000, // 30秒超时
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    console.log('发送请求:', config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('请求错误:', error.response?.status, error.response?.data);
    return Promise.reject(error);
  },
);

export default api;
