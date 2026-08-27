import React from 'react';
import { LearningProvider } from '../../context/LearningContext';
import StartAnyConceptSession from './StartAnyConceptSession';

const StartAnyConceptSessionRoute = () => {
    return (
        <LearningProvider>
            <StartAnyConceptSession />
        </LearningProvider>
    );
};

export default StartAnyConceptSessionRoute;