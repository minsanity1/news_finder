import { useState } from 'react';
import { Settings, AlertTriangle, HelpCircle, Users, Newspaper, MessageSquare } from 'lucide-react';
import { useAIUsage } from '../hooks/useAIAnalysis';
import { useFilterStore } from '../stores/filterStore';
import SettingsModal from './SettingsModal';
import HelpModal from './HelpModal';
import CommunityModal from './CommunityModal';

export default function Header() {
  const [isCommunityOpen, setIsCommunityOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isHelpOpen, setIsHelpOpen] = useState(false);
  const { data: aiUsage } = useAIUsage();
  const { filter, setFilter } = useFilterStore();

  return (
    <>
      {/* API Key Warning Banner */}
      {aiUsage && !aiUsage.api_key_configured && (
        <div className="bg-amber-50 border-b border-amber-200">
          <div className="max-w-7xl mx-auto px-4 py-3 flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0" />
            <p className="text-sm text-amber-800">
              <strong>Gemini API 키가 설정되지 않았습니다.</strong>{' '}
              AI 필터링 기능을 사용하려면 backend/.env 파일에 GOOGLE_API_KEY를 설정하세요.
              <a
                href="https://aistudio.google.com/app/apikey"
                target="_blank"
                rel="noopener noreferrer"
                className="ml-2 underline text-amber-700 hover:text-amber-900"
              >
                API 키 발급받기
              </a>
            </p>
          </div>
        </div>
      )}

      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <h1 className="text-xl font-bold text-gray-900">
              News Finder
            </h1>

            {/* 뉴스/커뮤니티 탭 */}
            <div className="flex items-center bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setFilter({ source_type: 'news', source: '' })}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  filter.source_type === 'news' || !filter.source_type
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <Newspaper className="w-4 h-4" />
                뉴스
              </button>
              <button
                onClick={() => setFilter({ source_type: 'community', source: '' })}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  filter.source_type === 'community'
                    ? 'bg-white text-purple-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <MessageSquare className="w-4 h-4" />
                커뮤니티
              </button>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {aiUsage && (
              <div className={`text-sm ${aiUsage.api_key_configured ? 'text-gray-600' : 'text-amber-600'}`} title={
                aiUsage.keys && aiUsage.keys.length > 1
                  ? `Keys: ${aiUsage.keys.map((k, i) => `#${i + 1}: ${k.used}/${k.used + k.remaining}`).join(', ')}`
                  : undefined
              }>
                AI: {aiUsage.api_key_configured
                  ? `${aiUsage.today}/${aiUsage.daily_limit}${aiUsage.total_keys && aiUsage.total_keys > 1 ? ` (${aiUsage.total_keys} keys)` : ''}`
                  : 'Not configured'}
              </div>
            )}

            <button
              onClick={() => setIsCommunityOpen(true)}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              <Users className="w-4 h-4" />
              Community
            </button>

            <button
              onClick={() => setIsHelpOpen(true)}
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
              title="도움말"
            >
              <HelpCircle className="w-5 h-5" />
            </button>

            <button
              onClick={() => setIsSettingsOpen(true)}
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
              title="설정"
            >
              <Settings className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      <CommunityModal isOpen={isCommunityOpen} onClose={() => setIsCommunityOpen(false)} />
      <SettingsModal isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />
      <HelpModal isOpen={isHelpOpen} onClose={() => setIsHelpOpen(false)} />
    </>
  );
}
