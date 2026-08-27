// frontend/src/components/Learning/WeakTopicDetector.jsx
import React, { useState, useEffect } from 'react';
import { AlertCircle, Target, TrendingUp, BookOpen, RefreshCw } from 'lucide-react';
import { useLearning } from '../../context/LearningContext';

const WeakTopicDetector = ({ conceptData, sessionId, onReviewStart }) => {
  const [showDetails, setShowDetails] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const { fetchWeakTopics, weakTopics, loading } = useLearning();

  // Get color based on mastery score
  const getMasteryColor = (score) => {
    if (score >= 0.7) return 'text-emerald-500';
    if (score >= 0.5) return 'text-yellow-500';
    if (score >= 0.3) return 'text-orange-500';
    return 'text-error';
  };

  // Get background color based on mastery score
  const getMasteryBgColor = (score) => {
    if (score >= 0.7) return 'bg-emerald-500/10';
    if (score >= 0.5) return 'bg-yellow-500/10';
    if (score >= 0.3) return 'bg-orange-500/10';
    return 'bg-error/10';
  };

  // Get progress bar color
  const getProgressColor = (score) => {
    if (score >= 0.7) return 'bg-emerald-500';
    if (score >= 0.5) return 'bg-yellow-500';
    if (score >= 0.3) return 'bg-orange-500';
    return 'bg-error';
  };

  // If no concept data or no weakest atom, don't render
  if (!conceptData || !conceptData.weakest_atom) {
    return null;
  }

  const { weakest_atom, lowest_mastery, final_mastery, accuracy, passed } = conceptData;

  return (
    <div className="bg-surface rounded-theme-xl shadow-theme-lg border border-theme-border overflow-hidden animate-fade-in-up">
      {/* Header */}
      <div className="gradient-primary px-6 py-4 text-white flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Target className="w-6 h-6" />
          <div>
            <h3 className="font-semibold text-lg">Topic Mastery Analysis</h3>
            <p className="text-sm text-white/80">Personalized learning insights</p>
          </div>
        </div>
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="px-3 py-1 bg-white/20 rounded-theme-lg text-sm font-medium hover:bg-white/30 transition-colors"
        >
          {showDetails ? 'Hide Details' : 'View Details'}
        </button>
      </div>

      {/* Main Content */}
      <div className="p-6">
        {/* Overall Performance */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-surface-alt rounded-theme-lg p-4">
            <p className="text-sm text-theme-text-muted mb-1">Final Mastery</p>
            <p className="text-2xl font-bold text-theme-text">
              {Math.round(final_mastery * 100)}%
            </p>
            <div className="w-full h-2 bg-theme-border rounded-full mt-2">
              <div
                className="h-full bg-primary rounded-full transition-all duration-500"
                style={{ width: `${final_mastery * 100}%` }}
              />
            </div>
          </div>

          <div className="bg-surface-alt rounded-theme-lg p-4">
            <p className="text-sm text-theme-text-muted mb-1">Challenge Accuracy</p>
            <p className="text-2xl font-bold text-theme-text">
              {Math.round(accuracy * 100)}%
            </p>
            <div className="flex items-center gap-2 mt-2">
              <span className={`text-sm font-medium ${passed ? 'text-emerald-500' : 'text-error'}`}>
                {passed ? '✓ Passed' : '✗ Needs Work'}
              </span>
            </div>
          </div>

          <div className="bg-surface-alt rounded-theme-lg p-4">
            <p className="text-sm text-theme-text-muted mb-1">Concept Mastery</p>
            <p className="text-2xl font-bold text-theme-text">
              {Math.round(conceptData.concept_mastery * 100)}%
            </p>
            <p className="text-xs text-theme-text-muted mt-2">
              Average of all atoms
            </p>
          </div>
        </div>

        {/* Weakest Topic Alert */}
        <div className={`${getMasteryBgColor(lowest_mastery)} rounded-theme-lg p-5 border ${getMasteryColor(lowest_mastery).replace('text', 'border')}/20`}>
          <div className="flex items-start gap-4">
            <div className={`p-3 rounded-full ${getMasteryBgColor(lowest_mastery)}`}>
              <AlertCircle className={`w-6 h-6 ${getMasteryColor(lowest_mastery)}`} />
            </div>
            
            <div className="flex-1">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-semibold text-theme-text">Weakest Topic Identified</h4>
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${getMasteryBgColor(lowest_mastery)} ${getMasteryColor(lowest_mastery)}`}>
                  Priority Review
                </span>
              </div>
              
              <p className="text-lg font-bold text-theme-text mb-2">
                {weakest_atom}
              </p>
              
              <div className="flex items-center gap-4 mb-3">
                <div className="flex-1">
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-theme-text-muted">Current Mastery</span>
                    <span className={`font-medium ${getMasteryColor(lowest_mastery)}`}>
                      {Math.round(lowest_mastery * 100)}%
                    </span>
                  </div>
                  <div className="w-full h-2 bg-theme-border rounded-full overflow-hidden">
                    <div
                      className={`h-full ${getProgressColor(lowest_mastery)} transition-all duration-500`}
                      style={{ width: `${lowest_mastery * 100}%` }}
                    />
                  </div>
                </div>
                
                <button
                  onClick={() => onReviewStart?.(weakest_atom)}
                  className="px-4 py-2 gradient-primary text-white rounded-theme-lg text-sm font-medium hover:opacity-90 transition-opacity flex items-center gap-2"
                >
                  <RefreshCw className="w-4 h-4" />
                  Review Now
                </button>
              </div>

              {/* Recommendation */}
              <div className="mt-4 p-3 bg-theme-bg rounded-theme-lg border border-theme-border">
                <p className="text-sm text-theme-text">
                  {conceptData.recommendation}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Detailed Analysis (Conditional) */}
        {showDetails && (
          <div className="mt-6 animate-fade-in">
            <h4 className="font-semibold text-theme-text mb-3 flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-primary" />
              Learning Recommendations
            </h4>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-surface-alt rounded-theme-lg p-4">
                <h5 className="font-medium text-theme-text mb-2">Focus Areas</h5>
                <ul className="space-y-2">
                  <li className="flex items-start gap-2 text-sm text-theme-text-secondary">
                    <span className="text-primary mt-1">•</span>
                    <span>Review fundamental concepts of "{weakest_atom}"</span>
                  </li>
                  <li className="flex items-start gap-2 text-sm text-theme-text-secondary">
                    <span className="text-primary mt-1">•</span>
                    <span>Practice with targeted exercises</span>
                  </li>
                  <li className="flex items-start gap-2 text-sm text-theme-text-secondary">
                    <span className="text-primary mt-1">•</span>
                    <span>Watch video explanations for better understanding</span>
                  </li>
                </ul>
              </div>

              <div className="bg-surface-alt rounded-theme-lg p-4">
                <h5 className="font-medium text-theme-text mb-2">Mastery Gap</h5>
                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-theme-text-muted">Current</span>
                      <span className="text-orange-500">{Math.round(lowest_mastery * 100)}%</span>
                    </div>
                    <div className="w-full h-2 bg-theme-border rounded-full overflow-hidden">
                      <div className="h-full bg-orange-500" style={{ width: `${lowest_mastery * 100}%` }} />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-theme-text-muted">Target</span>
                      <span className="text-emerald-500">70%</span>
                    </div>
                    <div className="w-full h-2 bg-theme-border rounded-full overflow-hidden">
                      <div className="h-full bg-emerald-500" style={{ width: '70%' }} />
                    </div>
                  </div>
                  <p className="text-xs text-theme-text-muted mt-2">
                    Need to improve by {Math.max(0, 70 - lowest_mastery * 100).toFixed(0)}% to reach mastery
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default WeakTopicDetector;