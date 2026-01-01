import { RefreshCw, Settings, AlertTriangle } from 'lucide-react';
import { useCollectorRun, useCollectorStatus, useAIUsage } from '../hooks/useAIAnalysis';

export default function Header() {
  const { mutate: runCollector, isPending } = useCollectorRun();
  const { data: status } = useCollectorStatus();
  const { data: aiUsage } = useAIUsage();

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
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-bold text-gray-900">
              Korean News Filter
            </h1>
            {status?.last_run && (
              <span className="text-sm text-gray-500">
                Last: {new Date(status.last_run).toLocaleString('ko-KR')}
                {status.last_collected_count > 0 && ` (${status.last_collected_count})`}
              </span>
            )}
          </div>

          <div className="flex items-center gap-4">
            {aiUsage && (
              <div className={`text-sm ${aiUsage.api_key_configured ? 'text-gray-600' : 'text-amber-600'}`}>
                AI: {aiUsage.api_key_configured ? `${aiUsage.today}/${aiUsage.daily_limit}` : 'Not configured'}
              </div>
            )}

            <button
              onClick={() => runCollector()}
              disabled={isPending}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${isPending ? 'animate-spin' : ''}`} />
              {isPending ? 'Collecting...' : 'Collect'}
            </button>

            <button className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors">
              <Settings className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>
    </>
  );
}
