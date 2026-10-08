/**
 * Gabriel Homes — Deployment Readiness Checklist (.docx)
 * Skill compliance: R1 cover recipe (report), MIN-1 palette, Profile A formal,
 * Horizontal-Only tables, calcTitleLayout + calcCoverSpacing, allNoBorders,
 * line 312 throughout, tableHeader/cantSplit/keepNext, no body page breaks.
 */
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, PageNumber, NumberFormat, AlignmentType, HeadingLevel,
  WidthType, BorderStyle, ShadingType, SectionType, TableLayoutType,
} = require("docx");
const fs = require("fs");

// ---------- Palette: MIN-1 Warm Gold (consulting/business, matches brand warmth) ----------
const P = {
  bg: "F3F1ED", accent: "D6C096",
  cover: { titleColor: "000000", subtitleColor: "606060", metaColor: "707070", footerColor: "A0A0A0" },
  table: { headerBg: "D6C096", headerText: "1A1A1A", accentLine: "000000", innerLine: "DDD8CC", surface: "F5F3ED" },
};
const BODY = "000000"; // Profile A: pure black body text
const GRAY = "808080";

const NB = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: NB, bottom: NB, left: NB, right: NB };
const allNoBorders = { top: NB, bottom: NB, left: NB, right: NB, insideHorizontal: NB, insideVertical: NB };

const EN = { ascii: "Times New Roman", eastAsia: "SimSun" };

// ---------- Cover helpers (design-system.md, verbatim logic) ----------
function splitTitleLines(title, charsPerLine) {
  if (title.length <= charsPerLine) return [title];
  const breakAfter = new Set([..."\uFF0C\u3002\u3001\uFF1B\uFF1A\uFF01\uFF1F", ..."-_/", ..." \t"]);
  const lines = [];
  let remaining = title;
  while (remaining.length > charsPerLine) {
    let breakAt = -1;
    for (let i = charsPerLine; i >= Math.floor(charsPerLine * 0.6); i--) {
      if (i < remaining.length && breakAfter.has(remaining[i - 1])) { breakAt = i; break; }
    }
    if (breakAt === -1) {
      const limit = Math.min(remaining.length, Math.ceil(charsPerLine * 1.3));
      for (let i = charsPerLine + 1; i < limit; i++) {
        if (breakAfter.has(remaining[i - 1])) { breakAt = i; break; }
      }
    }
    if (breakAt === -1) breakAt = charsPerLine;
    lines.push(remaining.slice(0, breakAt).trim());
    remaining = remaining.slice(breakAt).trim();
  }
  if (remaining) lines.push(remaining);
  if (lines.length > 1 && lines[lines.length - 1].length <= 2) {
    const last = lines.pop();
    lines[lines.length - 1] += last;
  }
  return lines;
}

function calcTitleLayout(title, maxWidthTwips, preferredPt = 40, minPt = 24) {
  const charsPerLine = (pt) => Math.floor(maxWidthTwips / (pt * 20));
  let titlePt = preferredPt, lines;
  while (titlePt >= minPt) {
    const cpl = charsPerLine(titlePt);
    if (cpl < 2) { titlePt -= 2; continue; }
    lines = splitTitleLines(title, cpl);
    if (lines.length <= 3) break;
    titlePt -= 2;
  }
  if (!lines || lines.length > 3) {
    lines = splitTitleLines(title, charsPerLine(minPt));
    titlePt = minPt;
  }
  return { titlePt, titleLines: lines };
}

function calcCoverSpacing(params) {
  const { titleLineCount = 1, titlePt = 36, hasSubtitle = false, hasEnglishLabel = false,
    metaLineCount = 0, fixedHeight = 800, pageHeight = 16838, marginTop = 0, marginBottom = 0 } = params;
  const SAFETY = 1200;
  const usableHeight = pageHeight - marginTop - marginBottom - SAFETY;
  const titleHeight = titleLineCount * (titlePt * 23 + 200);
  const subtitleHeight = hasSubtitle ? (12 * 23 + 600) : 0;
  const englishLabelHeight = hasEnglishLabel ? (9 * 23 + 600) : 0;
  const metaHeight = metaLineCount * (10 * 23 + 100);
  const implicitParaHeight = 3 * 300;
  const contentHeight = titleHeight + subtitleHeight + englishLabelHeight + metaHeight + fixedHeight + implicitParaHeight;
  const safeRemaining = Math.max(usableHeight - contentHeight, 400);
  const FOOTER_MIN = 800;
  const rawTop = Math.floor(safeRemaining * 0.45);
  const rawBottom = Math.floor(safeRemaining * 0.45);
  const bottomSpacing = Math.max(rawBottom, FOOTER_MIN);
  const topSpacing = Math.max(rawTop - Math.max(0, FOOTER_MIN - rawBottom), 400);
  const midSpacing = Math.max(safeRemaining - topSpacing - bottomSpacing, 0);
  return { topSpacing, midSpacing, bottomSpacing };
}

// ---------- Recipe R1: Pure Paragraph Cover (left-aligned) ----------
function buildCoverR1(config) {
  const C = config.palette;
  const padL = 1200, padR = 800;
  const availableWidth = 11906 - padL - padR - 300;
  const { titlePt, titleLines } = calcTitleLayout(config.title, availableWidth, 40, 24);
  const titleSize = titlePt * 2;
  const spacing = calcCoverSpacing({
    titleLineCount: titleLines.length, titlePt,
    hasSubtitle: !!config.subtitle, hasEnglishLabel: !!config.englishLabel,
    metaLineCount: (config.metaLines || []).length, fixedHeight: 400,
  });
  const accentLeft = { style: BorderStyle.SINGLE, size: 8, color: C.accent, space: 12 };
  const children = [];

  children.push(new Paragraph({ spacing: { before: spacing.topSpacing } }));

  if (config.englishLabel) {
    children.push(new Paragraph({
      indent: { left: padL, right: padR }, spacing: { after: 500 },
      border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: C.accent, space: 8 } },
      children: [new TextRun({ text: config.englishLabel.split("").join("  "),
        size: 18, color: C.accent, font: { ascii: "Calibri", eastAsia: "SimHei" }, characterSpacing: 40 })],
    }));
  }

  for (let i = 0; i < titleLines.length; i++) {
    children.push(new Paragraph({
      indent: { left: padL },
      spacing: { after: i < titleLines.length - 1 ? 100 : 300, line: Math.ceil(titlePt * 23), lineRule: "atLeast" },
      children: [new TextRun({ text: titleLines[i], size: titleSize, bold: true,
        color: C.cover.titleColor, font: EN })],
    }));
  }

  if (config.subtitle) {
    children.push(new Paragraph({
      indent: { left: padL }, spacing: { after: 800 },
      children: [new TextRun({ text: config.subtitle, size: 24, color: C.cover.subtitleColor, font: EN })],
    }));
  }

  for (const line of (config.metaLines || [])) {
    children.push(new Paragraph({
      indent: { left: padL + 200 }, spacing: { after: 80 },
      border: { left: accentLeft },
      children: [new TextRun({ text: line, size: 24, color: C.cover.metaColor, font: EN })],
    }));
  }

  children.push(new Paragraph({ spacing: { before: spacing.bottomSpacing } }));

  children.push(new Paragraph({
    indent: { left: padL, right: padR },
    border: { top: { style: BorderStyle.SINGLE, size: 2, color: C.accent, space: 8 } },
    spacing: { before: 200 },
    children: [
      new TextRun({ text: config.footerLeft || "", size: 16, color: C.cover.footerColor, font: { ascii: "Calibri" } }),
      new TextRun({ text: "                                        " }),
      new TextRun({ text: config.footerRight || "", size: 16, color: C.cover.footerColor, font: { ascii: "Calibri" } }),
    ],
  }));

  return [new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    layout: TableLayoutType.FIXED,
    borders: allNoBorders,
    rows: [new TableRow({
      height: { value: 16838, rule: "exact" },
      children: [new TableCell({
        shading: { type: ShadingType.CLEAR, fill: C.bg }, borders: noBorders,
        verticalAlign: "top",
        children,
      })],
    })],
  })];
}

// ---------- Body helpers ----------
function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 160, line: 312 },
    children: [new TextRun({ text, bold: true, size: 32, color: BODY, font: EN })],
  });
}
function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 260, after: 120, line: 312 },
    children: [new TextRun({ text, bold: true, size: 28, color: BODY, font: EN })],
  });
}
function p(text, opts = {}) {
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    spacing: { line: 312, after: opts.after !== undefined ? opts.after : 120 },
    keepNext: !!opts.keepNext,
    children: [new TextRun({ text, size: 24, color: BODY, font: EN })],
  });
}
function caption(text) {
  return new Paragraph({
    keepNext: true,
    spacing: { line: 312, before: 60, after: 80 },
    children: [new TextRun({ text, bold: true, size: 21, color: BODY, font: EN })],
  });
}
function cell(text, opts = {}) {
  return new TableCell({
    width: { size: opts.w, type: WidthType.PERCENTAGE },
    shading: opts.fill ? { type: ShadingType.CLEAR, fill: opts.fill } : undefined,
    margins: { top: 60, bottom: 60, left: 120, right: 120 },
    children: [new Paragraph({
      spacing: { line: 312 },
      children: [new TextRun({
        text, size: 21, bold: !!opts.bold,
        color: opts.color || BODY, font: EN,
      })],
    })],
  });
}
function mkTable(widths, headerCells, rows) {
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: {
      top: { style: BorderStyle.SINGLE, size: 2, color: P.table.accentLine },
      bottom: { style: BorderStyle.SINGLE, size: 2, color: P.table.accentLine },
      left: NB, right: NB,
      insideHorizontal: { style: BorderStyle.SINGLE, size: 1, color: P.table.innerLine },
      insideVertical: NB,
    },
    rows: [
      new TableRow({
        tableHeader: true, cantSplit: true,
        children: headerCells.map((t, i) => cell(t, { w: widths[i], bold: true, fill: P.table.headerBg, color: P.table.headerText })),
      }),
      ...rows.map(r => new TableRow({
        cantSplit: true,
        children: r.map((t, i) => cell(t, { w: widths[i], bold: i === 0 && r.length > 2 ? false : false })),
      })),
    ],
  });
}

// ---------- Content data ----------
const W5 = [7, 32, 10, 9, 42];
const H5 = ["ID", "Task", "Owner", "Time", "Why it matters"];
const blockA = [
  ["A1", "Restore runtime environment: virtualenv, database migration, demo seed, accounts", "Dev", "0.75 h", "The workspace database and dependencies were reset between sessions; every later step depends on a green baseline of 232/232 tests."],
  ["A2", "Normalise media storage: move 287 images into the served media directory", "Dev", "0.5 h", "Images outside the media root render as broken images in production; a five-minute fix now, an incident after launch."],
  ["A3", "Health-check the development and preview servers", "Dev", "0.25 h", "Confirms the verified baseline renders correctly before any change begins."],
];
const blockB = [
  ["B1", "Brand the login, signup and password-reset pages", "Dev", "2.0 h", "These are the only off-brand pages on the site, and the client will log in on day one; first impressions are made here."],
  ["B2", "Add a working inquiry form to the contact page", "Dev", "1.5 h", "The contact page is currently information-only; the form completes the conversion path using the existing spam-protected pipeline."],
  ["B3", "Typography sweep on inner pages", "Dev", "1.0 h", "Extends the corrected minimum font sizes from the home page to every other page, so no text renders below 13 pixels."],
  ["B4", "SEO verification pass", "Dev", "1.0 h", "Confirms share cards, structured data and the sitemap behave correctly before search engines index the production domain."],
  ["B5", "Wire WhatsApp buttons to the real business number", "Dev", "0.5 h", "The customer-facing contact buttons currently point to a placeholder; the real number is a client input (Section 4)."],
];
const blockC = [
  ["C1", "Load real listings, or approve the curated demo pack", "You + Dev", "2.5 h", "A client demo is only convincing with real inventory; the demo pack is a designed fallback, swappable later through the admin."],
  ["C2", "Publish real agency profiles", "You + Dev", "1.0 h", "Names, portraits, phone and WhatsApp numbers and biographies must match the client's actual team."],
  ["C3", "Finalise the about and founder copy", "You + Dev", "0.75 h", "The story section carries the brand voice; it should read as the client, not as a template."],
  ["C4", "Image quality pass", "Dev", "0.75 h", "Verifies every cover and interior image is curated and captioned, with no placeholder art remaining."],
];
const blockD = [
  ["D1", "Provision the VPS: Ubuntu, PostgreSQL, gunicorn, nginx", "Dev", "2.5 h", "Creates the production server, following the deployment runbook already in the repository. Blocked by the hosting account."],
  ["D2", "Domain, DNS and SSL certificate", "Dev", "1.0 h", "HTTPS with a valid certificate is mandatory for a trusted business site. Blocked by the domain name."],
  ["D3", "Transactional email with SPF and DKIM", "Dev", "1.0 h", "Inquiry notifications must reach the client's inbox rather than the spam folder. Blocked by the email sending account."],
  ["D4", "Production hardening", "Dev", "1.0 h", "Real secret key, debugging off, allowed hosts set, and Django's deployment security check passing clean."],
  ["D5", "Automated nightly backups", "Dev", "0.75 h", "Database and media snapshots with a rehearsed restore; a business website without backups is an unacceptable liability."],
  ["D6", "Content entry on the live site and smoke test", "Dev", "0.75 h", "Loads the production content and verifies the public URL end-to-end."],
];
const blockE = [
  ["E1", "Full test suites against production", "Dev", "1.0 h", "All 232 automated tests and 104 scripted URL and flow checks pass on the live HTTPS address."],
  ["E2", "Performance and accessibility audit", "Dev", "1.0 h", "Lighthouse scores of 90 or above on five key pages; slow or inaccessible pages lose visitors and rankings."],
  ["E3", "Device sweep: desktop, tablet and phone", "Dev", "1.0 h", "Most property browsing in Kenya is mobile; layout, menus and forms must be verified at every breakpoint."],
  ["E4", "Client handoff pack", "Dev", "1.5 h", "Credentials sheet, a one-page admin guide and a ten-minute demo script, so the team can operate the site without a developer."],
  ["E5", "Demo rehearsal", "Dev", "0.5 h", "A full run-through the day before the demo, leaving time to resolve anything the rehearsal surfaces."],
];
const statusRows = [
  ["Public pages (home, search, detail, agents, about, contact, legal)", "Complete. All routes live and covered by automated tests."],
  ["Search and filtering", "Complete. Price, bedrooms, type, location, amenities and sort, all URL-driven."],
  ["Listing detail and inquiry pipeline", "Complete. Gallery, agent card, HTMX form, honeypot, rate limiting, agent email."],
  ["Agent dashboard and admin", "Complete. Listing creation, image manager, inquiry inbox, tuned admin."],
  ["Accounts and saved properties", "Complete. Email login via allauth; pages unthemed (polish item B1)."],
  ["SEO surface", "Complete. Sitemap, robots, Open Graph tags, structured data on detail pages."],
  ["Deployment artifacts", "Documented, not yet executed. Split settings, runbook, WhiteNoise and gunicorn pinned."],
  ["Content", "Demo data only. 80 seeded listings with real photography; client inventory pending."],
];
const needsRows = [
  ["Domain name (gabrielhomes.co.ke recommended)", "The site's permanent address; the SSL certificate in task D2 is issued against it.", "approx. USD 10 / year", "D2"],
  ["Hosting account (small VPS: Hetzner, DigitalOcean or similar)", "The production server for task D1; sized for a launch-stage property portal.", "USD 6-12 / month", "D1"],
  ["Email sending account (for example Brevo free tier)", "Sends inquiry notifications from the site's own address.", "Free tier is sufficient", "D3"],
  ["WhatsApp business number", "The customer-facing contact buttons (task B5) and agent profiles.", "None", "B5"],
  ["Real listing content, or approval of the demo pack", "Determines whether task C1 loads client inventory or launch content.", "None", "C1"],
  ["Demo date and time", "Anchors day four and the rehearsal the day before.", "None", "Schedule"],
];
const gateRows = [
  ["Live at https with a valid certificate and www redirects", "Certificate and redirect check on the domain"],
  ["Django deployment security check passes with no issues", "manage.py check --deploy output"],
  ["All automated tests pass on production", "232/232 tests plus 104 scripted checks"],
  ["Performance and accessibility at or above 90", "Lighthouse runs on five key pages"],
  ["Nightly backups running and a restore rehearsed once", "Backup logs and a documented test restore"],
  ["A non-technical agent can add a listing unaided", "Handoff session using the admin guide"],
];
const timelineRows = [
  ["Day 0 (today)", "Block A pre-flight; client procures domain, hosting and email accounts.", "Verified baseline; accounts in hand."],
  ["Day 1", "Block B polish: branded auth pages, contact form, typography, SEO.", "Every page client-ready."],
  ["Day 2", "Block C content build-out with the client's input.", "Real or approved content loaded."],
  ["Day 3", "Block D deployment: server, domain, SSL, email, backups, hardening.", "Site live at https."],
  ["Day 4", "Block E QA and handoff, rehearsal, then the client demo.", "Deployment-ready declared; demo delivered."],
];

// ---------- Assemble body ----------
const body = [];
body.push(h1("1  Executive Summary"));
body.push(p("The Gabriel Homes website is functionally complete. Every public page, including home, search with filters, listing detail, agent directory, about and contact, is built and covered by 232 passing automated tests, together with a role-gated agent dashboard, a spam-protected inquiry pipeline and a fully configured admin. The remaining distance to a live, client-ready deployment is therefore operational rather than constructive: a small set of environment fixes, four brand-critical polish items, real content, and the production stack itself, namely hosting, domain, SSL certificate and transactional email."));
body.push(p("This document lists every outstanding item in a single checklist, states the owner, the estimated effort and the reason each item matters, defines the objective quality gate that declares the site deployment-ready, and maps the work onto a four-day schedule totalling approximately 28 hours including buffer. Three items, specifically the domain name, a hosting account and an email sending account, can only be procured by the client side; purchasing them on day one protects the launch date. Everything else requires no further input and can begin immediately."));

body.push(h1("2  Where the Project Stands"));
body.push(p("A full audit of the codebase on 7 October 2026 inventoried every route, model, template, test and configuration file. The finding is that the application layer is finished and regression-gated, not partially built: nothing in the checklist below involves designing or coding new product features. Table 1 summarises the verified state of each major component as recorded by the automated test suite (232/232 passing), the scripted smoke suite (58/58) and the functional suite (46/46)."));
body.push(caption("Table 1: Verified state of major components (audit of 7 October 2026)"));
body.push(mkTable([32, 68], ["Component", "State at audit"], statusRows));
body.push(p("Two workspace-level defects were also recorded by the audit and are addressed in Block A: the working database and uploaded media were reset between sessions, and 287 property images sit at the project root instead of the media directory that Django serves from. Neither defect affects the codebase itself. Both, however, would break a naive deployment attempt, which is why the pre-flight block exists.", { after: 160 }));

body.push(h1("3  What Is Left: The Complete Checklist"));
body.push(p("The checklist below is the complete set of outstanding work. Items are grouped into five blocks in execution order, and each item carries an owner, an effort estimate and a plain-language reason it matters. Estimates assume focused execution; the schedule in Section 6 adds a 15 percent buffer."));

body.push(h2("3.1  Block A: Pre-Flight Environment Fixes (1.5 hours)"));
body.push(p("Block A restores a clean, verified baseline before anything is deployed. It is deliberately small, because skipping it risks rehearsing the launch against a broken workspace rather than the verified application."));
body.push(caption("Table 2: Block A tasks"));
body.push(mkTable(W5, H5, blockA));

body.push(h2("3.2  Block B: Final Client-Facing Polish (6 hours)"));
body.push(p("Block B closes the four gaps a client would notice within the first five minutes, plus one wiring task. These are the last items that are cheaper to fix before the site is public than after."));
body.push(caption("Table 3: Block B tasks"));
body.push(mkTable(W5, H5, blockB));

body.push(h2("3.3  Block C: Content (5 hours)"));
body.push(p("Block C replaces demo data with the client's real content, or finalises the curated demonstration pack as launch content if the real inventory is not yet available. Either path operates through the admin interface only; no code changes are involved, and the two paths can be swapped at any time."));
body.push(caption("Table 4: Block C tasks"));
body.push(mkTable(W5, H5, blockC));

body.push(h2("3.4  Block D: Deployment (7 hours)"));
body.push(p("Block D is the deployment itself, executed against the written runbook already in the repository. Three of its inputs are client purchases listed in Section 4; the block is scheduled on day three precisely so that purchases made on day zero do not delay it."));
body.push(caption("Table 5: Block D tasks"));
body.push(mkTable(W5, H5, blockD));

body.push(h2("3.5  Block E: QA and Handoff (5 hours)"));
body.push(p("Block E is the quality gate and the handoff. It runs against the production URL rather than the development machine, so that what is verified is exactly what the client will see during the demonstration."));
body.push(caption("Table 6: Block E tasks"));
body.push(mkTable(W5, H5, blockE));
body.push(p("The checklist totals 24.5 hours of focused work across 21 tasks, approximately 28 hours including buffer. Nineteen of the 21 tasks are executable by the development side starting immediately; the two content tasks depend on the client inputs in Section 4.", { after: 160 }));

body.push(h1("4  Client Inputs Required for Launch"));
body.push(p("Six inputs are needed from the client side, and only the first three are schedule-critical. Each is a purchase or a decision measured in minutes rather than a work item. Acquiring the first three on day zero is the single action that protects the four-day launch date; every one of them can be completed online in under half an hour."));
body.push(caption("Table 7: Client inputs, costs and what each blocks"));
body.push(mkTable([30, 38, 16, 16], ["Item", "Why it is needed", "Indicative cost", "Blocks"], needsRows));

body.push(h1("5  The Go-Live Quality Gate"));
body.push(p("Deployment-ready is declared against objective criteria rather than judgement. Every gate below is verified on the production URL during Block E, and the site goes in front of the client only when all six pass. If any gate fails, the demo proceeds on the staged environment while the failure is resolved, never on an unverified site."));
body.push(caption("Table 8: Go-live gates and how each is verified"));
body.push(mkTable([52, 48], ["Criterion", "Verified by"], gateRows));

body.push(h1("6  Timeline to Launch"));
body.push(p("The schedule assumes focused days of seven to eight hours including buffer. Block A runs today, the client purchases in Section 4 are made today, and each following block occupies one day. DNS waiting time on day three is absorbed by any content work carried over from day two, so propagation delay does not move the launch date."));
body.push(caption("Table 9: Four-day schedule to client demo"));
body.push(mkTable([16, 52, 32], ["Day", "Focus", "Output"], timelineRows));
body.push(p("The immediate next action is Block A, which requires no input and starts on confirmation. While it runs, the only parallel action that matters is the purchase of the domain, hosting and email accounts in Section 4. Those three purchases are the difference between launching on day four and slipping; everything else in this document is already within the development side's control."));

// ---------- Document ----------
const doc = new Document({
  styles: {
    default: {
      document: {
        run: { font: EN, size: 24, color: BODY },
        paragraph: { spacing: { line: 312 } },
      },
      heading1: {
        run: { font: EN, size: 32, bold: true, color: BODY },
        paragraph: { spacing: { before: 360, after: 160, line: 312 } },
      },
      heading2: {
        run: { font: EN, size: 28, bold: true, color: BODY },
        paragraph: { spacing: { before: 260, after: 120, line: 312 } },
      },
    },
  },
  sections: [
    {
      properties: {
        page: { size: { width: 11906, height: 16838 }, margin: { top: 0, bottom: 0, left: 0, right: 0 } },
      },
      children: buildCoverR1({
        title: "Deployment Readiness Checklist",
        subtitle: "Gabriel Homes, Coastal Kenya Real Estate: what remains to go live",
        englishLabel: "GABRIEL HOMES",
        metaLines: [
          "Status: Feature-complete v1, 232/232 automated tests passing",
          "Purpose: Client demo and production launch",
          "Date: 7 October 2026",
        ],
        footerLeft: "Gabriel Homes",
        footerRight: "Internal working document, v1.0",
        palette: P,
      }),
    },
    {
      properties: {
        type: SectionType.NEXT_PAGE,
        page: {
          size: { width: 11906, height: 16838 },
          margin: { top: 1440, bottom: 1440, left: 1701, right: 1417 },
          pageNumbers: { start: 1, formatType: NumberFormat.DECIMAL },
        },
      },
      headers: {
        default: new Header({
          children: [new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [new TextRun({ text: "Gabriel Homes: Deployment Readiness Checklist", size: 18, color: GRAY, font: EN })],
          })],
        }),
      },
      footers: {
        default: new Footer({
          children: [new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [new TextRun({ children: [PageNumber.CURRENT], size: 18, color: GRAY, font: EN })],
          })],
        }),
      },
      children: body,
    },
  ],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync("/home/z/my-project/download/Gabriel-Homes-Deployment-Readiness-Checklist.docx", buf);
  console.log("OK — docx written:", buf.length, "bytes");
});
