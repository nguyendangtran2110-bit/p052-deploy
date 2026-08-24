import { readdir } from "node:fs/promises";
import path from "node:path";
import Link from "next/link";
import { LandingFeatureRail } from "@/components/landing-feature-rail";
import { ThemeControl } from "@/components/theme-control";

const LANDING_ROOT = path.join(process.cwd(), "public", "landing");

async function gallery(folder: string, limit: number) {
  try {
    const filenames = await readdir(path.join(LANDING_ROOT, folder));
    return filenames.filter((filename) => filename.toLowerCase().endsWith(".jpg")).sort((a, b) => a.localeCompare(b, undefined, { numeric: true })).slice(0, limit).map((filename) => `/landing/${folder}/${encodeURIComponent(filename)}`);
  } catch {
    return [];
  }
}

export default async function HomePage() {
  const imageFolders = [
    ["onboarding", 2], ["benefits", 4], ["assistant", 2], ["tickets", 3], ["announcements", 4], ["operations", 3],
  ] as const;
  const [onboarding, benefits, assistant, tickets, announcements, operations] = await Promise.all(imageFolders.map(([folder, limit]) => gallery(folder, limit)));
  const features = [
    { index: "01", icon: "onboarding", accent: "clay", kicker: "Chào mừng cư dân", title: "Khởi đầu nhẹ nhàng, mọi thứ rõ ràng.", description: "OnBxrd gom thông tin tòa nhà, căn hộ và việc cần làm tiếp theo vào một hành trình dễ theo dõi.", cta: "Bắt đầu hành trình cư dân", href: "/register", images: onboarding },
    { index: "02", icon: "benefits", accent: "sage", kicker: "Giá trị mỗi ngày", title: "Khám phá những quyền lợi quanh bạn.", description: "Tìm tiện ích, ưu đãi và thông tin thiết thực phù hợp với chính tòa nhà bạn đang sống.", cta: "Khám phá quyền lợi", href: "/login", images: benefits },
    { index: "03", icon: "assistant", accent: "gold", kicker: "Hỗ trợ có căn cứ", title: "Cứ hỏi Hommie, bạn vẫn luôn là người quyết định.", description: "Hommie Agent giải thích thông tin đã được phê duyệt và cùng bạn chuẩn bị yêu cầu hỗ trợ trước khi gửi đi.", cta: "Trò chuyện cùng Hommie", href: "/login", images: assistant },
    { index: "04", icon: "tickets", accent: "blue", kicker: "Hỗ trợ cư dân", title: "Theo dõi yêu cầu từ lúc gửi đến khi có cập nhật.", description: "Tạo ticket rõ ràng, bổ sung ngữ cảnh hữu ích và biết chính xác bước tiếp theo mà không phải tìm giữa nhiều kênh.", cta: "Mở không gian của bạn", href: "/login", images: tickets },
    { index: "05", icon: "announcements", accent: "rose", kicker: "Tin tức tòa nhà", title: "Điều quan trọng luôn ở đúng nơi bạn cần.", description: "Thông báo và cập nhật cư dân được giữ dễ đọc, dễ xem lại và gắn với nơi bạn đang sống.", cta: "Xem OnBxrd hoạt động", href: "/login", images: announcements },
    { index: "06", icon: "operations", accent: "cocoa", kicker: "Không gian quản lý", title: "Một góc vận hành tập trung cho đội ngũ tòa nhà.", description: "Hàng đợi, phạm vi cư dân, bàn giao, thông báo, tri thức và căn hộ luôn chính xác mà không biến công việc hằng ngày thành bảng số liệu rườm rà.", cta: "Đăng nhập quản lý", href: "/login", images: operations },
  ] as const;
  return <div className="public-shell landing-shell"><a className="skip-link" href="#landing-content">Đến thư viện tính năng</a><header className="landing-header"><Link className="landing-brand" href="/" aria-label="Trang chủ OnBxrd"><span className="brand-mark" aria-hidden="true">O</span><span><strong>OnBxrd</strong><small>Không gian cư dân</small></span></Link><nav className="landing-nav" aria-label="Điều hướng công khai"><a href="#landing-content">Khám phá tính năng</a><Link href="/register">Tạo tài khoản</Link><Link className="landing-sign-in" href="/login">Đăng nhập</Link><ThemeControl compact /></nav></header><main id="landing-content"><LandingFeatureRail features={[...features]} /></main></div>;
}
