import { useState } from 'react';
import { ChevronDown, X, Sparkles, RotateCcw } from 'lucide-react';
import { useFilterStore, useAIFilterModalStore } from '../stores/filterStore';
import { useNewsSources, useNewsCategories } from '../hooks/useNews';

export default function FilterPanel() {
  const { filter, setFilter, resetFilter } = useFilterStore();
  const { openModal } = useAIFilterModalStore();
  const { data: sources = [] } = useNewsSources();
  const { data: categories = [] } = useNewsCategories();

  const [keyword, setKeyword] = useState(filter.keyword || '');
  const [isExpanded, setIsExpanded] = useState(true);

  const handleApplyFilter = () => {
    setFilter({ keyword });
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleApplyFilter();
    }
  };

  const handleReset = () => {
    setKeyword('');
    resetFilter();
  };

  const aiCategories = [
    { value: '', label: 'All' },
    { value: 'failure', label: 'Failure' },
    { value: 'success', label: 'Success' },
    { value: 'comeback', label: 'Comeback' },
  ];

  return (
    <div className="bg-white rounded-lg shadow-sm border p-4 mb-4">
      <div className="flex items-center justify-between mb-4">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-2 text-gray-700 font-medium"
        >
          <ChevronDown className={`w-4 h-4 transition-transform ${isExpanded ? '' : '-rotate-90'}`} />
          Filter
        </button>

        <div className="flex items-center gap-2">
          <button
            onClick={openModal}
            className="flex items-center gap-1 px-3 py-1.5 text-sm bg-purple-50 text-purple-700 rounded-lg hover:bg-purple-100 transition-colors"
          >
            <Sparkles className="w-4 h-4" />
            AI Filter
          </button>

          <button
            onClick={handleReset}
            className="flex items-center gap-1 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
            Reset
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="space-y-4">
          {/* Keyword Search */}
          <div>
            <label className="block text-sm text-gray-600 mb-1">Keyword</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Search in title and summary..."
                className="flex-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              />
              {keyword && (
                <button
                  onClick={() => setKeyword('')}
                  className="px-2 text-gray-400 hover:text-gray-600"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>

          {/* Filters Row */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {/* Source */}
            <div>
              <label className="block text-sm text-gray-600 mb-1">Source</label>
              <select
                value={filter.source || ''}
                onChange={(e) => setFilter({ source: e.target.value || undefined })}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              >
                <option value="">All</option>
                {sources.map((source) => (
                  <option key={source} value={source}>
                    {source}
                  </option>
                ))}
              </select>
            </div>

            {/* Category */}
            <div>
              <label className="block text-sm text-gray-600 mb-1">Category</label>
              <select
                value={filter.category || ''}
                onChange={(e) => setFilter({ category: e.target.value || undefined })}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              >
                <option value="">All</option>
                {categories.map((category) => (
                  <option key={category} value={category}>
                    {category}
                  </option>
                ))}
              </select>
            </div>

            {/* AI Category */}
            <div>
              <label className="block text-sm text-gray-600 mb-1">AI Category</label>
              <select
                value={filter.ai_category || ''}
                onChange={(e) => setFilter({ ai_category: e.target.value || undefined })}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              >
                {aiCategories.map((cat) => (
                  <option key={cat.value} value={cat.value}>
                    {cat.label}
                  </option>
                ))}
              </select>
            </div>

            {/* AI Min Score */}
            <div>
              <label className="block text-sm text-gray-600 mb-1">
                Min AI Score: {filter.ai_min_score ?? 0}
              </label>
              <input
                type="range"
                min="0"
                max="100"
                value={filter.ai_min_score ?? 0}
                onChange={(e) => {
                  const value = parseInt(e.target.value);
                  setFilter({ ai_min_score: value > 0 ? value : undefined });
                }}
                className="w-full"
              />
            </div>
          </div>

          {/* Bookmark Filter */}
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={filter.is_bookmarked === true}
                onChange={(e) => setFilter({ is_bookmarked: e.target.checked ? true : undefined })}
                className="rounded"
              />
              <span className="text-sm text-gray-600">Bookmarked only</span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={filter.is_read === false}
                onChange={(e) => setFilter({ is_read: e.target.checked ? false : undefined })}
                className="rounded"
              />
              <span className="text-sm text-gray-600">Unread only</span>
            </label>
          </div>

          {/* Apply Button */}
          <button
            onClick={handleApplyFilter}
            className="w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Apply Filter
          </button>
        </div>
      )}
    </div>
  );
}
