// Gabriel Homes — Launch Checklist: document assembly
const {
  Document, Packer, Paragraph, TextRun, Header, Footer, PageNumber, NumberFormat,
  AlignmentType, buildCoverR1, h1, h2, body, taskPara, makeTable, tableTitle, PAL, INK, FONT, fs,
} = require("/home/z/my-project/scripts/gen_launch_checklist_lib.js");

// ---------------- cover ----------------
const cover = buildCoverR1({
  title: "Gabriel Homes Launch Checklist",
  subtitle: "Deployment-readiness gap list: what is already closed, what remains on my side, and the seven inputs only you can provide.",
  englishLabel: "DEPLOYMENT READINESS",
  metaLines: [
    "Project: gabriel_homes \u00B7 Django property portal",
    "Date: 8 October 2026",
    "Live status: 258/258 tests green \u00B7 6 security blockers closed today",
    "Source plan: docs/PLAN.md (Production Plan v1.0)",
  ],
  footerLeft: "Gabriel Homes \u00B7 internal working document",
  footerRight: "gabrielhomes.co.ke",
  palette: PAL,
});

// ---------------- body content ----------------
const children = [];

// 1 ---- Executive summary ----
children.push(h1("1. Where We Stand"));
children.push(body(
  "The site itself is feature-complete: search and filters, listing pages with maps and JSON-LD, the enquiry pipeline with rate limiting and honeypot, agent dashboards, saved listings, admin, sitemap and social cards all work and are covered by tests. What stood between it and a real launch was a list of production-grade gaps \u2014 security hardening, deploy plumbing, content provenance and operations. That list is now tracked as a written plan (docs/PLAN.md) with an automated quality gate, and work started immediately."
));
children.push(body(
  "Today's run closed the foundation and the first six security blockers: the repository is under git with a green quality gate; a listing-title XSS hole is closed; rate limiting no longer trusts forged IP headers and is shared across workers; demo passwords can never reach production; production now refuses to start without a real secret key, a domain allowlist and a PostgreSQL URL; and hashed static filenames are finally active. The suite grew from 232 to 258 tests, all passing. Everything left is listed in the next two sections \u2014 roughly 24 hours of my engineering work, plus seven inputs that only you can provide."
));

// 2 ---- remaining engineering ----
children.push(h1("2. What Remains on My Side (Engineering)"));

children.push(h2("2.1 Finish security hardening (P1)"));
children.push(taskPara("S7", "Upgrade to Django 5.2 LTS", "~2 h",
  ". Django 5.1 is past its security-support window, and the launch should run on the current long-term-support release. I bump the pinned version, run the full gate and fix anything the upgrade shakes loose."));
children.push(taskPara("S8", "Dependency vulnerability audit", "~0.5 h",
  ". A pip-audit scan over the pinned requirements catches any package with a known CVE. Anything vulnerable gets upgraded to its fixed version before launch."));
children.push(taskPara("S9", "Never lose an enquiry silently", "~2 h",
  ". Today a failed enquiry email leaves no trace except the saved row. I add sent-at and error fields plus a visible \u201Cemail not delivered\u201D badge in the agent dashboard, so missed leads are impossible to miss. Includes one database migration."));
children.push(taskPara("S10", "Security headers and self-hosted map", "~2.5 h",
  ". Leaflet currently loads from unpkg.com, a third-party host. I download it into the repo, add a strict Content-Security-Policy header, and move inline scripts into static files \u2014 so no outside host can inject or serve scripts."));
children.push(taskPara("S11", "Template and XSS audit", "~1 h",
  ". A sweep of every |safe, mark_safe and innerHTML usage with a written verdict for each. Anything that can carry user text gets fixed."));
children.push(taskPara("S12", "Input length caps", "~1 h",
  ". Confirm and test size limits on enquiry and listing fields so absurd or oversized submissions are rejected at the form, not in production."));

children.push(h2("2.2 Platform, deploy and data (P2\u2013P3)"));
children.push(taskPara("D2", "Full test run on PostgreSQL", "~1.5 h",
  ". All 258 tests currently run on SQLite. I run the suite against a real PostgreSQL and fix any dialect quirks, so the production database is not the first time the code meets Postgres."));
children.push(taskPara("D3", "Health endpoint and logging", "~1 h",
  ". A /healthz/ endpoint that reports 200 when the database is reachable and 503 when it is not \u2014 the hook your uptime monitor needs \u2014 plus logs sent to stdout with sensible levels."));
children.push(taskPara("D4", "Correct the deploy runbook", "~2 h",
  ". DEPLOY.md gets every fix from the review: no demo seeding in production, createcachetable, nginx real-IP header, gunicorn timeout, and every .env key documented. The goal: follow the document on a fresh server and nothing is left to memory."));
children.push(taskPara("D5", "Backups with a real restore drill", "~2 h",
  ". A nightly pg_dump script with 30-day retention, plus a drill script that proves a backup actually restores onto a scratch database. A backup that has never been restored is a hope, not a backup."));
children.push(taskPara("D6", "make gate", "~0.25 h",
  ". One command that runs every quality check, so pre-deploy verification is a habit rather than a checklist."));
children.push(taskPara("C1", "Media cleanup", "~1 h",
  ". List every unused or junk image, and \u2014 after your OK \u2014 move them out of the repo. A test then guarantees every listing photo on disk is referenced."));
children.push(taskPara("C2", "Production starts empty", "~0.5 h",
  ". A guard so the demo-seeding command refuses to run on the live server. Fictional listings must never appear on a real site."));
children.push(taskPara("C3", "Enquiry data retention", "~1 h",
  ". A purge command that deletes enquiries older than the retention period you choose (365 days suggested), with a cron line in the runbook \u2014 part of being able to honour deletion requests."));

children.push(h2("2.3 Verification and launch rehearsal (P5\u2013P6)"));
children.push(taskPara("V1", "Test coverage \u2265 80%", "~1.5 h",
  ". On the three core apps (listings, agents, inquiries), wired into the gate so coverage cannot silently rot."));
children.push(taskPara("V2", "Browser QA at three widths", "~1 h",
  ". Headless-browser screenshots of home, search, detail, enquiry and dashboard at 360, 810 and 1280 px, checked against the owner QA list."));
children.push(taskPara("V3", "Load smoke test", "~0.5 h",
  ". 20 concurrent users for 60 seconds against the staging server; target is zero errors and sub-500 ms p95 on the 2 GB VPS."));
children.push(taskPara("R1\u2013R2", "Fresh-server rehearsal and smoke script", "~3 h",
  ". Follow DEPLOY.md word-for-word on a clean VM, log every deviation, fix the document, and confirm the site answers over HTTPS with /healthz/ green. Launch then becomes a replay, not an experiment."));

// 3 ---- owner inputs ----
children.push(h1("3. What Only You Can Provide (Owner Inputs)"));
children.push(body(
  "These are decisions and credentials no code can conjure. None of them require you to be technical \u2014 each row says exactly what to hand over and what it unblocks. The earlier they arrive, the more runs in parallel; items O6 and O7 gate the launch rehearsal itself."
));
children.push(tableTitle("Table 1 \u00B7 Owner decisions and inputs (from PLAN \u00A76)"));
children.push(makeTable(
  [26, 48, 26],
  ["What I need from you", "Why it matters", "Unblocks"],
  [
    ["O6 \u00B7 Email: Brevo (or similar) credentials for hello@gabrielhomes.co.ke, SPF/DKIM set on the domain",
     "Enquiries, signups and password resets all send from this address; without authenticated mail it lands in spam or nowhere.",
     "S9 staging test, go-live"],
    ["O7 \u00B7 VPS (Ubuntu 22.04/24.04) + DNS for gabrielhomes.co.ke",
     "The rehearsal deploys the real runbook to the real server; DNS must point at it before SSL can be issued.",
     "R1 rehearsal, launch"],
    ["O1 \u00B7 Photo licences / provenance for demo-photos and property-images",
     "Every public photo needs a source we are allowed to use; unknown-origin images get replaced with owner-supplied or neutral placeholders.",
     "C1 cleanup, go-live"],
    ["O3 \u00B7 Lawyer review of Privacy & Terms",
     "The privacy page must satisfy the Kenya Data Protection Act, 2019; I prepare the text, a Kenyan lawyer approves it.",
     "Legal pages live"],
    ["O4 \u00B7 Enquiry retention period (365 days suggested)",
     "How long enquiry personal data is kept, and who may delete it on request.",
     "C3 retention cron"],
    ["O8 \u00B7 Backup destination (e.g. Backblaze B2 or S3) and credentials",
     "Nightly database dumps need an off-site home with access keys.",
     "D5 off-site step"],
    ["O5 \u00B7 Uptime checker of your choice + alert destination",
     "An external monitor watches /healthz/ and tells you before clients do.",
     "Operations sign-off"],
    ["O2 \u00B7 OK to archive unused media (list provided by C1)",
     "Confirms the junk files leave the repo rather than waiting in limbo.",
     "C1 completion"],
    ["O9\u2013O12 \u00B7 Confirmations: admin-only agent creation; logs-only error reporting at launch; Postgres test run if my side stalls; launcher check on a clean machine",
     "Small sign-offs that close their linked tasks.",
     "various"],
  ]
));

// 4 ---- definition of done ----
children.push(h1("4. Definition of Done"));
children.push(body(
  "The plan's exit criteria, condensed. Launch is declared when every box below has recorded evidence in the status file \u2014 not when things look finished. Each group maps to tasks above, so nothing here is new work; it is the finish line restated."
));
children.push(tableTitle("Table 2 \u00B7 Exit criteria by group"));
children.push(makeTable(
  [22, 78],
  ["Group", "Launch requires"],
  [
    ["Security", "No unallowlisted |safe; XSS and rate-limit regressions tested green; real-client-IP limiting with a shared store; production refuses unsafe configuration; Content-Security-Policy live with no third-party scripts; pip-audit clean; Django on a supported LTS."],
    ["Config & deploy", "check --deploy clean under prod settings; collectstatic emits hashed files; full suite green on PostgreSQL; DEPLOY.md reproducible on a fresh VM; /healthz/ reports honestly."],
    ["Data & content", "No demo seeding in production; every referenced image resolves; photo provenance confirmed by you; privacy text lawyer-reviewed."],
    ["Operations", "Nightly backups with a proven restore; failed enquiry emails visible in the dashboard; logs on stdout; external uptime check configured."],
    ["Quality", "Coverage \u2265 80% on core apps; smoke script green against staging; browser QA passed on desktop and phone; Lighthouse mobile scores recorded."],
  ]
));

// 5 ---- order of play ----
children.push(h1("5. Order of Play"));
children.push(body(
  "The work above sequences into roughly three focused days once your inputs start arriving. Day one finishes security (S7\u2013S12) and the health endpoint \u2014 none of it needs anything from you. Day two is platform and data: PostgreSQL test run, runbook corrections, backups, media cleanup and retention \u2014 ideal alongside your O1, O4 and O8 answers. Day three is verification and the launch rehearsal, which needs the VPS and DNS (O7) and mail credentials (O6) on the table."
));
children.push(body(
  "The critical path to a live site is short: S7\u2013S12 \u2192 D2 \u2192 D4\u2013D5 \u2192 R1 rehearsal \u2192 go-live sign-off, with owner inputs landing no later than the rehearsal. Everything else can run in parallel or follow within the first week after launch. Progress is tracked task-by-task in docs/STATUS.md with gate output as proof, so at any moment you can ask \u201Cwhat is left?\u201D and get an audited answer instead of a feeling."
));

// ---------------- document ----------------
const doc = new Document({
  styles: {
    default: {
      document: {
        run: { font: FONT, size: 24, color: "000000" },
        paragraph: { spacing: { line: 312 } },
      },
      heading1: {
        run: { font: FONT, size: 30, bold: true, color: INK },
        paragraph: { spacing: { before: 360, after: 160, line: 312 } },
      },
      heading2: {
        run: { font: FONT, size: 26, bold: true, color: INK },
        paragraph: { spacing: { before: 260, after: 120, line: 312 } },
      },
    },
  },
  sections: [
    {
      properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 0, bottom: 0, left: 0, right: 0 } } },
      children: cover,
    },
    {
      properties: {
        page: {
          size: { width: 11906, height: 16838 },
          margin: { top: 1440, bottom: 1440, left: 1701, right: 1417 },
          pageNumbers: { start: 1, formatType: NumberFormat.DECIMAL },
        },
      },
      footers: {
        default: new Footer({
          children: [new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "888888", font: FONT })],
          })],
        }),
      },
      children,
    },
  ],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync("/home/z/my-project/download/gabriel-homes-launch-checklist.docx", buf);
  console.log("WROTE /home/z/my-project/download/gabriel-homes-launch-checklist.docx", buf.length, "bytes");
});
