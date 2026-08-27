import React, { useEffect, useMemo } from 'react';
import { useLearning } from '../../context/LearningContext';

/**
 * Lightweight inline velocity sparkline + engagement badge.
 * Uses raw canvas-free SVG so no chart library dependency.
 */
export default function LearningVelocityGraph({ sessionId }) {
  const { velocityData, engagementScore, fetchVelocityGraph } = useLearning();

  useEffect(() => {
    if (sessionId) fetchVelocityGraph(sessionId);
  }, [sessionId, fetchVelocityGraph]);

  // Build points for SVG sparkline from velocity snapshots
  const { points, masteryPoints, maxQ } = useMemo(() => {
    if (!velocityData || velocityData.length === 0) return { points: '', masteryPoints: '', maxQ: 0 };

    const maxQ = velocityData.length;
    const W = 240;
    const H = 60;
    const pad = 4;

    // accuracy line
    const accPts = velocityData.map((v, i) => {
      const x = pad + (i / Math.max(maxQ - 1, 1)) * (W - 2 * pad);
      const acc = v.rolling_accuracy ?? v.accuracy ?? 0;
      const y = H - pad - acc * (H - 2 * pad);
      return `${x},${y}`;
    });

    // mastery line
    const mPts = velocityData.map((v, i) => {
      const x = pad + (i / Math.max(maxQ - 1, 1)) * (W - 2 * pad);
      const m = v.mastery ?? 0;
      const y = H - pad - m * (H - 2 * pad);
      return `${x},${y}`;
    });

    return { points: accPts.join(' '), masteryPoints: mPts.join(' '), maxQ };
  }, [velocityData]);

  // Engagement color
  const engColor = engagementScore >= 0.7 ? 'text-emerald-500' : engagementScore >= 0.4 ? 'text-amber-500' : 'text-error';

  if (!velocityData || velocityData.length < 2) {
    return (
      <div className="text-xs text-theme-text-muted italic">
        Answer a few questions to see your learning velocity…
      </div>
    );
  }

  return (
    <div className="bg-surface/80 rounded-theme-lg p-3 border border-theme-border">
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs font-semibold text-theme-text-secondary">Learning Velocity</span>
        <span className={`text-xs font-bold ${engColor}`}>
          Engagement {Math.round(engagementScore * 100)}%
        </span>
      </div>

      <svg viewBox="0 0 240 60" className="w-full h-14" preserveAspectRatio="none">
        {/* gridlines */}
        <line x1="4" y1="30" x2="236" y2="30" stroke="#e5e7eb" strokeWidth="0.5" strokeDasharray="3,3" />
        <line x1="4" y1="56" x2="236" y2="56" stroke="#e5e7eb" strokeWidth="0.5" />

        {/* mastery line */}
        <polyline
          fill="none"
          stroke="#a78bfa"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          points={masteryPoints}
        />

        {/* accuracy line */}
        <polyline
          fill="none"
          stroke="#6366f1"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          points={points}
        />
      </svg>

      <div className="flex items-center gap-4 mt-1 text-[10px] text-theme-text-muted">
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-0.5 bg-indigo-500 rounded" /> Accuracy
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-0.5 bg-purple-400 rounded" /> Mastery
        </span>
        <span className="ml-auto">{maxQ} questions</span>
      </div>
    </div>
  );
}
