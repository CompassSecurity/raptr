/**
 * Shared component types and interfaces
 */

// Re-export pagination types from utils.ts (single source of truth)
export type {
    ColumnFilters,
    ColumnFilterValue,
    PaginationParams,
    PaginationState,
} from './utils';

// Modal component types
export interface ModalProps {
    open: boolean;
}

export interface ModalEmits {
    (e: 'update:open', value: boolean): void;
    (e: 'success'): void;
}

// Confirm Dialog types
export interface ConfirmDialogProps {
    open: boolean;
    title: string;
    description: string;
    confirmText?: string;
    cancelText?: string;
    variant?: 'default' | 'destructive';
    loading?: boolean;
}

export interface ConfirmDialogEmits {
    (e: 'update:open', value: boolean): void;
    (e: 'confirm'): void;
    (e: 'cancel'): void;
}
