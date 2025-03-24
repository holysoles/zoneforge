const { defineConfig } = require("eslint/config");
const js = require("@eslint/js")
const globals = require("globals")

module.exports = defineConfig([
  {
    plugins: {
			js,
		},
    extends: ["js/recommended"],
    files: ["static/js/*.js"],
    languageOptions: { 
      ecmaVersion: 2022,
      sourceType: "script",
      globals: {
        ...globals.browser,
      }
    },
		rules: {
      "no-unused-vars": ["error", { 
        "varsIgnorePattern": "^_", 
        "argsIgnorePattern": "^_" 
      }]
		},
  },
]);