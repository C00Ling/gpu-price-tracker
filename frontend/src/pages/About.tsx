// About page - Project information
import { useEffect } from 'react';
import { Card, CardHeader, CardContent } from '../components';
import { config } from '../lib/config';

export function About() {
  useEffect(() => {
    document.title = 'GPU Market - За проекта';
  }, []);

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <Card className="mb-6">
        <CardHeader title="За проекта" />
        <CardContent>
          <div className="prose prose-blue max-w-none">
            <p className="text-lg text-gray-300">
              <strong>{config.app.name}</strong> е проект за анализ на цените на видео карти на
              българския вторичен пазар. Събираме данни от OLX и предоставяме детайлна статистика
              и анализ на стойността.
            </p>

            <h3 className="text-xl font-semibold text-white mt-6 mb-3">
              Функционалности
            </h3>
            <ul className="space-y-2 text-gray-300">
              <li>📊 Автоматично scraping на обяви от OLX</li>
              <li>📈 Детайлна ценова статистика по модели</li>
              <li>💎 Анализ на стойността (FPS/лв)</li>
              <li>🔔 Известия за промени в цените (Email, Telegram)</li>
              <li>⚡ Real-time updates през WebSocket</li>
              <li>🚀 Redis кеширане за максимална производителност</li>
              <li>🐳 Docker контейнеризация</li>
              <li>✅ CI/CD pipeline с GitHub Actions</li>
            </ul>

            <h3 className="text-xl font-semibold text-white mt-6 mb-3">
              Технологичен стек
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
              <div>
                <h4 className="font-semibold text-white mb-2">Backend</h4>
                <ul className="space-y-1 text-sm text-gray-300">
                  <li>• Python 3.11+ & FastAPI</li>
                  <li>• PostgreSQL & SQLAlchemy</li>
                  <li>• Redis за кеширане</li>
                  <li>• Celery за scheduled tasks</li>
                  <li>• WebSocket support</li>
                  <li>• Alembic за миграции</li>
                </ul>
              </div>

              <div>
                <h4 className="font-semibold text-white mb-2">Frontend</h4>
                <ul className="space-y-1 text-sm text-gray-300">
                  <li>• React 18 & TypeScript</li>
                  <li>• Vite за build</li>
                  <li>• TailwindCSS за стилове</li>
                  <li>• React Query за data fetching</li>
                  <li>• React Router v6</li>
                  <li>• Zustand за state management</li>
                </ul>
              </div>
            </div>

            <h3 className="text-xl font-semibold text-white mt-6 mb-3">
              Методология
            </h3>
            <p className="text-gray-300">
              Анализът на стойността се базира на съотношението FPS/лв, където FPS са
              benchmark резултати за 1080p игри (използваме данни от{' '}
              <a
                href="https://www.tomshardware.com/reviews/gpu-hierarchy,4388.html"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary-600 hover:text-primary-700 underline"
              >
                Tom's Hardware GPU Hierarchy 2025
              </a>
              ), а цената е медианната стойност от всички обяви за съответния модел.
            </p>

            <div className="mt-4 bg-zinc-800 rounded-lg p-4 border border-zinc-700">
              <h4 className="font-semibold text-white mb-2 flex items-center gap-2">
                <span className="text-red-500">🎮</span>
                Benchmark настройки
              </h4>
              <ul className="space-y-1 text-sm text-gray-300">
                <li>• <strong>Игра:</strong> Red Dead Redemption 2</li>
                <li>• <strong>Резолюция:</strong> 1920 x 1080 (Full HD)</li>
                <li>• <strong>Настройки:</strong> Highest</li>
                <li>• <strong>Тестова система:</strong> AMD Ryzen 9 9950X3D CPU</li>
              </ul>
              <p className="text-xs text-gray-400 mt-3">
                Benchmark данните представляват средна производителност в реални игрови сценарии.
                Стойностите могат да варират в зависимост от конкретната система и настройки.
              </p>
            </div>

            <h3 className="text-xl font-semibold text-white mt-6 mb-3">
              API endpoints
            </h3>
            <div className="bg-zinc-800 rounded-lg p-4 text-sm font-mono text-gray-200 space-y-1">
              <div><span className="text-green-600">GET</span> /api/listings - Всички обяви</div>
              <div><span className="text-green-600">GET</span> /api/stats/summary - Обща статистика</div>
              <div><span className="text-green-600">GET</span> /api/value - Анализ на стойността</div>
              <div><span className="text-blue-600">WS</span> /api/ws - WebSocket връзка</div>
            </div>

            <h3 className="text-xl font-semibold text-white mt-6 mb-3">
              Версия
            </h3>
            <p className="text-gray-300">
              Текуща версия: <strong>{config.app.version}</strong>
            </p>

            <div className="mt-8 p-4 bg-blue-950/30 rounded-lg border border-blue-500/30">
              <p className="text-sm text-gray-300">
                <strong>Забележка:</strong> Данните се обновяват автоматично на всеки 6 часа.
                Цените са взети от реални обяви и могат да не отразяват точната пазарна стойност.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Contact Card */}
      <Card>
        <CardHeader title="Контакти" />
        <CardContent>
          <p className="text-gray-300 mb-4">
            Проектът е с отворен код и приема допринасяния.
          </p>
          <div className="flex space-x-4">
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary-600 hover:text-primary-700 font-medium"
            >
              GitHub →
            </a>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
