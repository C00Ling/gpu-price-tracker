// Home page - Dashboard with summary stats and top GPUs
import { Link } from 'react-router-dom';
import { useSummaryStats, useTopValue } from '../hooks/useGPUData';
import {
  Card,
  CardHeader,
  CardContent,
  Button,
  LoadingPage,
  ErrorMessage,
} from '../components';

export function Home() {
  const { data: stats, isLoading: statsLoading, error: statsError } = useSummaryStats();
  const { data: topGPUs, isLoading: topLoading, error: topError } = useTopValue(5);

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
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Анализ на цени на видео карти в България
        </h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Проследяваме цените на GPU-та от OLX и предоставяме детайлна статистика и анализ на стойността
        </p>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
        <Card>
          <div className="text-center">
            <p className="text-sm text-gray-500 mb-2">Обяви</p>
            <p className="text-3xl font-bold text-primary-600">{stats?.total_listings || 0}</p>
          </div>
        </Card>

        <Card>
          <div className="text-center">
            <p className="text-sm text-gray-500 mb-2">Модели</p>
            <p className="text-3xl font-bold text-primary-600">{stats?.unique_models || 0}</p>
          </div>
        </Card>

        <Card>
          <div className="text-center">
            <p className="text-sm text-gray-500 mb-2">Средна цена</p>
            <p className="text-3xl font-bold text-primary-600">
              {stats?.avg_price ? `${stats.avg_price.toFixed(0)}лв` : '-'}
            </p>
          </div>
        </Card>

        <Card>
          <div className="text-center">
            <p className="text-sm text-gray-500 mb-2">Мин. цена</p>
            <p className="text-3xl font-bold text-primary-600">
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
                  className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center justify-center w-8 h-8 bg-primary-600 text-white rounded-full font-bold">
                      {index + 1}
                    </div>
                    <div>
                      <p className="font-semibold text-gray-900">{gpu.model}</p>
                      <p className="text-sm text-gray-500">
                        {gpu.fps} FPS @ {gpu.price.toFixed(0)}лв
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold text-primary-600">
                      {gpu.fps_per_lv.toFixed(2)}
                    </p>
                    <p className="text-xs text-gray-500">FPS/лв</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center text-gray-500 py-8">Няма данни</p>
          )}
        </CardContent>
      </Card>

      {/* CTA Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card hover>
          <CardHeader title="Разгледай всички обяви" />
          <CardContent>
            <p className="text-gray-600 mb-4">
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
            <p className="text-gray-600 mb-4">
              Виж коя видео карта предлага най-добра стойност за парите
            </p>
            <Link to="/value">
              <Button>Виж анализа</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
