import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface User {
  id: string;
  telegram_id: number;
  username: string;
  first_name?: string;
  last_name?: string;
  photo_url?: string;
  balance: string;
  available_balance?: string;
  is_2fa_enabled: boolean;
  is_verified: boolean;
  created_at: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  /** True when the server indicates the user has no active Passkey yet (Req 9.3). */
  passkeySetupRequired: boolean;
  setAuth: (user: User, token: string) => void;
  clearAuth: () => void;
  updateUser: (user: Partial<User>) => void;
  /** Set or clear the passkey setup required flag (Req 9.3, 9.4). */
  setPasskeySetupRequired: (value: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      passkeySetupRequired: false,
      setAuth: (user, token) => {
        localStorage.setItem('auth_token', token);
        localStorage.setItem('user', JSON.stringify(user));
        set({ user, token, isAuthenticated: true, passkeySetupRequired: false });
      },
      clearAuth: () => {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user');
        set({ user: null, token: null, isAuthenticated: false, passkeySetupRequired: false });
      },
      updateUser: (userData) =>
        set((state) => ({
          user: state.user ? { ...state.user, ...userData } : null,
        })),
      setPasskeySetupRequired: (value) => set({ passkeySetupRequired: value }),
    }),
    {
      name: 'auth-storage',
    }
  )
);
