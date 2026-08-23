"use client";

import Image from "next/image";
import Link from "next/link";
import { ArrowLeft, ArrowRight, BellRing, Bot, CheckCircle2, Gift, Headphones, LayoutDashboard, MapPin, Sparkles } from "lucide-react";
import { useEffect, useRef, useState } from "react";

type Feature = {
  accent: "clay" | "sage" | "gold" | "blue" | "rose" | "cocoa";
  cta: string;
  description: string;
  href: string;
  icon: "onboarding" | "benefits" | "assistant" | "tickets" | "announcements" | "operations";
  images: string[];
  index: string;
  kicker: string;
  title: string;
};

const icons = { onboarding: CheckCircle2, benefits: Gift, assistant: Bot, tickets: Headphones, announcements: BellRing, operations: LayoutDashboard };
const AUTO_ADVANCE_MS = 20_000;
const IMAGE_ADVANCE_MS = 11_000;
const RESUME_AFTER_MS = 7_000;

function prefersReducedMotion() {
  return typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function useSceneImageIndex(images: string[], active: boolean) {
  const [imageIndex, setImageIndex] = useState(0);
  useEffect(() => {
    setImageIndex(0);
    if (!active || images.length < 2 || prefersReducedMotion()) return;
    const timer = window.setInterval(() => setImageIndex((current) => (current + 1) % images.length), IMAGE_ADVANCE_MS);
    return () => window.clearInterval(timer);
  }, [active, images.length]);
  return imageIndex;
}

function SceneImage({ alt, className, images, index, offset = 0 }: { alt: string; className: string; images: string[]; index: number; offset?: number }) {
  const src = images.length ? images[(index + offset) % images.length] : undefined;
  if (!src) return <div className={`${className} scene-image-empty`} aria-label={`${alt} will appear here`} role="img"><Sparkles size={20} aria-hidden="true" /><span>Ảnh giao diện sẽ xuất hiện ở đây</span></div>;
  return <div className={`${className} scene-image-frame`}><Image key={src} src={src} alt={alt} fill sizes="(max-width: 760px) 86vw, 48vw" className="scene-image" /></div>;
}

function FeatureVisual({ active, feature }: { active: boolean; feature: Feature }) {
  const index = useSceneImageIndex(feature.images, active);
  const imageProps = { images: feature.images, index };
  if (feature.icon === "onboarding") return <div className="scene scene-welcome"><div className="scene-welcome-note"><span>Chào mừng bạn về nhà</span><strong>Một khởi đầu gọn gàng</strong><small>Hồ sơ · Tòa nhà · Việc cần làm</small></div><SceneImage {...imageProps} className="scene-welcome-main" alt="Màn hình chào mừng OnBxrd" /><SceneImage {...imageProps} offset={1} className="scene-welcome-mini" alt="Tiến độ onboarding" /></div>;
  if (feature.icon === "benefits") return <div className="scene scene-benefits"><div className="scene-benefits-heading"><Gift size={18} /><span>Quyền lợi quanh bạn</span></div><SceneImage {...imageProps} className="scene-benefit-card scene-benefit-card-one" alt="Quyền lợi cư dân" /><SceneImage {...imageProps} offset={1} className="scene-benefit-card scene-benefit-card-two" alt="Tiện ích cư dân" /><SceneImage {...imageProps} offset={2} className="scene-benefit-card scene-benefit-card-three" alt="Ưu đãi cư dân" /><SceneImage {...imageProps} offset={3} className="scene-benefit-card scene-benefit-card-four" alt="Khám phá quyền lợi" /></div>;
  if (feature.icon === "assistant") return <div className="scene scene-assistant"><div className="hommie-chat"><header><span className="hommie-avatar"><Bot size={19} /></span><div><strong>Hommie Agent</strong><small>Trợ lý cư dân · Sẵn sàng hỗ trợ</small></div><span className="hommie-status">Trực tuyến</span></header><div className="hommie-messages"><p className="hommie-bubble">Xin chào, mình là trợ lý Hommie Agent.</p><p className="hommie-bubble">Mình có thể giúp bạn tìm hiểu thông tin tòa nhà, theo dõi yêu cầu hỗ trợ và chuẩn bị ticket.</p><p className="hommie-bubble hommie-bubble-warm">Bạn có thể hỏi mình về tiện ích, quy định hoặc một sự cố ở căn hộ. Xin hân hạnh làm quen nha!</p></div><div className="hommie-composer">Hỏi Hommie về tòa nhà của bạn <ArrowRight size={16} /></div></div><div className="hommie-sources"><span>Nguồn tham khảo</span><SceneImage {...imageProps} className="hommie-source-one" alt="Nguồn thông tin của Hommie" /><SceneImage {...imageProps} offset={1} className="hommie-source-two" alt="Bản xem trước câu trả lời Hommie" /></div></div>;
  if (feature.icon === "tickets") return <div className="scene scene-tickets"><div className="ticket-path"><span className="ticket-path-active">01<br /><small>Gửi yêu cầu</small></span><i /><span>02<br /><small>Đang xử lý</small></span><i /><span>03<br /><small>Cập nhật</small></span></div><SceneImage {...imageProps} className="ticket-evidence ticket-evidence-one" alt="Tạo ticket OnBxrd" /><SceneImage {...imageProps} offset={1} className="ticket-evidence ticket-evidence-two" alt="Trạng thái ticket OnBxrd" /><SceneImage {...imageProps} offset={2} className="ticket-evidence ticket-evidence-three" alt="Cập nhật hỗ trợ OnBxrd" /><div className="ticket-note"><CheckCircle2 size={16} /> Mọi bước đều rõ ràng</div></div>;
  if (feature.icon === "announcements") return <div className="scene scene-noticeboard"><div className="noticeboard-title"><BellRing size={18} /><span>Bảng tin tòa nhà</span></div><SceneImage {...imageProps} className="notice-card notice-card-one" alt="Thông báo tòa nhà" /><SceneImage {...imageProps} offset={1} className="notice-card notice-card-two" alt="Chi tiết thông báo" /><SceneImage {...imageProps} offset={2} className="notice-card notice-card-three" alt="Cập nhật cư dân" /><SceneImage {...imageProps} offset={3} className="notice-card notice-card-four" alt="Thông báo OnBxrd" /><span className="notice-pin notice-pin-one" /><span className="notice-pin notice-pin-two" /></div>;
  return <div className="scene scene-operations"><div className="operations-label"><LayoutDashboard size={18} /><span>Không gian vận hành</span></div><SceneImage {...imageProps} className="operations-main" alt="Không gian vận hành OnBxrd" /><div className="operations-scope"><MapPin size={15} /><div><strong>Phạm vi đang xem</strong><span>Tòa A · Tầng 12</span></div></div><SceneImage {...imageProps} offset={1} className="operations-float operations-float-one" alt="Hàng đợi quản lý" /><SceneImage {...imageProps} offset={2} className="operations-float operations-float-two" alt="Thông tin vận hành" /></div>;
}

export function LandingFeatureRail({ features }: { features: Feature[] }) {
  const railRef = useRef<HTMLDivElement>(null);
  const pauseUntil = useRef(0);
  const focusIsWithinRail = useRef(false);
  const scrollFrame = useRef<number | null>(null);
  const [activeIndex, setActiveIndex] = useState(0);
  function pauseForInteraction() { pauseUntil.current = Date.now() + RESUME_AFTER_MS; }
  function goTo(index: number) {
    const rail = railRef.current;
    if (!rail) return;
    const next = (index + features.length) % features.length;
    pauseForInteraction();
    rail.scrollTo({ left: rail.clientWidth * next, behavior: prefersReducedMotion() ? "auto" : "smooth" });
    setActiveIndex(next);
  }
  useEffect(() => {
    if (prefersReducedMotion() || features.length < 2) return;
    const timer = window.setInterval(() => {
      const rail = railRef.current;
      if (!rail || focusIsWithinRail.current || Date.now() < pauseUntil.current) return;
      setActiveIndex((current) => { const next = (current + 1) % features.length; rail.scrollTo({ left: rail.clientWidth * next, behavior: "smooth" }); return next; });
    }, AUTO_ADVANCE_MS);
    return () => window.clearInterval(timer);
  }, [features.length]);
  useEffect(() => {
    const rail = railRef.current;
    if (!rail) return;
    const onWheel = (event: WheelEvent) => { if (Math.abs(event.deltaY) <= Math.abs(event.deltaX)) return; event.preventDefault(); pauseForInteraction(); rail.scrollLeft += event.deltaY; };
    rail.addEventListener("wheel", onWheel, { passive: false });
    return () => rail.removeEventListener("wheel", onWheel);
  }, []);
  function syncActive() {
    const rail = railRef.current;
    if (!rail) return;
    if (scrollFrame.current) window.cancelAnimationFrame(scrollFrame.current);
    scrollFrame.current = window.requestAnimationFrame(() => setActiveIndex(Math.max(0, Math.min(features.length - 1, Math.round(rail.scrollLeft / Math.max(rail.clientWidth, 1))))));
  }
  return <section className="landing-journey" aria-label="Khám phá các tính năng OnBxrd"><div className="landing-progress" aria-hidden="true"><span style={{ transform: `scaleX(${(activeIndex + 1) / features.length})` }} /></div><p className="sr-only" aria-live="polite">Tính năng {activeIndex + 1} trong {features.length}: {features[activeIndex]?.title}</p><div ref={railRef} className="feature-rail" tabIndex={0} role="region" aria-label="Thư viện tính năng OnBxrd" onScroll={syncActive} onFocus={() => { focusIsWithinRail.current = true; pauseForInteraction(); }} onBlur={(event) => { focusIsWithinRail.current = event.currentTarget.contains(event.relatedTarget); }} onPointerDown={pauseForInteraction} onPointerEnter={pauseForInteraction} onKeyDown={(event) => { if (event.key === "ArrowRight") { event.preventDefault(); goTo(activeIndex + 1); } if (event.key === "ArrowLeft") { event.preventDefault(); goTo(activeIndex - 1); } if (event.key === "Home") { event.preventDefault(); goTo(0); } if (event.key === "End") { event.preventDefault(); goTo(features.length - 1); } }}>{features.map((feature, index) => { const Icon = icons[feature.icon]; const Heading = index === 0 ? "h1" : "h2"; return <article className={`feature-banner feature-banner-${feature.accent} feature-banner-${feature.icon}`} key={feature.icon} aria-roledescription="slide" aria-label={`${feature.index}: ${feature.title}`}><div className="feature-copy"><div className="feature-chapter"><span>{feature.index}</span><span>{feature.kicker}</span></div><div className="feature-icon"><Icon size={24} aria-hidden="true" /></div><Heading>{feature.title}</Heading><p>{feature.description}</p><Link className="feature-cta" href={feature.href}>{feature.cta} <ArrowRight size={17} aria-hidden="true" /></Link></div><div className="feature-visual"><FeatureVisual active={activeIndex === index} feature={feature} /></div></article>; })}</div><div className="landing-rail-controls"><div className="landing-dots" aria-label="Chọn tính năng">{features.map((feature, index) => <button key={feature.icon} type="button" aria-current={activeIndex === index ? "true" : undefined} aria-label={`Xem ${feature.title}`} className={activeIndex === index ? "landing-dot-active" : ""} onClick={() => goTo(index)}><span>{feature.index}</span></button>)}</div><div className="landing-arrow-controls"><button type="button" onClick={() => goTo(activeIndex - 1)} aria-label="Tính năng trước"><ArrowLeft size={18} /></button><button type="button" onClick={() => goTo(activeIndex + 1)} aria-label="Tính năng tiếp theo"><ArrowRight size={18} /></button></div></div></section>;
}
