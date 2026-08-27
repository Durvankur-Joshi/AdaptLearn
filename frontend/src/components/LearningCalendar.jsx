import React, { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from './Navbar';
import axios from '../axiosConfig';

const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const MONTH_NAMES = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

function buildMonthGrid(year, month) {
  const first = new Date(year, month - 1, 1);
  const daysInMonth = new Date(year, month, 0).getDate();
  const startWeekday = first.getDay();
  const totalCells = 42;
  const grid = [];
  let day = 1;
  for (let i = 0; i < totalCells; i++) {
    if (i < startWeekday || day > daysInMonth) {
      grid.push({ date: null, dateKey: null, dayNum: null });
    } else {
      const dateKey = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      grid.push({ date: new Date(year, month - 1, day), dateKey, dayNum: day });
      day++;
    }
  }
  return grid;
}

const LearningCalendar = () => {
  const navigate = useNavigate();
  const now = new Date();
  const [viewYear, setViewYear] = useState(now.getFullYear());
  const [viewMonth, setViewMonth] = useState(now.getMonth() + 1);
  const [data, setData] = useState({ days: {}, streak_days: [], streak_count: 0, this_week_summary: null });
  const [loading, setLoading] = useState(true);
  const [selectedDateKey, setSelectedDateKey] = useState(null);

  const todayKey = useMemo(() => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  }, []);

  useEffect(() => {
    const fetchCalendar = async () => {
      setLoading(true);
      try {
        const res = await axios.get('/auth/api/learning-calendar/', {
          params: { year: viewYear, month: viewMonth },
        });
        setData(res.data);
      } catch (err) {
        console.error('Failed to fetch calendar:', err);
        setData({ days: {}, streak_days: [], streak_count: 0, this_week_summary: null });
      } finally {
        setLoading(false);
      }
    };
    fetchCalendar();
  }, [viewYear, viewMonth]);

  const grid = useMemo(() => buildMonthGrid(viewYear, viewMonth), [viewYear, viewMonth]);

  const prevMonth = () => {
    if (viewMonth === 1) {
      setViewMonth(12);
      setViewYear(viewYear - 1);
    } else {
      setViewMonth(viewMonth - 1);
    }
    setSelectedDateKey(null);
  };

  const nextMonth = () => {
    if (viewMonth === 12) {
      setViewMonth(1);
      setViewYear(viewYear + 1);
    } else {
      setViewMonth(viewMonth + 1);
    }
    setSelectedDateKey(null);
  };

  const dayData = selectedDateKey ? (data.days && data.days[selectedDateKey]) : null;
  const streakSet = useMemo(() => new Set(data.streak_days || []), [data.streak_days]);

  if (loading && Object.keys(data.days || {}).length === 0) {
    return (
      <div className="min-h-screen bg-theme-bg flex items-center justify-center">
        <Navbar />
        <div className="text-center animate-fade-in mt-20">
          <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-theme-text-secondary font-medium">Loading calendar...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-theme-bg">
      <Navbar />

      <main className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="mb-6 animate-fade-in-up">
          <div className="flex flex-wrap items-center gap-4">
            <div>
              <h1 className="text-3xl font-bold text-theme-text">Learning Calendar</h1>
              <p className="text-theme-text-secondary mt-1">Day-wise learning path and activity</p>
            </div>
            {data.streak_count != null && data.streak_count > 0 && (
              <div className="px-4 py-2 rounded-theme-lg bg-amber-500/10 border border-amber-500/30">
                <span className="text-sm font-medium text-amber-700 dark:text-amber-400">Current streak: {data.streak_count} day{data.streak_count !== 1 ? 's' : ''}</span>
              </div>
            )}
          </div>
        </div>

        {/* This week strip */}
        {data.this_week_summary && (
          <div className="mb-6 p-4 rounded-theme-xl bg-surface border border-theme-border">
            <p className="text-sm font-medium text-theme-text">
              This week: <span className="font-semibold text-primary">{data.this_week_summary.sessions}</span> session{data.this_week_summary.sessions !== 1 ? 's' : ''} completed, <span className="font-semibold text-amber-600 dark:text-amber-400">{data.this_week_summary.suggested}</span> suggested.
            </p>
            <button
              type="button"
              onClick={() => setSelectedDateKey(todayKey)}
              className="mt-2 text-sm text-primary font-medium hover:underline"
            >
              Jump to today
            </button>
          </div>
        )}

        {/* Today summary strip */}
        {data.days && data.days[todayKey] && (
          <div className="mb-6 p-4 rounded-theme-xl bg-primary/10 border border-primary/20">
            <p className="text-sm font-medium text-theme-text">
              Today: {(data.days[todayKey].sessions || []).length} session(s) completed.
              {(data.days[todayKey].review_due || []).length + (data.days[todayKey].suggested || []).length > 0 && (
                <span className="ml-1">
                  {(data.days[todayKey].review_due || []).length + (data.days[todayKey].suggested || []).length} suggested.
                </span>
              )}
            </p>
            <button
              type="button"
              onClick={() => setSelectedDateKey(todayKey)}
              className="mt-2 text-sm text-primary font-medium hover:underline"
            >
              View today&apos;s detail
            </button>
          </div>
        )}

        {/* Month navigation */}
        <div className="flex items-center justify-between mb-4">
          <button
            type="button"
            onClick={prevMonth}
            className="px-3 py-2 rounded-theme bg-surface border border-theme-border text-theme-text font-medium hover:bg-surface-alt transition-colors"
          >
            Previous
          </button>
          <h2 className="text-xl font-bold text-theme-text">
            {MONTH_NAMES[viewMonth - 1]} {viewYear}
          </h2>
          <button
            type="button"
            onClick={nextMonth}
            className="px-3 py-2 rounded-theme bg-surface border border-theme-border text-theme-text font-medium hover:bg-surface-alt transition-colors"
          >
            Next
          </button>
        </div>

        {/* Calendar grid */}
        <div className="bg-surface rounded-theme-xl border border-theme-border overflow-hidden shadow-theme">
          <div className="grid grid-cols-7">
            {WEEKDAYS.map((wd) => (
              <div
                key={wd}
                className="py-2 text-center text-xs font-semibold text-theme-text-secondary border-b border-r border-theme-border last:border-r-0 bg-surface-alt"
              >
                {wd}
              </div>
            ))}
            {grid.map((cell, idx) => {
              const isCurrentMonth = cell.dateKey !== null;
              const isToday = cell.dateKey === todayKey;
              const isStreak = cell.dateKey && streakSet.has(cell.dateKey);
              const d = data.days && cell.dateKey ? data.days[cell.dateKey] : null;
              const sessionCount = d && d.sessions ? d.sessions.length : 0;
              const hasDueOrSuggested = d && ((d.review_due && d.review_due.length > 0) || (d.suggested && d.suggested.length > 0));
              const isSelected = selectedDateKey === cell.dateKey;

              return (
                <button
                  key={idx}
                  type="button"
                  onClick={() => cell.dateKey && setSelectedDateKey(cell.dateKey)}
                  disabled={!cell.dateKey}
                  className={`
                    min-h-[80px] p-2 border-r border-b border-theme-border last:border-r-0 text-left
                    ${!isCurrentMonth ? 'bg-surface-alt/50 text-theme-text-muted' : 'bg-surface text-theme-text hover:bg-surface-alt'}
                    ${isToday ? 'ring-2 ring-primary ring-inset' : ''}
                    ${isStreak && isCurrentMonth ? 'border-l-2 border-l-amber-500' : ''}
                    ${isSelected ? 'bg-primary/10 ring-2 ring-primary' : ''}
                  `}
                >
                  {cell.dayNum != null && <span className="text-sm font-medium">{cell.dayNum}</span>}
                  {isCurrentMonth && d && (
                    <div className="mt-1 flex flex-wrap gap-0.5">
                      {sessionCount > 0 && (
                        <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-xs font-medium" title={`${sessionCount} session(s)`}>
                          {sessionCount}
                        </span>
                      )}
                      {hasDueOrSuggested && (
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-500" title="Review or suggested" />
                      )}
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Day detail panel */}
        {selectedDateKey && (
          <div className="mt-6 p-6 bg-surface rounded-theme-xl border border-theme-border shadow-theme">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-bold text-theme-text">
                {selectedDateKey}
                {selectedDateKey === todayKey && <span className="ml-2 text-sm font-normal text-primary">(Today)</span>}
              </h3>
              <button
                type="button"
                onClick={() => setSelectedDateKey(null)}
                className="text-sm text-theme-text-secondary hover:text-theme-text"
              >
                Close
              </button>
            </div>

            {!dayData && <p className="text-theme-text-secondary text-sm">No activity or suggestions for this day.</p>}

            {dayData && dayData.sessions && dayData.sessions.length > 0 && (
              <section className="mb-4">
                <h4 className="text-sm font-semibold text-theme-text mb-2">Sessions completed</h4>
                <ul className="space-y-2">
                  {dayData.sessions.map((s) => (
                    <li key={s.id} className="text-sm p-2 rounded-theme bg-surface-alt border border-theme-border">
                      <span className="font-medium text-theme-text">{s.concept_name}</span>
                      <span className="text-theme-text-muted ml-1">({s.subject})</span>
                      {s.duration_mins != null && <span className="text-theme-text-muted ml-1">· {s.duration_mins} min</span>}
                      {s.questions_answered != null && <span className="text-theme-text-muted ml-1">· {s.questions_answered} questions, {s.correct_answers} correct</span>}
                      {s.accuracy != null && <span className="text-theme-text-muted ml-1">· {Math.round(s.accuracy * 100)}% accuracy</span>}
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {dayData && dayData.review_due && dayData.review_due.length > 0 && (
              <section className="mb-4">
                <h4 className="text-sm font-semibold text-theme-text mb-2">Review due</h4>
                <ul className="space-y-2">
                  {dayData.review_due.map((r) => (
                    <li key={`${r.concept_id}-${r.atom_id}`} className="flex items-center justify-between text-sm p-2 rounded-theme bg-surface-alt border border-theme-border">
                      <span className="text-theme-text">{r.atom_name} ({r.concept_name}) · mastery {Math.round((r.mastery_score || 0) * 100)}%</span>
                      <button
                        type="button"
                        onClick={() => navigate(`/learn/${r.concept_id}`)}
                        className="px-2 py-1 rounded-theme bg-primary/20 text-primary font-medium hover:bg-primary/30 text-xs"
                      >
                        Start
                      </button>
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {dayData && dayData.suggested && dayData.suggested.length > 0 && (
              <section>
                <h4 className="text-sm font-semibold text-theme-text mb-2">Suggested</h4>
                <ul className="space-y-2">
                  {dayData.suggested.map((s, i) => (
                    <li key={s.concept_id + (s.atom_id || '') + i} className="flex items-center justify-between text-sm p-2 rounded-theme bg-surface-alt border border-theme-border">
                      <span className="text-theme-text">{s.atom_name} ({s.concept_name})</span>
                      <button
                        type="button"
                        onClick={() => navigate(`/learn/${s.concept_id}`)}
                        className="px-2 py-1 rounded-theme bg-primary/20 text-primary font-medium hover:bg-primary/30 text-xs"
                      >
                        Start
                      </button>
                    </li>
                  ))}
                </ul>
              </section>
            )}
          </div>
        )}
      </main>
    </div>
  );
};

export default LearningCalendar;
