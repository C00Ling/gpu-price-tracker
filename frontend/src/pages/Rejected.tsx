// Rejected Listings page - Shows all filtered/rejected listings with reasons
import { useState, useEffect } from 'react';
import {
  Card,
  CardHeader,
  CardContent,
  Table,
  LoadingPage,
  ErrorMessage,
} from '../components';
import { api } from '../services/api';

interface RejectedListing {
  title: string;
  price: number;
  url: string;
  model: string;
  reason: string;
  category: string;
}

export function Rejected() {
  const [listings, setListings] = useState<RejectedListing[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string | undefined>(undefined);
  const [summary, setSummary] = useState<Record<string, number>>({});

  useEffect(() => {
    document.title = 'GPU Market - Отхвърлени';
    fetchData();
  }, []);

  const fetchData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Fetch rejected listings
      const response = await fetch(`${api.getBaseUrl()}/api/rejected/`);
      if (!response.ok) {
        throw new Error('Failed to fetch rejected listings');
      }
      const data = await response.json();
      setListings(data);

      // Fetch summary
      const summaryResponse = await fetch(`${api.getBaseUrl()}/api/rejected/summary`);
      if (summaryResponse.ok) {
        const summaryData = await summaryResponse.json();
        setSummary(summaryData);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load rejected listings');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return <LoadingPage />;
  }

  if (error) {
    return <ErrorMessage message={error} retry={fetchData} />;
  }

  const filteredListings = selectedCategory
    ? listings.filter((item) => item.category === selectedCategory)
    : listings;

  const columns = [
    {
      key: 'title',
      label: 'Заглавие',
      sortable: true,
      render: (item: RejectedListing) => (
        <a
          href={item.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-primary-500 hover:text-primary-400 transition-colors underline decoration-primary-500/30 hover:decoration-primary-400"
        >
          {item.title}
        </a>
      ),
    },
    {
      key: 'model',
      label: 'Модел',
      sortable: true,
      render: (item: RejectedListing) => (
        <span className="text-gray-300">{item.model || '-'}</span>
      ),
    },
    {
      key: 'price',
      label: 'Цена',
      sortable: true,
      render: (item: RejectedListing) => (
        <span className="text-gray-300">{item.price?.toFixed(0)} лв</span>
      ),
    },
    {
      key: 'category',
      label: 'Категория',
      sortable: true,
      render: (item: RejectedListing) => (
        <span className="text-sm px-2 py-1 rounded bg-red-500/20 text-red-300 border border-red-500/30">
          {item.category}
        </span>
      ),
    },
  ];

  const categories = Object.keys(summary).sort();

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Info Card */}
      <Card className="mb-6 bg-dark-navy-800/50 border-dark-navy-700">
        <CardContent className="py-4">
          <div className="flex items-start space-x-3">
            <div className="w-10 h-10 rounded-full bg-red-500/20 flex items-center justify-center flex-shrink-0">
              <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
              </svg>
            </div>
            <div>
              <h3 className="font-semibold text-white mb-1">
                Отхвърлени обяви
              </h3>
              <p className="text-sm text-gray-300 mb-2">
                Тази страница показва всички обяви които са били филтрирани по време на последния scrape.
                Обявите са отхвърлени поради различни причини като съдържание на blacklist keywords,
                статистически outliers, лаптопи, пълни системи и др.
              </p>
              <p className="text-sm text-gray-400">
                <strong className="text-gray-300">Общо отхвърлени:</strong> {listings.length} обяви
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Rejected Listings Table */}
      <Card>
        <CardHeader
          title="Отхвърлени обяви"
          subtitle={`${filteredListings.length} ${selectedCategory ? `от категория "${selectedCategory}"` : 'общо'}`}
        />

        <CardContent>
          {/* Category Filter */}
          <div className="mb-6 flex items-center space-x-3 flex-wrap">
            <span className="text-sm font-medium text-gray-300">Филтър по категория:</span>
            <div className="flex gap-2 flex-wrap">
              <button
                onClick={() => setSelectedCategory(undefined)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  selectedCategory === undefined
                    ? 'bg-primary-500 text-white shadow-lg shadow-primary-500/30'
                    : 'bg-dark-navy-800 text-gray-300 border border-dark-navy-700 hover:border-primary-500/50 hover:text-primary-400'
                }`}
              >
                Всички ({listings.length})
              </button>
              {categories.map((category) => (
                <button
                  key={category}
                  onClick={() => setSelectedCategory(category)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    selectedCategory === category
                      ? 'bg-primary-500 text-white shadow-lg shadow-primary-500/30'
                      : 'bg-dark-navy-800 text-gray-300 border border-dark-navy-700 hover:border-primary-500/50 hover:text-primary-400'
                  }`}
                >
                  {category} ({summary[category]})
                </button>
              ))}
            </div>
          </div>

          {/* Table */}
          <Table
            data={filteredListings}
            columns={columns}
            keyExtractor={(item) => item.url}
            emptyMessage="Няма отхвърлени обяви"
            defaultSortKey="category"
            defaultSortDirection="asc"
          />
        </CardContent>
      </Card>
    </div>
  );
}
