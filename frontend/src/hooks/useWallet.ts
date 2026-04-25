import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { useWalletStore } from '@/store/wallet';

export function useBalance() {
  const { setBalance } = useWalletStore();

  return useQuery({
    queryKey: ['balance'],
    queryFn: async () => {
      const response = await api.get('/wallets/balance/');
      setBalance(response.data.balance);
      return response.data;
    },
    refetchInterval: 30000, // Refetch every 30 seconds
    retry: (failureCount, error: any) => {
      // Don't retry on 401 - token is invalid, redirect will handle it
      if (error?.response?.status === 401) return false;
      return failureCount < 2;
    },
  });
}

export function useDepositAddress() {
  const { setAddress } = useWalletStore();

  return useQuery({
    queryKey: ['depositAddress'],
    queryFn: async () => {
      const response = await api.get('/wallets/deposit_address/');
      setAddress(response.data.address);
      return response.data;
    },
  });
}

export function useWithdraw() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: { to_address: string; amount: string; totp_token?: string }) => {
      const response = await api.post('/wallets/withdraw/', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['balance'] });
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
    },
  });
}

export function useTransactions() {
  return useQuery({
    queryKey: ['transactions'],
    queryFn: async () => {
      const response = await api.get('/wallets/transactions/');
      return response.data;
    },
  });
}
