// frontend/lib/auth-store.ts

import { create } from "zustand";
import { persist } from "zustand/middleware";

// Shape of the logged-in user
export interface AuthUser {
  user_id: number;
  school_id: number;
  role: "admin" | "teacher" | "parent" | "student";
  full_name: string;
  email: string;
}

interface AuthStore {
  user: AuthUser | null;
  token: string | null;
  isLoggedIn: boolean;
  hydrated: boolean;
  setAuth: (token: string, user: AuthUser) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthStore>()(
  // persist saves to localStorage automatically
  persist(
    (set) => ({
      user: null,
      token: null,
      isLoggedIn: false,
      hydrated: false,

      // In frontend/lib/auth-store.ts
      // Replace just the setAuth function body:

      setAuth: (token, user) => {
        localStorage.setItem("access_token", token);

        // Also write a cookie so middleware can read it
        // Zustand persist writes to localStorage but middleware
        // runs on the server and needs a cookie
        if (typeof document !== "undefined") {
          document.cookie = `school-os-auth=${JSON.stringify({
            state: { user, token, isLoggedIn: true },
          })}; path=/; max-age=${60 * 60 * 24 * 7}; SameSite=Lax`;
        }

        set({ token, user, isLoggedIn: true });
      },

      logout: () => {
        localStorage.removeItem("access_token");
        // Clear the cookie too
        if (typeof document !== "undefined") {
          document.cookie = "school-os-auth=; path=/; max-age=0";
        }
        set({ token: null, user: null, isLoggedIn: false });
      },
    }),
    {
      name: "school-os-auth", // localStorage key
      partialize: (state) => ({
        // only persist these fields
        user: state.user,
        token: state.token,
        isLoggedIn: state.isLoggedIn,
      }),
      onRehydrateStorage: () => (state) => {
        try {
          if (typeof window !== "undefined") {
            if (state?.token) {
              localStorage.setItem("access_token", state.token);
            } else {
              localStorage.removeItem("access_token");
            }
          }
        } finally {
          // Never leave dashboard screens stuck behind hydration gate.
          useAuthStore.setState({ hydrated: true });
        }
      },
    },
  ),
);
