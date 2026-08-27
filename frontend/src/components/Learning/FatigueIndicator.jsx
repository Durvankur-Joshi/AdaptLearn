import React from 'react';
import { useLearning } from '../../context/LearningContext';

const FATIGUE_CONFIG = {
  fresh:    { color: 'bg-emerald-500', text: 'Fresh',    icon: '🟢', bar: 'w-1/5' },
  mild:     { color: 'bg-amber-400',   text: 'Mild',     icon: '🟡', bar: 'w-2/5' },
  moderate: { color: 'bg-orange-400',   text: 'Moderate', icon: '🟠', bar: 'w-3/5' },
  high:     { color: 'bg-rose-400',     text: 'High',     icon: '🔴', bar: 'w-4/5' },
  critical: { color: 'bg-rose-600',     text: 'Critical', icon: '⛔', bar: 'w-full' },
};

export default function FatigueIndicator() {
  const { fatigueLevel, showBreakModal, setShowBreakModal, recordBreak, currentSession } = useLearning();

  const cfg = FATIGUE_CONFIG[fatigueLevel] || FATIGUE_CONFIG.fresh;

  const handleTakeBreak = async () => {
    if (currentSession?.session_id) {
      await recordBreak(currentSession.session_id);
    }
    setShowBreakModal(false);
  };

  return (
    <>
      {/* Compact indicator bar */}
      <div className="flex items-center gap-2 text-xs">
        <span>{cfg.icon}</span>
        <div className="flex-1 h-1.5 bg-theme-border rounded-full overflow-hidden">
          <div className={`h-full ${cfg.color} ${cfg.bar} transition-all duration-500 rounded-full`} />
        </div>
        <span className="text-theme-text-muted font-medium">{cfg.text}</span>
      </div>

      {/* Break modal */}
      {showBreakModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="bg-surface rounded-theme-xl shadow-theme-xl p-6 max-w-sm mx-4 text-center border border-theme-border animate-scale-in">
            <div className="text-4xl mb-3">😮‍💨</div>
            <h3 className="text-lg font-semibold text-theme-text mb-1">You seem tired</h3>
            <p className="text-sm text-theme-text-muted mb-4">
              Your response times and accuracy suggest fatigue. A short break can boost retention by up to 20%.
            </p>
            <div className="flex gap-3 justify-center">
              <button
                onClick={handleTakeBreak}
                className="px-4 py-2 gradient-primary text-white rounded-theme text-sm font-medium hover:opacity-90 transition-opacity"
              >
                Take a 5-min break
              </button>
              <button
                onClick={() => setShowBreakModal(false)}
                className="px-4 py-2 bg-theme-bg text-theme-text-secondary rounded-theme text-sm font-medium hover:bg-surface-alt transition-colors border border-theme-border"
              >
                Continue
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
