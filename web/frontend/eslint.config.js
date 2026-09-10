import js from '@eslint/js'
import pluginVue from 'eslint-plugin-vue'
import tseslint from 'typescript-eslint'
import prettier from 'eslint-config-prettier'
import globals from 'globals'

export default tseslint.config(
  {
    ignores: [
      'dist/**',
      'node_modules/**',
      'playwright-report/**',
      'test-results/**',
      'src/api/schema.d.ts',
    ],
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  ...pluginVue.configs['flat/recommended'],
  {
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
  },
  {
    files: ['**/*.vue'],
    languageOptions: {
      parserOptions: {
        parser: tseslint.parser,
      },
    },
    rules: {
      // <Toaster/> is the documented public name for the FE-010 toast host.
      // FE-012 primitives use the conventional short names as their public API.
      'vue/multi-word-component-names': [
        'error',
        {
          ignores: ['Toaster', 'Button', 'Input', 'Select', 'Badge', 'Chip', 'Card', 'Modal', 'Spinner'],
        },
      ],
    },
  },
  {
    files: ['src/components/ui/**/*.vue'],
    rules: {
      // Primitives expose optional props on purpose (undefined selects the slot
      // fallback / default styling); defaults are handled via `withDefaults`
      // and template fallbacks rather than per-prop default values.
      'vue/require-default-prop': 'off',
    },
  },
  prettier,
)
