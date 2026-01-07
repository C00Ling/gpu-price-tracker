// Value Analysis page - FPS per лв ranking
import { useState, useEffect } from 'react';
import { useValueAnalysis } from '../hooks/useGPUData';
import {
  Card,
  CardHeader,
  CardContent,
  Table,
  ValueBadge,
  LoadingPage,
  ErrorMessage,
  TableSkeleton,
} from '../components';

// Helper function to remove VRAM suffix from model name for display
// e.g. "GTX 1060 6GB" → "GTX 1060", "RX 580 8GB" → "RX 580"
function stripVRAMFromModel(model: string): string {
  return model.replace(/\s+\d+GB$/i, '');
}

export function ValueAnalysis() {
  useEffect(() => {
    document.title = 'GPU Market - Стойност';
  }, []);

  const [vramFilter, setVramFilter] = useState<number | undefined>(undefined);
  const { data: valueData, isLoading, error, refetch } = useValueAnalysis(vramFilter);
  const [showAll, setShowAll] = useState(true);

  if (isLoading) {
    return <LoadingPage />;
  }

  if (error) {
    return <ErrorMessage message="Грешка при зареждане на анализа" retry={refetch} />;
  }

  const displayData = showAll ? valueData : valueData?.slice(0, 20);

  const columns = [
    {
      key: 'model',
      label: 'Модел',
      sortable: true,
      render: (item: any) => {
        const displayName = stripVRAMFromModel(item.model);
        return item.cheapest_url ? (
          <a
            href={item.cheapest_url}
            target="_blank"
            rel="noopener noreferrer"
            className="font-semibold text-primary-500 hover:text-primary-400 transition-colors underline decoration-primary-500/30 hover:decoration-primary-400"
          >
            {displayName}
          </a>
        ) : (
          <span className="font-semibold text-white">{displayName}</span>
        );
      },
    },
    {
      key: 'fps',
      label: 'FPS (1080p)',
      sortable: true,
      render: (item: any) => (
        <span className="text-gray-300">{item.fps}</span>
      ),
    },
    {
      key: 'relative_score',
      label: 'Performance',
      sortable: true,
      render: (item: any) => (
        <div className="flex items-center space-x-2">
          {item.relative_score ? (
            <>
              <div className="w-16 bg-dark-navy-800 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-gradient-to-r from-primary-600 to-primary-400 h-full rounded-full transition-all duration-300"
                  style={{ width: `${item.relative_score}%` }}
                />
              </div>
              <span className="text-sm font-medium text-gray-300 min-w-[2.5rem]">
                {item.relative_score}
              </span>
            </>
          ) : (
            <span className="text-gray-500">-</span>
          )}
        </div>
      ),
    },
    {
      key: 'vram',
      label: 'VRAM',
      sortable: true,
      render: (item: any) => (
        <span className="text-gray-300">
          {item.vram ? `${item.vram}GB` : '-'}
        </span>
      ),
    },
    {
      key: 'price',
      label: 'Цена',
      sortable: true,
      render: (item: any) => (
        <span className="text-gray-300 font-semibold">{item.price.toFixed(0)} лв</span>
      ),
    },
    {
      key: 'fps_per_lv',
      label: 'Стойност',
      sortable: true,
      render: (item: any) => (
        <div className="flex items-center space-x-3">
          <ValueBadge value={item.fps_per_lv} size="md" />
          <span className="text-sm text-gray-500">
            {item.fps_per_lv.toFixed(3)} FPS/лв
          </span>
        </div>
      ),
    },
  ];


  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Info Card */}
      <Card className="mb-6 bg-dark-navy-800/50 border-dark-navy-700">
        <CardContent className="py-4">
          <div className="flex items-start space-x-3">
            <div className="w-10 h-10 rounded-full bg-primary-500/20 flex items-center justify-center flex-shrink-0">
              <svg className="w-5 h-5 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <h3 className="font-semibold text-white mb-1">
                Как работи анализът на стойността?
              </h3>
              <p className="text-sm text-gray-300 mb-2">
                Изчисляваме FPS/лв (кадри в секунда на лев) за всеки модел, използвайки benchmark данни за 1080p игри
                и медианната цена от обявите. По-високата стойност означава по-добра стойност за парите.
              </p>
              <p className="text-sm text-gray-400">
                <strong className="text-gray-300">Performance:</strong> Относителен скор (0-100) спрямо RTX 5090 = 100.
                По-високият скор означава по-висока gaming производителност.
              </p>

              <div className="mt-4 relative overflow-hidden rounded-lg border border-dark-navy-700">
                {/* Background with gradient */}
                <div className="absolute inset-0 bg-gradient-to-br from-red-900/10 via-dark-navy-800/50 to-orange-900/10"></div>

                {/* Content */}
                <div className="relative p-4">
                  <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                    <svg className="w-4 h-4 text-red-500" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
                      <polyline points="7.5 4.21 12 6.81 16.5 4.21"></polyline>
                      <polyline points="7.5 19.79 7.5 14.6 3 12"></polyline>
                      <polyline points="21 12 16.5 14.6 16.5 19.79"></polyline>
                      <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
                      <line x1="12" y1="22.08" x2="12" y2="12"></line>
                    </svg>
                    <span>Benchmark настройки</span>
                    <span className="ml-auto text-xs font-normal text-gray-400 bg-dark-navy-800/60 px-2 py-1 rounded">
                      Red Dead Redemption 2
                    </span>
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm">
                    <div className="flex items-center gap-2">
                      <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                      </svg>
                      <span className="text-gray-400">Резолюция:</span>
                      <span className="text-gray-200 font-medium">1920x1080</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                      </svg>
                      <span className="text-gray-400">Настройки:</span>
                      <span className="text-gray-200 font-medium">Highest</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                      </svg>
                      <span className="text-gray-400">CPU:</span>
                      <span className="text-gray-200 font-medium">Ryzen 9 9950X3D</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Value Table */}
      <Card>
        <CardHeader
          title="Анализ на стойността (FPS/лв)"
          subtitle={`Класиране на ${valueData?.length || 0} модела по ефективност`}
        />

        <CardContent>
          {/* VRAM Filter */}
          <div className="mb-6 flex items-center space-x-3 flex-wrap">
            <span className="text-sm font-medium text-gray-300">VRAM филтър:</span>
            <div className="flex gap-2 flex-wrap">
              <button
                onClick={() => setVramFilter(undefined)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  vramFilter === undefined
                    ? 'bg-primary-500 text-white shadow-lg shadow-primary-500/30'
                    : 'bg-dark-navy-800 text-gray-300 border border-dark-navy-700 hover:border-primary-500/50 hover:text-primary-400'
                }`}
              >
                Всички
              </button>
              <button
                onClick={() => setVramFilter(8)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  vramFilter === 8
                    ? 'bg-primary-500 text-white shadow-lg shadow-primary-500/30'
                    : 'bg-dark-navy-800 text-gray-300 border border-dark-navy-700 hover:border-primary-500/50 hover:text-primary-400'
                }`}
              >
                8GB+
              </button>
              <button
                onClick={() => setVramFilter(12)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  vramFilter === 12
                    ? 'bg-primary-500 text-white shadow-lg shadow-primary-500/30'
                    : 'bg-dark-navy-800 text-gray-300 border border-dark-navy-700 hover:border-primary-500/50 hover:text-primary-400'
                }`}
              >
                12GB+
              </button>
              <button
                onClick={() => setVramFilter(16)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  vramFilter === 16
                    ? 'bg-primary-500 text-white shadow-lg shadow-primary-500/30'
                    : 'bg-dark-navy-800 text-gray-300 border border-dark-navy-700 hover:border-primary-500/50 hover:text-primary-400'
                }`}
              >
                16GB+
              </button>
              <button
                onClick={() => setVramFilter(20)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  vramFilter === 20
                    ? 'bg-primary-500 text-white shadow-lg shadow-primary-500/30'
                    : 'bg-dark-navy-800 text-gray-300 border border-dark-navy-700 hover:border-primary-500/50 hover:text-primary-400'
                }`}
              >
                20GB+
              </button>
            </div>
          </div>

          {/* Legend */}
          <div className="mb-6 flex flex-wrap gap-6 text-sm">
            <div className="flex items-center space-x-2">
              <ValueBadge value={0.5} size="sm" />
              <span className="text-gray-300">Отлична стойност (≥ 0.5)</span>
            </div>
            <div className="flex items-center space-x-2">
              <ValueBadge value={0.3} size="sm" />
              <span className="text-gray-300">Добра стойност (≥ 0.3)</span>
            </div>
            <div className="flex items-center space-x-2">
              <ValueBadge value={0.2} size="sm" />
              <span className="text-gray-300">Средна стойност (≥ 0.2)</span>
            </div>
          </div>

          {/* Table */}
          {isLoading ? (
            <TableSkeleton rows={20} />
          ) : (
            <>
              <Table
                data={displayData || []}
                columns={columns}
                keyExtractor={(item) => item.model}
                emptyMessage="Няма данни за анализ"
                defaultSortKey="relative_score"
                defaultSortDirection="desc"
              />

              {/* Show More Button */}
              {valueData && valueData.length > 20 && !showAll && (
                <div className="mt-6 text-center">
                  <button
                    onClick={() => setShowAll(true)}
                    className="text-primary-600 hover:text-primary-700 font-medium"
                  >
                    Покажи всички ({valueData.length} модела) →
                  </button>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
