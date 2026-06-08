"use strict";
const {
  Document, Packer, Paragraph, TextRun,
  AlignmentType, PageBreak, ShadingType, BorderStyle
} = require("docx");
const fs   = require("fs");
const path = require("path");

// ─── Sizes (half-points) ─────────────────────────────────────────────────
const SZ_HEADER = 52;   // 26pt — slide banner
const SZ_BODY   = 44;   // 22pt — spoken words
const SZ_CUE    = 32;   // 16pt — [PAUSE] / [DEMO]
const SZ_NOTE   = 26;   // 13pt — timing note

// ─── Colors ──────────────────────────────────────────────────────────────
const TEAL   = "0D9488";
const WHITE  = "FFFFFF";
const DARK   = "1F2937";
const GRAY   = "6B7280";
const AMBER  = "92400E";   // dark amber — readable on amber bg
const AMBERBG= "FEF3C7";
const REDBG  = "FEE2E2";
const REDFG  = "991B1B";

// ─── Helpers ─────────────────────────────────────────────────────────────
const BSPACING = { line: 360, lineRule: "auto", before: 0, after: 220 };
const CSPACING = { line: 280, lineRule: "auto", before: 140, after: 140 };

function slideHeader(num, title, timing) {
  return [
    new Paragraph({ children: [new PageBreak()] }),
    new Paragraph({
      shading: { fill: TEAL, type: ShadingType.CLEAR },
      spacing: { before: 0, after: 360 },
      children: [
        new TextRun({
          text: `  SLIDE ${num}  —  ${title}  `,
          bold: true, size: SZ_HEADER, color: WHITE, font: "Arial"
        }),
        new TextRun({
          text: `  ${timing}`,
          size: SZ_NOTE, color: "C7FFF9", font: "Arial", italic: true
        })
      ]
    })
  ];
}

function say(text) {
  return new Paragraph({
    spacing: BSPACING,
    children: [new TextRun({ text, size: SZ_BODY, color: DARK, font: "Arial" })]
  });
}

function pause(label) {
  return new Paragraph({
    spacing: CSPACING,
    children: [new TextRun({
      text: label || "[ PAUSE ]",
      size: SZ_CUE, color: GRAY, italic: true, bold: true, font: "Arial"
    })]
  });
}

function demo(instruction) {
  return new Paragraph({
    shading: { fill: AMBERBG, type: ShadingType.CLEAR },
    spacing: CSPACING,
    children: [new TextRun({
      text: `  ▶  ${instruction}  `,
      size: SZ_CUE, color: AMBER, bold: true, font: "Arial"
    })]
  });
}

function warn(instruction) {
  return new Paragraph({
    shading: { fill: REDBG, type: ShadingType.CLEAR },
    spacing: CSPACING,
    children: [new TextRun({
      text: `  ! ${instruction}  `,
      size: SZ_CUE, color: REDFG, bold: true, font: "Arial"
    })]
  });
}

function gap() {
  return new Paragraph({
    spacing: { before: 0, after: 280 },
    children: [new TextRun({ text: " ", size: 24 })]
  });
}

function divider() {
  return new Paragraph({
    border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "E5E7EB", space: 1 } },
    spacing: { before: 240, after: 240 },
    children: [new TextRun({ text: " " })]
  });
}

// ─── Build script ─────────────────────────────────────────────────────────

const slides = [];

// ── Cover page ────────────────────────────────────────────────────────────
slides.push(
  new Paragraph({
    spacing: { before: 720, after: 280 },
    children: [new TextRun({ text: "CareCircle", size: 88, bold: true, color: TEAL, font: "Arial" })]
  }),
  new Paragraph({
    spacing: { before: 0, after: 160 },
    children: [new TextRun({ text: "Teleprompter Script — Demo Presentation", size: 40, color: GRAY, font: "Arial" })]
  }),
  new Paragraph({
    spacing: { before: 0, after: 600 },
    children: [new TextRun({ text: "10 slides  ·  12–15 minutes  ·  Live demo included", size: 32, color: GRAY, font: "Arial", italic: true })]
  }),
  new Paragraph({
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: TEAL, space: 1 } },
    spacing: { before: 0, after: 440 },
    children: [new TextRun({ text: " " })]
  }),
  new Paragraph({
    spacing: { before: 0, after: 120 },
    children: [new TextRun({ text: "How to read this script:", size: 28, bold: true, color: DARK, font: "Arial" })]
  }),
  new Paragraph({
    spacing: { before: 0, after: 80 },
    children: [
      new TextRun({ text: "Large black text", size: 28, color: DARK, font: "Arial" }),
      new TextRun({ text: "  =  words to speak out loud", size: 28, color: GRAY, font: "Arial" })
    ]
  }),
  new Paragraph({
    spacing: { before: 0, after: 80 },
    children: [
      new TextRun({ text: "[ PAUSE ]", size: 28, color: GRAY, italic: true, bold: true, font: "Arial" }),
      new TextRun({ text: "  =  stop, let it breathe, look at the audience", size: 28, color: GRAY, font: "Arial" })
    ]
  }),
  new Paragraph({
    spacing: { before: 0, after: 80 },
    shading: { fill: AMBERBG, type: ShadingType.CLEAR },
    children: [
      new TextRun({ text: "  ▶  AMBER BLOCKS  ", size: 28, color: AMBER, bold: true, font: "Arial" }),
      new TextRun({ text: "  =  demo action (click, type, show screen)  ", size: 28, color: AMBER, font: "Arial" })
    ]
  }),
  new Paragraph({
    spacing: { before: 80, after: 80 },
    children: [new TextRun({ text: " " })]
  })
);

// ══════════════════════════════════════════════════════════════════════════
// SLIDE 1 — TITLE
// ══════════════════════════════════════════════════════════════════════════
slides.push(...slideHeader(1, "Title", "~30 seconds"));

slides.push(
  say("Good [morning / afternoon / evening], everyone."),
  gap(),
  say("I want to start with a simple question."),
  gap(),
  say("How many of you have a parent who lives in a different city?"),
  gap(),
  pause("[ PAUSE — let hands go up, acknowledge ]"),
  gap(),
  say("That's a lot of us. And every single day, those of us with hands up are doing the same thing."),
  gap(),
  say("We're calling to check if medications were taken. We're forwarding prescription photos on WhatsApp. We're asking the caregiver what the doctor said."),
  gap(),
  say("CareCircle is built for exactly that."),
  gap(),
  say("It's an AI-powered care coordination platform. For working professionals managing an aging parent's health... from 500 kilometers away."),
  gap(),
  say("Let me show you what that actually looks like.")
);

// ══════════════════════════════════════════════════════════════════════════
// SLIDE 2 — THE PROBLEM
// ══════════════════════════════════════════════════════════════════════════
slides.push(...slideHeader(2, "The Problem", "~90 seconds"));

slides.push(
  say("Let me paint the picture most of us are living."),
  gap(),
  say("Your parent is 65. Type 2 Diabetes. High blood pressure. Five different medications. Three different doctors who prescribed them."),
  gap(),
  say("You're in Bangalore. Or Hyderabad. Or Dubai."),
  gap(),
  say("Every morning you wonder — did they take their medicines? Was the blood sugar okay? What did the new test say?"),
  gap(),
  say("You get the prescription photo on WhatsApp. You screenshot the lab report. The home caregiver sends a voice note in Telugu."),
  gap(),
  say("None of it adds up to a picture. None of it tells you — is my parent okay today?"),
  gap(),
  pause("[ PAUSE ]"),
  gap(),
  say("And here's the dangerous part — when five medications come from three doctors, nobody checks if those drugs interact with each other."),
  gap(),
  say("That's not a hypothetical edge case. That's the standard of care for 140 million Indians over 60."),
  gap(),
  say("The healthcare system was built for patients who walk in. It was never designed for families who call in.")
);

// ══════════════════════════════════════════════════════════════════════════
// SLIDE 3 — THE SOLUTION
// ══════════════════════════════════════════════════════════════════════════
slides.push(...slideHeader(3, "The Solution", "~60 seconds"));

slides.push(
  say("CareCircle solves this in three layers. And the layers matter — so let me be specific."),
  gap(),
  say("Layer one is AI analysis. Powered by Claude and Gemini. It reads prescription photos, checks for drug interactions across all active medications, and generates a daily health briefing every morning."),
  gap(),
  say("Layer two is ABDM. Ayushman Bharat Digital Mission. India's national digital health infrastructure. We don't build a new data silo. We ride the existing rails. I'll spend the next two slides on this — because it's the most important differentiator."),
  gap(),
  say("Layer three is Telegram. Zero app install. Any phone. The same platform your parents already use to send you good morning messages at 6 AM."),
  gap(),
  say("Let's go deep on layer two.")
);

// ══════════════════════════════════════════════════════════════════════════
// SLIDE 4 — ABDM
// ══════════════════════════════════════════════════════════════════════════
slides.push(...slideHeader(4, "ABDM — India's Digital Health Stack", "~2 minutes"));

slides.push(
  say("Most health apps in India today are islands. Each one stores data in its own silo. If you switch hospitals, your records don't follow you. If you go to a specialist, they start from scratch."),
  gap(),
  say("ABDM changes that. Completely."),
  gap(),
  say("Think about what GSTN did for taxation. Or what ONDC is doing for e-commerce. It created a shared infrastructure that any business can plug into. The government built the highway. Anyone can drive on it."),
  gap(),
  say("That's what ABDM is for healthcare."),
  gap(),
  say("At the center is ABHA. Ayushman Bharat Health Account. Your 14-digit health ID. Think of it like Aadhaar — but specifically for health records. Every Indian gets one. It's permanent. It follows you for life."),
  gap(),
  say("On top of ABHA, there's the Personal Health Record — PHR. This is not a scanned PDF. This is FHIR R4 — a structured, machine-readable, international standard. That means any app, anywhere, can read it."),
  gap(),
  say("Then there's the HIU-HIP framework. Health Information User and Health Information Provider. HIU is what CareCircle is — an app that requests records. HIP is what hospitals and labs are — entities that provide them."),
  gap(),
  say("And critically — there's the Health Locker. Patient records are not stored in a central government database. They're stored in a locker the patient controls. You consent to share. You can revoke any time."),
  gap(),
  pause("[ PAUSE — this is a key point to let sink in ]"),
  gap(),
  say("Over 30 crore ABHA IDs have already been issued. Over 2,000 hospitals are live on the network. This infrastructure exists right now. We just need to connect to it.")
);

// ══════════════════════════════════════════════════════════════════════════
// SLIDE 5 — UHI DEEP DIVE
// ══════════════════════════════════════════════════════════════════════════
slides.push(...slideHeader(5, "UHI — The UPI of Healthcare", "~2 minutes"));

slides.push(
  say("Within ABDM, there is a specific protocol I want you to really understand. Because this is what makes CareCircle's roadmap genuinely exciting."),
  gap(),
  say("It's called UHI. Unified Health Interface."),
  gap(),
  say("Think about what UPI did."),
  gap(),
  say("UPI didn't create a new bank. It created an open protocol. Any app — Paytm, PhonePe, GPay — could use the same protocol to move money between any two accounts in India. The infrastructure was shared. The competition happened at the application layer."),
  gap(),
  say("UHI does the exact same thing for healthcare services."),
  gap(),
  say("It's built on BECKN protocol — the same open, decentralized protocol that powers ONDC. And it has three actors."),
  gap(),
  say("First — the EUA. End User Application. That's CareCircle. We're the caregiver-facing app. We send health service requests on behalf of the user."),
  gap(),
  say("Second — the UHI Gateway. Run by NHA — the National Health Authority. This routes requests between EUAs and healthcare providers. The patient never sees it. It just works in the background."),
  gap(),
  say("Third — the HSP. Health Service Provider. Any doctor, hospital, lab, or pharmacy that registers on UHI becomes discoverable and bookable by any EUA on the network. Apollo. AIIMS. A local clinic in Nellore. Same API. Same protocol."),
  gap(),
  pause("[ PAUSE ]"),
  gap(),
  say("What flows over this network? Doctor discovery. Appointment booking. Teleconsultation. Pulling health records with patient consent. Prescription digitization direct to the patient's ABHA locker. Lab report delivery."),
  gap(),
  say("This is the network. CareCircle connects to all of it.")
);

// ══════════════════════════════════════════════════════════════════════════
// SLIDE 6 — CARECIRCLE ON ABDM RAILS
// ══════════════════════════════════════════════════════════════════════════
slides.push(...slideHeader(6, "How CareCircle Uses ABDM", "~60 seconds"));

slides.push(
  say("Here's the analogy I use internally."),
  gap(),
  say("Paytm didn't build a payment network. They built an application on UPI rails. That's how they scaled so fast. The infrastructure was already there."),
  gap(),
  say("That is exactly what CareCircle is doing."),
  gap(),
  say("ABDM gives us — for free — patient identity through ABHA, record storage through the Health Locker, a provider directory of 2,000 plus hospitals and clinics through the UHI gateway, and a consent framework that is fully compliant with India's Digital Personal Data Protection Act."),
  gap(),
  say("We don't build any of that. That's not our job."),
  gap(),
  say("Our job is to build the AI layer on top. Claude's daily briefings. Gemini's OCR for prescriptions. Proactive drug interaction alerts. And a Telegram interface that any caregiver can use from day one, on day one, with zero training."),
  gap(),
  say("That's the platform. Let me show it to you live.")
);

// ══════════════════════════════════════════════════════════════════════════
// SLIDE 7 — PRODUCT DEMO: WEB DASHBOARD
// ══════════════════════════════════════════════════════════════════════════
slides.push(...slideHeader(7, "Product Demo — Web Dashboard", "~90 seconds"));

slides.push(
  demo("OPEN BROWSER → carecercle.vercel.app"),
  gap(),
  say("So I'm going to log in. Email — srikanthkarkampally01@gmail.com. Password — 123456."),
  gap(),
  demo("LOGIN — show dashboard loading"),
  gap(),
  say("This is the dashboard."),
  gap(),
  say("The patient here is Rajesh Sharma. 68 years old. Blood group B positive. Based in Nellore, Andhra Pradesh. He has Type 2 Diabetes and Hypertension."),
  gap(),
  say("Look at the top of the screen. Three abnormal lab values. Flagged in red."),
  gap(),
  say("BP Systolic at 150 — should be under 130. Diastolic at 95 — should be under 80. Fasting blood sugar at 180 — should be under 100."),
  gap(),
  say("These are not just numbers. These are flags. The system is telling you — something here needs attention."),
  gap(),
  pause("[ PAUSE — let them look at the screen ]"),
  gap(),
  say("On the medications tab — five active medications. Metformin, Glimepiride, Amlodipine, Aspirin, Atorvastatin. These were not manually typed. They were extracted from a prescription photo using Gemini's OCR."),
  gap(),
  demo("CLICK → Medications tab"),
  gap(),
  say("And this is the Claude AI daily briefing."),
  gap(),
  say("Every morning at 7 AM, Claude reads all this data — the labs, the medications, the appointments, the caregiver notes — and writes one paragraph. Not a data dump. A briefing. What's the most important thing to watch today."),
  gap(),
  say("That's what a son or daughter 500 km away needs at 7 in the morning.")
);

// ══════════════════════════════════════════════════════════════════════════
// SLIDE 8 — PRODUCT DEMO: TELEGRAM BOT
// ══════════════════════════════════════════════════════════════════════════
slides.push(...slideHeader(8, "Product Demo — Telegram Bot", "~2 minutes"));

slides.push(
  say("Now the Telegram bot. And this — this is where the product gets interesting."),
  gap(),
  demo("OPEN TELEGRAM → search @CarCercle_Bot"),
  gap(),
  say("Your parent doesn't need to learn a new app. Their home caregiver doesn't need to learn a new app. You don't need to install anything."),
  gap(),
  say("You just type a command."),
  gap(),
  demo("TYPE: /summary"),
  gap(),
  say("Watch."),
  gap(),
  pause("[ PAUSE — wait for bot response ]"),
  gap(),
  say("The bot went to the database. Pulled patient data. Ran it through Claude. And returned a health snapshot. In the chat. In under three seconds."),
  gap(),
  say("Rajesh Sharma. Five medications. Three abnormal lab values. Zero alerts. Zero events in the last 24 hours. Status: Warning."),
  gap(),
  say("BP elevated at 150 over 95."),
  gap(),
  say("That is a full clinical summary. In Telegram. In three seconds. On any phone."),
  gap(),
  pause("[ PAUSE ]"),
  gap(),
  say("Now let me show you /addappointment."),
  gap(),
  demo("TYPE: /addappointment"),
  gap(),
  say("The bot asks — 'What date is the appointment?'"),
  gap(),
  demo("TYPE: 20 May, Dr. Reddy, Cardiology"),
  gap(),
  say("Done. Stored. The appointment shows up on the web dashboard. The whole family can see it."),
  gap(),
  say("No form. No app. No phone call to a hospital reception. Just a conversation in Telegram."),
  gap(),
  say("This is how 1.4 billion Indians already communicate. We meet them there.")
);

// ══════════════════════════════════════════════════════════════════════════
// SLIDE 9 — ROADMAP
// ══════════════════════════════════════════════════════════════════════════
slides.push(...slideHeader(9, "Telegram + ABDM Integration Roadmap", "~90 seconds"));

slides.push(
  say("What you just saw is Phase 1. And it is live. You can try it right now."),
  gap(),
  say("Phase 2 — starting Q3 this year — is where we formally integrate with ABDM."),
  gap(),
  say("We register CareCircle as a Health Information User with NHA."),
  gap(),
  say("We add a /sync command to the Telegram bot. When your parent visits a hospital and gets a discharge summary — it goes to their ABHA locker. You type /sync in Telegram. The bot pulls it. Claude reads it. You get a briefing in the chat."),
  gap(),
  say("We also add /book. Appointment booking via the UHI gateway. You type the specialty you need. The bot discovers available doctors on the national network. You confirm. Booked. No phone calls."),
  gap(),
  pause("[ PAUSE ]"),
  gap(),
  say("Phase 3 — Q4 this year — is full UHI EUA registration."),
  gap(),
  say("Live discovery of every doctor, lab, and pharmacy on India's national health network. Prescriptions digitized to the ABHA locker automatically after every consult. Insurance claims initiated via Telegram through HCX."),
  gap(),
  say("And the end goal I want to leave you with —"),
  gap(),
  say("A caregiver in Bangalore. Books a specialist in Chennai. For a parent in Nellore."),
  gap(),
  say("From Telegram. Two messages. Via the national UHI network."),
  gap(),
  say("That's Phase 3.")
);

// ══════════════════════════════════════════════════════════════════════════
// SLIDE 10 — THE ASK
// ══════════════════════════════════════════════════════════════════════════
slides.push(...slideHeader(10, "The Opportunity — The Ask", "~45 seconds"));

slides.push(
  say("India has 140 million people over 60 today."),
  gap(),
  say("By 2050, that number hits 300 million. And their children — the caregivers — are scattered across cities. Across countries."),
  gap(),
  say("This is not a niche use case. This is the single largest unaddressed healthcare coordination problem in the world's most populous country."),
  gap(),
  pause("[ PAUSE ]"),
  gap(),
  say("ABDM gives us the rails. Claude gives us the intelligence. Telegram gives us the reach."),
  gap(),
  say("We are looking for three things."),
  gap(),
  say("Ten pilot families — free for six months. Help us tune the AI and the ABDM consent flows in a real-world setting."),
  gap(),
  say("Hospital and clinic partners — ABDM-registered providers willing to pilot UHI appointment booking and PHR sharing with us."),
  gap(),
  say("And investor conversations — pre-seed round opening Q3."),
  gap(),
  say("The demo is live. The bot is live. Come try it right now."),
  gap(),
  say("carecercle.vercel.app. Telegram: @CarCercle_Bot."),
  gap(),
  say("Thank you.")
);

// ─── Pack document ────────────────────────────────────────────────────────
const doc = new Document({
  sections: [{
    properties: {
      page: {
        size:   { width: 12240, height: 15840 },
        margin: { top: 1080, right: 1080, bottom: 1080, left: 1080 }
      }
    },
    children: slides
  }]
});

Packer.toBuffer(doc)
  .then(buf => {
    fs.writeFileSync(path.join(__dirname, "CareCircle_TeleprompterScript.docx"), buf);
    console.log("Done → CareCircle_TeleprompterScript.docx");
  })
  .catch(e => { console.error(e); process.exit(1); });
