// postcss.config.js
// Proper PostCSS setup for Tailwind v4 using the new plugin package.
import tailwind from "@tailwindcss/postcss";
import autoprefixer from "autoprefixer";

export default {
  plugins: [
    tailwind(),      // Enable Tailwind v4 as a PostCSS plugin
    autoprefixer()   // Add vendor prefixes automatically
  ]
};
