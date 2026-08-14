import Link from "next/link";
import fs from "node:fs";
import path from "node:path";
import { LandingImage, type LandingAssetSlot } from "@/src/components/landing-image";
import { ThemeButton } from "@/src/components/theme-button";

const features: Array<{ title: string; body: string; slot: "features/welcome" | "features/help" | "features/work" }> = [
  {
    title: "Arrive with your bearings",
    body: "A clear welcome path brings building guidance, resident benefits, and the next useful step into one place.",
    slot: "features/welcome",
  },
  {
    title: "Ask when you need to",
    body: "Homie Agent helps you find approved building guidance. When something needs attention, you can prepare a support request on your terms.",
    slot: "features/help",
  },
  {
    title: "Keep building work in context",
    body: "Residents see their own progress and requests. Managers work within their assigned building and floor scope.",
    slot: "features/work",
  },
];

const imageExtensions = new Set([".avif", ".gif", ".jpeg", ".jpg", ".png", ".webp"]);
const assetDirectories: Record<LandingAssetSlot, string[]> = {
  hero: ["hero"],
  "features/welcome": ["features/welcome", "features"],
  "features/help": ["features/help", "features"],
  "features/work": ["features/work", "features"],
  workflows: ["workflows"],
  stories: ["stories"],
};

function assetSources(slot: LandingAssetSlot) {
  const root = path.join(process.cwd(), "public", "landing");
  const featureName = slot.startsWith("features/") ? slot.split("/")[1] : null;
  const sources = assetDirectories[slot].flatMap((directory) => {
    const absoluteDirectory = path.join(root, directory);
    try {
      return fs.readdirSync(absoluteDirectory, { withFileTypes: true })
        .filter((entry) => entry.isFile() && imageExtensions.has(path.extname(entry.name).toLowerCase()))
        .filter((entry) => directory !== "features" || !featureName || entry.name.toLowerCase().startsWith(`${featureName}-`))
        .map((entry) => `/landing/${[...directory.split("/"), entry.name].map(encodeURIComponent).join("/")}`);
    } catch {
      return [];
    }
  });
  return [...new Set(sources)].sort((left, right) => left.localeCompare(right));
}

export default function Home() {
  return (
    <div className="public-shell landing-shell">
      <a className="skip-link" href="#main-content">Skip to content</a>
      <header className="public-topbar landing-topbar">
        <Link className="brand" href="/" aria-label="OnBxrd home">
          <span className="brand-mark" aria-hidden="true"><i /><i /><i /></span>
          <span>OnBxrd</span>
        </Link>
        <div className="landing-topbar-actions">
          <Link className="landing-sign-in" href="/login">Sign in</Link>
          <ThemeButton />
        </div>
      </header>

      <main id="main-content" tabIndex={-1} className="landing-main">
        <section className="landing-hero" aria-labelledby="landing-title">
          <div className="landing-hero-copy">
            <h1 id="landing-title">A more settled start to building life.</h1>
            <p>OnBxrd gives residents a calm place to get oriented, find what applies to their home, and ask for support. It gives building teams a focused workspace for the work they are trusted to do.</p>
            <div className="landing-actions">
              <Link className="button button-primary" href="/login">Sign in to OnBxrd</Link>
              <Link className="button button-secondary" href="/register">Create an account</Link>
            </div>
          </div>
          <div className="landing-hero-stage">
            <LandingImage className="landing-art landing-art-hero" slot="hero" sources={assetSources("hero")} label="A welcoming OnBxrd home stage. Local images from the landing hero folder rotate here." />
            <p className="landing-art-caption">Your building, made easier to understand.</p>
          </div>
        </section>

        <section className="landing-proof" aria-label="What OnBxrd helps with">
          <p>Welcome with clarity</p>
          <p>Guidance that stays grounded</p>
          <p>Support with a visible next step</p>
        </section>

        <section className="landing-features" aria-labelledby="features-title">
          <div className="landing-section-intro">
            <h2 id="features-title">One home for the moments that shape a good welcome.</h2>
            <p>From the first week through everyday questions, the experience stays clear about what is known, what happens next, and what needs your review.</p>
          </div>
          <div className="landing-feature-grid">
            {features.map((feature) => (
              <article className="landing-feature" key={feature.title}>
                <LandingImage className="landing-art landing-art-feature" slot={feature.slot} sources={assetSources(feature.slot)} label={`Local image set for ${feature.title.toLowerCase()}.`} />
                <h3>{feature.title}</h3>
                <p>{feature.body}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="landing-workflow" aria-labelledby="workflow-title">
          <div className="landing-workflow-art">
            <LandingImage className="landing-art landing-art-workflow" slot="workflows" sources={assetSources("workflows")} label="Local image set for the OnBxrd support workflow." />
          </div>
          <div className="landing-workflow-copy">
            <h2 id="workflow-title">A helpful answer is only useful when it leads somewhere clear.</h2>
            <p>Homie Agent can explain approved guidance and point residents toward the right next step. Requests remain visible and require the resident&apos;s own review before anything is submitted.</p>
            <ol className="landing-steps">
              <li>Find the building guidance that applies.</li>
              <li>Get help framing a request when needed.</li>
              <li>Review and submit only when you are ready.</li>
            </ol>
          </div>
        </section>

        <section className="landing-closing" aria-labelledby="closing-title">
          <LandingImage className="landing-art landing-art-story" slot="stories" sources={assetSources("stories")} label="Local image set for an OnBxrd building story." />
          <div className="landing-closing-copy">
            <h2 id="closing-title">Start with the workspace made for your role.</h2>
            <p>Sign in to continue your resident or manager journey, or create a synthetic preview account to explore OnBxrd.</p>
            <div className="landing-actions">
              <Link className="button button-primary" href="/login">Sign in</Link>
              <Link className="button button-quiet" href="/register">Create an account</Link>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
