import Header from './components/Header';
import FilterPanel from './components/FilterPanel';
import NewsList from './components/NewsList';
import AIFilterModal from './components/AIFilterModal';
import PresetManager from './components/PresetManager';
import { useAutoCollect } from './hooks/useNews';
import { Loader2 } from 'lucide-react';

export default function App() {
  const { isCollecting } = useAutoCollect();

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      {/* 자동 수집 중 알림 */}
      {isCollecting && (
        <div className="bg-green-50 border-b border-green-200">
          <div className="max-w-7xl mx-auto px-4 py-2 flex items-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin text-green-600" />
            <span className="text-sm text-green-800">뉴스를 수집하고 있습니다...</span>
          </div>
        </div>
      )}

      <main className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar */}
          <aside className="lg:col-span-1">
            <PresetManager />
          </aside>

          {/* Main Content */}
          <div className="lg:col-span-3">
            <FilterPanel />
            <NewsList />
          </div>
        </div>
      </main>

      <AIFilterModal />
    </div>
  );
}
