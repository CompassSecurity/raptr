import { ref } from 'vue';
import { toast } from 'vue-sonner';

export function useFormSubmit<T = any>(
    submitFn: (data: T) => Promise<void>,
    options?: {
        successMessage?: string;
        onSuccess?: () => void;
        onError?: (error: any) => void;
    },
) {
    const isSubmitting = ref(false);
    const error = ref<string | null>(null);

    const submit = async (data: T) => {
        isSubmitting.value = true;
        error.value = null;

        try {
            await submitFn(data);

            if (options?.successMessage) {
                toast.success(options.successMessage);
            }

            options?.onSuccess?.();
        } catch (err: any) {
            error.value = err.message || 'An error occurred';
            options?.onError?.(err);
            throw err; // Re-throw so caller can handle if needed
        } finally {
            isSubmitting.value = false;
        }
    };

    const reset = () => {
        isSubmitting.value = false;
        error.value = null;
    };

    return {
        isSubmitting,
        error,
        submit,
        reset,
    };
}
