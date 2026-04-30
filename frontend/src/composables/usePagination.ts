import { ref } from 'vue';
import type { ColumnFilters, ColumnFilterValue } from '@/types/components';

export const PAGE_SIZE_OPTIONS = [10, 20, 50, 100, 1000] as const;
export type PageSizeOption = (typeof PAGE_SIZE_OPTIONS)[number];

export type SortState = {
    column: string;
    direction: 'asc' | 'desc';
} | null;

// Flat params type - filters are flattened to top level
export type FlatPaginationParams = {
    offset?: number;
    limit?: number;
    sort_by?: string;
    sort_order?: 'asc' | 'desc';
    [key: string]: string | string[] | boolean | boolean[] | number | undefined;
};

export function usePagination(
    fetchFn: (params: FlatPaginationParams) => Promise<void>,
    initialPageSize: PageSizeOption = 100,
) {
    const currentPage = ref(1);
    const pageSize = ref<number>(initialPageSize);
    const columnFilters = ref<ColumnFilters>({});
    const sortState = ref<SortState>(null);

    const getParams = (): FlatPaginationParams => {
        const offset = (currentPage.value - 1) * pageSize.value;

        // Build flat params with filters at top level
        const params: FlatPaginationParams = {
            offset,
            limit: pageSize.value,
            sort_by: sortState.value?.column,
            sort_order: sortState.value?.direction,
        };

        // Flatten filters directly into params
        for (const [key, value] of Object.entries(columnFilters.value)) {
            if (value !== undefined && value !== null && value !== '') {
                if (Array.isArray(value) && value.length === 0) continue;
                params[key] = value;
            }
        }

        return params;
    };

    const fetch = async () => {
        await fetchFn(getParams());
    };

    const handleColumnFilterChange = async (
        columnId: string,
        value: ColumnFilterValue | undefined,
    ) => {
        if (
            value === undefined ||
            value === null ||
            value === '' ||
            (Array.isArray(value) && value.length === 0)
        ) {
            // eslint-disable-next-line @typescript-eslint/no-unused-vars
            const { [columnId]: _, ...rest } = columnFilters.value;
            columnFilters.value = rest;
        } else {
            columnFilters.value = { ...columnFilters.value, [columnId]: value };
        }
        currentPage.value = 1; // Reset to first page on filter change
        await fetch();
    };

    const handlePageChange = async (page: number) => {
        currentPage.value = page;
        await fetch();
    };

    const handlePageSizeChange = async (newSize: number) => {
        pageSize.value = newSize;
        currentPage.value = 1; // Reset to first page when changing page size
        await fetch();
    };

    const handleSortChange = async (
        column: string | null,
        direction: 'asc' | 'desc' | null,
    ) => {
        if (column && direction) {
            sortState.value = { column, direction };
        } else {
            sortState.value = null;
        }
        currentPage.value = 1; // Reset to first page when sorting changes
        await fetch();
    };

    const resetPagination = () => {
        currentPage.value = 1;
        columnFilters.value = {};
        sortState.value = null;
    };

    return {
        currentPage,
        pageSize,
        columnFilters,
        sortState,
        fetch,
        handleColumnFilterChange,
        handlePageChange,
        handlePageSizeChange,
        handleSortChange,
        resetPagination,
        getParams,
    };
}
