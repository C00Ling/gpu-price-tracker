// Navigation bar component
import { Link, useLocation } from 'react-router-dom';
import { config } from '../lib/config';

export function Navbar() {
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  const navItems = [
    { path: '/', label: 'Начало', icon: '🏠' },
    { path: '/listings', label: 'Обяви', icon: '📋' },
    { path: '/value', label: 'Стойност', icon: '💎' },
    { path: '/about', label: 'За проекта', icon: 'ℹ️' },
  ];

  return (
    <nav className="bg-white shadow-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <span className="text-2xl">🎮</span>
            <div>
              <h1 className="text-xl font-bold text-gray-900">{config.app.name}</h1>
              <p className="text-xs text-gray-500 hidden sm:block">{config.app.description}</p>
            </div>
          </Link>

          {/* Navigation Links */}
          <div className="flex space-x-1">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`
                  px-3 py-2 rounded-md text-sm font-medium transition-colors
                  ${isActive(item.path)
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-700 hover:bg-gray-100'
                  }
                `}
              >
                <span className="hidden sm:inline">{item.icon} </span>
                {item.label}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </nav>
  );
}
