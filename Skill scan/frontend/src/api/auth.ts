import client from './client';
import { AuthResponse, LoginRequest, RegisterRequest } from '@types';

export const authAPI = {
  login: async (credentials: LoginRequest): Promise<AuthResponse> => {
    const response = await client.post('/auth/login', credentials);
    return response.data;
  },

  register: async (data: RegisterRequest): Promise<AuthResponse> => {
    const response = await client.post('/auth/register', data);
    return response.data;
  },

  logout: async (): Promise<void> => {
    await client.post('/auth/logout');
  },

  refreshToken: async (refresh_token: string): Promise<AuthResponse> => {
    const response = await client.post('/auth/refresh', { refresh_token });
    return response.data;
  },

  getCurrentUser: async () => {
    const response = await client.get('/auth/me');
    return response.data;
  },
};
