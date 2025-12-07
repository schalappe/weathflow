# Product Mission

## Pitch

Money Map Manager is a personal finance web application that helps budget-conscious professionals automate the tedious work of categorizing bank transactions by providing AI-powered categorization aligned with the Money Map (50/30/20) framework.

## Users

### Primary Customers

- **Finance-conscious professionals**: Individuals who actively track their spending and want to optimize their savings rate for investment
- **Bankin' users**: People who already centralize their bank accounts via Bankin' and export transactions as CSV

### User Personas

**Abdallah** (25-40)

- **Role:** Professional with stable income
- **Context:** Uses Bankin' to aggregate multiple bank accounts, follows the 50/30/20 budgeting rule (Money Map), wants to maximize investment capital
- **Pain Points:** Spends 30+ minutes monthly categorizing transactions manually, no historical tracking of budget performance, no personalized insights on spending trends
- **Goals:** Reduce categorization time to under 5 minutes, track budget score over time, receive actionable advice to improve savings rate

## The Problem

### Manual Budget Tracking is Time-Consuming and Error-Prone

Following the Money Map framework requires exporting transactions from Bankin', manually categorizing each transaction as Core/Choice/Compound, calculating totals and percentages, and repeating this process every month. This takes 30+ minutes monthly and provides no historical insights or trend analysis.

**Our Solution:** Automate the entire workflow with AI-powered categorization that learns from the Money Map framework, calculate scores automatically, and generate personalized advice based on spending history.

## Differentiators

### AI-Powered Categorization with Domain Knowledge

Unlike generic budgeting apps that use simple keyword matching, we use Claude AI with deep understanding of the Money Map framework to intelligently categorize transactions. This results in 90%+ accuracy and handles edge cases that rule-based systems miss.

### Personal and Local-First

Unlike cloud-based budgeting services that require sharing financial data with third parties, Money Map Manager runs entirely on localhost with local SQLite storage. This provides complete privacy while maintaining full functionality.

### Framework-Native Design

Unlike general-purpose budget trackers, we are built specifically for the Money Map (50/30/20) methodology. Every feature, from score calculation to advice generation, is designed around this framework.

## Key Features

### Core Features

- **CSV Import**: Upload Bankin' exports with automatic multi-month detection and transaction grouping
- **AI Categorization**: Claude-powered transaction categorization into Core, Choice, Compound, or Excluded categories
- **Score Calculation**: Automatic Money Map score (0-3) based on adherence to 50/30/20 targets
- **Monthly Dashboard**: Visual breakdown of spending by category with percentage tracking

### Tracking Features

- **Historical Analysis**: Track score evolution and spending patterns over 12+ months
- **Trend Visualization**: Charts showing Core/Choice/Compound breakdown over time
- **Month-to-Month Comparison**: See progress and identify areas of improvement

### Intelligence Features

- **Personalized Advice**: AI-generated recommendations based on the last 3 months of spending data
- **Problem Area Detection**: Automatic identification of categories trending upward
- **Actionable Suggestions**: Concrete steps to improve budget score
