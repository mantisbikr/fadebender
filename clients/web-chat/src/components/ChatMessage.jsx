/**
 * ChatMessage Component
 * Displays individual chat messages with different types
 */

export default function ChatMessage({ message }) {
  const getMessageStyle = () => {
    switch (message.type) {
      case 'user':
        return 'bg-blue-100 border-blue-300 text-blue-900 ml-8';
      case 'success':
        return 'bg-green-100 border-green-300 text-green-900 mr-8';
      case 'error':
        return 'bg-red-100 border-red-300 text-red-900 mr-8';
      case 'info':
        return 'bg-gray-100 border-gray-300 text-gray-700 mr-8';
      case 'question':
        return 'bg-purple-100 border-purple-300 text-purple-900 mr-8';
      default:
        return 'bg-white border-gray-300 text-gray-900';
    }
  };

  const formatContent = () => {
    if (message.type === 'success' && message.data) {
      return (
        <div>
          <div className="font-medium mb-2">{message.content}</div>
          <details className="text-sm">
            <summary className="cursor-pointer text-gray-600">View Details</summary>
            <pre className="mt-2 p-2 bg-gray-50 rounded text-xs overflow-auto">
              {JSON.stringify(message.data, null, 2)}
            </pre>
          </details>
        </div>
      );
    }

    if (message.type === 'question') {
      return (
        <div>
          <div className="flex items-center mb-2">
            <span className="text-purple-600 mr-2">🤔</span>
            <span className="font-medium text-purple-900">Clarification Needed</span>
          </div>
          <div className="text-purple-800 mb-3">{message.content}</div>
          <div className="text-xs text-purple-600">
            Please respond with your clarification to continue...
          </div>
        </div>
      );
    }

    if (message.type === 'info' && message.data) {
      // Check for fallback indicators
      const isFallback = message.data.meta?.fallback;
      const fallbackReason = message.data.meta?.fallback_reason;
      const confidence = message.data.meta?.confidence;

      return (
        <div>
          <div className="font-medium mb-2">{message.content}</div>

          {isFallback && (
            <div className="mb-2 p-2 bg-yellow-100 border border-yellow-300 rounded text-sm">
              <div className="flex items-center">
                <span className="text-yellow-600 mr-2">⚠️</span>
                <span className="font-medium text-yellow-800">Fallback Mode</span>
              </div>
              <div className="text-yellow-700 text-xs mt-1">
                {fallbackReason || "AI unavailable - using basic parsing"}
              </div>
              {confidence && (
                <div className="text-yellow-600 text-xs mt-1">
                  Confidence: {Math.round(confidence * 100)}%
                </div>
              )}
            </div>
          )}

          <details className="text-sm">
            <summary className="cursor-pointer text-gray-600">View Details</summary>
            <pre className="mt-2 p-2 bg-gray-50 rounded text-xs overflow-auto">
              {JSON.stringify(message.data, null, 2)}
            </pre>
          </details>
        </div>
      );
    }

    return message.content;
  };

  return (
    <div className={`p-3 mb-3 border rounded-lg ${getMessageStyle()}`}>
      <div className="flex justify-between items-start">
        <div className="flex-1">
          {message.corrections && (
            <div className="text-xs text-orange-600 mb-1">
              Corrected: {message.original} → {message.processed}
            </div>
          )}
          {formatContent()}
        </div>
        <span className="text-xs text-gray-500 ml-2">
          {new Date(message.timestamp).toLocaleTimeString()}
        </span>
      </div>
    </div>
  );
}