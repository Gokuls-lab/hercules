// hercules/frontend/src/lib/supabaseClientMock.ts

// This is a mock Supabase client to allow frontend development
// to proceed without the actual supabase-js package.
// It should be replaced with the real Supabase client once installation issues are resolved.

console.warn(
  "Using MOCK Supabase client. Replace with actual Supabase client when available."
);

const mockUser = {
  id: "mock-user-id-123",
  email: "user@example.com",
  // Add other user properties if your app uses them
};

const mockSession = {
  access_token: "mock-access-token",
  token_type: "bearer",
  user: mockUser,
  // Add other session properties if your app uses them
};

export const supabase = {
  auth: {
    signUp: async (credentials: any) => {
      console.log("MOCK Supabase: signUp called with", credentials);
      if (credentials.email && credentials.password) {
        // Simulate a successful sign-up
        return {
          data: { user: { ...mockUser, email: credentials.email }, session: mockSession },
          error: null,
        };
      }
      return {
        data: { user: null, session: null },
        error: { message: "Mock error: Email and password are required for sign up." },
      };
    },
    signInWithPassword: async (credentials: any) => {
      console.log("MOCK Supabase: signInWithPassword called with", credentials);
      if (
        credentials.email === "user@example.com" &&
        credentials.password === "password"
      ) {
        return {
          data: { user: mockUser, session: mockSession },
          error: null,
        };
      }
      return {
        data: { user: null, session: null },
        error: { message: "Mock error: Invalid credentials." },
      };
    },
    signOut: async () => {
      console.log("MOCK Supabase: signOut called");
      // Simulate a successful sign-out
      return { error: null };
    },
    onAuthStateChange: (callback: (event: string, session: any) => void) => {
      console.log("MOCK Supabase: onAuthStateChange listener added");
      // Simulate an initial state (e.g., signed out)
      // callback("INITIAL_SESSION", null); 
      // To simulate a signed-in user for testing protected routes:
      // setTimeout(() => callback("SIGNED_IN", mockSession), 100); 
      
      // For now, let's not automatically trigger it to allow login forms to be tested.
      // The app will need to manage its own auth state based on login/logout calls.

      return {
        data: { subscription: { unsubscribe: () => console.log("MOCK Supabase: unsubscribed from onAuthStateChange") } },
      };
    },
    getSession: async () => {
      console.log("MOCK Supabase: getSession called");
      // Simulate no active session initially, or a mock session if needed for testing
      // For example, to simulate an existing session:
      // const storedToken = localStorage.getItem('mock_supabase_token');
      // if (storedToken) {
      //   return { data: { session: mockSession }, error: null };
      // }
      return { data: { session: null }, error: null };
    }
  },
  // Add other Supabase services if needed, e.g., functions, storage
  // from: (tableName: string) => { ... } // Mock for database operations
};

export type SupabaseClient = typeof supabase; // Basic type for the mock

export function createClient(url: string, key: string): SupabaseClient {
  console.log("MOCK Supabase: createClient called with (mocked)", url, key);
  return supabase;
}
