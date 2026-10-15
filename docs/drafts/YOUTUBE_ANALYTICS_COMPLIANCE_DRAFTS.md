# DRAFT — not published, not sent, not authority

> These are working drafts for the approved-but-unimplemented YouTube Analytics design recorded in
> [`CONVEYOR_CURRENT_STATE.md`](../CONVEYOR_CURRENT_STATE.md). Nothing here has been published on the website, sent
> to YouTube or Google, or implemented. `POLICY_VERSION` is unchanged. Operational truth stays in CURRENT_STATE.

## 1. Privacy-policy addition (reconciled against the published policy)

**Source checked:** https://conveyoros.co.uk/privacy/, retrieved 15 October 2026 (HTTP 200). Header: "Policy version:
2026-10-06", "Last updated: 6 October 2026". The contact address is obfuscated in the page source (email protection),
so it could not be verified from the fetch; the draft leaves the Contact section unchanged.

Marking: **[ADD]** new text, **[CHANGE]** replaces the quoted sentence, **[KEEP]** unchanged. Text in
**[CONDITIONAL]** describes behaviour that does not exist yet and may only be published once the implementation and
its tests are in place.

### Header

- **[CHANGE]** "Policy version: 2026-10-06" / "Last updated: 6 October 2026" → the new version and date, which must
  equal the shipped `POLICY_VERSION`.

### YouTube API Services

- **[KEEP]** The existing paragraph (uses YouTube API Services; YouTube Terms of Service; Google Privacy Policy). Check
  that its Google Privacy Policy link and the code constant `GOOGLE_PRIVACY_URL` point to the same current address.

### Information Conveyor may access

- **[KEEP]** The existing sentence listing channel and video identifiers, metadata, tokens, reconciliation information
  and upload material.
- **[ADD] [CONDITIONAL]** "If the YouTube Analytics feature is enabled and you expressly authorise it, Conveyor may
  also access YouTube Analytics reports for your own videos: non-monetary measures such as views, watch time, average
  view duration and percentage, likes, comments, shares, subscribers gained and lost, and audience retention.
  Conveyor does not request revenue or monetary data. This uses a separate permission that you grant or revoke
  independently in Conveyor."

### How information is used

- **[KEEP]** "Conveyor uses this information only to provide production, verification, reconciliation and authorised
  publishing features. Conveyor does not sell YouTube API data or use it for advertising or unrelated profiling."
- **[CHANGE] [CONDITIONAL]** Add after the first sentence: "With the YouTube Analytics feature enabled, Conveyor also
  uses YouTube Analytics data to help the operator learn how their own videos performed. Conveyor stores YouTube's
  values as reported and does not calculate new metrics from them; the operator's own notes are kept separately and
  are not YouTube data."

### Storage and retention

- **[KEEP]** The paragraph on storing only what is reasonably necessary, and the paragraph on running on the
  operator's computer, the protected credential store and the local acceptance record.
- **[ADD] [CONDITIONAL]** "YouTube Analytics data is kept on the operator's computer for as long as it is needed for
  that learning, and only while Conveyor re-confirms your authorisation at least every 30 days. If the authorisation
  cannot be confirmed within 30 days, Conveyor stops using that data and deletes it. If a video is deleted from
  YouTube, Conveyor deletes the analytics it stored for that video. Other YouTube API data continues to be refreshed
  or deleted within 30 days."
- **[KEEP]** The cookie sentence.

### Sharing

- **[KEEP]** The existing paragraph. **[ADD] [CONDITIONAL]** "YouTube Analytics data is accessible only to the
  operator on that computer and is not shared."

### User control, revocation and deletion

- **[KEEP]** The existing paragraphs (Conveyor's own controls; the Google security settings page; deletion requests;
  7 calendar days for revocation or deletion through Conveyor; 30 calendar days after revocation through Google).
- **[ADD] [CONDITIONAL]** "Revoking access through Google may remove every permission Conveyor holds, including
  YouTube Analytics; Conveyor then deletes all stored YouTube API data, including analytics, within the periods
  above."

### Security, Changes, Contact

- **[KEEP]** Unchanged.

## 2. Written notice to YouTube

To be sent by the founder through the confirmed route (see section 3), only after the build exists and before any
analytics API use.

> **Subject:** Conveyor (project 1031021502761) — notice of new YouTube API use: YouTube Analytics (read-only,
> non-monetary)
>
> Conveyor is a single-operator production tool used only for our own YouTube channel UC1cX-OTF9-LZeNo5TaFgrgQ, under
> Google Cloud project 1031021502761. In line with the attestation in our 6 October 2026 YouTube API Services
> submission, we are notifying you before starting a new use:
>
> - **API and method:** YouTube Analytics API `reports.query`, for our own channel's videos only.
> - **Scopes:** `https://www.googleapis.com/auth/yt-analytics.readonly` and
>   `https://www.googleapis.com/auth/youtube.readonly` (the latter is now required by `reports.query`). No monetary
>   scope.
> - **Data:** non-monetary video metrics and audience retention, collected about 24 hours, 72 hours, 7 days and 28
>   days after publication.
> - **Retention:** stored on the operator's computer while needed for our own editorial learning, with the
>   authorisation re-verified at least every 30 days (Developer Policies III.E.4(b)). If re-verification fails, the
>   data is no longer used and is deleted; data for a deleted video is deleted; revocation through Conveyor deletes
>   it within 7 days and through Google within 30 days.
> - **No derived metrics:** we store YouTube's values as reported and do not create new or derived metrics from API
>   data (III.E.4(h)).
> - **Quota:** no quota increase is requested.
> - **Privacy policy:** updated at https://conveyoros.co.uk/privacy/ (version [new version]) before any analytics
>   request is made.

## 3. Open evidence gaps

- **Exact 6 October submission wording.** The evidence folder
  (`D:\ConveyorOS\evidence\youtube-audit\2026-10-06\`) holds the attachments and screenshots but not the submitted
  form answers. The founder should locate the exact attestation text (form copy or Google's confirmation email) so
  the notice quotes it precisely.
- **Notification route not confirmed.** Developer Policies III.D.3 directs use-case changes through a resubmitted API
  Compliance Audit (the audit and quota-extension form used on 6 October). Whether that form, or a reply to Google's
  8 October closure email, is the right route for this notice is not confirmed.
- **Published policy contact address.** Obfuscated in the page source; confirm it on the live page before publishing.
