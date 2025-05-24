// hercules/frontend/src/App.tsx
import React, { useState } from 'react';
import { Routes, Route, Link, Outlet, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import { useAuth } from './contexts/AuthContext';
import './index.css';
import axios from 'axios';
import RoomPage from './pages/RoomPage'; // Import the new RoomPage

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// DashboardPage (from previous step)
const DashboardPage: React.FC = () => {
  const { user, logout } = useAuth();
  const [prompt, setPrompt] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [taskResponse, setTaskResponse] = useState<any>(null);
  const [taskError, setTaskError] = useState<string | null>(null);

  const handleTaskSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) {
      setTaskError("Prompt cannot be empty.");
      return;
    }
    setIsLoading(true);
    setTaskError(null);
    setTaskResponse(null);

    try {
      const token = localStorage.getItem('hercules_auth_token');
      if (!token) {
        setTaskError("Authentication token not found. Please login again.");
        logout();
        return;
      }
      const response = await axios.post(
        `${API_URL}/api/tasks`,
        { prompt },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setTaskResponse(response.data);
      setPrompt('');
    } catch (error: any) {
      console.error("Task submission error:", error.response?.data || error.message);
      setTaskError(error.response?.data?.detail || "Failed to submit task. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-4 md:p-8 bg-gray-800 shadow-lg rounded-lg">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-3xl font-semibold text-blue-300">Dashboard</h2>
        <button 
          onClick={logout} 
          className="bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded transition duration-150">
          Logout
        </button>
      </div>
      <p className="text-lg text-gray-300 mb-2">Welcome, {user?.email}!</p>
      <p className="text-gray-400 mb-8">Submit a new task for H.E.R.C.U.L.E.S. to process.</p>

      <form onSubmit={handleTaskSubmit} className="space-y-6">
        <div>
          <label htmlFor="taskPrompt" className="block text-sm font-medium text-gray-200 mb-1">
            Enter your complex task prompt:
          </label>
          <textarea
            id="taskPrompt"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            rows={4}
            className="w-full p-3 bg-gray-700 rounded border border-gray-600 focus:ring-blue-500 focus:border-blue-500 text-white"
            placeholder="e.g., Research the impact of AI on climate change and write a summary report..."
            required
          />
        </div>
        <button 
          type="submit"
          disabled={isLoading}
          className="w-full md:w-auto bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-lg disabled:opacity-60 transition duration-150"
        >
          {isLoading ? 'Submitting Task...' : 'Submit Task'}
        </button>
      </form>

      {taskError && (
        <div className="mt-6 p-4 bg-red-700 border border-red-900 text-white rounded-md">
          <p className="font-semibold">Error submitting task:</p>
          <p>{taskError}</p>
        </div>
      )}

      {taskResponse && (
        <div className="mt-6 p-4 bg-green-700 border border-green-900 text-white rounded-md">
          <p className="font-semibold">Task Submitted Successfully!</p>
          <p>Room ID: <Link to={`/room/${taskResponse.room_id}`} className="underline hover:text-blue-200">{taskResponse.room_id}</Link></p>
          <p>Message: {taskResponse.message}</p>
        </div>
      )}
    </div>
  );
};
   
const HomePagePublic: React.FC = () => (
  <div className="text-center py-10">
    <h1 className="text-5xl font-bold mb-4">Welcome to H.E.R.C.U.L.E.S.</h1>
    <p className="text-xl text-gray-400 mb-8">
      Human-Emulated Recursive Collaborative Unit using Layered Enhanced Simulation
    </p>
    <Link to="/login" className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg text-lg mr-2 transition duration-150">
      Login
    </Link>
    <Link to="/register" className="bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-lg text-lg transition duration-150">
      Register
    </Link>
  </div>
);

const ProtectedRoute: React.FC<{ children: JSX.Element }> = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) return <div className="min-h-screen flex items-center justify-center bg-gray-900 text-white text-xl">Loading session...</div>;
  return user ? children : <Navigate to="/login" replace />;
};

const MainLayout: React.FC = () => {
  const { user, loading, logout } = useAuth();
  return (
     <div className="min-h-screen bg-gray-900 text-white">
       <nav className="bg-gray-800 p-4 shadow-lg">
         <div className="container mx-auto flex justify-between items-center">
           <Link to="/" className="text-2xl font-bold text-blue-400 hover:text-blue-300 transition duration-150">HERCULES</Link>
           <div className="flex items-center">
             {loading && <span className="text-sm text-gray-400 mr-4">Checking auth...</span>}
             {user ? (
               <>
                 <span className="mr-4 text-gray-300 hidden sm:inline">Hello, {user.email}</span>
                 <Link to="/dashboard" className="text-gray-300 hover:text-white mr-4 transition duration-150">Dashboard</Link>
                 <button onClick={logout} className="text-gray-300 hover:text-red-400 transition duration-150">Logout</button>
               </>
             ) : (
               !loading &&
               <>
                 <Link to="/login" className="text-gray-300 hover:text-white mr-4 transition duration-150">Login</Link>
                 <Link to="/register" className="text-gray-300 hover:text-white transition duration-150">Register</Link>
               </>
             )}
           </div>
         </div>
       </nav>
       <main className="container mx-auto p-4 md:p-6">
         <Outlet />
       </main>
       <footer className="text-center p-4 text-gray-500 text-sm border-t border-gray-700 mt-8">
            Hercules AI Orchestration &copy; {new Date().getFullYear()}
       </footer>
     </div>
  )
}

function App() {
  const { user, loading } = useAuth();

  if (loading && localStorage.getItem('hercules_auth_token') === null) { 
     return <div className="min-h-screen flex items-center justify-center bg-gray-900 text-white text-xl">Initializing Hercules Interface...</div>;
  }

  return (
     <Routes>
         <Route element={<MainLayout />}>
             <Route path="/" element={user ? <Navigate to="/dashboard" /> : <HomePagePublic />} />
             <Route path="/login" element={user ? <Navigate to="/dashboard" /> : <LoginPage />} />
             <Route path="/register" element={user ? <Navigate to="/dashboard" /> : <RegisterPage />} />
             <Route 
                 path="/dashboard" 
                 element={
                     <ProtectedRoute>
                         <DashboardPage />
                     </ProtectedRoute>
                 } 
             />
             <Route // New route for individual room display
                 path="/room/:roomId"
                 element={
                     <ProtectedRoute>
                         <RoomPage />
                     </ProtectedRoute>
                 }
             />
         </Route>
     </Routes>
  );
}

export default App;
