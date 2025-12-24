# Spec Requirements: Advice Date Eligibility Improvement

## Initial Description

The advice can only be generated for the current and last month. But this restriction should be based on the last month transaction, not today's date.

**Example:** If we are in December, and the last transaction record in the database is in October, the current code will only allow generating advice for November and December. But there are no transactions in the database for those months. The new version should allow generating advice for September and October because the last transaction was made in October.

Also, if it is the very first advice generated (no other advice in the database), the prompt should receive more transaction history because the advisor needs as much information as possible to make the best first advice.

## Requirements Discussion

### Questions & Answers

**Q1:** I assume the eligibility should be based on the last transaction date in the database (not today's date). For example, if the last transaction is in October 2024 and today is December 2024, users should be able to generate advice for September and October only. Is that correct?
**A:** Yes

**Q2:** The previous reverted implementation used a window of 2 months (current + previous). I assume you want to keep this 2-month window but anchor it to the last transaction date. Is that correct, or should the window size be different?
**A:** Yes

**Q3:** For the very first advice (no other advice exists in the database), you mentioned the prompt should receive ALL transactions in the database rather than just the last 3 months. I assume this means: check if any advice records exist, if none exist fetch all months, otherwise fetch normal 3 months. Is this interpretation correct?
**A:** Yes, but add a limit of 12 months for prompt size management

**Q4:** If a user regenerates the very first advice (the only advice record in the database), should it still use ALL transactions, or should it fall back to the regular 3-month limit?
**A:** Same rule as the first advice (12 months), because user is trying to regenerate the first advice

**Q5:** Should the new implementation keep frontend-only enforcement, add backend enforcement, or both?
**A:** Both frontend + backend enforcement for fluidity and robustness

**Q6:** What should be explicitly OUT of scope for this feature?
**A:** Only the restriction to generate advice and the data fetch for advice. Everything else is out of scope.

### Existing Code References

- **Reverted implementation:** Commit `3e746f3` had `backend/app/services/advice/eligibility.py` with similar logic
- **Current frontend restriction:** `frontend/components/history/advice-panel-content.tsx` lines 112-129 (`isGenerationAllowed` function)
- **Backend API:** `backend/app/api/advice.py` - no restriction currently
- **History fetching:** `backend/app/services/data/months.py` - `get_months_history_with_transactions(limit=3)`

### Follow-up Questions

None needed - requirements are clear.

## Visual Assets

### Files Found

No visual assets provided.

## Requirements Summary

### Functional Requirements

1. **Eligibility based on last transaction date:**
   - Find the most recent month with transactions in the database
   - Allow advice generation for that month and the previous month only
   - Anchor eligibility to transaction data, not current calendar date

2. **Extended history for first advice:**
   - If no advice records exist in the database: fetch up to 12 months of history
   - If regenerating the only advice record: also fetch up to 12 months (treat as first advice)
   - Otherwise: fetch normal 3 months of history

3. **Dual enforcement:**
   - Frontend: Display appropriate UI based on eligibility (button vs message)
   - Backend: Validate eligibility and return clear error if not eligible

### Reusability Opportunities

- Reverted `eligibility.py` service can be referenced for logic patterns
- `EligibilityResult` dataclass pattern was well-designed
- `_is_within_eligible_window` helper function logic is reusable

### Scope Boundaries

**In Scope:**

- Eligibility determination logic (backend service)
- History limit calculation (3 vs 12 months)
- Backend API enforcement with clear error messages
- Frontend `isGenerationAllowed` function update
- API response to inform frontend of eligibility status

**Out of Scope:**

- Advice prompt changes
- Advice display/UI changes (beyond eligibility)
- Transaction categorization
- Score calculation
- Any other feature changes

### Technical Considerations

- Backend needs new endpoint or response field to communicate eligibility to frontend
- Frontend needs to fetch eligibility info from backend (not calculate locally)
- History limit must be dynamically determined (3 or 12) based on first-advice scenario
- Month repository needs method to get most recent month
- Advice repository needs method to check if any advice exists
