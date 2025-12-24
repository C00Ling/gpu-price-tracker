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
  const { data: valueData, isLoading, error, refetch } = useValueAnalysis();
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
      key: 'rank',
      label: '#',
      render: (item: any) => (
        <span className="font-bold text-gray-400">{item.rank}</span>
      ),
    },
    {
      key: 'model',
      label: 'Модел',
      sortable: true,
      render: (item: any) => (
        <span className="font-semibold text-white">{item.model}</span>
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

  // Add index to data for ranking
  const dataWithIndex = displayData?.map((item, index) => ({
    ...item,
    rank: index + 1,
  }));

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
              <p className="text-sm text-gray-300">
                Изчисляваме FPS/лв (кадри в секунда на лев) за всеки модел, използвайки benchmark данни за 1080p игри
                и медианната цена от обявите. По-високата стойност означава по-добра стойност за парите.
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
                data={dataWithIndex || []}
                columns={columns}
                keyExtractor={(item) => item.model}
                emptyMessage="Няма данни за анализ"
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
