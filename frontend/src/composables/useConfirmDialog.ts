import { ref } from 'vue';

export function useConfirmDialog<T = string>() {
    const isOpen = ref(false);
    const pendingItem = ref<T | null>(null);
    const isProcessing = ref(false);

    const open = (item: T) => {
        pendingItem.value = item;
        isOpen.value = true;
    };

    const close = () => {
        isOpen.value = false;
        setTimeout(() => {
            pendingItem.value = null;
        }, 300);
    };

    const confirm = async (action: (item: T) => Promise<void>) => {
        if (!pendingItem.value) return;

        isProcessing.value = true;
        try {
            await action(pendingItem.value);
            close();
        } finally {
            isProcessing.value = false;
        }
    };

    return {
        isOpen,
        pendingItem,
        isProcessing,
        open,
        close,
        confirm,
    };
}
