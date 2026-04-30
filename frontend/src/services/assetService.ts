import type {
    AssetBase,
    AssetRead,
    PaginatedResponse,
    PaginationParams,
} from '@/types/utils';
import { api } from './api';

export const assetService = {
    /**
     * Get all assets for an assessment
     * @param assessmentId - Assessment ID
     * @param params - Pagination parameters (offset, limit, query)
     * @returns Paginated list of assets
     */
    async getAssets(
        assessmentId: string,
        params?: PaginationParams,
    ): Promise<PaginatedResponse<AssetRead>> {
        const response = await api.get<PaginatedResponse<AssetRead>>(
            `/assessments/${assessmentId}/asset/`,
            { params },
        );
        return response.data;
    },

    /**
     * Get a single asset by ID
     * @param assessmentId - Assessment ID
     * @param assetId - Asset ID
     * @returns Asset details
     */
    async getAsset(assessmentId: string, assetId: string): Promise<AssetRead> {
        const response = await api.get<AssetRead>(
            `/assessments/${assessmentId}/asset/${assetId}`,
        );
        return response.data;
    },

    /**
     * Create a new asset
     * @param assessmentId - Assessment ID
     * @param data - Asset data (name, icon, properties)
     * @returns Created asset
     */
    async createAsset(
        assessmentId: string,
        data: AssetBase,
    ): Promise<AssetRead> {
        const response = await api.post<AssetRead>(
            `/assessments/${assessmentId}/asset/`,
            data,
        );
        return response.data;
    },

    /**
     * Update an existing asset
     * @param assessmentId - Assessment ID
     * @param assetId - Asset ID
     * @param data - Updated asset data
     * @returns Updated asset
     */
    async updateAsset(
        assessmentId: string,
        assetId: string,
        data: AssetBase,
    ): Promise<AssetRead> {
        const response = await api.put<AssetRead>(
            `/assessments/${assessmentId}/asset/${assetId}`,
            data,
        );
        return response.data;
    },

    /**
     * Toggle delete status of an asset (soft delete)
     * @param assessmentId - Assessment ID
     * @param assetId - Asset ID
     */
    async toggleDeleteAsset(
        assessmentId: string,
        assetId: string,
    ): Promise<void> {
        await api.put(`/assessments/${assessmentId}/asset/${assetId}/delete`);
    },
};
