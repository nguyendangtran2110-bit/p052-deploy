import coreWebVitals from "eslint-config-next/core-web-vitals";
import nextTypescript from "eslint-config-next/typescript";

const config = [
  ...coreWebVitals,
  ...nextTypescript,
  { ignores: [".next/**", "coverage/**", "playwright-report/**", "test-results/**"] },
];

export default config;
