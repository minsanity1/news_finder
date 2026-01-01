import Header from './components/Header';
import FilterPanel from './components/FilterPanel';
import NewsList from './components/NewsList';
import AIFilterModal from './components/AIFilterModal';
import PresetManager from './components/PresetManager';

export default function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

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
