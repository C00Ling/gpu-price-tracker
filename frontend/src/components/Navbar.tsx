// Navigation bar component
import { Link, useLocation } from 'react-router-dom';
import { config } from '../lib/config';
import { GpuIcon } from './GpuIcon';

export function Navbar() {
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  const navItems = [
    { path: '/', label: 'Начало' },
    { path: '/listings', label: 'Обяви' },
    { path: '/value', label: 'Стойност' },
    { path: '/about', label: 'За проекта' },
  ];

  return (
    <nav className="bg-[#1E1E1E] border-b border-zinc-800 shadow-lg shadow-black/50 sticky top-0 z-50 backdrop-blur-sm bg-[#1E1E1E]/95">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-3 group">
            <GpuIcon size={32} className="group-hover:scale-110 transition-transform" />
            <div>
              <h1 className="text-xl font-bold text-white">{config.app.name}</h1>
              <p className="text-xs text-gray-400 hidden sm:block">{config.app.description}</p>
            </div>
          </Link>

          {/* Navigation Links */}
          <div className="flex space-x-1">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`
                  px-3 py-2 rounded-md text-sm font-medium transition-all
                  ${isActive(item.path)
                    ? 'bg-primary-600 text-white shadow-lg shadow-primary-500/30'
                    : 'text-gray-300 hover:bg-zinc-800 hover:text-white'
                  }
                `}
              >
                {item.label}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </nav>
  );
}
