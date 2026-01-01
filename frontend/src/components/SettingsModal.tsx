import { useState } from 'react';
import { X, Key, Rss, Brain, Database, ChevronRight, ExternalLink, Check, AlertCircle } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { searchApi, aiApi, collectorApi } from '../api/client';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type TabType = 'api' | 'rss' | 'ai' | 'data';

export default function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const [activeTab, setActiveTab] = useState<TabType>('api');
  const queryClient = useQueryClient();

  const { data: aiUsage } = useQuery({
    queryKey: ['ai-usage'],
    queryFn: aiApi.getUsage,
    enabled: isOpen,
  });

  const { data: searchStatus } = useQuery({
    queryKey: ['search-status'],
    queryFn: searchApi.getStatus,
    enabled: isOpen,
  });

  const { data: rssSources } = useQuery({
    queryKey: ['rss-sources'],
    queryFn: collectorApi.getSources,
    enabled: isOpen,
  });

  if (!isOpen) return null;

  const tabs = [
    { id: 'api' as TabType, label: 'API 설정', icon: Key },
    { id: 'rss' as TabType, label: 'RSS 소스', icon: Rss },
    { id: 'ai' as TabType, label: 'AI 설정', icon: Brain },
    { id: 'data' as TabType, label: '데이터 관리', icon: Database },
  ];

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[80vh] overflow-hidden flex">
        {/* Sidebar */}
        <div className="w-48 bg-gray-50 border-r p-4">
          <h2 className="text-lg font-semibold mb-4">설정</h2>
          <nav className="space-y-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                  activeTab === tab.id
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b">
            <h3 className="font-semibold">
              {tabs.find((t) => t.id === activeTab)?.label}
            </h3>
            <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded">
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {activeTab === 'api' && (
              <APISettings aiUsage={aiUsage} searchStatus={searchStatus} />
            )}
            {activeTab === 'rss' && (
              <RSSSettings sources={rssSources} />
            )}
            {activeTab === 'ai' && (
              <AISettings aiUsage={aiUsage} />
            )}
            {activeTab === 'data' && (
              <DataSettings />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// API Settings Tab
function APISettings({ aiUsage, searchStatus }: { aiUsage: any; searchStatus: any }) {
  return (
    <div className="space-y-6">
      {/* Gemini API */}
      <div className="border rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <h4 className="font-medium">Gemini API (AI 분석)</h4>
          {aiUsage?.api_key_configured ? (
            <span className="flex items-center gap-1 text-sm text-green-600">
              <Check className="w-4 h-4" /> 설정됨
            </span>
          ) : (
            <span className="flex items-center gap-1 text-sm text-amber-600">
              <AlertCircle className="w-4 h-4" /> 미설정
            </span>
          )}
        </div>

        {aiUsage?.api_key_configured ? (
          <div className="space-y-2 text-sm text-gray-600">
            <p>오늘 사용량: {aiUsage.today} / {aiUsage.daily_limit}</p>
            <p>남은 횟수: {aiUsage.remaining}</p>
            {aiUsage.total_keys > 1 && (
              <p>등록된 키: {aiUsage.total_keys}개</p>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-sm text-gray-600">
              AI 분석 기능을 사용하려면 Gemini API 키가 필요합니다.
            </p>
            <div className="bg-gray-50 rounded p-3 text-sm font-mono">
              <p className="text-gray-500"># backend/.env</p>
              <p>GOOGLE_API_KEY=발급받은_API_키</p>
            </div>
            <a
              href="https://aistudio.google.com/app/apikey"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-sm text-blue-600 hover:underline"
            >
              Google AI Studio에서 API 키 발급받기
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        )}
      </div>

      {/* Naver API */}
      <div className="border rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <h4 className="font-medium">Naver API (뉴스 검색)</h4>
          {searchStatus?.naver_api_configured ? (
            <span className="flex items-center gap-1 text-sm text-green-600">
              <Check className="w-4 h-4" /> 설정됨
            </span>
          ) : (
            <span className="flex items-center gap-1 text-sm text-amber-600">
              <AlertCircle className="w-4 h-4" /> 미설정
            </span>
          )}
        </div>

        {searchStatus?.naver_api_configured ? (
          <p className="text-sm text-gray-600">
            네이버 뉴스 검색 API가 활성화되어 있습니다.
          </p>
        ) : (
          <div className="space-y-3">
            <p className="text-sm text-gray-600">
              과거 뉴스 검색 기능을 사용하려면 Naver API 키가 필요합니다.
            </p>
            <div className="bg-gray-50 rounded p-3 text-sm font-mono">
              <p className="text-gray-500"># backend/.env</p>
              <p>NAVER_CLIENT_ID=발급받은_클라이언트_ID</p>
              <p>NAVER_CLIENT_SECRET=발급받은_시크릿</p>
            </div>
            <a
              href="https://developers.naver.com/apps"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-sm text-blue-600 hover:underline"
            >
              네이버 개발자 센터에서 API 등록하기
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        )}
      </div>

      <div className="bg-blue-50 rounded-lg p-4 text-sm text-blue-800">
        <p className="font-medium mb-1">💡 API 키 설정 방법</p>
        <p>
          backend/.env 파일을 직접 편집한 후 서버를 재시작하세요.
          보안을 위해 웹에서 직접 API 키를 입력하는 기능은 제공하지 않습니다.
        </p>
      </div>
    </div>
  );
}

// RSS Settings Tab
function RSSSettings({ sources }: { sources: any[] | undefined }) {
  return (
    <div className="space-y-4">
      <p className="text-sm text-gray-600">
        현재 등록된 RSS 소스 목록입니다. 소스 관리는 backend/app/collector/sources.py에서 수정할 수 있습니다.
      </p>

      <div className="border rounded-lg divide-y">
        {sources?.map((source, index) => (
          <div key={index} className="flex items-center justify-between p-3">
            <div>
              <p className="font-medium text-sm">{source.name}</p>
              <p className="text-xs text-gray-500">{source.category}</p>
            </div>
            <span className={`px-2 py-0.5 rounded text-xs ${
              source.enabled
                ? 'bg-green-100 text-green-700'
                : 'bg-gray-100 text-gray-500'
            }`}>
              {source.enabled ? '활성' : '비활성'}
            </span>
          </div>
        )) || (
          <p className="p-4 text-sm text-gray-500">소스 정보를 불러오는 중...</p>
        )}
      </div>
    </div>
  );
}

// AI Settings Tab
function AISettings({ aiUsage }: { aiUsage: any }) {
  return (
    <div className="space-y-6">
      <div className="border rounded-lg p-4">
        <h4 className="font-medium mb-3">AI 모델 설정</h4>
        <div className="space-y-3 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-600">현재 모델</span>
            <span className="font-mono">gemini-2.0-flash</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">일일 한도 (키당)</span>
            <span>1,500회</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">등록된 API 키</span>
            <span>{aiUsage?.total_keys || 0}개</span>
          </div>
        </div>
      </div>

      <div className="border rounded-lg p-4">
        <h4 className="font-medium mb-3">AI 프리셋</h4>
        <div className="space-y-2 text-sm">
          <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
            <span>브랜드 실패 스토리</span>
            <span className="text-gray-500">brand_failure</span>
          </div>
          <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
            <span>브랜드 성공 스토리</span>
            <span className="text-gray-500">brand_success</span>
          </div>
          <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
            <span>브랜드 부활 스토리</span>
            <span className="text-gray-500">brand_comeback</span>
          </div>
          <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
            <span>프랜차이즈 스토리</span>
            <span className="text-gray-500">franchise_story</span>
          </div>
        </div>
      </div>

      <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-600">
        <p>
          AI 모델 및 프리셋 설정은 backend/.env 및 backend/app/filter/ai_filter.py에서 수정할 수 있습니다.
        </p>
      </div>
    </div>
  );
}

// Data Settings Tab
function DataSettings() {
  const queryClient = useQueryClient();
  const [deleteOlderThan, setDeleteOlderThan] = useState(30);

  return (
    <div className="space-y-6">
      <div className="border rounded-lg p-4">
        <h4 className="font-medium mb-3">데이터베이스 정보</h4>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-600">위치</span>
            <span className="font-mono text-xs">backend/data/news.db</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">타입</span>
            <span>SQLite</span>
          </div>
        </div>
      </div>

      <div className="border rounded-lg p-4">
        <h4 className="font-medium mb-3">캐시 관리</h4>
        <button
          onClick={() => {
            queryClient.invalidateQueries();
            alert('캐시가 새로고침되었습니다.');
          }}
          className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm transition-colors"
        >
          캐시 새로고침
        </button>
      </div>

      <div className="border border-red-200 rounded-lg p-4">
        <h4 className="font-medium mb-3 text-red-700">위험 영역</h4>
        <p className="text-sm text-gray-600 mb-3">
          오래된 뉴스를 삭제하여 데이터베이스 크기를 줄일 수 있습니다.
          이 작업은 되돌릴 수 없습니다.
        </p>
        <div className="flex items-center gap-3">
          <select
            value={deleteOlderThan}
            onChange={(e) => setDeleteOlderThan(Number(e.target.value))}
            className="px-3 py-2 border rounded-lg text-sm"
          >
            <option value={7}>7일 이상</option>
            <option value={14}>14일 이상</option>
            <option value={30}>30일 이상</option>
            <option value={60}>60일 이상</option>
            <option value={90}>90일 이상</option>
          </select>
          <button
            onClick={() => {
              if (confirm(`${deleteOlderThan}일 이상 된 뉴스를 삭제하시겠습니까?`)) {
                alert('이 기능은 아직 구현되지 않았습니다.');
              }
            }}
            className="px-4 py-2 bg-red-100 hover:bg-red-200 text-red-700 rounded-lg text-sm transition-colors"
          >
            오래된 뉴스 삭제
          </button>
        </div>
      </div>
    </div>
  );
}
