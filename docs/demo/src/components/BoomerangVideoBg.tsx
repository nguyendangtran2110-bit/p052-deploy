import { useEffect, useRef, useState } from "react";

const VIDEO_URL =
  "https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260715_090628_7052d8a6-a094-4341-a4a2-ad58493a67a9.mp4";

type VideoWithFrameCallback = HTMLVideoElement & {
  requestVideoFrameCallback?: (callback: (now: number, metadata: { mediaTime: number }) => void) => number;
  cancelVideoFrameCallback?: (handle: number) => void;
};

export default function BoomerangVideoBg() {
  const videoRef = useRef<VideoWithFrameCallback | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const scratchRef = useRef<HTMLCanvasElement | null>(null);
  const framesRef = useRef<ImageData[]>([]);
  const captureHandleRef = useRef<number | null>(null);
  const captureActiveRef = useRef(false);
  const lastTimeRef = useRef<number | null>(null);
  const [framesReady, setFramesReady] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    const updatePreference = () => setReducedMotion(mediaQuery.matches);
    updatePreference();
    mediaQuery.addEventListener("change", updatePreference);
    return () => mediaQuery.removeEventListener("change", updatePreference);
  }, []);

  useEffect(() => {
    const video = videoRef.current;
    const displayCanvas = canvasRef.current;
    if (!video || !displayCanvas) return;

    const scratch = document.createElement("canvas");
    scratchRef.current = scratch;
    const scratchContext = scratch.getContext("2d", { willReadFrequently: true });
    const displayContext = displayCanvas.getContext("2d");
    if (!scratchContext || !displayContext) return;

    const drawFrame = (frame: ImageData) => {
      displayCanvas.width = frame.width;
      displayCanvas.height = frame.height;
      displayContext.putImageData(frame, 0, 0);
    };

    const captureFrame = () => {
      if (!captureActiveRef.current || video.readyState < 2 || video.ended) return;
      const naturalWidth = video.videoWidth || 960;
      const naturalHeight = video.videoHeight || Math.round(naturalWidth * 0.5625);
      const width = Math.min(960, naturalWidth);
      const height = Math.max(1, Math.round((width / naturalWidth) * naturalHeight));
      if (scratch.width !== width || scratch.height !== height) {
        scratch.width = width;
        scratch.height = height;
      }
      if (lastTimeRef.current === video.currentTime) return;
      scratchContext.drawImage(video, 0, 0, width, height);
      framesRef.current.push(scratchContext.getImageData(0, 0, width, height));
      lastTimeRef.current = video.currentTime;
      if (framesRef.current.length === 1) drawFrame(framesRef.current[0]);
    };

    const scheduleCapture = () => {
      if (!captureActiveRef.current) return;
      if (typeof video.requestVideoFrameCallback === "function") {
        captureHandleRef.current = video.requestVideoFrameCallback(() => {
          captureFrame();
          scheduleCapture();
        });
      } else {
        captureHandleRef.current = window.requestAnimationFrame(() => {
          captureFrame();
          scheduleCapture();
        });
      }
    };

    const handleLoaded = () => {
      if (reducedMotion) {
        video.pause();
        return;
      }
      captureActiveRef.current = true;
      void video.play().then(scheduleCapture).catch(() => undefined);
    };

    const handleEnded = () => {
      captureActiveRef.current = false;
      if (captureHandleRef.current !== null && typeof video.cancelVideoFrameCallback === "function") {
        video.cancelVideoFrameCallback(captureHandleRef.current);
      }
      if (framesRef.current.length > 0) {
        drawFrame(framesRef.current[0]);
        setFramesReady(true);
      }
    };

    video.addEventListener("loadeddata", handleLoaded);
    video.addEventListener("ended", handleEnded);
    if (video.readyState >= 2) handleLoaded();

    return () => {
      captureActiveRef.current = false;
      if (captureHandleRef.current !== null) {
        if (typeof video.cancelVideoFrameCallback === "function") {
          video.cancelVideoFrameCallback(captureHandleRef.current);
        } else {
          window.cancelAnimationFrame(captureHandleRef.current);
        }
      }
      video.removeEventListener("loadeddata", handleLoaded);
      video.removeEventListener("ended", handleEnded);
    };
  }, [reducedMotion]);

  useEffect(() => {
    if (!framesReady || reducedMotion) return;
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d");
    if (!canvas || !context || framesRef.current.length === 0) return;

    let index = 0;
    let direction = 1;
    const draw = () => {
      const frames = framesRef.current;
      if (frames.length === 0) return;
      context.putImageData(frames[index], 0, 0);
      if (index >= frames.length - 1) direction = -1;
      if (index <= 0) direction = 1;
      index += direction;
    };
    draw();
    const interval = window.setInterval(draw, 1000 / 30);
    return () => window.clearInterval(interval);
  }, [framesReady, reducedMotion]);

  return (
    <div className="absolute inset-0 z-0 scale-[1.15] origin-top overflow-hidden" aria-hidden="true">
      <video
        ref={videoRef}
        src={VIDEO_URL}
        muted
        playsInline
        preload="auto"
        crossOrigin="anonymous"
        className={`h-full w-full object-cover object-top ${framesReady ? "hidden" : "block"}`}
      />
      <canvas
        ref={canvasRef}
        className={`h-full w-full object-cover object-top ${framesReady ? "block" : "hidden"}`}
      />
      <div className="pointer-events-none absolute inset-0 bg-white/15" />
    </div>
  );
}
