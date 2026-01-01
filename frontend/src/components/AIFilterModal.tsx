import { useEffect } from 'react';
import { X, Sparkles, Loader2 } from 'lucide-react';
import { useAIFilterModalStore, useFilterStore } from '../stores/filterStore';
import { useAIPresets, useAIPresetDetail } from '../hooks/useFilters';
import { useAIUsage } from '../hooks/useAIAnalysis';

export default function AIFilterModal() {
  const {
    isOpen,
    closeModal,
    selectedPresetKey,
    setPresetKey,
    customPrompt,
    setCustomPrompt,
    minScore,
    setMinScore,
  } = useAIFilterModalStore();

  const { setFilter } = useFilterStore();
  const { data: presets, isLoading: presetsLoading } = useAIPresets();
  const { data: presetDetail } = useAIPresetDetail(selectedPresetKey);
  const { data: aiUsage } = useAIUsage();

  useEffect(() => {
    if (presetDetail?.prompt && selectedPresetKey !== 'custom') {
      setCustomPrompt(presetDetail.prompt);
    }
  }, [presetDetail, selectedPresetKey, setCustomPrompt]);

  if (!isOpen) return null;

  const handleApply = () => {
    setFilter({
      ai_min_score: minScore > 0 ? minScore : undefined,
      ai_category: selectedPresetKey !== 'custom' ? selectedPresetKey.replace('brand_', '') : undefined,
    });
    closeModal();
  };

  const presetOptions = [
    { key: 'brand_failure', name: 'Failure Story' },
    { key: 'brand_success', name: 'Success Story' },
    { key: 'brand_comeback', name: 'Comeback Story' },
    { key: 'franchise_story', name: 'Franchise Story' },
    { key: 'custom', name: 'Custom Prompt' },
  ];

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-purple-600" />
            <h2 className="text-lg font-semibold">AI Filter Settings</h2>
          </div>
          <button
            onClick={closeModal}
            className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-6">
          {/* Preset Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Preset
            </label>
            {presetsLoading ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="w-6 h-6 animate-spin text-purple-600" />
              </div>
            ) : (
              <div className="space-y-2">
                {presetOptions.map((option) => (
                  <label
                    key={option.key}
                    className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                      selectedPresetKey === option.key
                        ? 'border-purple-500 bg-purple-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <input
                      type="radio"
                      name="preset"
                      value={option.key}
                      checked={selectedPresetKey === option.key}
                      onChange={() => setPresetKey(option.key)}
                      className="text-purple-600"
                    />
                    <span className="font-medium">{option.name}</span>
                  </label>
                ))}
              </div>
            )}
          </div>

          {/* Prompt */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              AI Prompt
            </label>
            <textarea
              value={customPrompt}
              onChange={(e) => setCustomPrompt(e.target.value)}
              disabled={selectedPresetKey !== 'custom'}
              rows={6}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none disabled:bg-gray-50 disabled:text-gray-500"
              placeholder="Enter custom prompt..."
            />
          </div>

          {/* Min Score Slider */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Minimum Relevance Score: {minScore}
            </label>
            <input
              type="range"
              min="0"
              max="100"
              value={minScore}
              onChange={(e) => setMinScore(parseInt(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-400 mt-1">
              <span>0</span>
              <span>50</span>
              <span>100</span>
            </div>
          </div>

          {/* API Usage Info */}
          {aiUsage && (
            <div className="bg-gray-50 rounded-lg p-3 text-sm text-gray-600">
              <div className="flex items-center justify-between">
                <span>Gemini Flash Free Tier</span>
                <span>
                  {aiUsage.today} / {aiUsage.daily_limit} daily
                </span>
              </div>
              <div className="mt-1 bg-gray-200 rounded-full h-2">
                <div
                  className="bg-purple-600 rounded-full h-2 transition-all"
                  style={{ width: `${(aiUsage.today / aiUsage.daily_limit) * 100}%` }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-4 border-t">
          <button
            onClick={closeModal}
            className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleApply}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
          >
            Apply
          </button>
        </div>
      </div>
    </div>
  );
}
