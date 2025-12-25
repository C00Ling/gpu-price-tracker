// Home page - Dashboard with summary stats and top GPUs
import { Link } from 'react-router-dom';
import { useState, useEffect } from 'react';
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
import api from '../services/api';

export function Home() {
  const { data: stats, isLoading: statsLoading, error: statsError } = useSummaryStats();
  const { data: topGPUs, isLoading: topLoading, error: topError } = useTopValue(5);

  // Scraper progress with automatic WebSocket → Polling fallback
  const scrapeProgress = useScrapeProgress({
    pollingInterval: 2000, // Poll every 2 seconds
    wsFailoverTimeout: 5000 // Fall back to polling if no WS updates for 5 seconds
  });

  const [scrapeMessage, setScrapeMessage] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null);

  // Watch for scrape completion to show success message
  useEffect(() => {
    if (!scrapeProgress.isRunning && scrapeProgress.completedAt && scrapeProgress.progress === 100) {
      setScrapeMessage({
        type: 'success',
        text: 'Scraping завършен успешно!',
      });

      // Clear message after 5 seconds
      const timeout = setTimeout(() => {
        setScrapeMessage(null);
      }, 5000);

      return () => clearTimeout(timeout);
    }

    if (scrapeProgress.error) {
      setScrapeMessage({
        type: 'error',
        text: scrapeProgress.error,
      });
    }
  }, [scrapeProgress.isRunning, scrapeProgress.completedAt, scrapeProgress.progress, scrapeProgress.error]);

  const handleTriggerScrape = async () => {
    try {
      setScrapeMessage(null);
      await api.admin.triggerScrape();
      // Progress updates will come via WebSocket or polling
    } catch (error) {
      setScrapeMessage({
        type: 'error',
        text: error instanceof Error ? error.message : 'Грешка при стартиране на scraper',
      });
    }
  };

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
            <p className="text-3xl font-bold text-primary-500">{stats?.total_listings || 0}</p>
          </div>
        </Card>

        <Card>
          <div className="text-center">
            <p className="text-sm text-gray-400 mb-2">Модели</p>
            <p className="text-3xl font-bold text-primary-500">{stats?.unique_models || 0}</p>
          </div>
        </Card>

        <Card>
          <div className="text-center">
            <p className="text-sm text-gray-400 mb-2">Средна цена</p>
            <p className="text-3xl font-bold text-primary-500">
              {stats?.avg_price ? `${stats.avg_price.toFixed(0)}лв` : '-'}
            </p>
          </div>
        </Card>

        <Card>
          <div className="text-center">
            <p className="text-sm text-gray-400 mb-2">Мин. цена</p>
            <p className="text-3xl font-bold text-primary-500">
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
              {topGPUs.map((gpu, index) => (
                <div
                  key={gpu.model}
                  className="flex items-center justify-between p-4 bg-dark-navy-800/50 border border-dark-navy-700 rounded-lg hover:bg-dark-navy-800 hover:border-primary-500/50 transition-all"
                >
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center justify-center w-8 h-8 bg-primary-500 text-white rounded-full font-bold">
                      {index + 1}
                    </div>
                    <div>
                      <p className="font-semibold text-white">{gpu.model}</p>
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
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <Card hover>
          <CardHeader title="Разгледай всички обяви" />
          <CardContent>
            <p className="text-gray-400 mb-4">
              Преглед на всички обяви с филтри и търсене по модел
            </p>
            <Link to="/listings">
              <Button>Отвори обяви</Button>
            </Link>
          </CardContent>
        </Card>

        <Card hover>
          <CardHeader title="Анализ на стойността" />
          <CardContent>
            <p className="text-gray-400 mb-4">
              Виж коя видео карта предлага най-добра стойност за парите
            </p>
            <Link to="/value">
              <Button>Виж анализа</Button>
            </Link>
          </CardContent>
        </Card>
      </div>

      {/* Admin Section - Update Data */}
      <Card className={`border-2 bg-dark-navy-800/50 transition-all ${
        scrapeProgress.isRunning
          ? 'border-primary-500 animate-pulse'
          : 'border-primary-500/30'
      }`}>
        <CardHeader
          title="🔄 Обнови данните"
          subtitle="Стартирай нов scrape за най-нови обяви от OLX"
        />
        <CardContent>
          {scrapeMessage && (
            <div
              className={`mb-4 p-4 rounded-lg ${
                scrapeMessage.type === 'success'
                  ? 'bg-dark-navy-800/50 border border-green-500/50 text-green-400'
                  : scrapeMessage.type === 'error'
                  ? 'bg-dark-navy-800/50 border border-red-500/50 text-red-400'
                  : 'bg-dark-navy-800/50 border border-primary-500/50 text-primary-400'
              }`}
            >
              <p className="text-sm font-medium">{scrapeMessage.text}</p>
            </div>
          )}

          <div className="flex items-center justify-between mb-4">
            <div className="flex-1 mr-4">
              <p className="text-gray-300 text-sm mb-2">
                Последните данни: {stats?.total_listings || 0} обяви от {stats?.unique_models || 0} модела
              </p>
              <p className="text-gray-500 text-xs">
                Scraping отнема ~2-5 минути и ще обнови production базата данни.
              </p>
            </div>
            <Button
              onClick={handleTriggerScrape}
              disabled={scrapeProgress.isRunning}
              className="min-w-[140px]"
            >
              {scrapeProgress.isRunning ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Стартиране...
                </>
              ) : (
                '🚀 Стартирай Scrape'
              )}
            </Button>
          </div>

          {/* Progress Bar */}
          {scrapeProgress.isRunning && (
            <div className="space-y-3">
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
