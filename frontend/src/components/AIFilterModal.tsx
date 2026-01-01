import { useEffect, useState } from 'react';
import { X, Sparkles, Loader2, Play } from 'lucide-react';
import { useAIFilterModalStore, useFilterStore } from '../stores/filterStore';
import { useAIPresets, useAIPresetDetail } from '../hooks/useFilters';
import { useAIUsage, useAnalyzeUnanalyzed } from '../hooks/useAIAnalysis';

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
  const { isLoading: presetsLoading } = useAIPresets();
  const { data: presetDetail } = useAIPresetDetail(selectedPresetKey);
  const { data: aiUsage, refetch: refetchUsage } = useAIUsage();
  const { mutate: analyzeUnanalyzed, isPending: isAnalyzing } = useAnalyzeUnanalyzed();

  const [analysisLimit, setAnalysisLimit] = useState(20);
  const [lastResult, setLastResult] = useState<{ analyzed: number; message: string } | null>(null);

  useEffect(() => {
    if (presetDetail?.prompt && selectedPresetKey !== 'custom') {
      setCustomPrompt(presetDetail.prompt);
    }
  }, [presetDetail, selectedPresetKey, setCustomPrompt]);

  useEffect(() => {
    if (isOpen) {
      setLastResult(null);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleApply = () => {
    setFilter({
      ai_min_score: minScore > 0 ? minScore : undefined,
      ai_category: selectedPresetKey !== 'custom' ? selectedPresetKey.replace('brand_', '') : undefined,
    });
    closeModal();
  };

  const handleRunAnalysis = () => {
    const presetKey = selectedPresetKey === 'custom' ? 'brand_failure' : selectedPresetKey;
    analyzeUnanalyzed(
      { presetKey, limit: analysisLimit },
      {
        onSuccess: (data) => {
          setLastResult({
            analyzed: data.results?.length || 0,
            message: data.message,
          });
          refetchUsage();
        },
        onError: () => {
          setLastResult({
            analyzed: 0,
            message: '분석 중 오류가 발생했습니다.',
          });
        },
      }
    );
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

          {/* Run Analysis Section */}
          <div className="border rounded-lg p-4 bg-purple-50">
            <h3 className="font-medium text-purple-900 mb-3">일괄 AI 분석 실행</h3>
            <div className="flex items-center gap-3 mb-3">
              <label className="text-sm text-purple-700">분석할 뉴스 수:</label>
              <select
                value={analysisLimit}
                onChange={(e) => setAnalysisLimit(Number(e.target.value))}
                className="px-3 py-1.5 border rounded-lg text-sm"
                disabled={isAnalyzing}
              >
                <option value={10}>10개</option>
                <option value={20}>20개</option>
                <option value={50}>50개</option>
                <option value={100}>100개</option>
              </select>
              <button
                onClick={handleRunAnalysis}
                disabled={isAnalyzing || selectedPresetKey === 'custom'}
                className="flex items-center gap-2 px-4 py-1.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isAnalyzing ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    분석 중...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    분석 실행
                  </>
                )}
              </button>
            </div>
            {lastResult && (
              <div className={`text-sm p-2 rounded ${lastResult.analyzed > 0 ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                {lastResult.message}
              </div>
            )}
            {selectedPresetKey === 'custom' && (
              <p className="text-xs text-purple-600">* Custom Prompt는 개별 분석만 지원합니다.</p>
            )}
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
        <div className="flex items-center justify-between p-4 border-t">
          <p className="text-xs text-gray-500">
            * Apply: 분석된 뉴스 필터링 | 분석 실행: 미분석 뉴스 AI 분석
          </p>
          <div className="flex items-center gap-3">
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
              Apply Filter
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
