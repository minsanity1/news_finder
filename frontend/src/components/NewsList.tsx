import { ChevronLeft, ChevronRight, Loader2, Sparkles } from 'lucide-react';
import { useNewsList } from '../hooks/useNews';
import { useBatchAIAnalyze } from '../hooks/useAIAnalysis';
import { useFilterStore, useSelectedNewsStore, useAIFilterModalStore } from '../stores/filterStore';
import NewsCard from './NewsCard';

export default function NewsList() {
  const { filter, setPage } = useFilterStore();
  const { selectedIds, toggleSelect, selectAll, clearSelection } = useSelectedNewsStore();
  const { selectedPresetKey } = useAIFilterModalStore();
  const { data, isLoading, error } = useNewsList(filter);
  const { mutate: batchAnalyze, isPending: isAnalyzing } = useBatchAIAnalyze();

  const handleBatchAnalyze = () => {
    if (selectedIds.length === 0) return;
    batchAnalyze({
      newsIds: selectedIds,
      presetKey: selectedPresetKey,
    });
    clearSelection();
  };

  const handleSelectAll = () => {
    if (!data) return;

    const allIds = data.items.map((item) => item.id);
    const allSelected = allIds.every((id) => selectedIds.includes(id));

    if (allSelected) {
      clearSelection();
    } else {
      selectAll(allIds);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 text-red-600 p-4 rounded-lg">
        Failed to load news. Please try again.
      </div>
    );
  }

  if (!data || data.items.length === 0) {
    return (
      <div className="bg-gray-50 text-gray-500 p-8 rounded-lg text-center">
        No news found. Try collecting or adjusting filters.
      </div>
    );
  }

  const { items, total, page, total_pages } = data;
  const analyzedCount = items.filter((item) => item.ai_analyzed).length;
  const unanalyzedCount = items.length - analyzedCount;

  return (
    <div>
      {/* Stats Bar */}
      <div className="flex items-center justify-between mb-4 text-sm text-gray-600">
        <div className="flex items-center gap-4">
          <span>Total: {total}</span>
          <span>|</span>
          <span>AI Analyzed: {analyzedCount}</span>
          <span>|</span>
          <span>Unanalyzed: {unanalyzedCount}</span>
        </div>

        <div className="flex items-center gap-2">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={items.length > 0 && items.every((item) => selectedIds.includes(item.id))}
              onChange={handleSelectAll}
              className="rounded"
            />
            <span>Select All</span>
          </label>

          {selectedIds.length > 0 && (
            <button
              onClick={handleBatchAnalyze}
              disabled={isAnalyzing}
              className="flex items-center gap-1 px-3 py-1.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors"
            >
              {isAnalyzing ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Sparkles className="w-4 h-4" />
              )}
              Analyze {selectedIds.length}
            </button>
          )}
        </div>
      </div>

      {/* News Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {items.map((news) => (
          <NewsCard
            key={news.id}
            news={news}
            isSelected={selectedIds.includes(news.id)}
            onSelect={() => toggleSelect(news.id)}
          />
        ))}
      </div>

      {/* Pagination */}
      {total_pages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-6">
          <button
            onClick={() => setPage(page - 1)}
            disabled={page <= 1}
            className="p-2 rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>

          <div className="flex items-center gap-1">
            {Array.from({ length: Math.min(5, total_pages) }, (_, i) => {
              let pageNum: number;
              if (total_pages <= 5) {
                pageNum = i + 1;
              } else if (page <= 3) {
                pageNum = i + 1;
              } else if (page >= total_pages - 2) {
                pageNum = total_pages - 4 + i;
              } else {
                pageNum = page - 2 + i;
              }

              return (
                <button
                  key={pageNum}
                  onClick={() => setPage(pageNum)}
                  className={`w-8 h-8 rounded-lg transition-colors ${
                    pageNum === page
                      ? 'bg-blue-600 text-white'
                      : 'hover:bg-gray-100 text-gray-700'
                  }`}
                >
                  {pageNum}
                </button>
              );
            })}
          </div>

          <button
            onClick={() => setPage(page + 1)}
            disabled={page >= total_pages}
            className="p-2 rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      )}
    </div>
  );
}
