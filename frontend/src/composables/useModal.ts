import { ref } from 'vue';

export function useModal() {
    const isOpen = ref(false);

    const open = () => {
        isOpen.value = true;
    };

    const close = () => {
        isOpen.value = false;
    };

    const toggle = () => {
        isOpen.value = !isOpen.value;
    };

    return {
        isOpen,
        open,
        close,
        toggle,
    };
}

export function useModalWithData<T>() {
    const isOpen = ref(false);
    const data = ref<T | null>(null);

    const open = (item: T) => {
        data.value = item;
        isOpen.value = true;
    };

    const close = () => {
        isOpen.value = false;
        // Don't clear data immediately to prevent flash during close animation
        setTimeout(() => {
            data.value = null;
        }, 300);
    };

    const toggle = (item?: T) => {
        if (isOpen.value) {
            close();
        } else if (item) {
            open(item);
        }
    };

    return {
        isOpen,
        data,
        open,
        close,
        toggle,
    };
}
