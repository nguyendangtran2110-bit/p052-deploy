import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const path = "D:/data.30-07.scored.xlsx";
const previewDir = "D:/P-052/.tmp-score-topics";
const blob = await FileBlob.load(path);
const workbook = await SpreadsheetFile.importXlsx(blob);
const check = await workbook.inspect({
  kind: "table",
  range: "Đánh giá đề tài!A1:R8",
  include: "values,formulas",
  tableMaxRows: 8,
  tableMaxCols: 18,
});
const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 100 },
  summary: "formula error scan",
});
await fs.mkdir(previewDir, { recursive: true });
for (const [sheetName, fileName, range] of [
  ["Đánh giá đề tài", "scores-preview.png", "A1:R8"],
  ["Hướng dẫn chấm điểm", "rubric-preview.png", "A1:B13"],
]) {
  const image = await workbook.render({ sheetName, range, scale: 1.2, format: "png" });
  await fs.writeFile(`${previewDir}/${fileName}`, new Uint8Array(await image.arrayBuffer()));
}
console.log(JSON.stringify({ check: check.ndjson, errors: errors.ndjson, previewDir }));
