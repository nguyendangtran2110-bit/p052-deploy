# OnBxrd demo

Local Vite/React prototype for the resident onboarding, simulated Zalo signal, ticket draft, and manager workflow.

```bash
npm install
npm run dev
```

Run deterministic detection checks and a production build with:

```bash
npm run test:rules
npm run build
```

The Zalo tab is simulated: it replays local fixtures and never calls Zalo or sends a real message.
