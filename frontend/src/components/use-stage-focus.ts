"use client";

import { useLayoutEffect, useRef } from "react";

export function useStageFocus(stage: string) {
  const rootRef = useRef<HTMLDivElement>(null);
  const initialStage = useRef(stage);

  useLayoutEffect(() => {
    if (initialStage.current === stage) return;
    const target = rootRef.current?.querySelector<HTMLElement>("[data-stage-focus]");
    if (!target) return;
    if (!target.hasAttribute("tabindex")) target.tabIndex = -1;
    target.focus({ preventScroll: true });
  }, [stage]);

  return rootRef;
}
