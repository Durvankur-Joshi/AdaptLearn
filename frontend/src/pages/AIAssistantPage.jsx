// frontend/src/components/AIAssistantWidget.jsx
import React, { useState, useRef, useEffect } from 'react';
import axios from '../axiosConfig';

// Helper function to format AI responses
const formatAIResponse = (text) => {
  if (!text) return text;

  // Check if the response already has markdown-style formatting
  const hasFormatting = text.includes('**') || text.includes('*') || text.includes('#');
  
  if (!hasFormatting) {
    // If no formatting, try to detect and add structure
    return text;
  }

  // Convert markdown-style formatting to HTML/JSX
  let formatted = text
    // Headers
    .replace(/^### (.*$)/gim, '<h3 class="text-lg font-bold text-primary mt-4 mb-2">$1</h3>')
    .replace(/^## (.*$)/gim, '<h2 class="text-xl font-bold text-primary mt-5 mb-3">$1</h2>')
    .replace(/^# (.*$)/gim, '<h1 class="text-2xl font-bold text-primary mt-6 mb-4">$1</h1>')
    
    // Bold
    .replace(/\*\*(.*?)\*\*/gim, '<strong class="font-bold text-theme-text">$1</strong>')
    
    // Italic
    .replace(/\*(.*?)\*/gim, '<em class="italic text-theme-text-secondary">$1</em>')
    
    // Bullet points
    .replace(/^\* (.*$)/gim, '<li class="flex items-start gap-2 ml-4 mb-1"><span class="text-primary mt-1">•</span><span>$1</span></li>')
    .replace(/^- (.*$)/gim, '<li class="flex items-start gap-2 ml-4 mb-1"><span class="text-primary mt-1">•</span><span>$1</span></li>')
    
    // Numbered lists
    .replace(/^(\d+)\. (.*$)/gim, '<li class="flex items-start gap-2 ml-4 mb-1"><span class="text-primary font-medium mt-1">$1.</span><span>$2</span></li>')
    
    // Code blocks
    .replace(/```([\s\S]*?)```/gim, '<pre class="bg-surface-alt p-3 rounded-theme-lg font-mono text-sm overflow-x-auto my-3 border border-theme-border">$1</pre>')
    
    // Inline code
    .replace(/`(.*?)`/gim, '<code class="bg-surface-alt px-1.5 py-0.5 rounded font-mono text-sm text-primary border border-theme-border">$1</code>')
    
    // Tables (basic)
    .replace(/\|(.*)\|/gim, (match, content) => {
      const cells = content.split('|').map(cell => cell.trim());
      if (cells.some(cell => cell.includes('---'))) return ''; // Skip separator rows
      return `<tr class="border-b border-theme-border">${cells.map(cell => `<td class="px-3 py-2">${cell}</td>`).join('')}</tr>`;
    });

  // Add paragraph breaks
  formatted = formatted
    .split('\n\n')
    .map(para => para.trim())
    .filter(para => para.length > 0)
    .map(para => {
      // Don't wrap if it's already HTML
      if (para.startsWith('<') && para.endsWith('>')) return para;
      return `<p class="mb-3 leading-relaxed">${para}</p>`;
    })
    .join('');

  return formatted;
};

// Component to render formatted AI message
const FormattedAIMessage = ({ text }) => {
  const formattedText = formatAIResponse(text);
  
  return (
    <div 
      className="prose prose-sm max-w-none"
      dangerouslySetInnerHTML={{ __html: formattedText }}
    />
  );
};

const AIAssistantpage = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [topic, setTopic] = useState('General');
  const [level, setLevel] = useState('Beginner');
  const [showSettings, setShowSettings] = useState(false);
  const messagesEndRef = useRef(null);
  const widgetRef = useRef(null);
  const buttonRef = useRef(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Close on click outside (but not on the button)
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (buttonRef.current && buttonRef.current.contains(event.target)) {
        return;
      }
      
      if (widgetRef.current && !widgetRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const toggleAssistant = () => {
    setIsOpen(!isOpen);
  };

  const closeAssistant = (e) => {
    if (e) e.stopPropagation();
    setIsOpen(false);
  };

  const handleAsk = async () => {
    if (!question.trim()) return;

    const userMessage = { role: 'user', text: question };
    setMessages(prev => [...prev, userMessage]);
    setQuestion('');
    setLoading(true);

    try {
      const response = await axios.post('/auth/ai-assistant/', {
        question: question,
        topic: topic,
        level: level
      });

      setMessages(prev => [
        ...prev,
        { 
          role: 'ai', 
          text: response.data.ai_answer,
          isFormatted: true // Mark as formatted
        }
      ]);
    } catch (error) {
      console.error('AI Assistant error:', error);
      setMessages(prev => [
        ...prev,
        {
          role: 'ai',
          text: 'Sorry, I encountered an error. Please try again.',
          isError: true
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleAsk();
    }
  };

  const clearChat = (e) => {
    e.stopPropagation();
    setMessages([]);
    setShowSettings(false);
  };

  const toggleSettings = (e) => {
    e.stopPropagation();
    setShowSettings(!showSettings);
  };

  const handleTopicChange = (e) => {
    e.stopPropagation();
    setTopic(e.target.value);
  };

  const handleLevelChange = (e) => {
    e.stopPropagation();
    setLevel(e.target.value);
  };

  return (
    <>
      {/* Floating Robot Button */}
      <button
        ref={buttonRef}
        onClick={toggleAssistant}
        className={`fixed bottom-6 right-6 w-14 h-14 gradient-primary rounded-full flex items-center justify-center text-white text-2xl shadow-theme-lg hover:scale-110 transition-all duration-300 z-50 ${
          isOpen ? 'rotate-90' : ''
        }`}
        aria-label="AI Assistant"
      >
        {isOpen ? '✕' : '🤖'}
      </button>

      {/* Assistant Panel */}
      {isOpen && (
        <div
          ref={widgetRef}
          onClick={(e) => e.stopPropagation()}
          className="fixed bottom-24 right-6 w-96 max-w-[calc(100vw-2rem)] bg-surface rounded-theme-xl shadow-theme-xl border border-theme-border overflow-hidden animate-slide-in-right z-50 flex flex-col"
          style={{ maxHeight: 'min(600px, 80vh)' }}
        >
          {/* Header */}
          <div className="gradient-primary px-4 py-3 text-white flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xl">🤖</span>
              <div>
                <h3 className="font-semibold">AI Doubt Assistant</h3>
                <p className="text-xs text-white/80">Ask anything, get instant help</p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={toggleSettings}
                className="w-8 h-8 hover:bg-white/20 rounded-lg flex items-center justify-center transition-colors"
                title="Settings"
              >
                ⚙️
              </button>
              <button
                onClick={clearChat}
                className="w-8 h-8 hover:bg-white/20 rounded-lg flex items-center justify-center transition-colors"
                title="Clear chat"
              >
                🗑️
              </button>
              <button
                onClick={closeAssistant}
                className="w-8 h-8 hover:bg-white/20 rounded-lg flex items-center justify-center transition-colors"
                title="Close"
              >
                ✕
              </button>
            </div>
          </div>

          {/* Settings Panel */}
          {showSettings && (
            <div className="p-4 border-b border-theme-border bg-surface-alt animate-fade-in">
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-theme-text-secondary mb-1">
                    Topic / Subject
                  </label>
                  <input
                    type="text"
                    value={topic}
                    onChange={handleTopicChange}
                    onClick={(e) => e.stopPropagation()}
                    placeholder="e.g., Programming, Mathematics"
                    className="w-full px-3 py-2 bg-surface border border-theme-border rounded-theme-lg text-sm focus:ring-2 focus:ring-primary/50 focus:border-primary text-theme-text placeholder:text-theme-text-muted"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-theme-text-secondary mb-1">
                    Your Level
                  </label>
                  <select
                    value={level}
                    onChange={handleLevelChange}
                    onClick={(e) => e.stopPropagation()}
                    className="w-full px-3 py-2 bg-surface border border-theme-border rounded-theme-lg text-sm focus:ring-2 focus:ring-primary/50 focus:border-primary text-theme-text"
                  >
                    <option value="Beginner">Beginner</option>
                    <option value="Intermediate">Intermediate</option>
                    <option value="Advanced">Advanced</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-[300px] max-h-[400px]">
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-4">
                <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center text-3xl mb-3">
                  💭
                </div>
                <p className="text-theme-text-secondary text-sm mb-4">
                  Ask me anything about your studies!
                </p>
                <div className="space-y-2 w-full">
                  {[
                    "Explain the difference between for and while loops",
                    "What is a closure in JavaScript?",
                    "How does React useState work?"
                  ].map((suggestion) => (
                    <button
                      key={suggestion}
                      onClick={(e) => {
                        e.stopPropagation();
                        setQuestion(suggestion);
                        setTimeout(() => handleAsk(), 100);
                      }}
                      className="w-full p-2 text-left text-sm bg-surface-alt hover:bg-primary/10 text-theme-text-secondary rounded-theme-lg transition-colors border border-theme-border"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <>
                {messages.map((msg, index) => (
                  <div
                    key={index}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in-up`}
                    style={{ animationDelay: `${index * 50}ms` }}
                    onClick={(e) => e.stopPropagation()}
                  >
                    <div
                      className={`max-w-[85%] rounded-theme-lg p-3 ${
                        msg.role === 'user'
                          ? 'gradient-primary text-white'
                          : msg.isError
                          ? 'bg-error/10 border border-error/30 text-error'
                          : 'bg-surface-alt border border-theme-border text-theme-text'
                      }`}
                    >
                      {msg.role === 'ai' && !msg.isError && (
                        <div className="flex items-center gap-1 mb-2">
                          <span className="text-sm">🤖</span>
                          <span className="text-xs font-medium text-theme-text-muted">AI</span>
                        </div>
                      )}
                      
                      {msg.role === 'ai' && msg.isFormatted ? (
                        <FormattedAIMessage text={msg.text} />
                      ) : (
                        <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.text}</p>
                      )}
                    </div>
                  </div>
                ))}
                {loading && (
                  <div className="flex justify-start animate-fade-in">
                    <div className="bg-surface-alt border border-theme-border rounded-theme-lg p-3">
                      <div className="flex items-center gap-2">
                        <span className="text-sm">🤖</span>
                        <div className="flex gap-1">
                          <span className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                          <span className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                          <span className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="p-4 border-t border-theme-border bg-surface-alt">
            <div className="flex gap-2">
              <textarea
                value={question}
                onChange={(e) => {
                  e.stopPropagation();
                  setQuestion(e.target.value);
                }}
                onKeyPress={handleKeyPress}
                onClick={(e) => e.stopPropagation()}
                placeholder="Type your doubt... (Enter to send)"
                className="flex-1 p-2 bg-surface border border-theme-border rounded-theme-lg text-sm resize-none focus:ring-2 focus:ring-primary/50 focus:border-primary text-theme-text placeholder:text-theme-text-muted"
                rows="2"
                disabled={loading}
              />
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleAsk();
                }}
                disabled={loading || !question.trim()}
                className={`px-4 py-2 gradient-primary text-white rounded-theme-lg font-medium self-end transition-all ${
                  loading || !question.trim()
                    ? 'opacity-50 cursor-not-allowed'
                    : 'hover:shadow-theme hover:scale-105'
                }`}
              >
                {loading ? '...' : 'Send'}
              </button>
            </div>
            <p className="text-xs text-theme-text-muted mt-2">
              AI responses are tailored to your selected level
            </p>
          </div>
        </div>
      )}
    </>
  );
};

export default AIAssistantpage;