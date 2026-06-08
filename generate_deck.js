"use strict";
const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.title = "CareCircle — Demo Script";

// ─── Palette (no # prefix) ────────────────────────────────────────────────
const BG      = "09090B";
const SURF    = "18181B";
const BORDER  = "27272A";
const TEAL    = "14B8A6";
const TEAL_LT = "2DD4BF";
const TEAL_DK = "0D9488";
const WHITE   = "FFFFFF";
const SEC     = "A1A1AA";
const MUTED   = "52525B";
const EMERALD = "34D399";
const AMBER   = "FBBF24";
const RED     = "F87171";
const PURPLE  = "A78BFA";
const BLUE    = "60A5FA";
const ORANGE  = "FB923C";

const DIR = path.join(__dirname);

// ─── Helpers ─────────────────────────────────────────────────────────────
function mkShadow() {
  return { type: "outer", blur: 8, offset: 3, angle: 135, color: "000000", opacity: 0.22 };
}

function addCard(s, x, y, w, h, accent) {
  s.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h,
    fill: { color: SURF },
    line: { color: BORDER, width: 0.75 },
    shadow: mkShadow()
  });
  if (accent) {
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 0.055, h,
      fill: { color: accent },
      line: { color: accent }
    });
  }
}

function addFooter(s, label) {
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 5.42, w: 10, h: 0.205,
    fill: { color: TEAL_DK }, line: { color: TEAL_DK }
  });
  s.addText("CareCircle", {
    x: 0.35, y: 5.435, w: 1.8, h: 0.17,
    fontSize: 8, color: WHITE, bold: true, margin: 0
  });
  if (label) {
    s.addText("— " + label, {
      x: 2.1, y: 5.435, w: 5.5, h: 0.17,
      fontSize: 8, color: "C7FFF9", margin: 0
    });
  }
  s.addText("carecercle.vercel.app", {
    x: 7.5, y: 5.435, w: 2.2, h: 0.17,
    fontSize: 8, color: "C7FFF9", align: "right", margin: 0
  });
}

function addTag(s, label, color) {
  const col = color || TEAL;
  const w = Math.max(label.length * 0.115 + 0.28, 1.1);
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 0.28, w, h: 0.27,
    fill: { color: col, transparency: 80 },
    line: { color: col, width: 0.75 }
  });
  s.addText(label.toUpperCase(), {
    x: 0.5, y: 0.275, w, h: 0.28,
    fontSize: 7.5, color: col, bold: true, align: "center",
    charSpacing: 2, margin: 0
  });
}

function imgBase64(filename) {
  const fp = path.join(DIR, filename);
  if (!fs.existsSync(fp)) return null;
  return "image/png;base64," + fs.readFileSync(fp).toString("base64");
}

// ══════════════════════════════════════════════════════════════════════════
// SLIDE 1 — TITLE
// ══════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: BG };

  // Left teal bar
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.14, h: 5.625,
    fill: { color: TEAL_DK }, line: { color: TEAL_DK }
  });
  // Top accent line
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.14, y: 0, w: 9.86, h: 0.07,
    fill: { color: TEAL }, line: { color: TEAL }
  });

  s.addText("CareCircle", {
    x: 0.7, y: 0.9, w: 9, h: 1.35,
    fontSize: 76, fontFace: "Calibri", color: WHITE,
    bold: true, align: "left", margin: 0
  });

  // Teal underline
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.7, y: 2.12, w: 5.0, h: 0.065,
    fill: { color: TEAL }, line: { color: TEAL }
  });

  s.addText("AI Care Coordination for India's Aging Parents", {
    x: 0.7, y: 2.28, w: 9, h: 0.55,
    fontSize: 22, fontFace: "Calibri", color: TEAL_LT,
    align: "left", margin: 0
  });
  s.addText("Built on ABDM  ·  Powered by Claude AI  ·  Delivered via Telegram", {
    x: 0.7, y: 2.9, w: 9, h: 0.38,
    fontSize: 13, color: SEC, align: "left", margin: 0
  });

  // Stat cards
  const stats = [
    { val: "140M+",  lbl: "Indians over 60" },
    { val: "5+ Meds", lbl: "avg per elderly patient" },
    { val: "0 Apps",  lbl: "needed — just Telegram" },
  ];
  stats.forEach((st, i) => {
    const x = 0.7 + i * 3.1;
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: 3.62, w: 2.88, h: 1.35,
      fill: { color: SURF }, line: { color: BORDER, width: 0.75 },
      shadow: mkShadow()
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: 3.62, w: 0.055, h: 1.35,
      fill: { color: TEAL }, line: { color: TEAL }
    });
    s.addText(st.val, {
      x: x + 0.2, y: 3.72, w: 2.55, h: 0.62,
      fontSize: 32, color: TEAL_LT, bold: true, margin: 0
    });
    s.addText(st.lbl, {
      x: x + 0.2, y: 4.34, w: 2.55, h: 0.3,
      fontSize: 11, color: SEC, margin: 0
    });
  });
}

// ══════════════════════════════════════════════════════════════════════════
// SLIDE 2 — THE PROBLEM
// ══════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: BG };
  addTag(s, "The Problem");

  s.addText("Your parent is sick. You're 500 km away.", {
    x: 0.5, y: 0.62, w: 9, h: 0.75,
    fontSize: 32, color: WHITE, bold: true, margin: 0
  });
  s.addText("140M+ Indians over 60. Most are managed remotely by working children who live far away.", {
    x: 0.5, y: 1.42, w: 9, h: 0.38,
    fontSize: 14, color: SEC, margin: 0
  });

  const problems = [
    {
      title: "Fragmented Records",
      body: "Prescriptions on paper. Lab reports in WhatsApp. Caregiver updates via voice note. Nobody has the full picture at any point in time.",
      color: RED
    },
    {
      title: "Invisible Drug Interactions",
      body: "Average elderly patient takes 5+ daily medications prescribed by 2-3 different doctors. No system checks for conflicts. Until something goes wrong.",
      color: AMBER
    },
    {
      title: "Caregiver Blindspot",
      body: "You find out about a hospitalization hours later. No proactive alerts. No daily health summary. Just anxiety every time the phone rings.",
      color: ORANGE
    }
  ];

  problems.forEach((p, i) => {
    const x = 0.5 + i * 3.1;
    addCard(s, x, 2.0, 2.92, 3.1, p.color);
    s.addText(p.title, {
      x: x + 0.22, y: 2.12, w: 2.6, h: 0.38,
      fontSize: 14.5, color: WHITE, bold: true, margin: 0
    });
    s.addText(p.body, {
      x: x + 0.22, y: 2.58, w: 2.62, h: 1.9,
      fontSize: 11.5, color: SEC, margin: 0
    });
  });

  // Bottom callout bar
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 5.08, w: 9, h: 0.3,
    fill: { color: SURF }, line: { color: BORDER }
  });
  s.addText("Today's healthcare system was designed for patients who walk in — not families who call in.", {
    x: 0.65, y: 5.09, w: 8.7, h: 0.28,
    fontSize: 11, color: TEAL_LT, italic: true, margin: 0
  });

  addFooter(s, "Problem Statement");
}

// ══════════════════════════════════════════════════════════════════════════
// SLIDE 3 — THE SOLUTION
// ══════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: BG };
  addTag(s, "The Solution");

  s.addText("CareCircle", {
    x: 0.5, y: 0.62, w: 9, h: 0.72,
    fontSize: 40, color: WHITE, bold: true, margin: 0
  });
  s.addText("One AI-powered platform. Three layers that work together.", {
    x: 0.5, y: 1.38, w: 9, h: 0.38,
    fontSize: 15, color: SEC, margin: 0
  });

  const pillars = [
    {
      num: "01",
      title: "AI Analysis",
      sub: "Claude AI + Gemini Flash",
      points: [
        "OCR: extract meds from prescription photos",
        "Drug interaction check across all active meds",
        "Daily briefing: one paragraph, what matters most",
        "Abnormal lab flag with clinical context"
      ],
      color: TEAL
    },
    {
      num: "02",
      title: "ABDM Rails",
      sub: "India's digital health highway",
      points: [
        "ABHA ID links patient to national health records",
        "UHI protocol: discover doctors, book appointments",
        "FHIR-based PHR: structured, machine-readable",
        "Consent-gated: patient owns their own data"
      ],
      color: BLUE
    },
    {
      num: "03",
      title: "Telegram Interface",
      sub: "Zero app install required",
      points: [
        "/summary: AI health snapshot in seconds",
        "/addappointment: book via conversation",
        "Works on any phone, any data plan",
        "India's most-used messaging platform"
      ],
      color: EMERALD
    }
  ];

  pillars.forEach((p, i) => {
    const x = 0.5 + i * 3.1;
    addCard(s, x, 1.92, 2.92, 3.3, p.color);

    s.addText(p.num, {
      x: x + 0.22, y: 2.05, w: 0.7, h: 0.45,
      fontSize: 24, color: p.color, bold: true, margin: 0
    });
    s.addText(p.title, {
      x: x + 0.22, y: 2.52, w: 2.6, h: 0.38,
      fontSize: 16.5, color: WHITE, bold: true, margin: 0
    });
    s.addText(p.sub, {
      x: x + 0.22, y: 2.9, w: 2.6, h: 0.26,
      fontSize: 10, color: p.color, margin: 0
    });

    const items = p.points.map((pt, idx) => ({
      text: pt,
      options: { bullet: true, breakLine: idx < p.points.length - 1, color: SEC, fontSize: 10.5 }
    }));
    s.addText(items, {
      x: x + 0.12, y: 3.24, w: 2.72, h: 1.82,
      margin: [0, 0, 0, 8]
    });
  });

  addFooter(s, "Solution Overview");
}

// ══════════════════════════════════════════════════════════════════════════
// SLIDE 4 — ABDM: INDIA'S DIGITAL HEALTH STACK
// ══════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: BG };
  addTag(s, "India's Health Stack", BLUE);

  s.addText("ABDM: Ayushman Bharat Digital Mission", {
    x: 0.5, y: 0.62, w: 9, h: 0.65,
    fontSize: 28, color: WHITE, bold: true, margin: 0
  });
  s.addText("India's national digital health highway — like GSTN for taxes, ONDC for commerce, now for healthcare.", {
    x: 0.5, y: 1.3, w: 9, h: 0.36,
    fontSize: 13, color: SEC, margin: 0
  });

  // Left column: 5 components
  const components = [
    { label: "ABHA",     full: "Ayushman Bharat Health Account",     desc: "14-digit health ID for every Indian citizen. Permanent, portable, interoperable.",      color: TEAL },
    { label: "PHR",      full: "Personal Health Record",             desc: "Longitudinal health record. FHIR R4 standard. Linked to ABHA. Owned by patient.",        color: BLUE },
    { label: "HIU/HIP",  full: "Health Information User & Provider", desc: "HIU = apps that request records (CareCircle). HIP = hospitals/labs that provide them.",  color: PURPLE },
    { label: "Locker",   full: "ABDM Health Locker",                 desc: "Federated record storage. Patient consents to share. No central government database.",   color: EMERALD },
    { label: "HCX",      full: "Health Claims Exchange",             desc: "Open insurance claims protocol. Automates the entire claim cycle without paper forms.",   color: AMBER },
  ];

  components.forEach((c, i) => {
    const y = 1.82 + i * 0.67;
    // Pill
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.5, y: y + 0.03, w: 1.0, h: 0.36,
      fill: { color: c.color, transparency: 78 },
      line: { color: c.color, width: 0.75 }
    });
    s.addText(c.label, {
      x: 0.5, y: y + 0.03, w: 1.0, h: 0.36,
      fontSize: 9.5, color: c.color, bold: true, align: "center", valign: "middle", margin: 0
    });
    s.addText(c.full, {
      x: 1.62, y: y + 0.03, w: 3.65, h: 0.2,
      fontSize: 10.5, color: WHITE, bold: true, margin: 0
    });
    s.addText(c.desc, {
      x: 1.62, y: y + 0.22, w: 3.65, h: 0.24,
      fontSize: 9.5, color: SEC, margin: 0
    });
  });

  // Right: why it matters card
  addCard(s, 5.55, 1.75, 4.0, 3.32, BLUE);
  s.addText("Why this matters", {
    x: 5.78, y: 1.88, w: 3.6, h: 0.34,
    fontSize: 13, color: BLUE, bold: true, margin: 0
  });

  const whys = [
    "30+ crore ABHA IDs issued — India's health identity layer is live",
    "2,000+ hospitals on ABDM network and growing",
    "Records are portable — follow the patient, not the hospital",
    "Zero data lock-in — patient can revoke consent anytime",
    "Govt mandate: all new digital health apps must be ABDM-compliant",
    "CareCircle doesn't store health records — ABHA does. We read, analyze, alert."
  ];

  const whyItems = whys.map((w, idx) => ({
    text: w,
    options: { bullet: true, breakLine: idx < whys.length - 1, color: SEC, fontSize: 10 }
  }));
  s.addText(whyItems, {
    x: 5.68, y: 2.32, w: 3.72, h: 2.6,
    margin: [0, 0, 0, 6]
  });

  addFooter(s, "ABDM Background");
}

// ══════════════════════════════════════════════════════════════════════════
// SLIDE 5 — UHI: THE UPI OF HEALTHCARE
// ══════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: BG };
  addTag(s, "UHI Deep Dive", PURPLE);

  s.addText("UHI: Unified Health Interface", {
    x: 0.5, y: 0.62, w: 9, h: 0.65,
    fontSize: 30, color: WHITE, bold: true, margin: 0
  });
  s.addText("Open protocol for health service discovery and delivery — the BECKN layer on top of ABDM.", {
    x: 0.5, y: 1.3, w: 9, h: 0.34,
    fontSize: 13, color: SEC, margin: 0
  });

  // Analogy bar
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.72, w: 9, h: 0.42,
    fill: { color: SURF }, line: { color: BORDER }
  });
  s.addText([
    { text: "Think UPI for payments, ONDC for commerce — ", options: { color: SEC, fontSize: 11.5 } },
    { text: "UHI does the same for healthcare services.", options: { color: TEAL_LT, fontSize: 11.5, bold: true } }
  ], {
    x: 0.65, y: 1.725, w: 8.7, h: 0.41,
    valign: "middle", margin: 0
  });

  // Three actors
  const actors = [
    {
      label: "EUA",
      full: "End User Application",
      desc: "Patient-facing apps. CareCircle registers as an EUA. Sends health service requests on behalf of the caregiver or patient.",
      example: "CareCircle, ABHA App, Practo",
      color: TEAL
    },
    {
      label: "Gateway",
      full: "UHI Gateway",
      desc: "Routes requests between EUAs and HSPs. Operated by NHA. Handles service discovery, matching, and routing — invisible to users.",
      example: "gateway.abdm.gov.in (NHA)",
      color: PURPLE
    },
    {
      label: "HSP",
      full: "Health Service Provider",
      desc: "Any doctor, hospital, lab, or pharmacy registered on UHI. Public or private. Apollo to a local clinic — all discoverable via the same API.",
      example: "Apollo, AIIMS, SRL Diagnostics",
      color: BLUE
    }
  ];

  actors.forEach((a, i) => {
    const x = 0.5 + i * 3.1;
    addCard(s, x, 2.25, 2.92, 1.68, a.color);

    s.addText(a.label, {
      x: x + 0.22, y: 2.33, w: 0.85, h: 0.42,
      fontSize: 22, color: a.color, bold: true, margin: 0
    });
    s.addText(a.full, {
      x: x + 0.22, y: 2.75, w: 2.6, h: 0.24,
      fontSize: 10.5, color: WHITE, bold: true, margin: 0
    });
    s.addText(a.desc, {
      x: x + 0.22, y: 2.98, w: 2.62, h: 0.65,
      fontSize: 9.5, color: SEC, margin: 0
    });
    s.addText("e.g. " + a.example, {
      x: x + 0.22, y: 3.67, w: 2.62, h: 0.2,
      fontSize: 8.5, color: a.color, italic: true, margin: 0
    });
  });

  // Flow line connector
  s.addShape(pres.shapes.LINE, {
    x: 1.5, y: 2.59, w: 7.1, h: 0,
    line: { color: BORDER, width: 0.75, dashType: "dash" }
  });
  s.addText("EUA  →  Gateway  →  HSP", {
    x: 3.5, y: 2.48, w: 3, h: 0.22,
    fontSize: 8, color: MUTED, align: "center", margin: 0
  });

  // What flows over UHI
  s.addText("What transacts over UHI", {
    x: 0.5, y: 4.05, w: 5, h: 0.3,
    fontSize: 13, color: WHITE, bold: true, margin: 0
  });

  const flows = [
    { label: "Doctor & specialist discovery by location, specialty, language", color: TEAL },
    { label: "Appointment booking (standardized, open protocol)", color: TEAL },
    { label: "Teleconsultation (video / audio)", color: BLUE },
    { label: "PHR request & share (FHIR R4, consent-gated)", color: PURPLE },
    { label: "Prescription digitization to ABHA locker post-consult", color: EMERALD },
    { label: "Lab report delivery direct to patient's health record", color: AMBER },
  ];

  flows.forEach((f, i) => {
    const col = i < 3 ? 0 : 1;
    const row = i % 3;
    const x = 0.5 + col * 4.85;
    const y = 4.42 + row * 0.29;
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: y + 0.03, w: 0.08, h: 0.19,
      fill: { color: f.color }, line: { color: f.color }
    });
    s.addText(f.label, {
      x: x + 0.18, y, w: 4.5, h: 0.25,
      fontSize: 10.5, color: SEC, margin: 0
    });
  });

  addFooter(s, "UHI Protocol — Deep Dive");
}

// ══════════════════════════════════════════════════════════════════════════
// SLIDE 6 — CARECIRCLE ON THE ABDM STACK
// ══════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: BG };
  addTag(s, "How We Use It", TEAL);

  s.addText("CareCircle rides ABDM rails.", {
    x: 0.5, y: 0.62, w: 5.5, h: 0.65,
    fontSize: 30, color: WHITE, bold: true, margin: 0
  });
  s.addText("Like Paytm rides UPI rails — we don't build health infrastructure. We build the AI and UX layer on top.", {
    x: 0.5, y: 1.3, w: 9.2, h: 0.38,
    fontSize: 13.5, color: SEC, margin: 0
  });

  // Left: what ABDM gives free
  addCard(s, 0.5, 1.82, 4.28, 3.32, BLUE);
  s.addText("What ABDM gives us — for free", {
    x: 0.73, y: 1.94, w: 3.88, h: 0.33,
    fontSize: 12.5, color: BLUE, bold: true, margin: 0
  });

  const freeItems = [
    { item: "Patient Identity",      detail: "ABHA ID = no user health database to build or secure" },
    { item: "Record Storage",        detail: "ABHA Locker = zero infrastructure; records stay with patient" },
    { item: "Provider Directory",    detail: "UHI Gateway = 2,000+ providers auto-discoverable via API" },
    { item: "Consent Management",    detail: "ABDM framework = DPDP-compliant, patient-controlled access" },
    { item: "Record Portability",    detail: "FHIR R4 = records from Apollo, AIIMS, local clinic — same format" },
  ];

  freeItems.forEach((fi, i) => {
    const y = 2.38 + i * 0.56;
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.73, y: y + 0.04, w: 0.08, h: 0.2,
      fill: { color: EMERALD }, line: { color: EMERALD }
    });
    s.addText(fi.item, {
      x: 0.92, y: y + 0.02, w: 3.7, h: 0.22,
      fontSize: 11.5, color: WHITE, bold: true, margin: 0
    });
    s.addText(fi.detail, {
      x: 0.92, y: y + 0.24, w: 3.7, h: 0.2,
      fontSize: 9.5, color: SEC, margin: 0
    });
  });

  // Right: what CareCircle builds
  addCard(s, 5.12, 1.82, 4.28, 3.32, TEAL);
  s.addText("What CareCircle builds on top", {
    x: 5.35, y: 1.94, w: 3.88, h: 0.33,
    fontSize: 12.5, color: TEAL, bold: true, margin: 0
  });

  const buildItems = [
    { item: "AI Analysis Layer",       detail: "Claude briefings + Gemini OCR — no ABDM app has this yet" },
    { item: "Caregiver-First UX",      detail: "Designed for the adult child 500 km away, not just the patient" },
    { item: "Telegram Interface",      detail: "WhatsApp-like familiarity. Zero install friction. Any phone." },
    { item: "Proactive Alerting",      detail: "Abnormal labs, drug interactions, missed meds — pushed, not pulled" },
    { item: "Family Coordination",     detail: "Multiple caregivers share one health view across distance" },
  ];

  buildItems.forEach((bi, i) => {
    const y = 2.38 + i * 0.56;
    s.addShape(pres.shapes.RECTANGLE, {
      x: 5.35, y: y + 0.04, w: 0.08, h: 0.2,
      fill: { color: TEAL }, line: { color: TEAL }
    });
    s.addText(bi.item, {
      x: 5.55, y: y + 0.02, w: 3.7, h: 0.22,
      fontSize: 11.5, color: WHITE, bold: true, margin: 0
    });
    s.addText(bi.detail, {
      x: 5.55, y: y + 0.24, w: 3.7, h: 0.2,
      fontSize: 9.5, color: SEC, margin: 0
    });
  });

  addFooter(s, "CareCircle Architecture Position");
}

// ══════════════════════════════════════════════════════════════════════════
// SLIDE 7 — PRODUCT DEMO: WEB DASHBOARD
// ══════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: BG };
  addTag(s, "Product Demo", EMERALD);

  s.addText("Web Dashboard", {
    x: 0.5, y: 0.62, w: 4.8, h: 0.65,
    fontSize: 30, color: WHITE, bold: true, margin: 0
  });
  s.addText("Full caregiver view — medications, labs, appointments, AI briefing.", {
    x: 0.5, y: 1.3, w: 4.8, h: 0.36,
    fontSize: 12.5, color: SEC, margin: 0
  });

  // Demo steps (left)
  const steps = [
    { num: "1", action: "Login",          detail: "srikanthkarkampally01@gmail.com", color: TEAL },
    { num: "2", action: "Patient Profile", detail: "Rajesh Sharma — B+, Nellore AP. Conditions: Type 2 Diabetes, Hypertension.", color: BLUE },
    { num: "3", action: "Lab Flags",       detail: "3 abnormal results: BP 150/95 mmHg, FBS 180 mg/dL — all flagged in amber/red.", color: RED },
    { num: "4", action: "Medications",     detail: "5 active meds: Metformin, Glimepiride, Amlodipine, Aspirin, Atorvastatin.", color: EMERALD },
    { num: "5", action: "AI Briefing",     detail: "Claude reads all data → one-paragraph morning summary at 7 AM IST.", color: AMBER },
  ];

  steps.forEach((st, i) => {
    const y = 1.82 + i * 0.67;
    s.addShape(pres.shapes.OVAL, {
      x: 0.5, y: y + 0.05, w: 0.36, h: 0.36,
      fill: { color: st.color }, line: { color: st.color }
    });
    s.addText(st.num, {
      x: 0.5, y: y + 0.05, w: 0.36, h: 0.36,
      fontSize: 12, color: BG, bold: true, align: "center", valign: "middle", margin: 0
    });
    s.addText(st.action, {
      x: 0.98, y: y + 0.05, w: 4.15, h: 0.22,
      fontSize: 12, color: WHITE, bold: true, margin: 0
    });
    s.addText(st.detail, {
      x: 0.98, y: y + 0.27, w: 4.15, h: 0.28,
      fontSize: 9.5, color: SEC, margin: 0
    });
  });

  // Right: actual dashboard screenshot
  const dashImg = imgBase64("ss_dashboard.png");
  if (dashImg) {
    // Screenshot frame
    s.addShape(pres.shapes.RECTANGLE, {
      x: 5.55, y: 1.55, w: 4.0, h: 3.75,
      fill: { color: "111111" }, line: { color: "333333", width: 1 },
      shadow: mkShadow()
    });
    // Browser chrome bar
    s.addShape(pres.shapes.RECTANGLE, {
      x: 5.55, y: 1.55, w: 4.0, h: 0.3,
      fill: { color: "1C1C1C" }, line: { color: "2A2A2A" }
    });
    ["F87171", "FBBF24", "34D399"].forEach((c, i) => {
      s.addShape(pres.shapes.OVAL, {
        x: 5.68 + i * 0.21, y: 1.64, w: 0.12, h: 0.12,
        fill: { color: c }, line: { color: c }
      });
    });
    s.addText("carecercle.vercel.app/dashboard", {
      x: 6.2, y: 1.59, w: 2.8, h: 0.22,
      fontSize: 7, color: "666666", align: "center", valign: "middle", margin: 0
    });
    // Screenshot
    s.addImage({ data: dashImg, x: 5.56, y: 1.85, w: 3.98, h: 3.44 });
  } else {
    // Fallback shape mockup
    addCard(s, 5.55, 1.55, 4.0, 3.75, TEAL);
    s.addText("Dashboard Screenshot\n(carecercle.vercel.app)", {
      x: 5.7, y: 3.1, w: 3.7, h: 0.8,
      fontSize: 12, color: SEC, align: "center", margin: 0
    });
  }

  addFooter(s, "Product Demo — Web Dashboard");
}

// ══════════════════════════════════════════════════════════════════════════
// SLIDE 8 — PRODUCT DEMO: TELEGRAM BOT
// ══════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: BG };
  addTag(s, "Product Demo", EMERALD);

  s.addText("Telegram Bot: @CarCercle_Bot", {
    x: 0.5, y: 0.62, w: 5.5, h: 0.65,
    fontSize: 28, color: WHITE, bold: true, margin: 0
  });
  s.addText("Zero app install. Works on any smartphone. India's most-used messaging platform.", {
    x: 0.5, y: 1.3, w: 5.4, h: 0.36,
    fontSize: 12.5, color: SEC, margin: 0
  });

  // Commands list
  const commands = [
    { cmd: "/connect",        desc: "Links your Telegram to your CareCircle account. One-time setup.", color: PURPLE },
    { cmd: "/summary",        desc: "AI-generated health snapshot. Patient data + Claude analysis in seconds.", color: TEAL },
    { cmd: "/addappointment", desc: "Conversational booking flow. Bot asks date, doctor, reason — stores in DB.", color: BLUE },
    { cmd: "/addlab",         desc: "Log lab values in chat. Flags abnormal results automatically.", color: EMERALD },
  ];

  commands.forEach((c, i) => {
    const y = 1.78 + i * 0.87;
    addCard(s, 0.5, y, 5.0, 0.75, c.color);
    s.addText(c.cmd, {
      x: 0.72, y: y + 0.09, w: 4.6, h: 0.28,
      fontSize: 14, color: c.color, bold: true, fontFace: "Consolas", margin: 0
    });
    s.addText(c.desc, {
      x: 0.72, y: y + 0.39, w: 4.6, h: 0.26,
      fontSize: 10, color: SEC, margin: 0
    });
  });

  // Right: phone + chat mockup
  // Phone body
  s.addShape(pres.shapes.RECTANGLE, {
    x: 6.0, y: 0.5, w: 3.5, h: 5.0,
    fill: { color: "0A0A0A" }, line: { color: "2A2A2A", width: 1.5 },
    shadow: mkShadow()
  });
  // Screen
  s.addShape(pres.shapes.RECTANGLE, {
    x: 6.1, y: 0.78, w: 3.3, h: 4.45,
    fill: { color: "17212B" }, line: { color: "17212B" }
  });
  // Telegram app header
  s.addShape(pres.shapes.RECTANGLE, {
    x: 6.1, y: 0.78, w: 3.3, h: 0.42,
    fill: { color: "242F3D" }, line: { color: "242F3D" }
  });
  s.addShape(pres.shapes.OVAL, {
    x: 6.18, y: 0.84, w: 0.28, h: 0.28,
    fill: { color: TEAL }, line: { color: TEAL }
  });
  s.addText("CarCercle_Bot", {
    x: 6.54, y: 0.86, w: 2.5, h: 0.2,
    fontSize: 9, color: WHITE, bold: true, margin: 0
  });
  s.addText("online", {
    x: 6.54, y: 1.04, w: 2, h: 0.13,
    fontSize: 7.5, color: EMERALD, margin: 0
  });

  // User: /summary
  s.addShape(pres.shapes.RECTANGLE, {
    x: 7.28, y: 1.3, w: 2.95, h: 0.28,
    fill: { color: "2B5278" }, line: { color: "2B5278" }
  });
  s.addText("/summary", {
    x: 7.32, y: 1.31, w: 2.85, h: 0.26,
    fontSize: 9.5, color: WHITE, fontFace: "Consolas", margin: 0
  });

  // Bot response: summary
  s.addShape(pres.shapes.RECTANGLE, {
    x: 6.12, y: 1.67, w: 3.05, h: 1.72,
    fill: { color: "182533" }, line: { color: "182533" }
  });
  s.addText([
    { text: "Summary — Rajesh Sharma", options: { bold: true, color: TEAL_LT, fontSize: 8.5, breakLine: true } },
    { text: "5 meds  |  3 abnormal labs", options: { color: WHITE, fontSize: 8, breakLine: true } },
    { text: "0 alerts  |  0 events in 24h", options: { color: WHITE, fontSize: 8, breakLine: true } },
    { text: " ", options: { fontSize: 5, breakLine: true } },
    { text: "STATUS: ", options: { color: AMBER, fontSize: 8.5, bold: true } },
    { text: "WARNING", options: { color: AMBER, fontSize: 8.5, bold: true, breakLine: true } },
    { text: "BP elevated: 150/95 mmHg", options: { color: "AAAAAA", fontSize: 8, breakLine: true } },
    { text: "FBS elevated: 180 mg/dL", options: { color: "AAAAAA", fontSize: 8, breakLine: true } },
    { text: "All 5 meds logged.", options: { color: "AAAAAA", fontSize: 8 } }
  ], {
    x: 6.18, y: 1.72, w: 2.92, h: 1.6,
    valign: "top", margin: [3, 4, 3, 4]
  });

  // User: /addappointment
  s.addShape(pres.shapes.RECTANGLE, {
    x: 6.88, y: 3.48, w: 2.95, h: 0.28,
    fill: { color: "2B5278" }, line: { color: "2B5278" }
  });
  s.addText("/addappointment", {
    x: 6.9, y: 3.49, w: 2.9, h: 0.26,
    fontSize: 8.5, color: WHITE, fontFace: "Consolas", margin: 0
  });

  // Bot response 2
  s.addShape(pres.shapes.RECTANGLE, {
    x: 6.12, y: 3.84, w: 3.05, h: 0.52,
    fill: { color: "182533" }, line: { color: "182533" }
  });
  s.addText("Sure. What date is the appointment?", {
    x: 6.18, y: 3.87, w: 2.9, h: 0.45,
    fontSize: 9, color: WHITE, valign: "middle", margin: [3, 4, 3, 4]
  });

  // User: 20 May, Dr. Reddy
  s.addShape(pres.shapes.RECTANGLE, {
    x: 6.88, y: 4.44, w: 2.95, h: 0.28,
    fill: { color: "2B5278" }, line: { color: "2B5278" }
  });
  s.addText("20 May, Dr. Reddy - Cardiology", {
    x: 6.9, y: 4.45, w: 2.9, h: 0.26,
    fontSize: 7.5, color: WHITE, margin: 0
  });

  // Bot: Booked
  s.addShape(pres.shapes.RECTANGLE, {
    x: 6.12, y: 4.8, w: 3.05, h: 0.32,
    fill: { color: "182533" }, line: { color: "182533" }
  });
  s.addText("Appointment saved for May 20.", {
    x: 6.18, y: 4.82, w: 2.9, h: 0.26,
    fontSize: 8.5, color: EMERALD, margin: [2, 4, 2, 4]
  });

  addFooter(s, "Product Demo — Telegram Bot");
}

// ══════════════════════════════════════════════════════════════════════════
// SLIDE 9 — TELEGRAM + ABDM INTEGRATION ROADMAP
// ══════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: BG };
  addTag(s, "Roadmap", AMBER);

  s.addText("Telegram as the ABDM Interface", {
    x: 0.5, y: 0.62, w: 9, h: 0.65,
    fontSize: 28, color: WHITE, bold: true, margin: 0
  });
  s.addText("The bot you see today will be the front door to India's entire digital health network.", {
    x: 0.5, y: 1.3, w: 9, h: 0.35,
    fontSize: 13.5, color: SEC, margin: 0
  });

  const phases = [
    {
      phase: "Phase 1",
      label: "Now — Live Today",
      color: EMERALD,
      items: [
        "Standalone health record management",
        "Claude AI daily briefings at 7AM IST",
        "Gemini Flash OCR: prescription scanning",
        "/summary, /addappointment via Telegram",
        "Supabase + Vercel — fully deployed"
      ]
    },
    {
      phase: "Phase 2",
      label: "Q3 2026 — ABDM Integration",
      color: TEAL,
      items: [
        "/sync command: pull PHR from ABHA locker",
        "ABHA ID linking inside /connect flow",
        "Register CareCircle as a HIU with NHA",
        "/book command: UHI appointment booking",
        "Consent-gated record access via ABDM API"
      ]
    },
    {
      phase: "Phase 3",
      label: "Q4 2026 — Full UHI EUA",
      color: BLUE,
      items: [
        "Full UHI EUA registration with NHA",
        "Live doctor/lab discovery via UHI gateway",
        "Prescriptions pushed to ABHA locker post-consult",
        "HCX: insurance claim initiation via Telegram",
        "Multi-family, multi-patient coordinator mode"
      ]
    }
  ];

  phases.forEach((p, i) => {
    const x = 0.5 + i * 3.1;
    addCard(s, x, 1.82, 2.92, 3.22, p.color);

    // Phase pill
    s.addShape(pres.shapes.RECTANGLE, {
      x: x + 0.15, y: 1.94, w: 1.22, h: 0.27,
      fill: { color: p.color, transparency: 78 },
      line: { color: p.color, width: 0.75 }
    });
    s.addText(p.phase, {
      x: x + 0.15, y: 1.94, w: 1.22, h: 0.27,
      fontSize: 8, color: p.color, bold: true, align: "center", valign: "middle", margin: 0
    });

    s.addText(p.label, {
      x: x + 0.22, y: 2.28, w: 2.6, h: 0.36,
      fontSize: 12, color: WHITE, bold: true, margin: 0
    });

    const items = p.items.map((it, idx) => ({
      text: it,
      options: { bullet: true, breakLine: idx < p.items.length - 1, color: SEC, fontSize: 10 }
    }));
    s.addText(items, {
      x: x + 0.12, y: 2.72, w: 2.72, h: 2.2,
      margin: [0, 0, 0, 6]
    });
  });

  // Bottom callout
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 5.1, w: 9, h: 0.28,
    fill: { color: SURF }, line: { color: BORDER }
  });
  s.addText("End goal: caregiver in Bangalore books a specialist in Chennai for a parent in Nellore — from Telegram, in 2 messages, via UHI.", {
    x: 0.65, y: 5.11, w: 8.7, h: 0.26,
    fontSize: 10, color: TEAL_LT, italic: true, margin: 0
  });

  addFooter(s, "Roadmap — Telegram + ABDM");
}

// ══════════════════════════════════════════════════════════════════════════
// SLIDE 10 — THE ASK
// ══════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: BG };

  // Left teal bar
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.14, h: 5.625,
    fill: { color: TEAL_DK }, line: { color: TEAL_DK }
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.14, y: 0, w: 9.86, h: 0.07,
    fill: { color: TEAL }, line: { color: TEAL }
  });

  s.addText("The Opportunity", {
    x: 0.6, y: 0.5, w: 9, h: 0.42,
    fontSize: 13, color: TEAL, bold: true, charSpacing: 3, margin: 0
  });
  s.addText("India's aging-care gap is a\n₹50,000 crore problem waiting\nfor the right infrastructure.", {
    x: 0.6, y: 0.98, w: 9, h: 1.35,
    fontSize: 30, color: WHITE, bold: true, margin: 0
  });
  s.addText("ABDM gives us the rails.  Claude gives us the intelligence.  Telegram gives us the reach.", {
    x: 0.6, y: 2.42, w: 9.1, h: 0.4,
    fontSize: 15, color: TEAL_LT, margin: 0
  });

  const asks = [
    {
      label: "Pilot Families",
      desc: "10 families with an aging parent. Free for 6 months. Help us tune AI, UX, and ABDM consent flows.",
      color: TEAL
    },
    {
      label: "Hospital / Clinic Partners",
      desc: "ABDM-registered HIPs to pilot UHI appointment booking and PHR sharing. Public or private.",
      color: BLUE
    },
    {
      label: "Investor Interest",
      desc: "Pre-seed round opening Q3 2026. Focus: ABDM HIU registration, UHI EUA build-out, engineering team.",
      color: PURPLE
    }
  ];

  asks.forEach((a, i) => {
    const x = 0.6 + i * 3.1;
    addCard(s, x, 3.0, 2.92, 2.12, a.color);
    s.addText(a.label, {
      x: x + 0.22, y: 3.1, w: 2.6, h: 0.38,
      fontSize: 14, color: a.color, bold: true, margin: 0
    });
    s.addText(a.desc, {
      x: x + 0.22, y: 3.55, w: 2.6, h: 1.3,
      fontSize: 10.5, color: SEC, margin: 0
    });
  });

  // Bottom bar
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 5.22, w: 10, h: 0.405,
    fill: { color: SURF }, line: { color: BORDER }
  });
  s.addText("Demo: carecercle.vercel.app  ·  Bot: @CarCercle_Bot  ·  srikanthkarkampally01@gmail.com", {
    x: 0.5, y: 5.3, w: 9, h: 0.25,
    fontSize: 10.5, color: TEAL_LT, align: "center", margin: 0
  });
}

// ══════════════════════════════════════════════════════════════════════════
// Write
// ══════════════════════════════════════════════════════════════════════════
pres.writeFile({ fileName: "CareCircle_Demo.pptx" })
  .then(() => console.log("Done → CareCircle_Demo.pptx"))
  .catch(e => { console.error(e); process.exit(1); });
