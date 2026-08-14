"use client";

import { useEffect, useState } from "react";

export type LandingAssetSlot = "hero" | "features/welcome" | "features/help" | "features/work" | "workflows" | "stories";

// Local files are discovered by the landing page and passed into this focused client sequencer.
export function LandingImage({ slot, label, className, sources }: { slot: LandingAssetSlot; label: string; className: string; sources: string[] }) {
  const [index, setIndex] = useState(0);
  const [availableSources, setAvailableSources] = useState(sources);
  const src = availableSources[index];
  const sourceKey = sources.join("\u0000");

  useEffect(() => {
    setAvailableSources(sources);
    setIndex(0);
  }, [sourceKey]);

  useEffect(() => {
    if (availableSources.length < 2) return;
    const timer = window.setInterval(() => setIndex((current) => (current + 1) % availableSources.length), 5200);
    return () => window.clearInterval(timer);
  }, [availableSources.length]);

  const discardBrokenSource = () => {
    setAvailableSources((current) => {
      const next = current.filter((candidate) => candidate !== src);
      setIndex((currentIndex) => Math.min(currentIndex, Math.max(next.length - 1, 0)));
      return next;
    });
  };

  return (
    <div className={className} data-asset-slot={slot} data-image-count={availableSources.length} role="img" aria-label={label}>
      {src ? <img className="landing-image-frame" key={src} src={src} alt="" onError={discardBrokenSource} /> : null}
    </div>
  );
}
