import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';

export interface Deal {
  id: string;
  buyer: {
    id: string;
    username: string;
    telegram_username?: string;
  };
  seller: {
    id: string;
    username: string;
    telegram_username?: string;
  };
  title: string;
  description: string;
  amount: string;
  fee: string;
  status: 'DRAFT' | 'FUNDED' | 'IN_PROGRESS' | 'COMPLETED' | 'DISPUTED' | 'CANCELLED';
  created_at: string;
  funded_at?: string;
  started_at?: string;
  completed_at?: string;
  disputed_at?: string;
  cancelled_at?: string;
}

export function useDeals() {
  return useQuery({
    queryKey: ['deals'],
    queryFn: async () => {
      const response = await api.get('/deals/');
      return response.data as Deal[];
    },
  });
}

export function useDeal(dealId: string) {
  return useQuery({
    queryKey: ['deal', dealId],
    queryFn: async () => {
      const response = await api.get(`/deals/${dealId}/`);
      return response.data as Deal;
    },
    enabled: !!dealId,
  });
}

export function useCreateDeal() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: { seller?: string; seller_username?: string; title: string; description: string; amount: string }) => {
      const response = await api.post('/deals/', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deals'] });
    },
  });
}

export function useFundDeal() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (dealId: string) => {
      const response = await api.post(`/deals/${dealId}/fund/`);
      return response.data;
    },
    onSuccess: (_, dealId) => {
      queryClient.invalidateQueries({ queryKey: ['deals'] });
      queryClient.invalidateQueries({ queryKey: ['deal', dealId] });
      queryClient.invalidateQueries({ queryKey: ['balance'] });
    },
  });
}

export function useStartDeal() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (dealId: string) => {
      const response = await api.post(`/deals/${dealId}/start/`);
      return response.data;
    },
    onSuccess: (_, dealId) => {
      queryClient.invalidateQueries({ queryKey: ['deals'] });
      queryClient.invalidateQueries({ queryKey: ['deal', dealId] });
    },
  });
}

export function useCompleteDeal() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (dealId: string) => {
      const response = await api.post(`/deals/${dealId}/complete/`);
      return response.data;
    },
    onSuccess: (_, dealId) => {
      queryClient.invalidateQueries({ queryKey: ['deals'] });
      queryClient.invalidateQueries({ queryKey: ['deal', dealId] });
      queryClient.invalidateQueries({ queryKey: ['balance'] });
    },
  });
}

export function useDisputeDeal() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ dealId, reason }: { dealId: string; reason: string }) => {
      const response = await api.post(`/deals/${dealId}/dispute/`, { reason });
      return response.data;
    },
    onSuccess: (_, { dealId }) => {
      queryClient.invalidateQueries({ queryKey: ['deals'] });
      queryClient.invalidateQueries({ queryKey: ['deal', dealId] });
    },
  });
}

export function useCancelDeal() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (dealId: string) => {
      const response = await api.post(`/deals/${dealId}/cancel/`);
      return response.data;
    },
    onSuccess: (_, dealId) => {
      queryClient.invalidateQueries({ queryKey: ['deals'] });
      queryClient.invalidateQueries({ queryKey: ['deal', dealId] });
      queryClient.invalidateQueries({ queryKey: ['balance'] });
    },
  });
}

export function useDealMessages(dealId: string) {
  return useQuery({
    queryKey: ['dealMessages', dealId],
    queryFn: async () => {
      const response = await api.get(`/deals/${dealId}/messages/`);
      return response.data;
    },
    enabled: !!dealId,
    refetchInterval: 5000, // Refetch every 5 seconds
  });
}

export function useSendMessage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ dealId, content }: { dealId: string; content: string }) => {
      const response = await api.post(`/deals/${dealId}/send_message/`, { content });
      return response.data;
    },
    onSuccess: (_, { dealId }) => {
      queryClient.invalidateQueries({ queryKey: ['dealMessages', dealId] });
    },
  });
}
