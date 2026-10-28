import {
    columnFilteringFeature,
    columnVisibilityFeature,
    createFilteredRowModel,
    createSortedRowModel,
    filterFn_equals,
    filterFn_includesString,
    rowSortingFeature,
    sortFn_alphanumeric,
    sortFn_basic,
    sortFn_datetime,
    sortFn_text,
    tableFeatures,
} from '@tanstack/vue-table';

// Features of the shared DataTable. The row models and functions are only used for
// client-side sorting/filtering; in manual (server-side) mode the table shows rows as given.
export const dataTableFeatures = tableFeatures({
    // columnVisibilityFeature provides row.getVisibleCells() used for rendering
    columnVisibilityFeature,
    columnFilteringFeature,
    rowSortingFeature,
    filteredRowModel: createFilteredRowModel(),
    sortedRowModel: createSortedRowModel(),
    filterFns: {
        includesString: filterFn_includesString,
        equals: filterFn_equals,
    },
    sortFns: {
        alphanumeric: sortFn_alphanumeric,
        text: sortFn_text,
        datetime: sortFn_datetime,
        basic: sortFn_basic,
    },
});

export type DataTableFeatures = typeof dataTableFeatures;
