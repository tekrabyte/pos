import { useState, useMemo } from 'react';
import Layout from '@/components/Layout';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Search, RefreshCw } from 'lucide-react';
import { useFetch, useDebounce } from '@/hooks/useApi';

const Categories = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const debouncedSearch = useDebounce(searchTerm, 300);

  const { data: categories = [], loading, refetch } = useFetch('/categories', {
    initialData: [],
    cacheKey: 'categories-list',
  });

  const filteredCategories = useMemo(() => {
    // Ensure categories is always an array
    const categoriesList = Array.isArray(categories) ? categories : [];
    if (!debouncedSearch) return categoriesList;
    const search = debouncedSearch.toLowerCase();
    return categoriesList.filter((c) =>
      c.name?.toLowerCase().includes(search)
    );
  }, [debouncedSearch, categories]);

  if (loading) {
    return (
      <Layout>
        <div className="flex flex-col items-center justify-center h-64 space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <div className="text-gray-500">Memuat data kategori...</div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-800">Kategori Produk</h1>
          <div className="flex items-center gap-3">
            <div className="text-sm text-gray-500">
              Total: {filteredCategories.length} kategori
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              disabled={loading}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </div>

        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Cari kategori..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
          {searchTerm && (
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-xs text-gray-400">
              {filteredCategories.length} hasil
            </div>
          )}
        </div>

        {filteredCategories.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <p className="text-gray-500">Tidak ada kategori ditemukan</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredCategories.map((category) => (
              <Card key={category.id} className="hover:shadow-lg transition-shadow">
                <CardContent className="p-6">
                  <h3 className="font-semibold text-lg text-gray-800 mb-2">{category.name}</h3>
                  <p className="text-sm text-gray-600">{category.description || 'Tidak ada deskripsi'}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
};

export default Categories;