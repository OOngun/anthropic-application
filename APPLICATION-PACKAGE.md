# Application Package — Startup Partnerships, EMEA
## Ongun Ozdemir | March 2026

---

## PACKAGE CONTENTS

### 1. Core Application Materials
| File | Location | Status | Notes |
|------|----------|--------|-------|
| **CV** (PDF) | `cv/Ongun_Ozdemir_CV.pdf` | ✅ Ready | LaTeX source at `cv/Ongun_Ozdemir_CV.tex` |
| **Cover Letter** | `cover-letter.md` | ✅ Ready | Tailored to Startup Partnerships EMEA |
| **Job Description** | `job-description.md` | ✅ Saved | Greenhouse posting, saved Mar 16 |

### 2. Differentiator Materials (What Sets You Apart)
| File | Location | Status | Notes |
|------|----------|--------|-------|
| **Hex Dashboard** | `hex-dashboard-project/dashboard.html` | ✅ Built | Interactive 3-tier dashboard (Pulse → Partners → Detail) |
| **Dashboard Summary** | `hex-dashboard-project/DASHBOARD-SUMMARY.md` | 📝 To create | One-pager for email sharing |
| **Analytical Framework** | `hex-dashboard-project/ANALYTICAL-FRAMEWORK.md` | ✅ Ready | Tribe Capital growth accounting adaptation |
| **Case Studies** | `hex-dashboard-project/CASE-STUDIES-ANALYSIS.docx` | ✅ Ready | Lovable, Dust, Cursor deep dives |
| **EMEA Landscape Research** | `EMEA_AI_Startup_Landscape_Research.md` | ✅ Ready | 7 hubs, 50+ companies, VC landscape |

### 3. Interview Prep
| File | Location | Status | Notes |
|------|----------|--------|-------|
| **Profile & Context** | `ongun-profile.md` | ✅ Ready | Full career context with transferable skills mapped |
| **Raw Detail** | `raw-context-detailed.md` | ✅ Ready | Project-by-project stories for interview answers |
| **Interview Questions** | `interview-questions.md` | ✅ Ready | Anticipated questions and prep notes |
| **Role Research Dossier** | `role-research-dossier.md` | ✅ Ready | Deep research on the role and team |
| **Transcripts** | `transcripts/` | ✅ Ready | Round 1 & 2 interview practice notes |

### 4. Networking & Outreach
| File | Location | Status | Notes |
|------|----------|--------|-------|
| **CV Send List** | `networking-research/outreach-list-cv-send.md` | ✅ Ready | 14 contacts, prioritised, with verified emails |
| **Outreach Emails** | `networking-research/outreach-emails.md` | ✅ Ready | 9 personalised emails + 5 LinkedIn notes |
| **Full Contact Database** | `networking-research/tiered-contact-list.md` | ✅ Ready | 55+ contacts across 5 tiers |
| **EMEA GTM Contacts** | `networking-research/anthropic-emea-gtm-contacts.md` | ✅ Ready | 43 contacts with backgrounds |
| **Org Chart** | `networking-research/org-chart.html` | ✅ Ready | Interactive visualisation |
| **Hiring Manager Intel** | `networking-research/hiring-manager-and-contacts.md` | ✅ Ready | Guillaume Princen research |

---

## HOW TO DEPLOY

### Step 1: Submit Formal Application
- [ ] Go to [Greenhouse link](https://job-boards.greenhouse.io/anthropic/jobs/5021140008)
- [ ] Upload CV (`cv/Ongun_Ozdemir_CV.pdf`)
- [ ] Paste cover letter into the application form
- [ ] Note: Do NOT attach the dashboard or extras to the formal application — save those for outreach

### Step 2: Host Dashboard Online
- [ ] Push `hex-dashboard-project/dashboard.html` to GitHub Pages (see hosting instructions below)
- [ ] Get a clean URL like `oongun.github.io/anthropic-application/dashboard`
- [ ] Test the link works on mobile and desktop

### Step 3: Week 1 Outreach (Peers + Recruiters)
- [ ] Send LinkedIn connection request to **Rebecca Harbeck** (use LinkedIn note from outreach-emails.md)
- [ ] Email **Garry O'Brien** (garry@anthropic.com) — attach CV, include dashboard link
- [ ] Email **Danny Murphy** (danny@anthropic.com) — attach CV, include dashboard link
- [ ] Email **Delia Dumbravescu** (delia@anthropic.com) — attach CV, include dashboard link

### Step 4: Week 2 Outreach (Decision Makers)
- [ ] Email **Guillaume Princen** (guillaume@anthropic.com) — the big one. CV + dashboard link + EMEA analysis
- [ ] LinkedIn connection request to Guillaume (use LinkedIn note)
- [ ] Email **Aiden Blake** (aiden@anthropic.com) — peer framing, offer to share materials

### Step 5: Week 3 Outreach (Expand Network)
- [ ] Email **Steve Corfield** (steve@anthropic.com)
- [ ] Email **Abby Westby** (abby@anthropic.com) — rock climbing angle
- [ ] LinkedIn connect **Eleanor Dorfman** — venture scout angle
- [ ] LinkedIn connect **Conor Devitt** — Stripe/Bain angle

### Step 6: Follow Up
- [ ] 5 business days after each email — one short follow-up if no response
- [ ] After follow-up — move on, don't chase

---

## DASHBOARD HOSTING (GitHub Pages)

```bash
# From the repo root
cd hex-dashboard-project

# Create a docs folder for GitHub Pages
mkdir -p ../docs
cp dashboard.html ../docs/index.html

# Commit and push
cd ..
git add docs/
git commit -m "Add dashboard for GitHub Pages hosting"
git push

# Then go to GitHub → repo Settings → Pages → Source: Deploy from branch → /docs folder
# URL will be: https://oongun.github.io/anthropic-application/
```

---

## WHAT TO SEND TO WHOM

### Recruiters (Garry, Danny, Delia)
**Attach:** CV (PDF)
**Include in email:** Dashboard link, 1-line on EMEA analysis
**Tone:** Professional, direct, here are my materials

### Hiring Manager (Guillaume)
**Attach:** Nothing (offer to share — creates second touchpoint)
**Include in email:** Dashboard link, mention EMEA analysis and case studies
**Tone:** Confident, specific, show you understand his Stripe→Anthropic journey

### Peers (Rebecca, Aiden, Abby)
**Attach:** Nothing
**Include in email:** Mention dashboard, offer to share CV
**Tone:** Collaborative, curious, "future colleague" energy

### Strategic (Eleanor, Conor, Steve)
**Attach:** Nothing
**Include in email:** Mention dashboard if relevant
**Tone:** Light, connection-based, personalised hook

---

## PRE-FLIGHT CHECKLIST

Before sending anything, confirm:
- [ ] CV PDF renders correctly (no LaTeX artifacts, all links work)
- [ ] Dashboard hosted and accessible via public URL
- [ ] Dashboard loads correctly on mobile
- [ ] LinkedIn profile updated to match new CV framing
- [ ] Cover letter proofread one final time
- [ ] Greenhouse application submitted before any outreach emails
- [ ] Email signature includes phone number and LinkedIn
