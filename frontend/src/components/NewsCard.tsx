import { format } from 'date-fns';
import { ko } from 'date-fns/locale';
import {
  Star,
  ExternalLink,
  TrendingDown,
  TrendingUp,
  RefreshCw,
  Sparkles,
  Loader2,
  Eye,
  ThumbsUp,
  MessageCircle,
} from 'lucide-react';
import type { News } from '../types';
import { useUpdateNews } from '../hooks/useNews';
import { useAIAnalyze } from '../hooks/useAIAnalysis';
import { useAIFilterModalStore } from '../stores/filterStore';

interface NewsCardProps {
  news: News;
  isSelected?: boolean;
  onSelect?: () => void;
}

const categoryConfig: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
  failure: {
    icon: <TrendingDown className="w-4 h-4" />,
    color: 'bg-red-100 text-red-700',
    label: 'Fail',
  },
  success: {
    icon: <TrendingUp className="w-4 h-4" />,
    color: 'bg-green-100 text-green-700',
    label: 'Success',
  },
  comeback: {
    icon: <RefreshCw className="w-4 h-4" />,
    color: 'bg-blue-100 text-blue-700',
    label: 'Comeback',
  },
  other: {
    icon: null,
    color: 'bg-gray-100 text-gray-700',
    label: 'Other',
  },
};

export default function NewsCard({ news, isSelected, onSelect }: NewsCardProps) {
  const { mutate: updateNews } = useUpdateNews();
  const { mutate: analyzeNews, isPending: isAnalyzing } = useAIAnalyze();
  const { selectedPresetKey } = useAIFilterModalStore();

  const handleBookmark = (e: React.MouseEvent) => {
    e.stopPropagation();
    updateNews({ id: news.id, data: { is_bookmarked: !news.is_bookmarked } });
  };

  const handleAnalyze = (e: React.MouseEvent) => {
    e.stopPropagation();
    analyzeNews({ newsId: news.id, presetKey: selectedPresetKey });
  };

  const handleClick = () => {
    if (!news.is_read) {
      updateNews({ id: news.id, data: { is_read: true } });
    }
    window.open(news.url, '_blank');
  };

  const categoryInfo = news.ai_category ? categoryConfig[news.ai_category] || categoryConfig.other : null;

  return (
    <div
      onClick={handleClick}
      className={`bg-white rounded-lg shadow-sm border p-4 cursor-pointer hover:shadow-md transition-shadow ${
        !news.is_read ? 'border-l-4 border-l-blue-500' : ''
      } ${isSelected ? 'ring-2 ring-blue-500' : ''}`}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-2 flex-wrap">
          {/* AI Category Badge */}
          {categoryInfo && (
            <span className={`flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${categoryInfo.color}`}>
              {categoryInfo.icon}
              {categoryInfo.label}
            </span>
          )}

          {/* AI Score Badge */}
          {news.ai_analyzed && news.ai_score !== null && (
            <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs font-medium">
              AI: {news.ai_score}
            </span>
          )}

          {/* YouTube Potential */}
          {news.ai_youtube_potential && news.ai_youtube_potential !== 'low' && (
            <span
              className={`px-2 py-0.5 rounded text-xs font-medium ${
                news.ai_youtube_potential === 'high'
                  ? 'bg-yellow-100 text-yellow-700'
                  : 'bg-orange-100 text-orange-700'
              }`}
            >
              YT: {news.ai_youtube_potential}
            </span>
          )}
        </div>

        <div className="flex items-center gap-1 flex-shrink-0">
          {/* Analyze Button */}
          {!news.ai_analyzed && (
            <button
              onClick={handleAnalyze}
              disabled={isAnalyzing}
              className="p-1.5 text-purple-600 hover:bg-purple-50 rounded-lg transition-colors disabled:opacity-50"
            >
              {isAnalyzing ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Sparkles className="w-4 h-4" />
              )}
            </button>
          )}

          {/* Bookmark Button */}
          <button
            onClick={handleBookmark}
            className={`p-1.5 rounded-lg transition-colors ${
              news.is_bookmarked
                ? 'text-yellow-500 bg-yellow-50'
                : 'text-gray-400 hover:text-yellow-500 hover:bg-yellow-50'
            }`}
          >
            <Star className={`w-4 h-4 ${news.is_bookmarked ? 'fill-current' : ''}`} />
          </button>

          {/* Select Checkbox */}
          {onSelect && (
            <input
              type="checkbox"
              checked={isSelected}
              onChange={(e) => {
                e.stopPropagation();
                onSelect();
              }}
              onClick={(e) => e.stopPropagation()}
              className="w-4 h-4 rounded border-gray-300"
            />
          )}
        </div>
      </div>

      {/* Title */}
      <h3 className={`font-medium mb-2 line-clamp-2 ${news.is_read ? 'text-gray-600' : 'text-gray-900'}`}>
        {news.title}
      </h3>

      {/* AI Reason */}
      {news.ai_reason && (
        <p className="text-sm text-purple-600 mb-2 line-clamp-2">
          {news.ai_reason}
        </p>
      )}

      {/* Summary */}
      {news.summary && (
        <p className="text-sm text-gray-500 mb-3 line-clamp-2">
          {news.summary}
        </p>
      )}

      {/* Key Points */}
      {news.ai_key_points && news.ai_key_points.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {news.ai_key_points.map((point, idx) => (
            <span key={idx} className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
              #{point}
            </span>
          ))}
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-gray-400">
        <div className="flex items-center gap-2">
          <span>{news.source}</span>
          {news.category && (
            <>
              <span>|</span>
              <span>{news.category}</span>
            </>
          )}
        </div>

        <div className="flex items-center gap-3">
          {/* 커뮤니티 메타 정보 */}
          {news.source_type === 'community' && (
            <div className="flex items-center gap-2 text-gray-500">
              {news.view_count !== null && news.view_count > 0 && (
                <span className="flex items-center gap-0.5" title="조회수">
                  <Eye className="w-3 h-3" />
                  {news.view_count.toLocaleString()}
                </span>
              )}
              {news.like_count !== null && news.like_count > 0 && (
                <span className="flex items-center gap-0.5" title="좋아요">
                  <ThumbsUp className="w-3 h-3" />
                  {news.like_count.toLocaleString()}
                </span>
              )}
              {news.comment_count !== null && news.comment_count > 0 && (
                <span className="flex items-center gap-0.5" title="댓글">
                  <MessageCircle className="w-3 h-3" />
                  {news.comment_count.toLocaleString()}
                </span>
              )}
            </div>
          )}

          {news.published_at && (
            <span>
              {format(new Date(news.published_at), 'MM/dd HH:mm', { locale: ko })}
            </span>
          )}
          <ExternalLink className="w-3 h-3" />
        </div>
      </div>
    </div>
  );
}
