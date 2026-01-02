// Value Analysis page - FPS per лв ranking
import { useState } from 'react';
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

export function ValueAnalysis() {
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
      render: (item: any) => (
        item.cheapest_url ? (
          <a
            href={item.cheapest_url}
            target="_blank"
            rel="noopener noreferrer"
            className="font-semibold text-primary-500 hover:text-primary-400 transition-colors underline decoration-primary-500/30 hover:decoration-primary-400"
          >
            {item.model}
          </a>
        ) : (
          <span className="font-semibold text-white">{item.model}</span>
        )
      ),
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
          <div className="mb-6 flex items-center space-x-3">
            <span className="text-sm font-medium text-gray-300">VRAM филтър:</span>
            <div className="flex gap-2">
              <button
                onClick={() => setVramFilter(undefined)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  vramFilter === undefined
                    ? 'bg-primary-500 text-white'
                    : 'bg-dark-navy-800 text-gray-300 border border-dark-navy-700 hover:border-primary-500/50'
                }`}
              >
                Всички
              </button>
              <button
                onClick={() => setVramFilter(8)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  vramFilter === 8
                    ? 'bg-primary-500 text-white'
                    : 'bg-dark-navy-800 text-gray-300 border border-dark-navy-700 hover:border-primary-500/50'
                }`}
              >
                ≥8GB VRAM
              </button>
              <button
                onClick={() => setVramFilter(9)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  vramFilter === 9
                    ? 'bg-primary-500 text-white'
                    : 'bg-dark-navy-800 text-gray-300 border border-dark-navy-700 hover:border-primary-500/50'
                }`}
              >
                &gt;8GB VRAM
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
