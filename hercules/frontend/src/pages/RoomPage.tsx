// hercules/frontend/src/pages/RoomPage.tsx
import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext'; // To potentially handle logout on auth error

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface RoomDetails {
  room_id: string;
  user_id: string;
  task_prompt: string;
  created_at: string;
  status: string;
  folder_path?: string; // Optional, may not always be sent to frontend
  // Add other fields from your 'rooms' table metadata as needed
}

export default function RoomPage() {
  const { roomId } = useParams<{ roomId: string }>();
  const { logout } = useAuth(); // Get logout from auth context
  const [roomDetails, setRoomDetails] = useState<RoomDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchRoomDetails = async () => {
      if (!roomId) {
        setError("Room ID not found in URL.");
        setLoading(false);
        return;
      }

      setLoading(true);
      setError(null);

      const token = localStorage.getItem('hercules_auth_token');
      if (!token) {
        setError("Authentication token not found. Please login again.");
        setLoading(false);
        // Consider redirecting to login or calling logout()
        logout(); // Example: force logout
        return;
      }

      try {
        const response = await axios.get(`${API_URL}/api/rooms/${roomId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setRoomDetails(response.data);
      } catch (err: any) {
        console.error("Error fetching room details:", err.response?.data || err.message);
        if (err.response?.status === 401 || err.response?.status === 403) {
         setError("Unauthorized or token expired. Please login again.");
         logout(); // Force logout on auth error
        } else {
         setError(err.response?.data?.detail || "Failed to fetch room details.");
        }
      } finally {
        setLoading(false);
      }
    };

    fetchRoomDetails();
  }, [roomId, logout]);

  if (loading) {
    return <div className="text-center p-10 text-xl">Loading room details...</div>;
  }

  if (error) {
    return (
      <div className="text-center p-10">
        <p className="text-red-500 text-xl">Error: {error}</p>
        <Link to="/dashboard" className="text-blue-400 hover:underline mt-4 inline-block">
          Back to Dashboard
        </Link>
      </div>
    );
  }

  if (!roomDetails) {
    return <div className="text-center p-10 text-xl">No room details available.</div>;
  }

  return (
    <div className="p-4 md:p-8 bg-gray-800 shadow-lg rounded-lg">
      <h2 className="text-3xl font-semibold text-blue-300 mb-6">
        Room: <span className="text-green-400">{roomDetails.room_id.substring(0, 12)}...</span>
      </h2>
      <div className="space-y-3 text-gray-300">
        <p><strong>Full Room ID:</strong> {roomDetails.room_id}</p>
        <p><strong>User ID:</strong> {roomDetails.user_id}</p>
        <p><strong>Status:</strong> <span className={`px-2 py-1 rounded text-sm font-semibold ${roomDetails.status === 'pending' ? 'bg-yellow-500 text-yellow-900' : roomDetails.status === 'active' || roomDetails.status === 'processing' ? 'bg-blue-500 text-blue-900' : roomDetails.status === 'completed' ? 'bg-green-500 text-green-900' : 'bg-red-500 text-red-900'}`}>{roomDetails.status}</span></p>
        <p><strong>Created At:</strong> {new Date(roomDetails.created_at).toLocaleString()}</p>
        <div className="mt-4 pt-4 border-t border-gray-700">
          <h4 className="text-lg font-medium text-gray-100 mb-1">Task Prompt:</h4>
          <pre className="whitespace-pre-wrap bg-gray-700 p-3 rounded text-gray-200 font-mono text-sm">
            {roomDetails.task_prompt}
          </pre>
        </div>
        {/* Placeholder for WebSocket messages and file list */}
        <div className="mt-6 pt-6 border-t border-gray-700">
             <h3 className="text-xl font-semibold text-blue-300 mb-3">Agent Activity (Real-time updates coming soon)</h3>
             {/* WebSocket messages will appear here */}
             <div className="h-48 bg-gray-700 p-3 rounded overflow-y-auto text-sm">
                 <p className="text-gray-500">Waiting for agent messages...</p>
             </div>
        </div>
        <div className="mt-6">
             <Link to="/dashboard" className="text-blue-400 hover:underline">
                 &larr; Back to Dashboard
             </Link>
        </div>
      </div>
    </div>
  );
}
