import { fixupPluginRules } from '@eslint/compat';
import eslint from '@eslint/js';
import microsoftSdlPlugin from '@microsoft/eslint-plugin-sdl';
import eslintConfigPrettier from 'eslint-config-prettier';
import importPlugin from 'eslint-plugin-import';
import jestPlugin from 'eslint-plugin-jest';
import jsxA11yPlugin from 'eslint-plugin-jsx-a11y';
import nodePlugin from 'eslint-plugin-n';
import noSecrets from 'eslint-plugin-no-secrets';
import promisePlugin from 'eslint-plugin-promise';
import reactPlugin from 'eslint-plugin-react';
import reactHooksPlugin from 'eslint-plugin-react-hooks';
import pluginSecurity from 'eslint-plugin-security';
import globals from 'globals';
import tsEslint from 'typescript-eslint'; // eslint-disable-line import/no-unresolved

const make_config_for_node_typescript_dir = (dir_path) => ({
  files: [`${dir_path}/src/**/*.ts`],

  ...nodePlugin.configs['flat/recommended'],

  languageOptions: {
    globals: {
      ...globals.node,
    },
  },

  settings: {
    'import/resolver': {
      node: {
        moduleDirectory: [dir_path, `${dir_path}/node_modules/`],
      },
    },
  },

  rules: {
    'n/no-extraneous-import': [
      'error',
      {
        allowModules: ['src'],
      },
    ],

    'n/no-unsupported-features/es-syntax': [
      'error',
      {
        ignores: ['modules'],
      },
    ],

    'n/no-unsupported-features/node-builtins': [
      'error',
      {
        ignores: ['fetch'],
      },
    ],

    'n/no-missing-import': 'off', // https://github.com/mysticatea/eslint-plugin-node/issues/248

    'no-console': 'off',
    'security/detect-object-injection': 'off',
  },
});

const make_config_for_react_spa_dir = (dir_path) => ({
  // React SPA environment
  files: [`${dir_path}/src/**/*.js`, `${dir_path}/src/**/*.jsx`],

  ...reactPlugin.configs.flat.recommended,
  ...reactPlugin.configs.flat['jsx-runtime'],
  ...jsxA11yPlugin.flatConfigs.recommended,

  plugins: {
    'react-hooks': fixupPluginRules(reactHooksPlugin),
  },

  languageOptions: {
    globals: {
      ...globals.browser,
    },
    ...reactPlugin.configs.flat.recommended.languageOptions,
  },

  settings: {
    'import/resolver': {
      node: {
        moduleDirectory: [dir_path, `${dir_path}/node_modules/`],
      },
    },

    react: {
      version: '18',
    },
  },

  rules: {
    ...reactHooksPlugin.configs.recommended.rules,

    'react/prop-types': 'off',
  },
});

export default [
  eslint.configs.recommended,

  ...tsEslint.configs.strict,
  ...tsEslint.configs.stylistic,

  ...microsoftSdlPlugin.configs.common,

  promisePlugin.configs['flat/recommended'],

  importPlugin.flatConfigs.errors,
  importPlugin.flatConfigs.warnings,
  importPlugin.flatConfigs.typescript,

  pluginSecurity.configs.recommended,

  eslintConfigPrettier,

  {
    ignores: [
      'k8s',
      '**/dist', // generated (build outputs)
    ],
  },

  {
    plugins: {
      'no-secrets': noSecrets,
    },

    languageOptions: {
      parser: tsEslint.parser,
      ecmaVersion: 5,
      sourceType: 'module',
    },

    rules: {
      camelcase: 'off',
      'comma-dangle': ['error', 'always-multiline'],
      'no-unused-vars': 'off', // covered by @typescript-eslint/no-unused-vars
      'no-use-before-define': 'off', // covered by @typescript-eslint/no-use-before-define
      'no-throw-literal': 'error',

      'no-restricted-imports': [
        'error',
        {
          patterns: ['../*'],
        },
      ],

      'import/order': [
        'warn',
        {
          'newlines-between': 'always-and-inside-groups',

          alphabetize: {
            order: 'asc',
            caseInsensitive: true,
          },

          groups: [
            'builtin',
            'external',
            'internal',
            'parent',
            ['sibling', 'index'],
          ],
          // We can group imports further by adding rules here, the order they're defined in breaks ties when group and position are equal
          pathGroups: [],
        },
      ],

      'import/extensions': ['error', 'ignorePackages'],
      '@typescript-eslint/no-use-before-define': 'error',
      '@typescript-eslint/no-explicit-any': 'error',

      '@typescript-eslint/no-unused-vars': [
        'warn',
        {
          ignoreRestSiblings: true,
          argsIgnorePattern: '^_.+',
        },
      ],

      '@typescript-eslint/no-redeclare': 'error',

      'no-secrets/no-secrets': 'error',
    },
  },

  {
    // jest environment
    files: ['**/*.test.js', '**/*.test.ts', '**/*.test.tsx'],

    plugins: {
      jest: jestPlugin,
    },

    languageOptions: {
      globals: {
        ...jestPlugin.environments.globals.globals,
      },
    },

    rules: {
      'jest/no-disabled-tests': 'warn',
      'jest/no-focused-tests': 'error',
      'jest/no-identical-title': 'error',
      'jest/prefer-to-have-length': 'warn',
      'jest/valid-expect': 'error',
    },
  },

  {
    // node scripts environment
    files: ['**/*.cjs', '**/*.mjs'],

    ...nodePlugin.configs['flat/recommended-script'],

    languageOptions: {
      globals: {
        ...globals.node,
      },
    },

    rules: {
      '@typescript-eslint/no-require-imports': 'off',
    },
  },

  ...['federator', 'transfer-inbound', 'transfer-outbound'].map(
    make_config_for_node_typescript_dir,
  ),

  ...['demo-transfer-dashboard'].map(make_config_for_react_spa_dir),
];
