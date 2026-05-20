import { fetchAPI } from './client';

export interface UserProfile {
  user_id: string;
  email: string;
  name?: string;
  role: string;
  region?: string;
  email_verified?: boolean;
  mfa_enabled?: boolean;
  is_active?: boolean;
}

export interface UserDetail extends UserProfile {
  property_ids: string[];
}

export interface UserCreateInput {
  email: string;
  name?: string;
  role: string;
  region?: string;
  property_ids?: string[];
}

export interface UserUpdateInput {
  name?: string;
  role?: string;
  region?: string;
  property_ids?: string[] | null; // null = don't change, [] = remove all
}

export async function getUsers(): Promise<UserProfile[]> {
  return fetchAPI<UserProfile[]>('/admin/users');
}

export async function getUser(userId: string): Promise<UserDetail> {
  return fetchAPI<UserDetail>(`/admin/users/${userId}`);
}

export async function createUser(data: UserCreateInput): Promise<{ user_id: string; email: string; role: string }> {
  return fetchAPI(`/admin/users`, {
    method: 'POST',
    body: JSON.stringify({
      email: data.email,
      name: data.name,
      role: data.role,
      region: data.region,
      property_ids: data.property_ids?.map((id) => id) ?? [],
    }),
  });
}

export async function updateUser(
  userId: string,
  data: UserUpdateInput
): Promise<{ user_id: string; email: string; role: string }> {
  return fetchAPI(`/admin/users/${userId}`, {
    method: 'PATCH',
    body: JSON.stringify({
      name: data.name,
      role: data.role,
      region: data.region,
      property_ids: data.property_ids === undefined ? undefined : data.property_ids,
    }),
  });
}

export async function deleteUser(userId: string): Promise<{ message: string; user_id: string }> {
  return fetchAPI(`/admin/users/${userId}`, {
    method: 'DELETE',
  });
}
