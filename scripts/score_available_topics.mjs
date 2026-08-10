import fs from "node:fs/promises";
import { Workbook, SpreadsheetFile } from "@oai/artifact-tool";

const inputPath = "D:/data.29-07.csv";
const csvOutputPath = "D:/data.30-07.scored.csv";
const xlsxOutputPath = "D:/data.30-07.scored.xlsx";

const profiles = {
  AIP:   { complexity: 4, scope: 4, data: 6, fit: 10, feasible: 4, need: 9, kpi: 9, demo: 7, risk: 7, note: "Nền tảng AI sát nhu cầu vận hành tập đoàn; khó ở tích hợp và quan sát production." },
  BDSO2O:{ complexity: 6, scope: 6, data: 6, fit: 9,  feasible: 6, need: 8, kpi: 7, demo: 8, risk: 7, note: "Sát quy trình bán hàng bất động sản; phù hợp làm pilot bằng dữ liệu CRM mô phỏng." },
  BO:    { complexity: 6, scope: 6, data: 6, fit: 8,  feasible: 7, need: 8, kpi: 7, demo: 7, risk: 6, note: "Back-office có nhu cầu rõ, nhưng tài liệu và dữ liệu nội bộ thường nhạy cảm." },
  CHAT:  { complexity: 6, scope: 6, data: 6, fit: 8,  feasible: 7, need: 7, kpi: 6, demo: 8, risk: 6, note: "Dễ tạo luồng hội thoại demo; cần khác biệt rõ so với chatbot phổ biến." },
  DATA:  { complexity: 6, scope: 6, data: 8, fit: 10, feasible: 7, need: 9, kpi: 9, demo: 8, risk: 7, note: "Khối dữ liệu có bài toán doanh nghiệp rõ và KPI kỹ thuật dễ đo." },
  DEV:   { complexity: 5, scope: 5, data: 6, fit: 9,  feasible: 5, need: 8, kpi: 7, demo: 9, risk: 6, note: "AI edge/thiết bị demo trực quan nhưng có ràng buộc realtime, phần cứng và quyền riêng tư." },
  EDU:   { complexity: 6, scope: 6, data: 6, fit: 9,  feasible: 7, need: 7, kpi: 6, demo: 7, risk: 7, note: "Có thể pilot với trường/lớp, nhưng phải chứng minh nhu cầu và tác động học tập thật." },
  FIN:   { complexity: 4, scope: 5, data: 5, fit: 9,  feasible: 4, need: 8, kpi: 8, demo: 7, risk: 4, note: "Sát ví điện tử nhưng dữ liệu tài chính, tuân thủ và rủi ro mô hình làm MVP khó hơn." },
  GSM:   { complexity: 5, scope: 5, data: 6, fit: 9,  feasible: 5, need: 8, kpi: 8, demo: 8, risk: 6, note: "Sát vận hành gọi xe; cần mô phỏng dữ liệu thời gian–không gian và bảo mật định danh." },
  ITOPS: { complexity: 6, scope: 6, data: 8, fit: 10, feasible: 7, need: 9, kpi: 9, demo: 7, risk: 7, note: "Data log/ticket công khai phong phú; cần chặn thao tác production không có phê duyệt." },
  MFG:   { complexity: 5, scope: 5, data: 8, fit: 10, feasible: 6, need: 9, kpi: 9, demo: 8, risk: 7, note: "Rất sát sản xuất; có nhiều bộ dữ liệu cảm biến/CV nhưng phải mô phỏng an toàn nhà máy." },
  PTNT:  { complexity: 5, scope: 5, data: 6, fit: 9,  feasible: 5, need: 8, kpi: 7, demo: 8, risk: 6, note: "Phù hợp nền tảng ứng dụng, nhưng tích hợp nhiều dịch vụ dễ làm scope phình to." },
  RAV:   { complexity: 3, scope: 3, data: 5, fit: 10, feasible: 3, need: 9, kpi: 8, demo: 8, risk: 6, note: "Sát VinFast/robot nhưng simulation, sensor và benchmark closed-loop vượt scope MVP phổ thông." },
  SC:    { complexity: 6, scope: 6, data: 7, fit: 9,  feasible: 7, need: 8, kpi: 8, demo: 8, risk: 7, note: "Smart City dễ tạo data mô phỏng và dashboard; cần tránh phụ thuộc hạ tầng IoT thật." },
  VFO2O: { complexity: 6, scope: 6, data: 6, fit: 10, feasible: 6, need: 8, kpi: 7, demo: 8, risk: 6, note: "Sát bán hàng ô tô; data CRM/giá/khách hàng thường không công khai hoàn toàn." },
  VHR:   { complexity: 6, scope: 6, data: 6, fit: 10, feasible: 7, need: 8, kpi: 7, demo: 9, risk: 6, note: "Sát ứng dụng cư dân, quy trình ticket/tiện ích trực quan và dễ pilot bằng dữ liệu mô phỏng." },
  VMEC:  { complexity: 4, scope: 5, data: 5, fit: 10, feasible: 4, need: 9, kpi: 7, demo: 7, risk: 3, note: "Rất sát y tế nhưng yêu cầu an toàn, dữ liệu sức khỏe và trách nhiệm chuyên môn cao." },
  VSOC:  { complexity: 5, scope: 5, data: 9, fit: 10, feasible: 6, need: 9, kpi: 9, demo: 8, risk: 7, note: "Nhiều data công khai và metric chuẩn; phải giới hạn an toàn, không tự động tấn công hay chặn production." },
};

const clamp = (n) => Math.max(1, Math.min(10, n));
const prefixOf = (code) => code.split("-")[0];
const lower = (text) => (text || "").toLocaleLowerCase("vi-VN");
const compact = (text, max = 190) => (text || "").replace(/\s+/g, " ").trim().slice(0, max).replace(/[,:;\-\s]+$/, "");

const companyContext = {
  AIP: "khối AI tập trung: quản lý chất lượng, chi phí và an toàn khi nhiều đơn vị dùng AI",
  BDSO2O: "kinh doanh O2O bất động sản: lead, tư vấn, chăm sóc và chuyển đổi khách hàng",
  BO: "khối back-office: quy trình hành chính, tài chính, nhân sự và tri thức nội bộ",
  CHAT: "ứng dụng nhắn tin: trải nghiệm hội thoại, an toàn và vận hành nền tảng",
  DATA: "khối dữ liệu tập trung: chất lượng, governance, metadata và self-service analytics",
  DEV: "hệ thiết bị/edge của hệ sinh thái: trải nghiệm tại xe, nhà, kiosk hoặc camera",
  EDU: "VinUni/đơn vị giáo dục: hỗ trợ học, nghiên cứu và vận hành học vụ",
  FIN: "ví điện tử/fintech: trải nghiệm giao dịch, rủi ro, tuân thủ và hỗ trợ người dùng",
  GSM: "GSM: vận hành chuyến đi, đội xe điện, tài xế và trải nghiệm khách hàng",
  ITOPS: "khối IT dùng chung: help desk, hạ tầng, SAP và vận hành dịch vụ",
  MFG: "VinFast/khối sản xuất: chất lượng, năng suất, bảo trì, an toàn và truy xuất",
  PTNT: "nền tảng ứng dụng: tích hợp dịch vụ, điều hướng và vận hành sản phẩm số",
  RAV: "robot/xe tự hành: perception, mô phỏng, dữ liệu fleet và kiểm thử an toàn",
  SC: "Smart City/Smart Home: IoT, vận hành đô thị và trải nghiệm cư dân",
  VFO2O: "VinFast O2O: bán xe, tư vấn, hậu mãi và vận hành đại lý",
  VHR: "Vinhomes Resident: tiện ích, phản ánh và vận hành khu đô thị",
  VMEC: "Vinmec: trải nghiệm bệnh nhân và hỗ trợ nghiệp vụ y tế có giám sát",
  VSOC: "SOC/an ninh mạng: triage, phát hiện, điều tra và ưu tiên rủi ro",
};

function archetypeFor(prefix, text) {
  if (prefix === "VSOC") return "security";
  if (prefix === "VMEC") return "health";
  if (prefix === "RAV") return "autonomy";
  if (prefix === "FIN") return "finance";
  if (prefix === "DEV" || /camera|video|thị giác|computer vision|on-device|edge|kiosk/.test(text)) return "vision";
  if (/hỏi đáp|tra cứu|knowledge|rag|tài liệu|policy|quy định|nội quy|document|sap/.test(text)) return "rag";
  if (/phân loại|định tuyến|triage|sàng lọc|routing|ticket|email/.test(text)) return "triage";
  if (/dự báo|bảo trì|anomaly|bất thường|spc|quality|drift|forecast/.test(text)) return "prediction";
  if (/tối ưu|điều phối|lập kế hoạch|scheduling|route|ghép chuyến/.test(text)) return "optimization";
  if (/báo cáo|dashboard|tổng hợp|phân tích phản hồi|insight/.test(text)) return "analytics";
  if (prefix === "AIP") return "platform";
  return "workflow";
}

const typeGuides = {
  rag: {
    complexity: "cần pipeline nạp tài liệu, retrieval/rerank, citation và phân quyền; chỉ nên chốt một kho tri thức hẹp cho MVP",
    data: "có thể dùng PDF, FAQ, quy định, manual công khai hoặc kho tài liệu được phê duyệt; Kaggle/HuggingFace chỉ hỗ trợ benchmark, còn corpus nghiệp vụ phải tự curate",
    kpi: "citation correctness, faithfulness/RAGAS, answer accuracy, tỷ lệ từ chối đúng khi không có nguồn và P95 latency",
    demo: "upload/duyệt tài liệu → hỏi đáp có dẫn đoạn nguồn → phản hồi thiếu căn cứ hoặc HITL",
  },
  triage: {
    complexity: "gồm chuẩn hóa text, mô hình phân loại/ưu tiên, định tuyến và màn hình duyệt; MVP nên giới hạn taxonomy và workflow xử lý",
    data: "có thể khởi đầu từ ticket, email, complaint hoặc support-text có nhãn trên Kaggle/HuggingFace; cần Việt hóa và bổ sung mẫu nghiệp vụ mô phỏng",
    kpi: "macro-F1 theo nhãn, routing accuracy, precision ở case khẩn, SLA và tỷ lệ ticket bị chuyển sai",
    demo: "người dùng gửi yêu cầu → AI tóm tắt/chấm ưu tiên → đề xuất queue → người phụ trách duyệt → dashboard SLA",
  },
  prediction: {
    complexity: "phải làm sạch chuỗi thời gian, đặt baseline và giải thích cảnh báo; cần tránh hứa realtime/forecast đa biến quá sớm",
    data: "Kaggle có sensor, maintenance, anomaly và quality-control data; dữ liệu nội bộ chỉ cần mô phỏng đúng schema cho pilot",
    kpi: "precision/recall hoặc ROC-AUC cho cảnh báo, false-alarm rate, MAE/RMSE nếu dự báo và thời gian phát hiện sớm",
    demo: "stream dữ liệu mô phỏng → biểu đồ xu hướng/cảnh báo → nguyên nhân gợi ý → kỹ sư phê duyệt hành động",
  },
  optimization: {
    complexity: "ngoài AI còn có ràng buộc nghiệp vụ, solver và dữ liệu trạng thái; MVP phải cố định một khu vực hoặc một loại quyết định",
    data: "có data benchmark công khai cho routing/scheduling và có thể sinh dữ liệu theo ràng buộc; data vận hành thật thường phải ẩn danh",
    kpi: "giảm chi phí/khoảng cách/thời gian chờ so với heuristic baseline, tỷ lệ ràng buộc hợp lệ và thời gian tính",
    demo: "nhập nhu cầu và ràng buộc → so sánh kế hoạch baseline với đề xuất → quản lý xác nhận → chỉ số tiết kiệm",
  },
  analytics: {
    complexity: "trọng tâm là ingestion, chuẩn hóa, truy vấn/nhóm cụm và kiểm tra số liệu; cần chốt schema dữ liệu trước UI",
    data: "có thể dùng review, survey, ticket hoặc bảng vận hành công khai và dữ liệu mô phỏng có nhãn; ít phụ thuộc thiết bị thật",
    kpi: "độ đúng thống kê, topic/cluster quality, precision phát hiện xu hướng và thời gian lập báo cáo so với thủ công",
    demo: "nạp dữ liệu → AI nhóm chủ đề/rút insight → dashboard, biểu đồ và bản báo cáo có người duyệt",
  },
  vision: {
    complexity: "cần model CV, tracking hoặc benchmark FPS/latency và xử lý thiết bị; nên dùng video mẫu thay vì tích hợp camera thật",
    data: "có public image/video benchmark trên Kaggle/HuggingFace và bộ dữ liệu ngành; cần kiểm tra license, điều kiện ánh sáng và khả năng đại diện",
    kpi: "mAP/F1 hoặc MAE đếm, false-positive rate, FPS, latency và tỷ lệ event được phát hiện đúng",
    demo: "video mẫu → overlay detection/blur → cảnh báo sự kiện → dashboard ẩn danh hoặc thao tác HITL",
  },
  security: {
    complexity: "cần parser/enrichment, rule hoặc model phân loại và trace bằng chứng; chỉ demo trong sandbox, không tự tấn công/chặn production",
    data: "dễ kiếm log, phishing, CVE, threat-intel và malware-report public trên Kaggle/HuggingFace; phải tách PII và tuân thủ license",
    kpi: "precision/recall, false-positive reduction, detection time, coverage bằng chứng và analyst agreement",
    demo: "nạp artifact an toàn → agent phân tích bằng chứng → xếp mức rủi ro → analyst phê duyệt hành động mô phỏng",
  },
  health: {
    complexity: "cần workflow có người chuyên môn duyệt, truy xuất nguồn và safety guardrail; MVP không được đưa ra chẩn đoán hay quyết định lâm sàng",
    data: "có dataset y sinh công khai nhưng quyền sử dụng/khả năng đại diện hạn chế; nên dùng case đã ẩn danh hoặc dữ liệu mô phỏng có chuyên gia rà soát",
    kpi: "độ đúng theo rubric chuyên môn, safety escalation, tỷ lệ citation đúng và agreement với người duyệt thay vì chỉ accuracy",
    demo: "bệnh nhân/case mô phỏng → khuyến nghị có nguồn và disclaimer → bác sĩ/điều dưỡng duyệt → audit trail",
  },
  finance: {
    complexity: "cần rule/ML, giải thích quyết định, kiểm soát gian lận và hạn chế hành động tài chính thật; MVP nên ở chế độ advisory",
    data: "có transaction/fraud benchmark công khai nhưng thường khác phân phối Việt Nam; cần synthetic data và tuyệt đối không dùng thông tin định danh thật",
    kpi: "precision/recall ở lớp hiếm, cost-sensitive error, calibration, tỷ lệ review đúng và latency",
    demo: "dữ liệu giao dịch mô phỏng → điểm rủi ro/giải thích → chuyên viên duyệt → audit log",
  },
  autonomy: {
    complexity: "phụ thuộc simulation, sensor đa modal, benchmark closed-loop hoặc phần cứng; phải thu hẹp xuống một scenario hoặc pipeline dữ liệu",
    data: "có benchmark camera/LiDAR/robot công khai nhưng nặng và tốn GPU; khó có fleet data thật trong 5 tuần",
    kpi: "mAP/IoU, success rate, scenario coverage, latency/FPS hoặc regression rate theo simulator",
    demo: "replay scene/simulator → phát hiện hoặc đánh giá scenario → so sánh metric → kỹ sư xem trace",
  },
  platform: {
    complexity: "cần tích hợp nhiều model/service, observability và policy; MVP phải adapter hóa 1–2 nhà cung cấp và chỉ một workflow cốt lõi",
    data: "dễ dùng prompt, log đã ẩn danh, benchmark public và synthetic traces; production telemetry vẫn cần quyền truy cập nội bộ",
    kpi: "latency, token cost, success rate, regression/eval score, policy-violation rate và coverage trace",
    demo: "nạp request/log mô phỏng → agent route/eval/giám sát → dashboard cost-quality → người vận hành duyệt cấu hình",
  },
  workflow: {
    complexity: "cần mô hình hóa quy trình, quyền hạn và HITL; nên chỉ triển khai happy path cùng một nhánh ngoại lệ quan trọng",
    data: "có thể dùng form, record nghiệp vụ mô phỏng và corpus công khai cùng loại; cần giữ schema sát bối cảnh doanh nghiệp",
    kpi: "task-completion rate, thời gian xử lý, tỷ lệ phải chuyển người, độ đúng trường trích xuất và satisfaction",
    demo: "người dùng tạo yêu cầu → AI đề xuất/soạn thảo → người có thẩm quyền duyệt → trạng thái và audit log",
  },
};

function scoreTopic(row) {
  const title = lower(row["Tên Đề Tài"]);
  const description = lower(row["Mô Tả Bài Toán"]);
  const text = `${title} ${description}`;
  const profile = profiles[prefixOf(row["Mã Đề"])] || profiles.AIP;
  const s = { ...profile };

  const hard = ["realtime", "thời gian thực", "đa tác tử", "multi-agent", "on-device", "edge", "computer vision", "thị giác", "giọng nói", "audio", "video", "lidar", "robot", "xe tự hành", "fuzz", "pentest", "red-team", "fine-tune", "mô phỏng", "tối ưu tuyến", "điều phối", "dự báo", "kỹ thuật số song sinh", "digital twin", "kiosk"];
  const sensitive = ["y tế", "bệnh", "triage", "chẩn đoán", "tín dụng", "gian lận", "aml", "kyc", "học bổng", "tuyển dụng", "cv", "khuôn mặt", "định danh", "bảo mật", "an ninh", "phishing", "lỗ hổng"];
  const dataRich = ["ticket", "log", "email", "phishing", "cve", "threat", "sentiment", "phản hồi", "survey", "đánh giá", "dataset", "data quality", "anomaly", "bảo trì", "sensor", "spc", "computer vision"];
  const quick = ["hỏi đáp", "tra cứu", "tóm tắt", "phân loại", "định tuyến", "dashboard", "báo cáo", "knowledge", "onboarding", "policy", "nội quy", "phân tích phản hồi", "trích xuất"];
  const kpiStrong = ["phát hiện", "phân loại", "xếp hạng", "dự báo", "tối ưu", "chấm điểm", "anomaly", "bất thường", "quality", "sla", "kpi", "eval"];
  const demoStrong = ["dashboard", "heatmap", "camera", "video", "ticket", "booking", "đặt lịch", "cảnh báo", "bản đồ", "kiosk", "điều phối"];

  const matches = (items) => items.reduce((n, item) => n + (text.includes(item) ? 1 : 0), 0);
  const h = matches(hard), r = matches(sensitive), d = matches(dataRich), q = matches(quick), k = matches(kpiStrong), m = matches(demoStrong);

  s.complexity -= Math.min(3, h);
  s.scope -= Math.min(3, h);
  s.feasible -= Math.min(3, h);
  s.data += Math.min(2, d);
  s.kpi += Math.min(2, k);
  s.demo += Math.min(2, m);
  s.complexity += Math.min(2, q);
  s.scope += Math.min(2, q);
  s.feasible += Math.min(2, q);
  s.risk -= Math.min(4, r);
  if (r >= 2) s.feasible -= 1;
  if (text.includes("rag") || text.includes("hỏi đáp")) s.data += 1;
  if (text.includes("tự động") && (text.includes("chặn") || text.includes("triển khai") || text.includes("rollback"))) s.risk -= 1;
  if (text.includes("cá nhân hóa")) s.need += 1;
  if (text.includes("quản trị") || text.includes("governance")) s.fit += 1;

  for (const key of ["complexity", "scope", "data", "fit", "feasible", "need", "kpi", "demo", "risk"]) s[key] = clamp(Math.round(s[key]));
  const total = [s.complexity, s.scope, s.data, s.fit, s.feasible, s.need, s.kpi, s.demo, s.risk].reduce((a, b) => a + b, 0);
  const prefix = prefixOf(row["Mã Đề"]);
  const kind = archetypeFor(prefix, text);
  const guide = typeGuides[kind];
  const context = companyContext[prefix] || "đơn vị được giao trong đề";
  const pain = compact(row["Mô Tả Bài Toán"], 185);
  const feasibility = s.feasible >= 7
    ? "Có thể hoàn thành nếu chốt một dataset, một persona và một luồng HITL; phần nâng cao chỉ nên chứng minh bằng một scenario end-to-end."
    : s.feasible >= 5
      ? "Chỉ khả thi khi cắt giảm tích hợp thật, dùng dữ liệu mô phỏng đúng schema và hoàn thành baseline trước các tính năng agent/automation."
      : "Rủi ro cao trong 5 tuần vì phụ thuộc hạ tầng, benchmark hoặc dữ liệu/đối tác; chỉ nên chọn khi đã có sẵn data, mentor và phần nền tảng.";
  const risk = s.risk >= 7
    ? "Rủi ro chính là quyền truy cập/PII; có thể quản lý bằng dữ liệu ẩn danh, RBAC, audit log và phê duyệt trước hành động."
    : s.risk >= 5
      ? "Cần tách PII, giới hạn agent ở mức đề xuất và bắt buộc HITL cho quyết định/tác vụ nhạy cảm."
      : "Có rủi ro cao về dữ liệu nhạy cảm, fairness hoặc an toàn; demo phải dùng dữ liệu ẩn danh/mô phỏng, nêu rõ giới hạn và không tự động ra quyết định có tác động thật.";
  const detailedNote = [
    `Bối cảnh/pain point: ${pain}.`,
    `1. Độ phức tạp ${s.complexity}/10: ${guide.complexity}.`,
    `2. Quy mô MVP ${s.scope}/10: ${s.scope >= 7 ? "có thể thu gọn thành một quy trình, một loại dữ liệu và hai vai trò." : "có nhiều thành phần hoặc luồng ngoại lệ; cần khóa chặt phạm vi ngay tuần đầu."}`,
    `3. Data ${s.data}/10: ${guide.data}.`,
    `4. Phù hợp công ty ${s.fit}/10: đề bám trực tiếp ${context}; giá trị chỉ thuyết phục khi demo dùng thuật ngữ, SLA và vai trò đúng nghiệp vụ.`,
    `5. Khả thi 5 tuần ${s.feasible}/10: ${feasibility}`,
    `6. Tính cần thiết ${s.need}/10: ${s.need >= 8 ? "pain point lặp lại, có ảnh hưởng rõ đến tốc độ, chi phí hoặc chất lượng vận hành." : "có ích nhưng cần pilot/user interview để chứng minh tần suất và mức sẵn sàng sử dụng."}`,
    `7. KPI ${s.kpi}/10: nên đo ${guide.kpi}.`,
    `8. Demo ${s.demo}/10: luồng nên là ${guide.demo}.`,
    `9. Rủi ro ${s.risk}/10: ${risk}`,
  ].join(" ");
  return { ...s, total, detailedNote };
}

function csvEscape(value) {
  const text = String(value ?? "");
  return /[",\n\r]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

const sourceCsv = await fs.readFile(inputPath, "utf8");
const sourceWorkbook = await Workbook.fromCSV(sourceCsv, { sheetName: "Nguồn" });
const sourceSheet = sourceWorkbook.worksheets.getItem("Nguồn");
const sourceValues = sourceSheet.getUsedRange().values;
const headers = sourceValues[0];
const keptHeaders = headers.filter((header) => header !== "Max team / đề tài");
const sourceRows = sourceValues.slice(1).filter((row) => row.some((cell) => cell !== null && cell !== ""));
const objects = sourceRows.map((values) => Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""])));

const scoreHeaders = [
  "Khả năng kiểm soát độ phức tạp (10=dễ)",
  "Quy mô MVP (10=gọn)",
  "Dễ kiếm data Kaggle/HuggingFace (10=dễ)",
  "Phù hợp công ty (10=cao)",
  "Khả thi trong 5 tuần (10=cao)",
  "Tính cần thiết (10=cao)",
  "Dễ đánh giá KPI (10=dễ)",
  "Sức mạnh demo (10=cao)",
  "Rủi ro dữ liệu/pháp lý (10=thấp)",
  "Nhận định chi tiết theo 9 metric",
  "Tổng điểm (90)",
];

const outputRows = objects.map((row) => {
  const score = scoreTopic(row);
  return [
    ...keptHeaders.map((header) => row[header]),
    score.complexity, score.scope, score.data, score.fit, score.feasible,
    score.need, score.kpi, score.demo, score.risk, score.detailedNote, score.total,
  ];
});

const allHeaders = keptHeaders.concat(scoreHeaders);
const csvText = [allHeaders, ...outputRows].map((row) => row.map(csvEscape).join(",")).join("\r\n") + "\r\n";
await fs.writeFile(csvOutputPath, "\uFEFF" + csvText, "utf8");

const workbook = Workbook.create();
const sheet = workbook.worksheets.add("Đánh giá đề tài");
sheet.getRangeByIndexes(0, 0, outputRows.length + 1, allHeaders.length).values = [allHeaders, ...outputRows];
sheet.freezePanes.freezeRows(1);
sheet.getRangeByIndexes(0, 0, 1, allHeaders.length).format = {
  fill: "#0F4C5C",
  font: { bold: true, color: "#FFFFFF" },
  wrapText: true,
  horizontalAlignment: "center",
  verticalAlignment: "center",
};
sheet.getRangeByIndexes(1, keptHeaders.length, outputRows.length, 9).format = { horizontalAlignment: "center" };
sheet.getRangeByIndexes(1, allHeaders.length - 1, outputRows.length, 1).format = { font: { bold: true }, horizontalAlignment: "center" };
sheet.getRangeByIndexes(0, 0, outputRows.length + 1, allHeaders.length).format.wrapText = true;
sheet.getRangeByIndexes(0, 0, outputRows.length + 1, allHeaders.length).format.borders = { preset: "inside", style: "thin", color: "#D9E2F3" };
sheet.getRangeByIndexes(0, 0, outputRows.length + 1, allHeaders.length).format.autofitColumns();
sheet.getRange("A:A").format.columnWidth = 8;
sheet.getRange("B:B").format.columnWidth = 28;
sheet.getRange("C:C").format.columnWidth = 12;
sheet.getRange("D:D").format.columnWidth = 42;
sheet.getRange("E:G").format.columnWidth = 28;
sheet.getRangeByIndexes(0, keptHeaders.length, outputRows.length + 1, 9).format.columnWidth = 14;
sheet.getRangeByIndexes(0, keptHeaders.length + 9, outputRows.length + 1, 1).format.columnWidth = 88;
sheet.getRangeByIndexes(0, allHeaders.length - 1, outputRows.length + 1, 1).format.columnWidth = 14;
sheet.getRangeByIndexes(1, keptHeaders.length, outputRows.length, 9).conditionalFormats.add("colorScale", { colors: ["#FDE2E2", "#FFF4CC", "#DCFCE7"] });
sheet.getRangeByIndexes(1, allHeaders.length - 1, outputRows.length, 1).conditionalFormats.add("colorScale", { colors: ["#FCA5A5", "#FDE68A", "#86EFAC"] });
sheet.tables.add(`A1:${String.fromCharCode(64 + allHeaders.length)}${outputRows.length + 1}`, true, "TopicScores");

const summary = workbook.worksheets.add("Hướng dẫn chấm điểm");
summary.getRange("A1:B13").values = [
  ["Rubric", "Ý nghĩa"],
  ["Phạm vi", "275 đề trong data.29-07.csv; chấm sơ bộ để lọc shortlist, không thay thế xác nhận từ doanh nghiệp."],
  ["Độ phức tạp", "10 = dễ kiểm soát kỹ thuật trong MVP; 1 = đòi hỏi realtime, phần cứng, dữ liệu nhạy cảm hoặc tích hợp phức tạp."],
  ["Quy mô MVP", "10 = có thể đóng gói thành MVP gọn; 1 = cần nhiều hệ thống/quy trình vận hành."],
  ["Dữ liệu", "10 = có nhiều dữ liệu công khai phù hợp trên Kaggle/HuggingFace hoặc dễ mô phỏng có nhãn."],
  ["Phù hợp công ty", "10 = rất sát nghiệp vụ của đơn vị được giao; đánh giá theo khối trong đề."],
  ["Khả thi 5 tuần", "10 = team nhỏ có thể hoàn thành luồng nâng cao có kiểm chứng; 1 = phụ thuộc hạ tầng, đối tác hoặc R&D dài hạn."],
  ["Tính cần thiết", "10 = pain point thường xuyên, tác động rõ đến chi phí/chất lượng/tốc độ."],
  ["KPI", "10 = có metric định lượng và ground truth tương đối rõ (F1, precision/recall, latency, SLA...)."],
  ["Demo", "10 = luồng input → AI → HITL → kết quả trực quan, dễ thuyết phục."],
  ["Rủi ro", "10 = rủi ro dữ liệu/pháp lý/an toàn thấp; điểm thấp cho y tế, tài chính, định danh, HR và tác vụ có thể gây hại."],
  ["Nhận định chi tiết", "Mỗi dòng giải thích đủ 9 metric: phạm vi kỹ thuật, dữ liệu khả dụng, fit nghiệp vụ, kế hoạch 5 tuần, KPI, demo và guardrail. Đây là screening có cấu trúc; điểm data cần được xác nhận lại license/dataset trước khi thi."],
  ["Tổng điểm", "Tổng của 9 metric, tối đa 90. Dùng để shortlist trước, sau đó đọc kỹ yêu cầu đầu ra của các đề top."],
];
summary.getRange("A1:B1").format = { fill: "#0F4C5C", font: { bold: true, color: "#FFFFFF" } };
summary.getRange("A1:B13").format.wrapText = true;
summary.getRange("A1:B13").format.borders = { preset: "inside", style: "thin", color: "#D9E2F3" };
summary.getRange("A:A").format.columnWidth = 24;
summary.getRange("B:B").format.columnWidth = 105;
summary.freezePanes.freezeRows(1);

const xlsx = await SpreadsheetFile.exportXlsx(workbook);
await xlsx.save(xlsxOutputPath);
console.log(JSON.stringify({ rows: outputRows.length, csvOutputPath, xlsxOutputPath, headers: allHeaders.length }));
