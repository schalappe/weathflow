# Spec Requirements: Advice Date Context Improvement

## Initial Description

The advice can be generated only for the current and last month. But this restriction should be based on the last month transaction. By example, let say we are in December, and the last transaction record in the database is in October. The current code will only allow to generate advice for November and December. But there is no transaction in the database. The new version should allow to generate advice for September and October because the last transaction was made in October.

Also if it is the very first advice generated (no other advice in the database), the prompt should receive all the transactions present in the database (not just the three last months). Because it is the first, the advisor needs as much information as possible to make the best advice.

## Requirements Discussion

### Questions & Answers

**Q1:** I understand that advice eligibility should be based on the last transaction date in the database (not today's date). So if the last transaction is from October 2025, users can generate advice for October and September. Is that correct, or should they be able to generate advice for even earlier months?
**A:** That is correct, if the last transaction is from October 2025, users can generate advice for October and September.

**Q2:** You mentioned that the first advice (when no prior advice exists in the database) should receive all transactions in the database, not just the last 3 months. Does "all" mean literally all months with transactions, or should there still be a reasonable upper limit to keep the prompt size manageable?
**A:** To keep the prompt size manageable, let have an upper limit, 12 months max seems good.

**Q3:** Currently, advice generation requires at least 2 months of data (current + 1 history). For the first advice case with limited data, should we allow generating advice with just 1 month of data, or maintain the 2-month minimum?
**A:** Maintain the 2-month minimum even for first advice. The change is to give more context for the first advice. 1 month doesn't give sufficient context.

**Q4:** The frontend likely needs to know which months are "advice-eligible." Should the API return a list of advice-eligible months, or should the frontend calculate this based on a "last transaction month" endpoint?
**A:** Choose what you think is appropriate.

**Q5:** If a user regenerates advice for a month where previous advice exists, should the regeneration still use the special "first advice" logic (all transactions), or stick to the regular 3-month window?
**A:** That depends. If it tries to regenerate the first advice, keep the logic of 'first advice', else follow the regular 3-month window.

**Q6:** What should be explicitly OUT of scope for this feature?
**A:** We work only on the restriction to generate advice and the data provided for the generation of advice. Everything else is out of scope.

### Existing Code References

Key files identified from codebase exploration:

| File                                       | Purpose                                                     |
| ------------------------------------------ | ----------------------------------------------------------- |
| `backend/app/api/advice.py`                | API endpoints for advice generation                         |
| `backend/app/services/advice/generator.py` | Core advice generation logic                                |
| `backend/app/services/advice/service.py`   | Data transformation for Claude                              |
| `backend/app/services/advice/prompt.py`    | Claude system prompt                                        |
| `backend/app/repositories/month.py`        | Month data access (includes `get_recent_with_transactions`) |

### Follow-up Questions

None required - all requirements are clear.

## Visual Assets

### Files Found

No visual assets provided.

### Visual Insights

N/A - This is a backend-only change with no UI modifications.

## Requirements Summary

### Functional Requirements

1. **Date Reference Change**: Advice eligibility must be based on the last transaction date in the database, not today's date
   - If last transaction is October 2025, eligible months are October and September
   - Current behavior incorrectly uses today's date as reference

2. **First Advice Extended Context**: When generating the first advice ever (no existing advice in database):
   - Include all available transaction history (up to 12 months max)
   - Provides maximum context for initial recommendations
   - Still requires minimum 2 months of data

3. **Regeneration Logic**: When regenerating existing advice:
   - If regenerating the first advice record: use extended context (up to 12 months)
   - If regenerating any subsequent advice: use regular 3-month window

4. **Maintain Minimum Requirement**: Keep the 2-month minimum data requirement for all advice generation

### Technical Approach (Recommended for Q4)

For frontend eligibility awareness, validate at generation time and return a clear error message indicating which months are eligible. This keeps the change backend-focused without requiring new endpoints.

### Reusability Opportunities

- `MonthRepository.get_recent_with_transactions()` - can be extended or overloaded for variable limits
- Existing advice caching logic can remain unchanged
- Error handling patterns already exist for insufficient data scenarios

### Scope Boundaries

**In Scope:**

- Modify advice eligibility date logic (use last transaction date, not today)
- Modify history fetching to support variable limits (3 vs 12 months)
- Detect "first advice" scenario and apply extended context
- Handle regeneration of first advice vs subsequent advice
- Clear error messages for ineligible months
- Unit tests for new logic

**Out of Scope:**

- Changing the Claude prompt structure or content
- Modifying transaction filtering (CORE/CHOICE/COMPOUND logic)
- Frontend/UI changes
- Adding new API endpoints
- Changing advice storage format
- Modifying the scoring system

### Technical Considerations

- The `limit=3` parameter in `get_months_history_with_transactions()` needs to become dynamic
- Need a way to detect if this is the "first advice" (query advice table for any existing records)
- Need to find the last transaction date efficiently (may need new repository method)
- Regeneration needs to check if the advice being regenerated is the first one chronologically
