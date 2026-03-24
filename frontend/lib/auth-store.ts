// frontend/lib/auth-store.ts

import { create } from "zustand";
import { persist } from "zustand/middleware";

// Shape of the logged-in user
export interface AuthUser {
  user_id:   number;
  school_id: number;
  role:      "admin" | "teacher" | "parent" | "student";
  full_name: string;
  email:     string;
}

interface AuthStore {
  user:         AuthUser | null;
  token:        string | null;
  isLoggedIn:   boolean;
  hydrated:     boolean;
  setAuth:      (token: string, user: AuthUser) => void;
  logout:       () => void;
}

export const useAuthStore = create<AuthStore>()(
  // persist saves to localStorage automatically
  persist(
    (set) => ({
      user:       null,
      token:      null,
      isLoggedIn: false,
      hydrated:   false,

      setAuth: (token, user) => {
        // Save token separately so axios interceptor can read it
        localStorage.setItem("access_token", token);
        set({ token, user, isLoggedIn: true });
      },

      logout: () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("school-os-auth");
        set({ token: null, user: null, isLoggedIn: false, hydrated: true });
      },
    }),
    {
      name: "school-os-auth",     // localStorage key
      partialize: (state) => ({   // only persist these fields
        user:       state.user,
        token:      state.token,
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
    }
  )
);
