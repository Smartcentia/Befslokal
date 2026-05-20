import next from 'eslint-config-next';

export default [
  ...next,
  {
    files: ['**/*.ts', '**/*.tsx'],
    rules: {
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/no-unused-vars': [
        'warn',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }
      ],
      'react-hooks/exhaustive-deps': 'warn',
      'react/jsx-no-comment-textnodes': 'off',
      'react/no-unescaped-entities': 'off',
      'prefer-const': 'warn',
      'react-hooks/set-state-in-effect': 'off',
      '@next/next/no-img-element': 'warn'
    }
  }
];