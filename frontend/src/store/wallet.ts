import { create } from 'zustand';

interface WalletState {
  balance: string;
  address: string | null;
  isLoading: boolean;
  setBalance: (balance: string) => void;
  setAddress: (address: string) => void;
  setLoading: (isLoading: boolean) => void;
}

export const useWalletStore = create<WalletState>((set) => ({
  balance: '0.000000',
  address: null,
  isLoading: false,
  setBalance: (balance) => set({ balance }),
  setAddress: (address) => set({ address }),
  setLoading: (isLoading) => set({ isLoading }),
}));
