import type {
    MessageResponse,
    PaginatedResponse,
    UserBase,
    UserCreate,
    UserPasswordReset,
    UserRead,
} from '@/types/utils';
import { api } from './api';

export const userService = {
    async getUsers(
        params?: Record<string, unknown>,
    ): Promise<PaginatedResponse<UserRead>> {
        const response = await api.get<PaginatedResponse<UserRead>>(
            '/admin/users',
            { params },
        );
        return response.data;
    },

    async getUser(userId: string): Promise<UserRead> {
        const response = await api.get<UserRead>(`/admin/users/${userId}`);
        return response.data;
    },

    async createUser(data: UserCreate): Promise<UserRead> {
        const response = await api.post<UserRead>('/admin/users/', data);
        return response.data;
    },

    async updateUser(userId: string, data: UserBase): Promise<UserRead> {
        const response = await api.put<UserRead>(
            `/admin/users/${userId}`,
            data,
        );
        return response.data;
    },

    async deleteUser(userId: string): Promise<void> {
        await api.delete(`/admin/users/${userId}`);
    },

    async resetUserPassword(
        userId: string,
        data: UserPasswordReset,
    ): Promise<MessageResponse> {
        const response = await api.post<MessageResponse>(
            `/admin/users/${userId}/reset_password`,
            data,
        );
        return response.data;
    },

    async resetUserMFA(userId: string): Promise<MessageResponse> {
        const response = await api.post<MessageResponse>(
            `/admin/users/${userId}/reset_mfa`,
        );
        return response.data;
    },

    async resetMyMFA(password: string): Promise<MessageResponse> {
        const response = await api.put<MessageResponse>('/user/me/mfa', {
            password,
        });
        return response.data;
    },
};
