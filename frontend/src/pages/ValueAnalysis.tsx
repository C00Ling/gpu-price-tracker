// Value Analysis page - FPS per лв ranking
import { useState } from 'react';
import { useValueAnalysis } from '../hooks/useGPUData';
import {
  Card,
  CardHeader,
  CardContent,
  Table,
  LoadingPage,
  ErrorMessage,
  TableSkeleton,
} from '../components';

export function ValueAnalysis() {
  const { data: valueData, isLoading, error, refetch } = useValueAnalysis();
  const [showAll, setShowAll] = useState(false);

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
        <span className="text-primary-400 font-bold">{item.price.toFixed(0)} лв</span>
      ),
    },
    {
      key: 'fps_per_lv',
      label: 'FPS/лв',
      sortable: true,
      render: (item: any) => {
        const value = item.fps_per_lv;
        let colorClass = 'text-gray-300';

        if (value >= 0.5) colorClass = 'text-green-400';
        else if (value >= 0.3) colorClass = 'text-blue-400';
        else if (value >= 0.2) colorClass = 'text-yellow-400';

        return (
          <span className={`font-bold text-lg ${colorClass}`}>
            {value.toFixed(3)}
          </span>
        );
      },
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
      <Card className="mb-6 bg-blue-950/30 border-blue-500/30">
        <CardContent className="py-4">
          <div className="flex items-start space-x-3">
            <span className="text-2xl">💡</span>
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
          <div className="mb-6 flex flex-wrap gap-4 text-sm">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-green-400 rounded-full"></div>
              <span className="text-gray-300">Отлична стойност (≥ 0.5)</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-blue-400 rounded-full"></div>
              <span className="text-gray-300">Добра стойност (≥ 0.3)</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-yellow-400 rounded-full"></div>
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
