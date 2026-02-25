import apiClient from './client'
import type { User, LoginCredentials, RegisterData, AuthResponse } from '@/types'

export const authAPI = {
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    const response = await apiClient.post<{ access: string; refresh: string }>('/token/', credentials)
    
    // Get user info with the token
    const userResponse = await apiClient.get<User>('/users/me/', {
      headers: { Authorization: `Bearer ${response.data.access}` }
    })
    
    return {
      access: response.data.access,
      refresh: response.data.refresh,
      user: userResponse.data
    }
  },

  register: async (data: RegisterData): Promise<AuthResponse> => {
    const response = await apiClient.post<User>('/users/', data)
    
    // Auto login after registration
    const loginResponse = await authAPI.login({
      username: data.username,
      password: data.password
    })
    
    return loginResponse
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get<User>('/users/me/')
    return response.data
  },

  refreshToken: async (refreshToken: string): Promise<{ access: string }> => {
    const response = await apiClient.post<{ access: string }>('/token/refresh/', {
      refresh: refreshToken,
    })
    return response.data
  },

  logout: async (): Promise<void> => {
    // No server-side logout needed for JWT
    return Promise.resolve()
  },

  requestPasswordReset: async (email: string): Promise<void> => {
    await apiClient.post('/users/password-reset/', { email })
  },

  confirmPasswordReset: async (token: string, password: string): Promise<void> => {
    await apiClient.post('/users/password-reset-confirm/', { token, password })
  },
}
