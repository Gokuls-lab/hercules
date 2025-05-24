import React from 'react';
import './index.css'; // Ensure Tailwind is imported

function App() {
  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col items-center justify-center">
      <header className="text-center">
        <h1 className="text-5xl font-bold mb-4">Welcome to H.E.R.C.U.L.E.S.</h1>
        <p className="text-xl text-gray-400 mb-8">
          Human-Emulated Recursive Collaborative Unit using Layered Enhanced Simulation
        </p>
        <button className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg text-lg">
          Get Started (Coming Soon!)
        </button>
      </header>
      {/* Future content will go here: task submission, room view, etc. */}
    </div>
  );
}

export default App;
