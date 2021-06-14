module.exports = {
  mode: 'jit',
  purge: [
    '/app/assets/**/*.js',
    '/app/**/*.html'
  ],
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
};
