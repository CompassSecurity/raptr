import { ref, watch } from 'vue';

const REQUIRED_CLICKS = 5;
const TIME_WINDOW_MS = 2000;
const HTML_CLASS = 'anaglyph-active';

/**
 * Anaglyph composable — tracks rapid clicks and toggles a whole-page
 * anaglyph effect by adding/removing a CSS class on <html>.
 *
 * Call `registerClick()` on each click. If 5 clicks land within 2 seconds,
 * the effect toggles on/off.
 */
export function useAnaglyph() {
    const activated = ref(false);
    const clickTimestamps: number[] = [];

    function registerClick() {
        const now = Date.now();
        clickTimestamps.push(now);

        // Keep only clicks within the time window
        while (
            clickTimestamps.length > 0 &&
            now - clickTimestamps[0] > TIME_WINDOW_MS
        ) {
            clickTimestamps.shift();
        }

        if (clickTimestamps.length >= REQUIRED_CLICKS) {
            activated.value = !activated.value;
            clickTimestamps.length = 0;
        }
    }

    // Sync the CSS class on <html>
    watch(activated, (active) => {
        if (active) {
            document.documentElement.classList.add(HTML_CLASS);
        } else {
            document.documentElement.classList.remove(HTML_CLASS);
        }
    });

    return { activated, registerClick };
}
