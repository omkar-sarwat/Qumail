import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react({
      // Use automatic JSX runtime for better performance
      jsxRuntime: 'automatic',
    }),
  ],
  optimizeDeps: {
    esbuildOptions: {
      loader: {
        '.js': 'jsx',
      },
    },
    // Pre-bundle commonly used dependencies
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      'axios',
      'zustand',
      'lucide-react',
      'react-hot-toast',
      '@tanstack/react-query',
    ],
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 5173,
    strictPort: false, // Allow fallback to another port
    // Enable HMR with overlay disabled to reduce visual noise
    hmr: {
      overlay: false,
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    // Production optimizations
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true, // Remove console.log in production
        drop_debugger: true,
      },
    },
    // Generate source maps for production debugging
    sourcemap: false,
    // Chunk splitting for better caching
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          'vendor-ui': ['@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu', '@radix-ui/react-select', '@radix-ui/react-switch', '@radix-ui/react-tabs', '@radix-ui/react-toast', '@radix-ui/react-tooltip'],
          'vendor-utils': ['axios', 'zustand', 'date-fns', 'clsx', 'tailwind-merge'],
          'vendor-icons': ['lucide-react'],
          'vendor-editor': ['@tiptap/react', '@tiptap/starter-kit', '@tiptap/extension-link', '@tiptap/extension-underline'],
        },
        // Consistent chunk naming for better caching
        chunkFileNames: 'assets/[name]-[hash].js',
        entryFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]',
      },
    },
    // Increase chunk size warning limit
    chunkSizeWarningLimit: 1000,
  },
  // Enable CSS code splitting
  css: {
    devSourcemap: true,
  },
  base: './',
  // Define environment variables
  define: {
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version || '1.0.0'),
  },
})