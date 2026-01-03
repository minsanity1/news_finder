import { useState } from 'react';
import { X, Users, Loader2, RefreshCw } from 'lucide-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { communityApi } from '../api/client';

interface CommunityModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function CommunityModal({ isOpen, onClose }: CommunityModalProps) {
  const queryClient = useQueryClient();
  const [collectingBoard, setCollectingBoard] = useState<string | null>(null);

  const { data: sources, isLoading: sourcesLoading } = useQuery({
    queryKey: ['community-sources'],
    queryFn: communityApi.getSources,
    enabled: isOpen,
  });

  const collectMutation = useMutation({
    mutationFn: ({ source, board }: { source: string; board: string }) =>
      communityApi.collect(source, board, 20),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['news'] });
    },
    onSettled: () => {
      setCollectingBoard(null);
    },
  });

  const collectAllMutation = useMutation({
    mutationFn: communityApi.collectAll,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['news'] });
    },
  });

  if (!isOpen) return null;

  const handleCollect = (source: string, board: string) => {
    setCollectingBoard(`${source}-${board}`);
    collectMutation.mutate({ source, board });
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg max-h-[80vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Users className="w-5 h-5" />
            커뮤니티 수집
          </h2>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(80vh-140px)]">
          {sourcesLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
            </div>
          ) : (
            <div className="space-y-4">
              {/* 전체 수집 버튼 */}
              <button
                onClick={() => collectAllMutation.mutate()}
                disabled={collectAllMutation.isPending}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {collectAllMutation.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    전체 수집 중...
                  </>
                ) : (
                  <>
                    <RefreshCw className="w-4 h-4" />
                    전체 커뮤니티 수집
                  </>
                )}
              </button>

              {collectAllMutation.isSuccess && (
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-800">
                  수집 완료! {collectAllMutation.data.total_collected}개 발견, {collectAllMutation.data.total_saved}개 저장
                </div>
              )}

              {/* 개별 커뮤니티 */}
              {sources && Object.entries(sources).map(([sourceId, source]) => (
                <div key={sourceId} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-medium">{source.name}</h3>
                    <span className={`text-xs px-2 py-0.5 rounded ${
                      source.enabled ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                    }`}>
                      {source.enabled ? '활성' : '비활성'}
                    </span>
                  </div>

                  {source.enabled ? (
                    <div className="flex flex-wrap gap-2">
                      {source.boards.map((board) => {
                        const boardKey = `${sourceId}-${board.id}`;
                        const isCollecting = collectingBoard === boardKey || collectMutation.isPending && collectingBoard === boardKey;

                        return (
                          <button
                            key={board.id}
                            onClick={() => handleCollect(sourceId, board.id)}
                            disabled={isCollecting || collectAllMutation.isPending}
                            className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-1"
                          >
                            {isCollecting && <Loader2 className="w-3 h-3 animate-spin" />}
                            {board.id}
                          </button>
                        );
                      })}
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500">Phase 2-B에서 지원 예정</p>
                  )}
                </div>
              ))}

              {/* 수집 결과 */}
              {collectMutation.isSuccess && (
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
                  <strong>{collectMutation.data.source} - {collectMutation.data.board}</strong>
                  <br />
                  수집: {collectMutation.data.collected}개 / 저장: {collectMutation.data.saved}개 / 중복: {collectMutation.data.duplicates}개
                </div>
              )}

              {collectMutation.isError && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-800">
                  수집 중 오류가 발생했습니다.
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t bg-gray-50">
          <p className="text-xs text-gray-500">
            에펨코리아, 뽐뿌 등 커뮤니티의 핫글을 수집합니다.
            수집된 글은 뉴스와 동일하게 AI 분석이 가능합니다.
          </p>
        </div>
      </div>
    </div>
  );
}
