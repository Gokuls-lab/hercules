# HERCULES Database Schema (Supabase PostgreSQL)

## `users` (Managed by Supabase Auth)
- Supabase automatically handles this table for user authentication.
- Contains user `id` (UUID), `email`, `password_hash`, etc.

## `rooms`
- Stores metadata for each task room.
- **Primary Key:** `id` (UUID, auto-generated) - *Note: The project description mentions `room_id` as PK, but using `id` as a standard UUID PK and having `room_id` as a separate unique identifier is often cleaner.*
- `room_id`: TEXT (UNIQUE, indexed) - The human-readable/shareable ID (e.g., sha256(user_id + timestamp)).
- `user_id`: UUID (FK to `auth.users.id`) - The user who created the room.
- `task_prompt`: TEXT - The initial prompt for the task.
- `created_at`: TIMESTAMPTZ (default: `now()`)
- `status`: TEXT (e.g., "pending", "active", "processing", "completed", "failed")
- `llm_used`: TEXT (nullable) - e.g., "OpenAI", "Gemini", "Mixed".
- `agents_used`: JSONB (nullable) - e.g., `["researcher", "writer", "coder"]`.
- `folder_path`: TEXT - Path to the room's data on the server (e.g., `/data/rooms/{room_id}`).

## `ai_messages`
- Logs all messages exchanged between AI agents and AI-to-system messages.
- **Primary Key:** `id` (UUID, auto-generated)
- `room_id`: UUID (FK to `rooms.id`, indexed)
- `agent_name`: TEXT (e.g., "@researcher", "@coder", "system_orchestrator")
- `content`: TEXT - The actual message content or prompt.
- `response`: TEXT (nullable) - The response from the LLM.
- `model_used`: TEXT (nullable) - Which LLM model was invoked.
- `tool_calls`: JSONB (nullable) - If the agent used tools.
- `timestamp`: TIMESTAMPTZ (default: `now()`)
- `token_count`: INTEGER (nullable)

## `files`
- Tracks files generated or used within a room.
- **Primary Key:** `id` (UUID, auto-generated)
- `room_id`: UUID (FK to `rooms.id`, indexed)
- `filename`: TEXT
- `file_path_on_server`: TEXT - Absolute path on the server.
- `file_size_bytes`: BIGINT
- `mime_type`: TEXT (nullable)
- `created_at`: TIMESTAMPTZ (default: `now()`)
- `description`: TEXT (nullable) - Optional description of the file.

## `websocket_connections` (Optional, for tracking active connections)
- `connection_id`: TEXT (PK)
- `room_id`: UUID (FK to `rooms.id`)
- `user_id`: UUID (FK to `auth.users.id`)
- `connected_at`: TIMESTAMPTZ (default: `now()`)
