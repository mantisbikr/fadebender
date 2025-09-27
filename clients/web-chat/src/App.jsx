/**
 * Main App Component
 * Orchestrates the chat interface
 */

import { useEffect } from 'react';
import ChatMessage from './components/ChatMessage.jsx';
import ChatInput from './components/ChatInput.jsx';
import { useDAWControl } from './hooks/useDAWControl.js';

function App() {
  const {
    messages,
    isProcessing,
    systemStatus,
    conversationContext,
    modelPref,
    setModelPref,
    processControlCommand,
    processHelpQuery,
    checkSystemHealth,
    clearMessages
  } = useDAWControl();

  useEffect(() => {
    checkSystemHealth();
  }, [checkSystemHealth]);

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-4 py-3">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-xl font-bold text-gray-900">🎛️ Fadebender</h1>
            <p className="text-sm text-gray-600">AI-Powered DAW Control</p>
          </div>
          <div className="flex gap-2 items-center">
            <div className={`px-2 py-1 rounded text-xs ${
              systemStatus?.status === 'healthy'
                ? 'bg-green-100 text-green-800'
                : 'bg-red-100 text-red-800'
            }`}>
              {systemStatus?.status || 'connecting...'}
            </div>

            <div className={`px-2 py-1 rounded text-xs ${
              systemStatus?.ai_parser_available
                ? 'bg-blue-100 text-blue-800'
                : 'bg-yellow-100 text-yellow-800'
            }`}>
              AI: {systemStatus?.ai_parser_available ? '🧠 Active' : '⚠️ Fallback'}
            </div>

            <div className="flex items-center gap-1 text-xs text-gray-700">
              <span>Model:</span>
              <select
                value={modelPref}
                onChange={(e) => setModelPref(e.target.value)}
                className="text-xs border rounded px-1 py-1 bg-white"
                disabled={isProcessing}
                title="LLM model preference"
              >
                <option value="gemini-2.5-flash">Gemini Flash</option>
                <option value="llama">Llama 8B</option>
              </select>
            </div>

            {conversationContext && (
              <div className="px-2 py-1 rounded text-xs bg-purple-100 text-purple-800">
                🤔 Awaiting clarification
              </div>
            )}

            <button
              onClick={clearMessages}
              className="px-3 py-1 text-xs bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
            >
              Clear
            </button>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 mt-8">
            <h2 className="text-lg font-medium mb-2">Welcome to Fadebender!</h2>
            <p className="mb-4">Control your DAW with natural language commands.</p>
            <div className="text-sm space-y-1">
              <p><strong>Try:</strong> "set track 1 volume to -6 dB"</p>
              <p><strong>Or:</strong> "pan track 2 left by 20%"</p>
              <p><strong>Help:</strong> "how to sidechain in Ableton?"</p>
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))
        )}

        {isProcessing && (
          <div className="flex items-center justify-center py-4">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
            <span className="ml-2 text-gray-600">Processing...</span>
          </div>
        )}
      </div>

      {/* Input */}
      <ChatInput
        onSubmit={processControlCommand}
        onHelp={processHelpQuery}
        disabled={isProcessing}
        model={modelPref}
        onModelChange={setModelPref}
      />
    </div>
  );
}

export default App;
