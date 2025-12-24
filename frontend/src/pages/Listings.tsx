// Listings page - All GPU listings with filters
import { useState } from 'react';
import { useListings, useAvailableModels } from '../hooks/useGPUData';
import {
  Card,
  CardHeader,
  CardContent,
  Table,
  Button,
  LoadingPage,
  ErrorMessage,
  TableSkeleton,
} from '../components';

export function Listings() {
  const [selectedModel, setSelectedModel] = useState<string>('');
  const page = 1;
  const pageSize = 50;

  const { data: listings, isLoading, error, refetch } = useListings({
    page,
    size: pageSize,
  });

  const { data: modelsData } = useAvailableModels();

  if (isLoading) {
    return <LoadingPage />;
  }

  if (error) {
    return <ErrorMessage message="Грешка при зареждане на обявите" retry={refetch} />;
  }

  const filteredListings = selectedModel
    ? listings?.filter((gpu) => gpu.model === selectedModel)
    : listings;

  const columns = [
    {
      key: 'model',
      label: 'Модел',
      sortable: true,
      render: (item: any) => (
        <span className="font-semibold text-white">{item.model}</span>
      ),
    },
    {
      key: 'price',
      label: 'Цена',
      sortable: true,
      render: (item: any) => (
        <span className="text-primary-400 font-bold">{item.price.toFixed(2)} лв</span>
      ),
    },
    {
      key: 'source',
      label: 'Източник',
      sortable: true,
      render: (item: any) => (
        <span className="text-sm text-gray-300">{item.source}</span>
      ),
    },
    {
      key: 'created_at',
      label: 'Дата',
      sortable: true,
      render: (item: any) => (
        <span className="text-sm text-gray-400">
          {item.created_at
            ? new Date(item.created_at).toLocaleDateString('bg-BG')
            : '-'}
        </span>
      ),
    },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <Card>
        <CardHeader
          title="Обяви за видео карти"
          subtitle={`Общо ${filteredListings?.length || 0} обяви`}
          action={
            <Button onClick={() => refetch()} variant="outline" size="sm">
              🔄 Обнови
            </Button>
          }
        />

        <CardContent>
          {/* Filters */}
          <div className="mb-6 flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Филтър по модел
              </label>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="w-full rounded-lg bg-zinc-800 border-zinc-700 text-white shadow-sm focus:border-primary-500 focus:ring-primary-500"
              >
                <option value="">Всички модели ({modelsData?.count || 0})</option>
                {modelsData?.models?.map((model) => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
              </select>
            </div>

            {selectedModel && (
              <div className="flex items-end">
                <Button
                  onClick={() => setSelectedModel('')}
                  variant="ghost"
                  size="sm"
                >
                  ✕ Изчисти
                </Button>
              </div>
            )}
          </div>

          {/* Table */}
          {isLoading ? (
            <TableSkeleton rows={10} />
          ) : (
            <Table
              data={filteredListings || []}
              columns={columns}
              keyExtractor={(item) => item.id}
              emptyMessage="Няма намерени обяви"
            />
          )}

          {/* Pagination info */}
          {filteredListings && filteredListings.length > 0 && (
            <div className="mt-6 text-center text-sm text-gray-400">
              Показани {filteredListings.length} обяви
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
