import type { AclBase, AclRead } from '@/types/utils';
import { api } from './api';

export const aclService = {
    async getAcls(): Promise<AclRead[]> {
        const response = await api.get<AclRead[]>('/acl/');
        return response.data;
    },

    async getAcl(aclId: string): Promise<AclRead> {
        const response = await api.get<AclRead>(`/acl/${aclId}`);
        return response.data;
    },

    async getAssessmentAcls(assessmentId: string): Promise<AclRead[]> {
        const response = await api.get<AclRead[]>(
            `/acl/assessment/${assessmentId}`,
        );
        return response.data;
    },

    async getUserAcls(userId: string): Promise<AclRead[]> {
        const response = await api.get<AclRead[]>(`/acl/user/${userId}`);
        return response.data;
    },

    async createAcl(data: AclBase): Promise<AclRead> {
        const response = await api.post<AclRead>('/acl/', data);
        return response.data;
    },

    async updateAcl(aclId: string, data: AclBase): Promise<AclRead> {
        const response = await api.put<AclRead>(`/acl/${aclId}`, data);
        return response.data;
    },

    async deleteAcl(aclId: string): Promise<void> {
        await api.delete(`/acl/${aclId}`);
    },
};
