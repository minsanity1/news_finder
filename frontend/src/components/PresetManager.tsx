import { useState } from 'react';
import { Plus, Trash2, Edit2, Save, X, Loader2 } from 'lucide-react';
import {
  useFilterPresets,
  useCreateFilterPreset,
  useUpdateFilterPreset,
  useDeleteFilterPreset,
} from '../hooks/useFilters';
import { useFilterStore } from '../stores/filterStore';
import type { FilterPreset } from '../types';

export default function PresetManager() {
  const { setFilter } = useFilterStore();
  const { data: presets = [], isLoading } = useFilterPresets();
  const { mutate: createPreset, isPending: isCreating } = useCreateFilterPreset();
  const { mutate: updatePreset, isPending: isUpdating } = useUpdateFilterPreset();
  const { mutate: deletePreset, isPending: isDeleting } = useDeleteFilterPreset();

  const [isAdding, setIsAdding] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    include_keywords: '',
    exclude_keywords: '',
    ai_min_score: 70,
  });

  const handleApplyPreset = (preset: FilterPreset) => {
    setFilter({
      ai_min_score: preset.ai_min_score ?? undefined,
    });
  };

  const handleCreate = () => {
    createPreset({
      name: formData.name,
      type: 'combined',
      include_keywords: formData.include_keywords.split(',').map((k) => k.trim()).filter(Boolean),
      exclude_keywords: formData.exclude_keywords.split(',').map((k) => k.trim()).filter(Boolean),
      ai_min_score: formData.ai_min_score,
      is_default: false,
      sources: null,
      categories: null,
      ai_prompt: null,
    });
    setIsAdding(false);
    setFormData({ name: '', include_keywords: '', exclude_keywords: '', ai_min_score: 70 });
  };

  const handleUpdate = (id: number) => {
    updatePreset({
      id,
      preset: {
        name: formData.name,
        include_keywords: formData.include_keywords.split(',').map((k) => k.trim()).filter(Boolean),
        exclude_keywords: formData.exclude_keywords.split(',').map((k) => k.trim()).filter(Boolean),
        ai_min_score: formData.ai_min_score,
      },
    });
    setEditingId(null);
  };

  const handleDelete = (id: number) => {
    if (confirm('Delete this preset?')) {
      deletePreset(id);
    }
  };

  const startEdit = (preset: FilterPreset) => {
    setEditingId(preset.id);
    setFormData({
      name: preset.name,
      include_keywords: preset.include_keywords?.join(', ') || '',
      exclude_keywords: preset.exclude_keywords?.join(', ') || '',
      ai_min_score: preset.ai_min_score || 70,
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-4">
        <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-medium text-gray-900">Saved Presets</h3>
        <button
          onClick={() => setIsAdding(true)}
          className="flex items-center gap-1 px-3 py-1.5 text-sm bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Add
        </button>
      </div>

      {/* Add Form */}
      {isAdding && (
        <div className="mb-4 p-3 bg-gray-50 rounded-lg space-y-3">
          <input
            type="text"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="Preset name"
            className="w-full px-3 py-2 border rounded-lg"
          />
          <input
            type="text"
            value={formData.include_keywords}
            onChange={(e) => setFormData({ ...formData, include_keywords: e.target.value })}
            placeholder="Include keywords (comma separated)"
            className="w-full px-3 py-2 border rounded-lg"
          />
          <input
            type="text"
            value={formData.exclude_keywords}
            onChange={(e) => setFormData({ ...formData, exclude_keywords: e.target.value })}
            placeholder="Exclude keywords (comma separated)"
            className="w-full px-3 py-2 border rounded-lg"
          />
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-600">Min AI Score:</label>
            <input
              type="number"
              min="0"
              max="100"
              value={formData.ai_min_score}
              onChange={(e) => setFormData({ ...formData, ai_min_score: parseInt(e.target.value) })}
              className="w-20 px-2 py-1 border rounded"
            />
          </div>
          <div className="flex justify-end gap-2">
            <button
              onClick={() => setIsAdding(false)}
              className="px-3 py-1.5 text-gray-600 hover:bg-gray-100 rounded-lg"
            >
              <X className="w-4 h-4" />
            </button>
            <button
              onClick={handleCreate}
              disabled={!formData.name || isCreating}
              className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white rounded-lg disabled:opacity-50"
            >
              {isCreating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
              Save
            </button>
          </div>
        </div>
      )}

      {/* Presets List */}
      <div className="space-y-2">
        {presets.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-4">No presets saved yet</p>
        ) : (
          presets.map((preset) => (
            <div
              key={preset.id}
              className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50"
            >
              {editingId === preset.id ? (
                <div className="flex-1 space-y-2">
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="Preset name"
                    className="w-full px-2 py-1 border rounded"
                  />
                  <input
                    type="text"
                    value={formData.include_keywords}
                    onChange={(e) => setFormData({ ...formData, include_keywords: e.target.value })}
                    placeholder="Include keywords (comma separated)"
                    className="w-full px-2 py-1 border rounded text-sm"
                  />
                  <input
                    type="text"
                    value={formData.exclude_keywords}
                    onChange={(e) => setFormData({ ...formData, exclude_keywords: e.target.value })}
                    placeholder="Exclude keywords (comma separated)"
                    className="w-full px-2 py-1 border rounded text-sm"
                  />
                  <div className="flex items-center gap-2">
                    <label className="text-sm text-gray-600">Min AI Score:</label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={formData.ai_min_score}
                      onChange={(e) => setFormData({ ...formData, ai_min_score: parseInt(e.target.value) || 0 })}
                      className="w-20 px-2 py-1 border rounded text-sm"
                    />
                  </div>
                  <div className="flex justify-end gap-2">
                    <button
                      onClick={() => setEditingId(null)}
                      className="px-3 py-1.5 text-gray-600 hover:bg-gray-100 rounded-lg"
                    >
                      <X className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleUpdate(preset.id)}
                      disabled={isUpdating}
                      className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white rounded-lg disabled:opacity-50"
                    >
                      {isUpdating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                      Save
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <button
                    onClick={() => handleApplyPreset(preset)}
                    className="flex-1 text-left"
                  >
                    <span className="font-medium">{preset.name}</span>
                    {preset.ai_min_score && (
                      <span className="ml-2 text-xs text-gray-500">
                        (AI: {preset.ai_min_score}+)
                      </span>
                    )}
                  </button>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => startEdit(preset)}
                      className="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(preset.id)}
                      disabled={isDeleting}
                      className="p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded"
                    >
                      {isDeleting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                    </button>
                  </div>
                </>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
