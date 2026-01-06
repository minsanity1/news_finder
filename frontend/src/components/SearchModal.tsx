import { useState, useMemo } from 'react';
import { X, TrendingUp, Loader2, MessageSquare, Eye } from 'lucide-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { rankingApi, PressInfo } from '../api/client';

interface SearchModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const RANKING_TYPE_LABELS: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
  popular: { label: '조회수 랭킹', icon: <Eye className="w-4 h-4" />, color: 'text-orange-600' },
  comment: { label: '댓글수 랭킹', icon: <MessageSquare className="w-4 h-4" />, color: 'text-blue-600' },
  all: { label: '전체 (조회수 + 댓글수)', icon: <TrendingUp className="w-4 h-4" />, color: 'text-purple-600' },
};

export default function SearchModal({ isOpen, onClose }: SearchModalProps) {
  const [rankingType, setRankingType] = useState<'popular' | 'comment' | 'all'>('popular');
  const [selectedPress, setSelectedPress] = useState<string[]>([]);
  const [limitPerPress, setLimitPerPress] = useState(10);
  const [targetDate, setTargetDate] = useState('');
  const queryClient = useQueryClient();

  const { data: pressList, isLoading: pressLoading } = useQuery({
    queryKey: ['press-list'],
    queryFn: rankingApi.getPressList,
    enabled: isOpen,
  });

  const { data: status } = useQuery({
    queryKey: ['ranking-status'],
    queryFn: rankingApi.getStatus,
    enabled: isOpen,
  });

  const collectMutation = useMutation({
    mutationFn: () => rankingApi.collect({
      press_ids: selectedPress.length > 0 ? selectedPress : undefined,
      ranking_type: rankingType,
      target_date: targetDate || undefined,
      limit_per_press: limitPerPress,
      save_to_db: true,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['news'] });
    },
  });

  // 카테고리별 그룹핑
  const groupedPress = useMemo(() => {
    if (!pressList) return {};
    return pressList.reduce((acc, press) => {
      if (!acc[press.category]) acc[press.category] = [];
      acc[press.category].push(press);
      return acc;
    }, {} as Record<string, PressInfo[]>);
  }, [pressList]);

  if (!isOpen) return null;

  const handleCollect = (e: React.FormEvent) => {
    e.preventDefault();
    collectMutation.mutate();
  };

  const togglePress = (pressId: string) => {
    setSelectedPress(prev =>
      prev.includes(pressId)
        ? prev.filter(id => id !== pressId)
        : [...prev, pressId]
    );
  };

  const selectAllPress = () => {
    if (pressList) {
      setSelectedPress(pressList.map(p => p.id));
    }
  };

  const clearAllPress = () => {
    setSelectedPress([]);
  };

  const selectByCategory = (category: string) => {
    const categoryPress = groupedPress[category] || [];
    const categoryIds = categoryPress.map(p => p.id);
    const allSelected = categoryIds.every(id => selectedPress.includes(id));

    if (allSelected) {
      setSelectedPress(prev => prev.filter(id => !categoryIds.includes(id)));
    } else {
      setSelectedPress(prev => [...new Set([...prev, ...categoryIds])]);
    }
  };

  // 예상 수집 개수 계산
  const estimatedCount = useMemo(() => {
    const pressCount = selectedPress.length > 0 ? selectedPress.length : (pressList?.length || 0);
    const typeMultiplier = rankingType === 'all' ? 2 : 1;
    return pressCount * limitPerPress * typeMultiplier;
  }, [selectedPress, pressList, limitPerPress, rankingType]);

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[85vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b bg-gradient-to-r from-green-600 to-green-700">
          <div className="flex items-center gap-2 text-white">
            <TrendingUp className="w-5 h-5" />
            <h2 className="text-lg font-semibold">네이버 뉴스 랭킹 수집</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-white/20 rounded text-white"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(85vh-180px)]">
          <form onSubmit={handleCollect} className="space-y-5">
            {/* 랭킹 타입 선택 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                랭킹 타입
              </label>
              <div className="grid grid-cols-3 gap-2">
                {Object.entries(RANKING_TYPE_LABELS).map(([key, { label, icon, color }]) => (
                  <button
                    key={key}
                    type="button"
                    onClick={() => setRankingType(key as 'popular' | 'comment' | 'all')}
                    className={`flex items-center justify-center gap-2 p-3 rounded-lg border transition-colors ${
                      rankingType === key
                        ? 'bg-green-50 border-green-500 text-green-800'
                        : 'bg-white border-gray-300 hover:bg-gray-50'
                    }`}
                    disabled={collectMutation.isPending}
                  >
                    <span className={rankingType === key ? 'text-green-600' : color}>{icon}</span>
                    <span className="text-sm font-medium">{label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* 수집 개수 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                언론사당 수집 개수
              </label>
              <select
                value={limitPerPress}
                onChange={(e) => setLimitPerPress(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                disabled={collectMutation.isPending}
              >
                <option value={5}>5개</option>
                <option value={10}>10개</option>
                <option value={20}>20개</option>
              </select>
            </div>

            {/* 날짜 선택 (선택사항) */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                날짜 (비우면 오늘)
              </label>
              <input
                type="date"
                value={targetDate}
                onChange={(e) => setTargetDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                disabled={collectMutation.isPending}
              />
            </div>

            {/* 언론사 선택 */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-gray-700">
                  언론사 선택 (비우면 전체 {pressList?.length || 0}개)
                </label>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={selectAllPress}
                    className="text-xs text-green-600 hover:underline"
                    disabled={collectMutation.isPending}
                  >
                    전체선택
                  </button>
                  <button
                    type="button"
                    onClick={clearAllPress}
                    className="text-xs text-gray-500 hover:underline"
                    disabled={collectMutation.isPending}
                  >
                    초기화
                  </button>
                </div>
              </div>

              {pressLoading ? (
                <div className="flex items-center justify-center p-4">
                  <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
                </div>
              ) : (
                <div className="max-h-48 overflow-y-auto border rounded-lg p-3 bg-gray-50">
                  {Object.entries(groupedPress).map(([category, presses]) => (
                    <div key={category} className="mb-3 last:mb-0">
                      <button
                        type="button"
                        onClick={() => selectByCategory(category)}
                        className="text-xs font-semibold text-gray-600 mb-1.5 hover:text-gray-900 uppercase tracking-wide"
                      >
                        {category} ({presses.length})
                      </button>
                      <div className="flex flex-wrap gap-1.5">
                        {presses.map((press) => (
                          <button
                            key={press.id}
                            type="button"
                            onClick={() => togglePress(press.id)}
                            className={`px-2.5 py-1 text-xs rounded-full transition-colors ${
                              selectedPress.includes(press.id)
                                ? 'bg-green-600 text-white'
                                : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-100'
                            }`}
                            disabled={collectMutation.isPending}
                          >
                            {press.name}
                          </button>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {selectedPress.length > 0 && (
                <p className="mt-1.5 text-xs text-gray-500">
                  {selectedPress.length}개 언론사 선택됨
                </p>
              )}
            </div>

            {/* 예상 수집 개수 */}
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-sm text-gray-600">
                예상 수집: <strong className="text-gray-900">최대 {estimatedCount.toLocaleString()}개</strong>
                <span className="text-gray-400 ml-2">
                  ({selectedPress.length || pressList?.length || 0}개 언론사 × {limitPerPress}개
                  {rankingType === 'all' && ' × 2종류'})
                </span>
              </p>
            </div>

            {/* 수집 버튼 */}
            <button
              type="submit"
              disabled={collectMutation.isPending}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
            >
              {collectMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  수집 중...
                </>
              ) : (
                <>
                  <TrendingUp className="w-4 h-4" />
                  랭킹 뉴스 수집
                </>
              )}
            </button>
          </form>

          {/* Results */}
          {collectMutation.isSuccess && (
            <div className="mt-5 p-4 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-green-800 font-medium mb-2">수집 완료!</p>
              <div className="text-sm text-green-700 space-y-1">
                <p>수집된 뉴스: {collectMutation.data.collected}개</p>
                <p>새로 저장: {collectMutation.data.saved}개</p>
                <p>중복 제외: {collectMutation.data.duplicates}개</p>
                {Object.keys(collectMutation.data.by_press).length > 0 && (
                  <details className="mt-2">
                    <summary className="cursor-pointer text-green-600 hover:underline">
                      언론사별 상세
                    </summary>
                    <div className="mt-2 pl-3 text-xs space-y-0.5">
                      {Object.entries(collectMutation.data.by_press).map(([press, count]) => (
                        <p key={press}>{press}: {count}개</p>
                      ))}
                    </div>
                  </details>
                )}
              </div>
            </div>
          )}

          {collectMutation.isError && (
            <div className="mt-5 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-800">
                수집 중 오류가 발생했습니다.
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t bg-gray-50">
          <p className="text-xs text-gray-500">
            네이버 미디어에서 언론사별 랭킹 뉴스를 수집합니다.
            조회수/댓글수로 이미 검증된 관심 뉴스를 발굴할 수 있습니다.
          </p>
        </div>
      </div>
    </div>
  );
}
