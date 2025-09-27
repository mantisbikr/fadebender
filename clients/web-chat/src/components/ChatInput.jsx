/**
 * ChatInput Component
 * Handles user input with validation and submission
 */

import { useState } from 'react';

export default function ChatInput({ onSubmit, onHelp, disabled, model, onModelChange }) {
  const [input, setInput] = useState('');
  const [mode, setMode] = useState('control'); // 'control' or 'help'

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || disabled) return;

    if (mode === 'control') {
      onSubmit(input.trim());
    } else {
      onHelp(input.trim());
    }

    setInput('');
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="border-t bg-white p-4">
      <div className="flex gap-2 mb-3 items-center justify-between">
        <div className="flex gap-2">
          <button
          type="button"
          onClick={() => setMode('control')}
          className={`px-3 py-1 rounded text-sm font-medium ${
            mode === 'control'
              ? 'bg-blue-500 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
          >
            🎛️ Control
          </button>
          <button
          type="button"
          onClick={() => setMode('help')}
          className={`px-3 py-1 rounded text-sm font-medium ${
            mode === 'help'
              ? 'bg-green-500 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
          >
            ❓ Help
          </button>
        </div>

        <div className="flex items-center gap-2 text-xs text-gray-700">
          <span>Model:</span>
          <select
            value={model}
            onChange={(e) => onModelChange?.(e.target.value)}
            className="text-xs border rounded px-2 py-1 bg-white"
            disabled={disabled}
          >
            <option value="gemini-2.5-flash">Gemini Flash</option>
            <option value="llama">Llama 8B</option>
          </select>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={
            mode === 'control'
              ? 'e.g., "set track 1 volume to -6 dB"'
              : 'e.g., "how to sidechain in Ableton?"'
          }
          disabled={disabled}
          autoCorrect="off"
          autoCapitalize="off"
          spellCheck="false"
          className="flex-1 p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
        />
        <button
          type="submit"
          disabled={!input.trim() || disabled}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          {mode === 'control' ? 'Execute' : 'Ask'}
        </button>
      </form>

      <div className="text-xs text-gray-500 mt-2">
        {mode === 'control'
          ? 'AI will understand your intent • Press Enter to execute'
          : 'Ask questions about DAW techniques • Press Enter to ask'
        }
      </div>
    </div>
  );
}
