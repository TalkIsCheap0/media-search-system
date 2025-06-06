import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Navbar from './components/Navbar';
import HomePage from './pages/HomePage';
import SearchPage from './pages/SearchPage';
import ScanPage from './pages/ScanPage';
import StatusPage from './pages/StatusPage';
import './index.css';

function App() {
  return (
    <Router>
      <div className='min-h-screen bg-gray-50'>
        <Navbar />
        <main className='container mx-auto px-4 py-8'>
          <Routes>
            <Route path='/' element={<HomePage />} />
            <Route path='/search' element={<SearchPage />} />
            <Route path='/scan' element={<ScanPage />} />
            <Route path='/status' element={<StatusPage />} />
          </Routes>
        </main>
        <Toaster
          position='top-right'
          toastOptions={{
            duration: 4000,
            style: {
              background: '#363636',
              color: '#fff',
            },
            success: {
              duration: 3000,
              iconTheme: {
                primary: '#4ade80',
                secondary: '#fff',
              },
            },
            error: {
              duration: 5000,
              iconTheme: {
                primary: '#ef4444',
                secondary: '#fff',
              },
            },
          }}
        />
      </div>
    </Router>
  );
}

export default App;
