// frontend/src/components/Learning/ExternalResources.jsx

import React, { useState, useEffect } from 'react';
import axios from '../../axiosConfig';

const ExternalResources = ({ subject, concept, atomName }) => {
    const [resources, setResources] = useState({ videos: [], images: [] });
    const [loading, setLoading] = useState(false);
    const [activeTab, setActiveTab] = useState('videos');

    useEffect(() => {
        if (subject && concept) {
            fetchResources();
        }
    }, [subject, concept, atomName]);

    const fetchResources = async () => {
        setLoading(true);
        try {
            const response = await axios.post('/auth/api/concept-resources/', {
                subject: subject,
                concept: concept,
                atom_name: atomName
            });
            setResources(response.data);
        } catch (error) {
            console.error('Failed to fetch resources:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="text-center py-4">
                <p className="text-theme-text-muted">Loading additional resources...</p>
            </div>
        );
    }

    if (!resources.videos.length && !resources.images.length) {
        return null;
    }

    return (
        <div className="bg-surface rounded-theme-xl shadow-theme border border-theme-border p-6 mt-6">
            <h3 className="text-xl font-semibold text-theme-text mb-4">Additional Learning Resources</h3>
            
            {/* Tabs */}
            <div className="flex border-b border-theme-border mb-4">
                {resources.videos.length > 0 && (
                    <button
                        className={`px-4 py-2 font-medium transition-colors ${
                            activeTab === 'videos'
                                ? 'text-primary border-b-2 border-primary'
                                : 'text-theme-text-muted hover:text-theme-text'
                        }`}
                        onClick={() => setActiveTab('videos')}
                    >
                        Videos ({resources.videos.length})
                    </button>
                )}
                {resources.images.length > 0 && (
                    <button
                        className={`px-4 py-2 font-medium transition-colors ${
                            activeTab === 'images'
                                ? 'text-primary border-b-2 border-primary'
                                : 'text-theme-text-muted hover:text-theme-text'
                        }`}
                        onClick={() => setActiveTab('images')}
                    >
                        Diagrams ({resources.images.length})
                    </button>
                )}
            </div>

            {/* Videos Tab */}
            {activeTab === 'videos' && resources.videos.length > 0 && (
                <div className="space-y-4">
                    {resources.videos.map((video, index) => (
                        <div key={index} className="border border-theme-border rounded-theme-lg p-4 hover:bg-surface-alt/50 transition-colors">
                            <a
                                href={video.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="block"
                            >
                                <h4 className="font-semibold text-primary hover:underline">
                                    {video.title}
                                </h4>
                                <div className="flex items-center text-sm text-theme-text-muted mt-2">
                                    <span className="mr-4">📺 {video.channel}</span>
                                    <span className="mr-4">⏱️ {video.duration}</span>
                                    {video.views && <span>👁️ {video.views}</span>}
                                </div>
                            </a>
                        </div>
                    ))}
                </div>
            )}

            {/* Images Tab */}
            {activeTab === 'images' && resources.images.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {resources.images.map((image, index) => (
                        <div key={index} className="border border-theme-border rounded-theme-lg overflow-hidden hover:shadow-theme transition-shadow">
                            <a
                                href={image.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="block"
                            >
                                <img
                                    src={image.thumbnail || image.url}
                                    alt={image.title}
                                    className="w-full h-48 object-cover"
                                    onError={(e) => {
                                        e.target.onerror = null;
                                        e.target.src = 'https://via.placeholder.com/300x200?text=Image+Not+Available';
                                    }}
                                />
                                <div className="p-3">
                                    <p className="text-sm text-theme-text truncate">{image.title}</p>
                                    <p className="text-xs text-theme-text-muted mt-1">Source: {image.source}</p>
                                </div>
                            </a>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default ExternalResources;