import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Search, Scan, BarChart3, Home } from 'lucide-react';

const Navbar = () => {
  const location = useLocation();

  const navItems = [
    { path: '/', label: '首页', icon: Home },
    { path: '/search', label: '搜索', icon: Search },
    { path: '/scan', label: '扫描', icon: Scan },
    { path: '/status', label: '状态', icon: BarChart3 },
  ];

  return (
    <nav className='bg-white shadow-sm border-b border-gray-200'>
      <div className='container mx-auto px-4'>
        <div className='flex items-center justify-between h-16'>
          {/* Logo */}
          <div className='flex items-center space-x-2'>
            <div className='w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center'>
              <Search className='w-5 h-5 text-white' />
            </div>
            <span className='text-xl font-bold text-gray-900'>
              本地媒体检索
            </span>
          </div>

          {/* Navigation Links */}
          <div className='flex space-x-1'>
            {navItems.map(({ path, label, icon: Icon }) => {
              const isActive = location.pathname === path;
              return (
                <Link
                  key={path}
                  to={path}
                  className={`
                    flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-200
                    ${
                      isActive
                        ? 'bg-primary-100 text-primary-700'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }
                  `}
                >
                  <Icon className='w-4 h-4' />
                  <span>{label}</span>
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
