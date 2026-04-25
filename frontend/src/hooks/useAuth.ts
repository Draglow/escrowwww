import { useMutation, useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { useAuthStore } from '@/store/auth';
import { useRouter } from 'next/navigation';

interface TelegramAuthData {
  id: number;
  first_name: string;
  username?: string;
  photo_url?: string;
  auth_date: number;
  hash: string;
}

interface LoginResponse {
  user: any;
  token: string;
}

export function useLogin() {
  const { setAuth } = useAuthStore();
  const router = useRouter();

  return useMutation({
    mutationFn: async (authData: TelegramAuthData) => {
      // Convert auth data to query string format
      const authString = Object.entries(authData)
        .map(([key, value]) => `${key}=${value}`)
        .join('&');

      const response = await api.post<LoginResponse>(
        '/users/auth/login/',
        {},
        {
          headers: {
            Authorization: `Telegram ${authString}`,
          },
        }
      );
      return response.data;
    },
    onSuccess: (data) => {
      setAuth(data.user, data.token);
      router.push('/dashboard');
    },
  });
}

export function useLogout() {
  const { clearAuth } = useAuthStore();
  const router = useRouter();

  return useMutation({
    mutationFn: async () => {
      await api.post('/users/auth/logout/');
    },
    onSuccess: () => {
      clearAuth();
      router.push('/login');
    },
  });
}

export function useCurrentUser() {
  return useQuery({
    queryKey: ['currentUser'],
    queryFn: async () => {
      const response = await api.get('/users/me/');
      return response.data;
    },
  });
}
