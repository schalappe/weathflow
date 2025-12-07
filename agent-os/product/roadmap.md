# Product Roadmap

1. [ ] Database Models — Create SQLAlchemy models for months, transactions, and advice tables with proper relationships and indexes `S`

2. [ ] CSV Parser Service — Build a service that parses Bankin' CSV exports, detects all months present, groups transactions by month, and returns structured data with summaries `M`

3. [ ] Transaction Categorization Service — Implement Claude API integration that categorizes transactions into Money Map categories (Core/Choice/Compound/Excluded) with batch processing for cost efficiency `M`

4. [ ] Score Calculation Service — Create a service that calculates Money Map percentages and scores (0-3) based on categorized transactions and the 50/30/20 thresholds `S`

5. [ ] Upload and Categorize API — Build FastAPI endpoints for CSV upload, parsing preview, and triggering categorization with support for replace/merge import modes `M`

6. [ ] Monthly Data API — Create endpoints to retrieve month data including totals, percentages, score, and transaction list with filtering capabilities `S`

7. [ ] Import Page UI — Build the file upload interface with drag-and-drop, multi-month preview table, month selection checkboxes, and categorization progress indicator `M`

8. [ ] Monthly Dashboard UI — Create the main dashboard showing score card, Core/Choice/Compound metric cards with percentage indicators, pie chart breakdown, and transaction table `L`

9. [ ] Transaction Correction — Add inline editing capability to change transaction categories with automatic score recalculation when corrections are made `M`

10. [ ] Historical Data API — Extend the months API to return aggregated history for the last N months with score and percentage trends `S`

11. [ ] Score Evolution Chart — Build a line chart component showing score progression over time using Recharts `S`

12. [ ] Spending Breakdown Chart — Create a stacked bar chart showing Core/Choice/Compound distribution month-over-month `S`

13. [ ] History Page UI — Combine evolution charts into a dedicated history page with period selector `M`

14. [ ] Advice Generation Service — Implement Claude API integration that analyzes the last 3 months and generates personalized recommendations with trend analysis `M`

15. [ ] Advice API and Storage — Create endpoints to generate and retrieve advice, storing generated advice in the database for the month `S`

16. [ ] Advice Panel UI — Build the advice display component showing analysis, problem areas, recommendations, and encouragement with a regenerate button `M`

17. [ ] Transaction Filters — Add filtering by category type, date range, and search by description to the transaction table `S`

18. [ ] Data Export — Implement JSON and CSV export of monthly data for backup purposes `XS`

> Notes
>
> - Order items by technical dependencies and product architecture
> - Each item represents an end-to-end (frontend + backend) functional and testable feature
> - Items 1-8 form the MVP, items 9-16 complete the core experience, items 17-18 are polish
