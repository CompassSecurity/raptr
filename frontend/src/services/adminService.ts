import type { MessageResponse } from '@/types/utils';
import { api } from './api';

/**
 * Admin service for non-user administrative operations.
 * User management operations are in userService.ts
 */
export const adminService = {
    /**
     * Import MITRE ATT&CK tactics and techniques
     */
    async importMitre(): Promise<MessageResponse> {
        const response = await api.post<MessageResponse>('/admin/seed/mitre/');
        return response.data;
    },

    /**
     * Import Atomic Red Team activity templates
     */
    async importARTActivityTemplates(): Promise<MessageResponse> {
        const response = await api.post<MessageResponse>('/admin/seed/ART');
        return response.data;
    },

    /**
     * Import custom activity templates from repository
     */
    async importCustomActivityTemplates(): Promise<MessageResponse> {
        const response = await api.post<MessageResponse>('/admin/seed/custom');
        return response.data;
    },
};
