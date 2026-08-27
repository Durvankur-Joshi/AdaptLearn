import React from 'react';
import { BrowserRouter as Router, Routes, Route, Outlet } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { TeacherProvider } from './context/TeacherContext';
import Home from './components/Home';
import Login from './components/Login';
import Register from './components/Register';
import Dashboard from './components/Dashboard';
import ProtectedRoute from './components/ProtectedRoute';
import LearningRoute from './components/Learning/LearningRoute';
import StartAnyConceptSessionRoute from './components/Learning/StartAnyConceptSessionRoute';
import Leaderboard from './components/Leaderboard';
import Progress from './components/Progress';
import LearningCalendar from './components/LearningCalendar';
import AIAssistantPage from './pages/AIAssistantPage.jsx';

// Teacher imports
import TeacherLogin from './components/Teacher/TeacherLogin';
import TeacherRegister from './components/Teacher/TeacherRegister';
import TeacherDashboard from './components/Teacher/TeacherDashboard';
import StudentAnalytics from './components/Teacher/StudentAnalytics';
import ContentManagement from './components/Teacher/ContentManagement';
import QuestionManagement from './components/Teacher/QuestionManagement';
import ClassAnalytics from './components/Teacher/ClassAnalytics';
import GoalsManagement from './components/Teacher/GoalsManagement';
import TeacherProtectedRoute from './components/Teacher/TeacherProtectedRoute';

// Parent imports
import { ParentProvider } from './context/ParentContext';
import ParentLogin from './components/Parent/ParentLogin';
import ParentRegister from './components/Parent/ParentRegister';
import ParentDashboard from './components/Parent/ParentDashboard';
import ParentChildInsights from './components/Parent/ParentChildInsights';
import ParentProtectedRoute from './components/Parent/ParentProtectedRoute';
// StudyPlanner import
import StudyPlanner from './components/Planner/StudyPlanner';

function App() {
    return (
        <ThemeProvider>
            <Router>
                <AuthProvider>
                    <Routes>
                        {/* Student Routes */}
                        <Route path="/" element={<Home />} />
                        <Route path="/login" element={<Login />} />
                        <Route path="/register" element={<Register />} />

                        <Route
                            path="/dashboard"
                            element={
                                <ProtectedRoute>
                                    <Dashboard />
                                </ProtectedRoute>
                            }
                        />

                        <Route
                            path="/leaderboard"
                            element={
                                <ProtectedRoute>
                                    <Leaderboard />
                                </ProtectedRoute>
                            }
                        />

                        <Route
                            path="/progress"
                            element={
                                <ProtectedRoute>
                                    <Progress />
                                </ProtectedRoute>
                            }
                        />

                        <Route
                            path="/calendar"
                            element={
                                <ProtectedRoute>
                                    <LearningCalendar />
                                </ProtectedRoute>
                            }
                        />

                        <Route
                            path="/learn/:conceptId"
                            element={
                                <ProtectedRoute>
                                    <LearningRoute />
                                </ProtectedRoute>
                            }
                        />

                        <Route
                            path="/learn/start"
                            element={
                                <ProtectedRoute>
                                    <StartAnyConceptSessionRoute />
                                </ProtectedRoute>
                            }
                        />

                        {/* Teacher Routes — single shared TeacherProvider */}
                        <Route element={<TeacherProvider><Outlet /></TeacherProvider>}>
                            <Route path="/teacher/login" element={<TeacherLogin />} />
                            <Route path="/teacher/register" element={<TeacherRegister />} />
                            <Route path="/teacher/dashboard" element={
                                <TeacherProtectedRoute><TeacherDashboard /></TeacherProtectedRoute>
                            } />
                            <Route path="/teacher/students" element={
                                <TeacherProtectedRoute><StudentAnalytics /></TeacherProtectedRoute>
                            } />
                            <Route path="/teacher/content" element={
                                <TeacherProtectedRoute><ContentManagement /></TeacherProtectedRoute>
                            } />
                            <Route path="/teacher/questions" element={
                                <TeacherProtectedRoute><QuestionManagement /></TeacherProtectedRoute>
                            } />
                            <Route path="/teacher/analytics" element={
                                <TeacherProtectedRoute><ClassAnalytics /></TeacherProtectedRoute>
                            } />
                            <Route path="/teacher/goals" element={
                                <TeacherProtectedRoute><GoalsManagement /></TeacherProtectedRoute>
                            } />
                        </Route>

                        {/* Parent Routes */}
                        <Route element={<ParentProvider><Outlet /></ParentProvider>}>
                            <Route path="/parent/login" element={<ParentLogin />} />
                            <Route path="/parent/register" element={<ParentRegister />} />
                            <Route path="/parent/dashboard" element={
                                <ParentProtectedRoute><ParentDashboard /></ParentProtectedRoute>
                            } />
                            <Route path="/parent/child/:childId/insights" element={
                                <ParentProtectedRoute><ParentChildInsights /></ParentProtectedRoute>
                            } />
                        </Route>
                        {/* Teacher Routes */}
                        <Route path="/teacher/login" element={
                            <TeacherProvider><TeacherLogin /></TeacherProvider>
                        } />
                        <Route path="/teacher/register" element={
                            <TeacherProvider><TeacherRegister /></TeacherProvider>
                        } />
                        <Route path="/teacher/dashboard" element={
                            <TeacherProvider><TeacherProtectedRoute><TeacherDashboard /></TeacherProtectedRoute></TeacherProvider>
                        } />
                        <Route path="/teacher/students" element={
                            <TeacherProvider><TeacherProtectedRoute><StudentAnalytics /></TeacherProtectedRoute></TeacherProvider>
                        } />
                        <Route path="/teacher/content" element={
                            <TeacherProvider><TeacherProtectedRoute><ContentManagement /></TeacherProtectedRoute></TeacherProvider>
                        } />
                        <Route path="/teacher/questions" element={
                            <TeacherProvider><TeacherProtectedRoute><QuestionManagement /></TeacherProtectedRoute></TeacherProvider>
                        } />
                        <Route path="/teacher/analytics" element={
                            <TeacherProvider><TeacherProtectedRoute><ClassAnalytics /></TeacherProtectedRoute></TeacherProvider>
                        } />
                        <Route path="/teacher/goals" element={
                            <TeacherProvider><TeacherProtectedRoute><GoalsManagement /></TeacherProtectedRoute></TeacherProvider>
                        } />
                        <Route
                            path="/planner"
                            element={
                                <ProtectedRoute>
                                    <StudyPlanner />
                                </ProtectedRoute>
                            }
                        />
                    </Routes>
                    <AIAssistantPage />
                </AuthProvider>
            </Router>
        </ThemeProvider>
    );
}

export default App; 