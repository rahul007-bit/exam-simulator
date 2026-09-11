import { apiRequest } from './client'

export interface User {
  username: string
  role: string
  created_at: string
}

export interface UsersResponse {
  users: User[]
  total: number
}

export interface CreateUserResponse {
  status: string
  user: User
}

export function listUsers(): Promise<UsersResponse> {
  return apiRequest<UsersResponse>('/api/admin/users')
}

export function createUser(
  username: string,
  password: string,
  role: string,
): Promise<CreateUserResponse> {
  return apiRequest<CreateUserResponse>('/api/admin/users', {
    method: 'POST',
    body: { username, password, role },
  })
}

export function deleteUser(username: string): Promise<{ status: string; username: string }> {
  return apiRequest<{ status: string; username: string }>(
    `/api/admin/users/${encodeURIComponent(username)}`,
    { method: 'DELETE' },
  )
}
