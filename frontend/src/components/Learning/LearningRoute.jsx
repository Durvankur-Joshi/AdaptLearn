import React from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { LearningProvider } from '../../context/LearningContext';
import TeachingFirstFlow from './TeachingFirstFlow';

const LearningRoute = () => {
    const { conceptId } = useParams();
    const navigate = useNavigate();
    const location = useLocation();
    const knowledgeLevel = location.state?.knowledge_level || 'intermediate';
    
    if (!conceptId) {
        return (
            <div className="min-h-screen bg-theme-bg flex items-center justify-center">
                <div className="text-center">
                    <p className="text-error mb-4">No concept selected.</p>
                    <button 
                        onClick={() => navigate('/dashboard')}
                        className="px-5 py-2.5 gradient-primary text-white rounded-theme font-semibold hover:opacity-90 transition-opacity"
                    >
                        Go to Dashboard
                    </button>
                </div>
            </div>
        );
    }

    return (
        <LearningProvider>
            <TeachingFirstFlow conceptId={parseInt(conceptId)} knowledgeLevel={knowledgeLevel} />
        </LearningProvider>
    );
};

export default LearningRoute;