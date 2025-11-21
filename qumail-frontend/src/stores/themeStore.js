import { create } from 'zustand';
import { persist } from 'zustand/middleware';
export const useThemeStore = create()(persist((set, get) => ({
    theme: 'system',
    actualTheme: 'light',
    setTheme: (theme) => {
        set({ theme });
        get().initializeTheme();
    },
    initializeTheme: () => {
        const { theme } = get();
        let actualTheme = 'light';
        if (theme === 'system') {
            actualTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        }
        else {
            actualTheme = theme;
        }
        set({ actualTheme });
        // Apply theme to document
        if (actualTheme === 'dark') {
            document.documentElement.classList.add('dark');
        }
        else {
            document.documentElement.classList.remove('dark');
        }
    },
}), {
    name: 'qumail-theme',
}));
// Listen for system theme changes
if (typeof window !== 'undefined') {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
        const store = useThemeStore.getState();
        if (store.theme === 'system') {
            store.initializeTheme();
        }
    });
}
