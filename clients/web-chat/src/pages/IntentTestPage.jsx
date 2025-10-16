import React from 'react';
import IntentTestPanel from '../components/IntentTestPanel';

/**
 * Standalone page for testing the Intents API
 * Can be accessed at a separate route or embedded in the main app
 */
const IntentTestPage = () => {
  return (
    <div className="min-h-screen bg-gray-950 p-6">
      <IntentTestPanel serverUrl="http://127.0.0.1:8722" />
    </div>
  );
};

export default IntentTestPage;
