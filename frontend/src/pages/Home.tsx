// Home page - Dashboard with summary stats and top GPUs
import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useSummaryStats, useTopValue } from '../hooks/useGPUData';
import { useScrapeProgress } from '../hooks/useScrapeProgress';
import {
  Card,
  CardHeader,
  CardContent,
  Button,
  LoadingPage,
  ErrorMessage,
  ValueBadge,
} from '../components';

function stripVRAMFromModel(model: string): string {
  return model.replace(/\s+\d+GB$/i, '');
}

export function Home() {
  useEffect(() => {
    document.title = 'GPU Market - Начало';
  }, []);

  const { data: stats, isLoading: statsLoading, error: statsError } = useSummaryStats();
  const { data: topGPUs, isLoading: topLoading, error: topError } = useTopValue(5);

  // Scraper progress with automatic WebSocket → Polling fallback
  const scrapeProgress = useScrapeProgress({
    pollingInterval: 2000, // Poll every 2 seconds
    wsFailoverTimeout: 5000 // Fall back to polling if no WS updates for 5 seconds
  });


  if (statsLoading || topLoading) {
    return <LoadingPage />;
  }

  if (statsError || topError) {
    return (
      <ErrorMessage message="Грешка при зареждане на данните" />
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Hero Section */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-white mb-4">
          Анализ на цени на видео карти в България
        </h1>
        <p className="text-lg text-gray-400 max-w-2xl mx-auto">
          Проследяваме цените на GPU-та от OLX и предоставяме детайлна статистика и анализ на стойността
        </p>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
        <Card>
          <div className="text-center">
            <p className="text-sm text-gray-400 mb-2">Обяви</p>
            <p className="text-3xl font-bold text-white">{stats?.total_listings || 0}</p>
          </div>
        </Card>

        <Card>
          <div className="text-center">
            <p className="text-sm text-gray-400 mb-2">Модели</p>
            <p className="text-3xl font-bold text-white">{stats?.unique_models || 0}</p>
          </div>
        </Card>

        <Card>
          <div className="text-center">
            <p className="text-sm text-gray-400 mb-2">Средна цена</p>
            <p className="text-3xl font-bold text-white">
              {stats?.avg_price ? `${stats.avg_price.toFixed(0)}лв` : '-'}
            </p>
          </div>
        </Card>

        <Card>
          <div className="text-center">
            <p className="text-sm text-gray-400 mb-2">Мин. цена</p>
            <p className="text-3xl font-bold text-white">
              {stats?.min_price ? `${stats.min_price.toFixed(0)}лв` : '-'}
            </p>
          </div>
        </Card>
      </div>

      {/* Top Value GPUs */}
      <Card className="mb-8">
        <CardHeader
          title="Топ 5 по стойност (FPS/лв)"
          subtitle="Най-добрата стойност за парите"
          action={
            <Link to="/value">
              <Button variant="outline" size="sm">
                Виж всички
              </Button>
            </Link>
          }
        />
        <CardContent>
          {topGPUs && topGPUs.length > 0 ? (
            <div className="space-y-3">
              {topGPUs.map((gpu) => (
                <div
                  key={gpu.model}
                  className="flex items-center justify-between p-4 bg-dark-navy-800/50 border border-dark-navy-700 rounded-lg hover:bg-dark-navy-800 hover:border-primary-500/50 transition-all"
                >
                  <div className="flex items-center space-x-4">
                    <div>
                      <p className="font-semibold text-white">{stripVRAMFromModel(gpu.model)}</p>
                      <p className="text-sm text-gray-400">
                        {gpu.fps} FPS @ {gpu.price.toFixed(0)}лв
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <ValueBadge value={gpu.fps_per_lv} size="md" />
                    <div className="text-right">
                      <p className="text-sm text-gray-400">
                        {gpu.fps_per_lv.toFixed(3)} FPS/лв
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center text-gray-400 py-8">Няма данни</p>
          )}
        </CardContent>
      </Card>

      {/* CTA Section */}
      <Card hover className={`mb-8 border-2 transition-all ${
          scrapeProgress.isRunning
            ? 'border-primary-500 animate-pulse'
            : 'border-primary-500/30'
        }`}>
          <CardHeader title="Анализ на стойността" />
          <CardContent>
            <p className="text-gray-400 mb-4">
              Виж коя видео карта предлага най-добра стойност за парите. Кликни на модела за да видиш най-евтината обява в OLX.
            </p>

            {/* Button */}
            <div className="mb-4">
              <Link to="/value">
                <Button>Виж анализа</Button>
              </Link>
            </div>

            {/* Last Update Info */}
            <div className="text-xs text-gray-500 space-y-1">
              <p>
                📊 Данни: {stats?.total_listings || 0} обяви от {stats?.unique_models || 0} модела
              </p>
              {scrapeProgress.completedAt && (
                <p>
                  🕒 Последно обновено: {new Date(scrapeProgress.completedAt).toLocaleString('bg-BG', {
                    day: '2-digit',
                    month: '2-digit',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </p>
              )}
              <p className="text-gray-600 italic">
                ℹ️ Данните се обновяват автоматично
              </p>
            </div>

            {/* Progress Bar */}
            {scrapeProgress.isRunning && (
              <div className="space-y-2 mt-4">
                {/* Status Text */}
                <div className="flex items-center justify-between text-sm">
                  <span className="text-primary-400 font-medium">{scrapeProgress.status}</span>
                  <span className="text-gray-400">{Math.round(scrapeProgress.progress)}%</span>
                </div>

                {/* Progress Bar */}
                <div className="relative w-full h-3 bg-dark-navy-900 rounded-full overflow-hidden border border-dark-navy-700">
                  <div
                    className="absolute top-0 left-0 h-full bg-gradient-to-r from-primary-500 to-cyan-500 rounded-full transition-all duration-1000 ease-out"
                    style={{ width: `${scrapeProgress.progress}%` }}
                  >
                    {/* Animated shimmer effect */}
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer"></div>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
    </div>
  );
}
