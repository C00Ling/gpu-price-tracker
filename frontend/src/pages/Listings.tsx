// Listings page - All GPU listings with filters
import { useState, useEffect } from 'react';
import { useListings, useListingsByModel, useAvailableModels } from '../hooks/useGPUData';
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

// Helper function to remove VRAM suffix from model name for display
// e.g. "GTX 1060 6GB" → "GTX 1060", "RX 580 8GB" → "RX 580"
function stripVRAMFromModel(model: string): string {
  return model.replace(/\s+\d+GB$/i, '');
}

export function Listings() {
  useEffect(() => {
    document.title = 'GPU Market - Обяви';
  }, []);

  const [selectedModel, setSelectedModel] = useState<string>('');
  const page = 1;
  const pageSize = 50;

  // Use different queries based on whether a model is selected
  const allListingsQuery = useListings({
    page,
    size: pageSize,
  });
  const modelListingsQuery = useListingsByModel(selectedModel);

  // Choose the appropriate query based on selection
  const { data: listings, isLoading, error, refetch } = selectedModel
    ? modelListingsQuery
    : allListingsQuery;

  const { data: modelsData } = useAvailableModels();

  if (isLoading) {
    return <LoadingPage />;
  }

  if (error) {
    return <ErrorMessage message="Грешка при зареждане на обявите" retry={refetch} />;
  }

  // No need for client-side filtering - backend handles it with normalization
  const filteredListings = listings;

  const columns = [
    {
      key: 'model',
      label: 'Модел',
      sortable: true,
      render: (item: any) => (
        <span className="font-semibold text-white">{stripVRAMFromModel(item.model)}</span>
      ),
    },
    {
      key: 'price',
      label: 'Цена',
      sortable: true,
      render: (item: any) => (
        <span className="text-primary-500 font-bold">{item.price.toFixed(2)} лв</span>
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
      key: 'url',
      label: 'Линк',
      sortable: false,
      render: (item: any) => (
        item.url ? (
          <a
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-primary-500 hover:text-primary-400 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
            <span className="text-sm">OLX</span>
          </a>
        ) : (
          <span className="text-xs text-gray-500">-</span>
        )
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
                className="w-full rounded-lg bg-dark-navy-800 border-dark-navy-700 text-white shadow-sm focus:border-primary-500 focus:ring-primary-500"
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
              keyExtractor={(item, index) => `${item.id}-${index}`}
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
