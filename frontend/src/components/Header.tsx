import { RefreshCw, Settings } from 'lucide-react';
import { useCollectorRun, useCollectorStatus, useAIUsage } from '../hooks/useAIAnalysis';

export default function Header() {
  const { mutate: runCollector, isPending } = useCollectorRun();
  const { data: status } = useCollectorStatus();
  const { data: aiUsage } = useAIUsage();

  return (
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
            <div className="text-sm text-gray-600">
              AI: {aiUsage.today}/{aiUsage.daily_limit}
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
  );
}
