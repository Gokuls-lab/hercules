// hercules/frontend/src/pages/RoomPage.tsx
import React, { useEffect, useState, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WS_URL = API_URL.replace(/^http/, 'ws');

interface RoomDetails {
  room_id: string;
  user_id: string;
  task_prompt: string;
  created_at: string;
  status: string;
  folder_path?: string;
}

interface AgentMessage {
  id?: string; // id from database for stored messages
  room_id?: string; // room_id from database
  agent: string; // Renamed from agent_name for consistency with WebSocket messages
  message: string; // Renamed from content for consistency
  timestamp: string; // Standardized field name
  model_used?: string | null;
  error?: string; // For system error messages from WebSocket
  custom_type?: string; // For special messages like llm_config_warning
  event?: string; // For special events like TERMINATE
}

export default function RoomPage() {
  const { roomId } = useParams<{ roomId: string }>();
  const { logout } = useAuth();
  const [roomDetails, setRoomDetails] = useState<RoomDetails | null>(null);
  const [loadingDetails, setLoadingDetails] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [chatMessages, setChatMessages] = useState<AgentMessage[]>([]); // Unified state for historical and live messages
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [wsStatus, setWsStatus] = useState<string>("Initializing...");
  const ws = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // Fetch initial room details (no change to this useEffect)
  useEffect(() => {
    const fetchRoomDetails = async () => {
      if (!roomId) {
        setError("Room ID not found in URL.");
        setLoadingDetails(false);
        return;
      }
      setLoadingDetails(true);
      setError(null);
      const token = localStorage.getItem('hercules_auth_token');
      if (!token) {
        setError("Authentication token not found.");
        setLoadingDetails(false);
        logout();
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
          logout();
        } else {
          setError(err.response?.data?.detail || "Failed to fetch room details.");
        }
      } finally {
        setLoadingDetails(false);
      }
    };
    fetchRoomDetails();
  }, [roomId, logout]);

  // Fetch historical chat messages
  useEffect(() => {
    if (!roomId) return;
    const fetchChatHistory = async () => {
      setLoadingHistory(true);
      const token = localStorage.getItem('hercules_auth_token');
      if (!token) {
        // This error will be caught by the main details loader typically
        // but good to have a check if this runs independently.
        setError("Authentication token not found for chat history."); 
        setLoadingHistory(false);
        return;
      }
      try {
        const response = await axios.get(`${API_URL}/api/rooms/${roomId}/messages`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        // Transform Supabase response (agent_name, content) to AgentMessage interface
        const historicalMessages = response.data.map((msg: any) => ({
            id: msg.id,
            room_id: msg.room_id,
            agent: msg.agent_name, // Transform field name
            message: msg.content,   // Transform field name
            timestamp: msg.timestamp, // Ensure this is ISO string
            model_used: msg.model_used,
            custom_type: msg.custom_type,
        }));
        setChatMessages(historicalMessages);
      } catch (err: any) {
        console.error("Error fetching chat history:", err.response?.data || err.message);
        // Don't overwrite main page error if room details loaded but history failed
        setWsStatus("Failed to load chat history. Live messages will still appear."); 
      } finally {
        setLoadingHistory(false);
      }
    };
    fetchChatHistory();
  }, [roomId]);


  // WebSocket connection (modified to append to chatMessages)
  useEffect(() => {
    if (!roomId) {
        setWsStatus("Room ID missing, WebSocket connection aborted.");
        return;
    }
    const socketUrl = `${WS_URL}/ws/room/${roomId}`;
    ws.current = new WebSocket(socketUrl);
    setWsStatus(`Attempting to connect to live feed: ${socketUrl}`);

    ws.current.onopen = () => setWsStatus("Live feed connected.");
    ws.current.onmessage = (event) => {
      try {
        const incomingMessage = JSON.parse(event.data as string) as AgentMessage;
        // Ensure incoming WebSocket messages also have a 'timestamp' if not provided by server
        if (!incomingMessage.timestamp) {
            incomingMessage.timestamp = new Date().toISOString();
        }
        setChatMessages((prevMessages) => [...prevMessages, incomingMessage]);
      } catch (e) {
        console.error("Failed to parse WebSocket message:", event.data, e);
        setChatMessages((prevMessages) => [...prevMessages, {agent: "System", message: `Raw unparseable message: ${event.data}`, timestamp: new Date().toISOString(), error: "Parse error"}]);
      }
    };
    ws.current.onerror = (event) => {
        console.error("WebSocket error:", event);
        setWsStatus("Live feed error.");
    };
    ws.current.onclose = (event) => {
      setWsStatus(event.wasClean ? `Live feed disconnected (Code: ${event.code}).` : `Live feed connection died (Code: ${event.code}).`);
    };
    return () => {
      if (ws.current) {
        ws.current.close();
        ws.current = null;
      }
    };
  }, [roomId]);

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]); // Trigger scroll whenever messages change


  // Main component rendering logic (loading states, error, room details, chat display)
  if (loadingDetails) return <div className="text-center p-10 text-xl">Loading room details...</div>;
  if (error) return <div className="text-center p-10"><p className="text-red-500 text-xl">Error: {error}</p><Link to="/dashboard" className="text-blue-400 hover:underline mt-4 inline-block">Back to Dashboard</Link></div>;
  if (!roomDetails) return <div className="text-center p-10 text-xl">No room details available.</div>;

  return (
    <div className="p-4 md:p-8 bg-gray-800 shadow-lg rounded-lg">
      {/* Room Info and Task Prompt (existing JSX) - slightly restyled */}
      <h2 className="text-3xl font-semibold text-blue-300 mb-1">
        Room: <span className="text-green-400">{roomDetails.room_id.substring(0, 12)}...</span>
      </h2>
      <p className="text-xs text-gray-500 mb-6">Full ID: {roomDetails.room_id}</p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="md:col-span-1 space-y-3 text-gray-300 bg-gray-700 p-4 rounded-md shadow">
          <h4 className="text-lg font-medium text-gray-100 border-b border-gray-600 pb-2 mb-2">Room Info</h4>
          <p><strong>User ID:</strong> {roomDetails.user_id.substring(0,12)}...</p>
          <p><strong>Status:</strong> <span className={`px-2 py-0.5 rounded text-xs font-semibold ${roomDetails.status === 'pending' ? 'bg-yellow-500 text-yellow-900' : roomDetails.status === 'active' || roomDetails.status === 'processing' ? 'bg-blue-500 text-blue-900' : roomDetails.status === 'completed' ? 'bg-green-500 text-green-900' : 'bg-red-500 text-red-900'}`}>{roomDetails.status}</span></p>
          <p><strong>Created At:</strong> {new Date(roomDetails.created_at).toLocaleString()}</p>
        </div>
        <div className="md:col-span-2 bg-gray-700 p-4 rounded-md shadow">
          <h4 className="text-lg font-medium text-gray-100 border-b border-gray-600 pb-2 mb-2">Task Prompt:</h4>
          <pre className="whitespace-pre-wrap bg-gray-600 p-3 rounded text-gray-200 font-mono text-sm max-h-40 overflow-y-auto">
            {roomDetails.task_prompt}
          </pre>
        </div>
      </div>
      
      {/* Agent Activity Section - now displays combined historical and live messages */}
      <div className="mt-6 pt-6 border-t border-gray-700">
        <h3 className="text-xl font-semibold text-blue-300 mb-1">Agent Converation Log</h3>
        <p className="text-sm text-gray-400 mb-3">WebSocket Status: <span className="font-semibold">{wsStatus}</span></p>
        <div className="h-[32rem] bg-gray-900 p-4 rounded overflow-y-auto border border-gray-700 shadow-inner flex flex-col">
          {loadingHistory && <p className="text-gray-400 italic p-2">Loading chat history...</p>}
          {!loadingHistory && chatMessages.length === 0 && (
            <p className="text-gray-500 italic p-2">No messages yet. Waiting for agent activity...</p>
          )}
          {chatMessages.map((msg, index) => (
            <div key={msg.id || `ws-${index}`} className={`mb-3 p-3 rounded-lg shadow text-sm ${
                msg.agent === 'UserProxy' ? 'bg-gray-700 self-start w-fit max-w-[85%]' : 
                msg.custom_type === 'llm_config_warning' || msg.error ? 'bg-yellow-700 text-yellow-100 self-center w-fit max-w-[85%]' : 
                msg.agent === 'System' ? 'bg-red-800 text-red-100 self-center w-fit max-w-[85%]' : 
                msg.event === 'TERMINATE' ? 'bg-purple-700 text-purple-100 self-center w-fit max-w-[85%]' :
                'bg-blue-900 self-start w-fit max-w-[85%]' // Default for assistant messages
            }`}>
              <div className="flex justify-between items-center text-xs text-gray-400 mb-1">
                <strong className={
                    msg.agent === 'UserProxy' ? 'text-green-300' : 
                    msg.agent === 'System' || msg.custom_type === 'llm_config_warning' || msg.error ? 'text-yellow-200' :
                    msg.event === 'TERMINATE' ? 'text-purple-200' :
                    'text-cyan-300'
                }>{msg.agent}</strong>
                <span className="ml-2">{new Date(msg.timestamp).toLocaleTimeString()} ({new Date(msg.timestamp).toLocaleDateString()})</span>
              </div>
              {msg.event === 'TERMINATE' ? (
                <p className="italic">{msg.message || `${msg.agent} has finished.`}</p>
              ) : msg.custom_type === 'llm_config_warning' || msg.error ? (
                <p className="whitespace-pre-wrap font-semibold">{msg.error || msg.message}</p>
              ) : (
                <p className="whitespace-pre-wrap">{msg.message}</p>
              )}
              {msg.model_used && <p className="text-xs text-gray-500 mt-1">Model: {msg.model_used}</p>}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="mt-8">
        <Link to="/dashboard" className="text-blue-400 hover:underline">&larr; Back to Dashboard</Link>
      </div>
    </div>
  );
}
