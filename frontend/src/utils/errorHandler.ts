import type { AxiosError } from 'axios';
import { toast } from 'vue-sonner';

interface ValidationError {
    loc: (string | number)[];
    msg: string;
    type: string;
}

interface FastAPIError {
    detail?: string | ValidationError[];
}

export function handleApiError(error: AxiosError<FastAPIError>) {
    // Network error (no response)
    if (!error.response) {
        toast.error('Network Error', {
            description:
                'Unable to connect to the server. Please check your internet connection.',
        });
        return;
    }

    const status = error.response.status;
    const data = error.response.data;

    switch (status) {
        case 401:
            toast.error('Unauthorized', {
                description:
                    typeof data?.detail === 'string'
                        ? data.detail
                        : 'Please log in.',
            });
            break;

        case 403:
            toast.error('Forbidden', {
                description:
                    typeof data?.detail === 'string'
                        ? data.detail
                        : 'You do not have permission to perform this action.',
            });
            break;

        case 404:
            toast.error('Not Found', {
                description:
                    typeof data?.detail === 'string'
                        ? data.detail
                        : 'The requested resource was not found.',
            });
            break;

        case 409:
            toast.error('Conflict', {
                description:
                    typeof data?.detail === 'string'
                        ? data.detail
                        : 'This resource was modified by another user.',
            });
            break;

        case 422:
            // FastAPI validation errors
            if (Array.isArray(data?.detail)) {
                const errors = data.detail as ValidationError[];
                const errorMessages = errors
                    .map((err) => {
                        const field = err.loc.slice(1).join('.');
                        return field ? `${field}: ${err.msg}` : err.msg;
                    })
                    .join(', ');

                toast.error('Validation Error', {
                    description: errorMessages,
                });
            } else if (typeof data?.detail === 'string') {
                toast.error('Validation Error', {
                    description: data.detail,
                });
            } else {
                toast.error('Validation Error', {
                    description: 'Please check your input and try again.',
                });
            }
            break;

        case 500:
            toast.error('Server Error', {
                description:
                    typeof data?.detail === 'string'
                        ? data.detail
                        : 'An internal server error occurred. Please try again later.',
            });
            break;

        default: {
            // Generic error with detail if available
            const message =
                typeof data?.detail === 'string'
                    ? data.detail
                    : `An error occurred (${status})`;

            toast.error('Error', {
                description: message,
            });
        }
    }
}
