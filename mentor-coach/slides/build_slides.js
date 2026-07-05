// AIメンターコーチ 使用説明書スライド生成
const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625 inch
pres.author = "AIメンターコーチ";
pres.title = "AIメンターコーチ 使用説明書";

// ---- パレット (Teal Trust) ----
const INK = "14322F";     // 深いパイングリーン(暗背景)
const TEAL = "2A9D8F";    // ティール
const TEAL_DK = "1E7268";
const GOLD = "E9C46A";    // 温かいアクセント
const WHITE = "FFFFFF";
const TINT = "EAF2F0";    // 淡いティール
const CODEBG = "10302D";  // コードブロック背景(暗)
const MUTE = "5A6B6A";    // 補助テキスト
const BODY = "213533";    // 本文

const JP = "Meiryo";
const JPB = "Meiryo";     // boldはoptionで指定
const MONO = "Courier New";

const shadow = () => ({ type: "outer", color: "000000", blur: 7, offset: 3, angle: 90, opacity: 0.12 });

function header(slide, section, title) {
  slide.addText(section, { x: 0.55, y: 0.34, w: 9, h: 0.3, fontFace: JP, fontSize: 12, bold: true, color: TEAL, charSpacing: 2, margin: 0 });
  slide.addText(title, { x: 0.55, y: 0.62, w: 9, h: 0.65, fontFace: JPB, fontSize: 30, bold: true, color: INK, margin: 0 });
}

function numCircle(slide, x, y, n, d = 0.5, fill = TEAL) {
  slide.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill } });
  slide.addText(String(n), { x, y, w: d, h: d, align: "center", valign: "middle", fontFace: JP, fontSize: 16, bold: true, color: WHITE, margin: 0 });
}

// ============ Slide 1: タイトル ============
{
  const s = pres.addSlide();
  s.background = { color: INK };
  // 装飾: 同心円モチーフ(右下)
  s.addShape(pres.shapes.OVAL, { x: 7.6, y: 3.4, w: 3.6, h: 3.6, fill: { color: TEAL, transparency: 82 } });
  s.addShape(pres.shapes.OVAL, { x: 8.35, y: 4.15, w: 2.1, h: 2.1, fill: { color: TEAL, transparency: 68 } });
  s.addShape(pres.shapes.OVAL, { x: 8.95, y: 4.75, w: 0.9, h: 0.9, fill: { color: GOLD, transparency: 20 } });

  s.addText("AIメンターコーチ", { x: 0.7, y: 1.55, w: 8.5, h: 0.95, fontFace: JPB, fontSize: 46, bold: true, color: WHITE, margin: 0 });
  s.addText("使 用 説 明 書", { x: 0.72, y: 2.55, w: 8, h: 0.6, fontFace: JP, fontSize: 26, bold: true, color: GOLD, charSpacing: 3, margin: 0 });
  s.addText("コーチングセッション後分析  ×  ICF PCCマーカー準拠", { x: 0.72, y: 3.35, w: 7, h: 0.4, fontFace: JP, fontSize: 15, color: TINT, margin: 0 });
  s.addText("Phase 1 プロトタイプ", { x: 0.72, y: 4.85, w: 5, h: 0.35, fontFace: JP, fontSize: 12, color: TEAL, bold: true, margin: 0 });
}

// ============ Slide 2: 概要・設計方針 ============
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  header(s, "OVERVIEW", "このツールは何か");

  s.addText([
    { text: "コーチングセッションの録音やトランスクリプトを分析し、", options: { breakLine: true } },
    { text: "ICF PCCマーカーに準拠したメンターコーチング・レポートを", options: { breakLine: true } },
    { text: "自動生成します。", options: { breakLine: true, bold: true, color: TEAL_DK } },
    { text: "" , options: { breakLine: true, fontSize: 6 } },
    { text: "人間のメンターコーチの", options: {} },
    { text: "準備・補完", options: { bold: true } },
    { text: "を目的とし、", options: { breakLine: true } },
    { text: "資格審査用の自己チェックにも使えます。", options: {} },
  ], { x: 0.55, y: 1.65, w: 4.3, h: 2.4, fontFace: JP, fontSize: 15, color: BODY, lineSpacingMultiple: 1.25, valign: "top", margin: 0 });

  const cards = [
    ["セッション後分析", "リアルタイム割り込みはコーチのプレゼンスを損なうため行いません。"],
    ["感情は断定しない", "話速や沈黙は「確認すべき候補」として提示します。"],
    ["表情分析はしない", "EU AI Act と科学的妥当性の観点から採用しません。"],
  ];
  let cy = 1.55;
  const cx = 5.15, cw = 4.3, ch = 1.15;
  cards.forEach(([t, d], i) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: cx, y: cy, w: cw, h: ch, rectRadius: 0.08, fill: { color: TINT }, shadow: shadow() });
    s.addText(t, { x: cx + 0.28, y: cy + 0.14, w: cw - 0.5, h: 0.4, fontFace: JPB, fontSize: 16, bold: true, color: INK, margin: 0 });
    s.addText(d, { x: cx + 0.28, y: cy + 0.55, w: cw - 0.5, h: 0.5, fontFace: JP, fontSize: 12, color: MUTE, margin: 0, lineSpacingMultiple: 1.1 });
    cy += ch + 0.2;
  });
}

// ============ Slide 3: 分析パイプライン ============
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  header(s, "PIPELINE", "分析パイプライン");

  const steps = [
    ["入力", "音声ファイル\nまたは JSON"],
    ["文字起こし・話者分離", "faster-whisper\n+ pyannote"],
    ["定量メトリクス", "発話比率・沈黙\n話速・質問 等"],
    ["Claude 分析", "PCCマーカー\n照合"],
    ["レポート", "Markdown\n出力"],
  ];
  const bw = 1.6, bh = 2.5, gap = (9.2 - bw * 5) / 4, x0 = 0.4, y0 = 1.75;
  steps.forEach(([t, d], i) => {
    const x = x0 + i * (bw + gap);
    const isEnd = i === steps.length - 1;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: y0, w: bw, h: bh, rectRadius: 0.09, fill: { color: isEnd ? INK : TINT }, shadow: shadow() });
    numCircle(s, x + bw / 2 - 0.27, y0 + 0.28, i + 1, 0.54, isEnd ? GOLD : TEAL);
    s.addText(t, { x: x + 0.08, y: y0 + 0.95, w: bw - 0.16, h: 0.85, align: "center", valign: "top", fontFace: JPB, fontSize: 13.5, bold: true, color: isEnd ? WHITE : INK, margin: 0, lineSpacingMultiple: 1.05 });
    s.addText(d, { x: x + 0.08, y: y0 + 1.72, w: bw - 0.16, h: 0.7, align: "center", valign: "top", fontFace: JP, fontSize: 10.5, color: isEnd ? TINT : MUTE, margin: 0, lineSpacingMultiple: 1.05 });
    if (i < steps.length - 1) {
      s.addText("›", { x: x + bw, y: y0 + bh / 2 - 0.35, w: gap, h: 0.7, align: "center", valign: "middle", fontFace: "Arial", fontSize: 26, bold: true, color: TEAL, margin: 0 });
    }
  });
  s.addText("録音・分析にはクライアントの同意が必要です（ICF倫理規程 2025）。", { x: 0.4, y: 4.75, w: 9.2, h: 0.35, align: "center", fontFace: JP, fontSize: 11, italic: true, color: MUTE, margin: 0 });
}

// ============ Slide 4: セットアップ ============
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  header(s, "SETUP", "セットアップ");

  function codeCard(x, w, title, badge, badgeColor, lines, h) {
    const y = 1.6;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.07, fill: { color: WHITE }, line: { color: TINT, width: 1.5 }, shadow: shadow() });
    s.addText(title, { x: x + 0.28, y: y + 0.18, w: w - 1.6, h: 0.4, fontFace: JPB, fontSize: 16, bold: true, color: INK, margin: 0 });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x + w - 1.55, y: y + 0.2, w: 1.28, h: 0.34, rectRadius: 0.17, fill: { color: badgeColor } });
    s.addText(badge, { x: x + w - 1.55, y: y + 0.2, w: 1.28, h: 0.34, align: "center", valign: "middle", fontFace: JP, fontSize: 10, bold: true, color: WHITE, margin: 0 });
    // コードブロック
    const cbY = y + 0.72;
    const cbH = h - 0.95;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x + 0.25, y: cbY, w: w - 0.5, h: cbH, rectRadius: 0.05, fill: { color: CODEBG } });
    s.addText(lines.map((t, i) => ({ text: t, options: { breakLine: i < lines.length - 1, color: i % 2 === 0 && t.startsWith("#") ? TEAL : (t.startsWith("$") || t.startsWith("#") ? GOLD : "D8E8E4") } })),
      { x: x + 0.45, y: cbY + 0.12, w: w - 0.85, h: cbH - 0.24, fontFace: MONO, fontSize: 10.5, color: "D8E8E4", valign: "top", margin: 0, lineSpacingMultiple: 1.35 });
  }

  codeCard(0.55, 4.55, "基本セットアップ", "必須", TEAL, [
    "# 仮想環境を有効化",
    ".\\.venv\\Scripts\\Activate.ps1",
    "# 依存パッケージ",
    "pip install -r mentor-coach\\requirements.txt",
    "# Claude APIキー",
    "$env:ANTHROPIC_API_KEY = \"sk-ant-...\"",
  ], 3.4);

  codeCard(5.35, 4.1, "音声分析", "任意", GOLD, [
    "# 文字起こし・話者分離",
    "pip install -r ...\\requirements-audio.txt",
    "# pyannote 用トークン",
    "$env:HF_TOKEN = \"hf_...\"",
  ], 3.4);

  s.addText("音声を使わずトランスクリプトJSONから始める場合、音声分析パッケージは不要です。", { x: 0.55, y: 5.12, w: 9, h: 0.3, fontFace: JP, fontSize: 11, italic: true, color: MUTE, margin: 0 });
}

// ============ Slide 5: 使い方 3コマンド ============
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  header(s, "USAGE", "使い方：3つのコマンド");

  const cmds = [
    ["metrics", "定量メトリクスのみ", "APIキー不要・オフライン", "python -m mentor_coach.cli\nmetrics --transcript \n samples\\sample.json", TEAL],
    ["analyze", "フル分析レポート", "Claude API で PCC照合", "... analyze\n --transcript samples\\...\n -o report.md", INK],
    ["audio", "音声から直接分析", "文字起こし＋話者分離", "... analyze\n --audio session.mp3\n -o report.md", TEAL_DK],
  ];
  const cw = 2.93, gap = 0.2, x0 = 0.55, y0 = 1.6, ch = 3.05;
  cmds.forEach(([name, t, d, code, accent], i) => {
    const x = x0 + i * (cw + gap);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: y0, w: cw, h: ch, rectRadius: 0.08, fill: { color: WHITE }, line: { color: TINT, width: 1.5 }, shadow: shadow() });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x + 0.25, y: y0 + 0.25, w: 1.55, h: 0.42, rectRadius: 0.08, fill: { color: accent } });
    s.addText(name, { x: x + 0.25, y: y0 + 0.25, w: 1.55, h: 0.42, align: "center", valign: "middle", fontFace: MONO, fontSize: 14, bold: true, color: WHITE, margin: 0 });
    s.addText(t, { x: x + 0.25, y: y0 + 0.82, w: cw - 0.5, h: 0.35, fontFace: JPB, fontSize: 14.5, bold: true, color: INK, margin: 0 });
    s.addText(d, { x: x + 0.25, y: y0 + 1.18, w: cw - 0.5, h: 0.35, fontFace: JP, fontSize: 11, color: MUTE, margin: 0 });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x + 0.25, y: y0 + 1.62, w: cw - 0.5, h: 1.2, rectRadius: 0.05, fill: { color: CODEBG } });
    s.addText(code, { x: x + 0.38, y: y0 + 1.72, w: cw - 0.72, h: 1.0, fontFace: MONO, fontSize: 8.5, color: "D8E8E4", valign: "top", margin: 0, lineSpacingMultiple: 1.2 });
  });
  s.addText([
    { text: "ヒント： ", options: { bold: true, color: TEAL_DK } },
    { text: "コーチ／クライアントの自動判定が逆のときは ", options: {} },
    { text: "--swap-speakers", options: { fontFace: MONO, color: INK, bold: true } },
    { text: " を付けてください。", options: {} },
  ], { x: 0.55, y: 4.85, w: 9, h: 0.35, fontFace: JP, fontSize: 11.5, color: MUTE, margin: 0 });
}

// ============ Slide 6: 抽出できる指標 ============
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  header(s, "METRICS", "抽出できる指標（すべて客観指標）");

  const items = [
    ["発話比率", "コーチとクライアントが話す時間の割合"],
    ["沈黙", "4秒以上の沈黙。コーチングでは重要なシグナル"],
    ["話速の変化", "急な加速・減速。感情変化の確認候補"],
    ["割り込み", "相手の発話に重ねて話し始めた箇所"],
    ["質問の分類", "開かれた質問／閉じた質問とその比率"],
    ["話題転換・ループ", "話題の切替と、同じ話題への回帰"],
  ];
  const cw = 2.93, ch = 1.28, gx = 0.2, gy = 0.22, x0 = 0.55, y0 = 1.55;
  items.forEach(([t, d], i) => {
    const col = i % 3, row = Math.floor(i / 3);
    const x = x0 + col * (cw + gx), y = y0 + row * (ch + gy);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: cw, h: ch, rectRadius: 0.07, fill: { color: TINT }, shadow: shadow() });
    numCircle(s, x + 0.25, y + 0.24, i + 1, 0.46, TEAL);
    s.addText(t, { x: x + 0.85, y: y + 0.22, w: cw - 1.0, h: 0.45, valign: "middle", fontFace: JPB, fontSize: 15, bold: true, color: INK, margin: 0 });
    s.addText(d, { x: x + 0.28, y: y + 0.72, w: cw - 0.5, h: 0.5, fontFace: JP, fontSize: 11, color: MUTE, margin: 0, lineSpacingMultiple: 1.1 });
  });
  s.addText("感情ラベルは付けません。数値は「コーチが振り返る手がかり」です。", { x: 0.55, y: 5.12, w: 9, h: 0.3, fontFace: JP, fontSize: 11, italic: true, color: MUTE, margin: 0 });
}

// ============ Slide 7: レポート構成 と 入力形式 ============
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  header(s, "OUTPUT & INPUT", "レポート構成 と 入力形式");

  // 左: レポート6セクション
  const secs = ["セッション概観", "強力だった質問", "PCCマーカー照合", "注目すべきシグナル", "見逃した可能性のあるテーマ", "次のセッションへの実験提案"];
  s.addText("生成されるレポート（6セクション）", { x: 0.55, y: 1.55, w: 4.3, h: 0.35, fontFace: JPB, fontSize: 14, bold: true, color: TEAL_DK, margin: 0 });
  let ly = 2.02;
  secs.forEach((t, i) => {
    numCircle(s, 0.6, ly, i + 1, 0.42, i < 3 ? TEAL : INK);
    s.addText(t, { x: 1.18, y: ly - 0.02, w: 3.7, h: 0.46, valign: "middle", fontFace: JP, fontSize: 13.5, bold: true, color: BODY, margin: 0 });
    ly += 0.5;
  });

  // 右: JSON形式
  s.addText("入力：トランスクリプトJSON", { x: 5.2, y: 1.55, w: 4.3, h: 0.35, fontFace: JPB, fontSize: 14, bold: true, color: TEAL_DK, margin: 0 });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 5.2, y: 2.0, w: 4.25, h: 2.55, rectRadius: 0.06, fill: { color: CODEBG }, shadow: shadow() });
  const json = [
    "[",
    "  {",
    "    \"speaker\": \"coach\",",
    "    \"start\": 0.0, \"end\": 6.0,",
    "    \"text\": \"…\"",
    "  },",
    "  {",
    "    \"speaker\": \"client\", …",
    "  }",
    "]",
  ];
  s.addText(json.map((t, i) => ({ text: t, options: { breakLine: i < json.length - 1 } })), { x: 5.45, y: 2.16, w: 3.85, h: 2.25, fontFace: MONO, fontSize: 11, color: "D8E8E4", valign: "top", margin: 0, lineSpacingMultiple: 1.15 });
  s.addText("speaker は coach / client を使用。start・end は秒。", { x: 5.2, y: 4.68, w: 4.3, h: 0.35, fontFace: JP, fontSize: 10.5, italic: true, color: MUTE, margin: 0 });
}

// ============ Slide 8: 倫理・法的注意 ============
{
  const s = pres.addSlide();
  s.background = { color: INK };
  s.addShape(pres.shapes.OVAL, { x: -1.2, y: 3.6, w: 3.6, h: 3.6, fill: { color: TEAL, transparency: 82 } });
  s.addText("IMPORTANT", { x: 0.6, y: 0.55, w: 9, h: 0.3, fontFace: JP, fontSize: 12, bold: true, color: GOLD, charSpacing: 2, margin: 0 });
  s.addText("倫理・法的な注意（必読）", { x: 0.6, y: 0.85, w: 9, h: 0.7, fontFace: JPB, fontSize: 30, bold: true, color: WHITE, margin: 0 });

  const pts = [
    ["クライアントの同意", "セッションの録音・AI分析には事前の同意が必要です（ICF倫理規程 2025 でAI利用の開示が義務）。"],
    ["EU AI Act 第5条", "職場での生体データからの感情推定は禁止。本ツールが感情を断定しないのはこのためです。"],
    ["資格時間の代替ではない", "ICF資格取得に必要なメンターコーチング時間には算入されません。練習・準備の補完に留めます。"],
  ];
  let py = 1.95;
  pts.forEach(([t, d], i) => {
    numCircle(s, 0.6, py, i + 1, 0.55, GOLD);
    s.addText(t, { x: 1.35, y: py - 0.04, w: 8, h: 0.4, fontFace: JPB, fontSize: 17, bold: true, color: WHITE, margin: 0 });
    s.addText(d, { x: 1.35, y: py + 0.36, w: 7.9, h: 0.55, fontFace: JP, fontSize: 12.5, color: TINT, margin: 0, lineSpacingMultiple: 1.15 });
    py += 1.02;
  });
}

pres.writeFile({ fileName: "AIメンターコーチ_使用説明書.pptx" }).then((f) => console.log("written:", f));
