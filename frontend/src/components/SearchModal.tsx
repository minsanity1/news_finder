import { useState } from 'react';
import { X, Search, Loader2, ExternalLink, Filter } from 'lucide-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { searchApi } from '../api/client';

interface SearchModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const AVAILABLE_SOURCES = [
  { id: '연합뉴스', name: '연합뉴스' },
  { id: '한국경제', name: '한국경제' },
  { id: '매일경제', name: '매일경제' },
  { id: '전자신문', name: '전자신문' },
  { id: '조선일보', name: '조선일보' },
  { id: '중앙일보', name: '중앙일보' },
  { id: '동아일보', name: '동아일보' },
  { id: '한겨레', name: '한겨레' },
  { id: '경향신문', name: '경향신문' },
  { id: 'SBS', name: 'SBS' },
  { id: 'KBS', name: 'KBS' },
  { id: 'MBC', name: 'MBC' },
  { id: 'YTN', name: 'YTN' },
];

export default function SearchModal({ isOpen, onClose }: SearchModalProps) {
  const [query, setQuery] = useState('');
  const [maxResults, setMaxResults] = useState(100);
  const [selectedSources, setSelectedSources] = useState<string[]>([]);
  const [showSourceFilter, setShowSourceFilter] = useState(false);
  const queryClient = useQueryClient();

  const { data: status } = useQuery({
    queryKey: ['search-status'],
    queryFn: searchApi.getStatus,
    enabled: isOpen,
  });

  const searchMutation = useMutation({
    mutationFn: () => searchApi.searchNaver(query, maxResults, true, selectedSources),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['news'] });
    },
  });

  if (!isOpen) return null;

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      searchMutation.mutate();
    }
  };

  const toggleSource = (sourceId: string) => {
    setSelectedSources(prev =>
      prev.includes(sourceId)
        ? prev.filter(s => s !== sourceId)
        : [...prev, sourceId]
    );
  };

  const selectAllSources = () => {
    setSelectedSources(AVAILABLE_SOURCES.map(s => s.id));
  };

  const clearAllSources = () => {
    setSelectedSources([]);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[80vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-lg font-semibold">네이버 뉴스 검색</h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {status && !status.naver_api_configured ? (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-4">
              <p className="text-amber-800 text-sm">
                <strong>네이버 API가 설정되지 않았습니다.</strong>
                <br />
                backend/.env 파일에 NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET을 설정하세요.
              </p>
              <a
                href="https://developers.naver.com/apps"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 mt-2 text-sm text-amber-700 hover:text-amber-900 underline"
              >
                네이버 개발자 센터에서 API 등록하기
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          ) : (
            <>
              <form onSubmit={handleSearch} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    검색어
                  </label>
                  <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="예: 스타벅스 폐점, 치킨 프랜차이즈 위기"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    disabled={searchMutation.isPending}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    최대 결과 수
                  </label>
                  <select
                    value={maxResults}
                    onChange={(e) => setMaxResults(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    disabled={searchMutation.isPending}
                  >
                    <option value={50}>50개</option>
                    <option value={100}>100개</option>
                    <option value={200}>200개</option>
                    <option value={500}>500개</option>
                    <option value={1000}>1000개 (최대)</option>
                  </select>
                </div>

                {/* Source Filter */}
                <div>
                  <button
                    type="button"
                    onClick={() => setShowSourceFilter(!showSourceFilter)}
                    className="flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-gray-900"
                  >
                    <Filter className="w-4 h-4" />
                    언론사 필터 {selectedSources.length > 0 && `(${selectedSources.length}개 선택)`}
                  </button>

                  {showSourceFilter && (
                    <div className="mt-2 p-3 border rounded-lg bg-gray-50">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs text-gray-500">
                          선택한 언론사 기사만 저장됩니다. 미선택시 전체 저장.
                        </span>
                        <div className="flex gap-2">
                          <button
                            type="button"
                            onClick={selectAllSources}
                            className="text-xs text-blue-600 hover:underline"
                          >
                            전체선택
                          </button>
                          <button
                            type="button"
                            onClick={clearAllSources}
                            className="text-xs text-gray-500 hover:underline"
                          >
                            초기화
                          </button>
                        </div>
                      </div>
                      <div className="grid grid-cols-3 gap-2">
                        {AVAILABLE_SOURCES.map((source) => (
                          <label
                            key={source.id}
                            className={`flex items-center gap-2 p-2 rounded cursor-pointer text-sm ${
                              selectedSources.includes(source.id)
                                ? 'bg-green-100 text-green-800'
                                : 'bg-white hover:bg-gray-100'
                            }`}
                          >
                            <input
                              type="checkbox"
                              checked={selectedSources.includes(source.id)}
                              onChange={() => toggleSource(source.id)}
                              className="rounded"
                            />
                            {source.name}
                          </label>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                <button
                  type="submit"
                  disabled={!query.trim() || searchMutation.isPending}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {searchMutation.isPending ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      검색 중...
                    </>
                  ) : (
                    <>
                      <Search className="w-4 h-4" />
                      검색 및 저장
                    </>
                  )}
                </button>
              </form>

              {/* Results */}
              {searchMutation.isSuccess && (
                <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
                  <p className="text-green-800">
                    <strong>검색 완료!</strong>
                    <br />
                    검색 결과: {searchMutation.data.total_found}개
                    {searchMutation.data.filtered_count !== searchMutation.data.total_found && (
                      <> → 필터 적용: {searchMutation.data.filtered_count}개</>
                    )}
                    <br />
                    새로 저장: {searchMutation.data.saved_count}개
                  </p>
                </div>
              )}

              {searchMutation.isError && (
                <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-red-800">
                    검색 중 오류가 발생했습니다.
                  </p>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t bg-gray-50">
          <p className="text-xs text-gray-500">
            네이버 뉴스 검색 API를 사용하여 과거 뉴스를 검색하고 DB에 저장합니다.
            RSS보다 더 많은 과거 기사를 가져올 수 있습니다.
          </p>
        </div>
      </div>
    </div>
  );
}
