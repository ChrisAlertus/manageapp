# Household Management Application - Project Plan

## Overview
A multi-platform household management application supporting expense splitting, chore scheduling, and shared to-do lists. The application will support multiple households with cross-platform access (iOS, Android, Web).

**Key Features:**
- Multi-currency expense tracking (USD, CAD, BBD, BRL, EUR) with real-time exchange rate conversion
- Split expenses with household members and external participants
- Recurring chore scheduling and tracking
- Shared household to-do lists

## Technology Stack Recommendations

### Backend
- **Framework**: FastAPI (Python) - Modern, fast, async support, automatic API documentation
- **Database**: PostgreSQL (via managed service or container)
- **ORM**: SQLAlchemy with Alembic for migrations
- **Authentication**: JWT tokens with password hashing (bcrypt)
- **Email Service**: SendGrid (free tier: 100 emails/day) or AWS SES (free tier: 62,000 emails/month)
- **SMS Service** (Future): Twilio (pay-as-you-go) or AWS SNS (pay-as-you-go) for expense notifications
- **Exchange Rate API**: ExchangeRate-API (free tier: 1,500 requests/month) or Fixer.io (free tier: 100 requests/month) or exchangerate-api.com

### Frontend
- **Mobile**: React Native (Expo) - Single codebase for iOS and Android
- **Web**: React with React Native Web (code sharing) or separate React web app
- **State Management**: React Query + Context API or Zustand
- **UI Framework**: React Native Paper (mobile) + Material-UI or Tailwind CSS (web)

### Infrastructure & Deployment
- **Cloud Provider**: Railway.app (primary, with Render.com support via abstraction layer)
  - Railway.app: $5/month free credit, PostgreSQL included, simple deployment
  - Render.com: Free tier available, supported via deployment abstraction layer for portability
  - Alternative: AWS/GCP (more complex but more control, supported via abstraction layer)
- **Database**: Railway PostgreSQL (primary) or Render PostgreSQL (via abstraction layer)
- **Containerization**: Docker
- **Infrastructure as Code**: Terraform (for AWS/GCP, Railway/Render use platform-native tools)
- **CI/CD**: GitHub Actions (free for public repos)
- **Deployment Abstraction**: Platform-agnostic configuration layer for easy migration between platforms

## Architecture Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Mobile    │     │    Web      │     │   Email     │
│  (React     │     │  (React)    │     │  Service    │
│   Native)   │     │             │     │             │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       └───────────────────┴───────────────────┘
                           │
                    ┌──────▼──────┐
                    │   FastAPI   │
                    │   Backend   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ PostgreSQL  │
                    │  Database   │
                    └─────────────┘
```

## Component Breakdown

### Phase 1: Foundation & Authentication

#### Task 1.1: Backend API Foundation
**Scope**: Set up FastAPI project structure, database models, and basic authentication
- Initialize FastAPI project with proper structure
- Set up SQLAlchemy models and database connection
- Implement user registration and login (JWT tokens)
- Create database migration system (Alembic)
- Set up environment configuration management
- Create basic API documentation structure

**Deliverables**:
- FastAPI application skeleton
- User model and authentication endpoints
- Database schema foundation
- Docker configuration for local development

#### Task 1.2: Household Management Core
**Scope**: Implement household creation, membership, and basic operations
- Household model (name, description, created_at, etc.)
- User-Household relationship (many-to-many with roles: owner, member)
- API endpoints for:
  - Creating a household
  - Listing user's households
  - Getting household details
  - Leaving a household
- Basic authorization middleware (verify household membership)

**Deliverables**:
- Household CRUD operations
- Membership management endpoints
- Authorization logic

#### Task 1.3: Email Invitation System
**Scope**: Implement email-based household invitations
- Invitation model (token, email, household, inviter, status, expires_at)
- Email service integration (SendGrid or AWS SES)
- API endpoints for:
  - Sending invitations
  - Accepting invitations (via token)
  - Listing pending invitations
  - Resending/canceling invitations
- Email templates for invitations

**Deliverables**:
- Invitation system with email integration
- Secure token-based invitation acceptance
- Email templates

#### Task 1.4: User Preferences Management
**Scope**: Implement user settings and preferences
- UserPreferences model (user, preferred_currency, timezone, language, etc.)
- API endpoints for:
  - Getting user preferences
  - Updating user preferences
  - Setting preferred currency (USD, CAD, BBD, BRL, EUR)
- Default preferences on user creation
- Currency preference validation

**Deliverables**:
- User preferences model and API
- Currency preference management
- Settings endpoints

### Phase 2: Expense Splitting Feature

#### Task 2.1: Expense Data Models
**Scope**: Design and implement database models for expense tracking
- Expense model (amount, description, date, paid_by, household, category, currency)
  - Currency field (ISO 4217 code: USD, CAD, BBD, BRL, EUR)
- ExpenseParticipant model (expense, user, percentage_owed, amount_owed, currency)
  - Store amount in original expense currency
- Payment model (from_user, to_user, amount, expense, status, date, currency)
  - Payments stored in original expense currency
- Support for external participants (email and phone number, not household members)
  - ExternalParticipant model (email, phone_number, name, expense, percentage_owed, amount_owed, currency)
  - Phone numbers stored for future SMS notification feature (expense breakdowns, payment reminders)
- User preferences model (user, preferred_currency)
  - Store user's preferred currency for viewing debts (USD, CAD, BBD, BRL, EUR)

**Deliverables**:
- Complete expense-related database schema with currency support
- Database migrations

#### Task 2.2: Expense CRUD Operations
**Scope**: Implement expense creation, editing, and viewing
- API endpoints for:
  - Creating expenses with participants and percentages
  - Listing expenses (filtered by household, date range)
  - Updating expenses
  - Deleting expenses
- Support for custom percentage splits
- Support for currency selection (USD, CAD, BBD, BRL, EUR)
  - Currency validation (ISO 4217 codes)
  - Store expense amount in selected currency
- Support for external participants (by email and/or phone number)
  - Phone number validation and formatting
  - Optional phone number (email is required, phone is optional for future SMS features)

**Deliverables**:
- Full expense management API
- Validation for percentage splits (must sum to 100%)
- Phone number validation and storage
- Currency selection and validation

#### Task 2.3: Payment Tracking
**Scope**: Track payments and calculate debts
- API endpoints for:
  - Recording payments (in original expense currency)
  - Listing debts (who owes whom)
  - Payment history
- Debt calculation logic (real-time based on expenses and payments)
  - Calculate debts in original expense currency
  - Support currency conversion when displaying debts
- Support for partial payments
- Currency-aware payment recording

**Deliverables**:
- Payment tracking system
- Debt calculation endpoints
- Multi-currency debt tracking

#### Task 2.4: Debt Simplification Algorithm
**Scope**: Implement Splitwise-style debt simplification
- Algorithm to minimize number of transactions
- Graph-based approach: build debt graph, find minimum transactions
- Multi-currency support:
  - Simplify debts within same currency first
  - Handle cross-currency debts (may require conversion)
  - Option to simplify in user's preferred currency
- API endpoint to get simplified debts
- Option to apply simplification (create virtual payments)

**Deliverables**:
- Debt simplification algorithm
- Simplified debt visualization endpoint
- Multi-currency debt simplification

#### Task 2.5: Exchange Rate Integration and Currency Conversion
**Scope**: Implement real-time exchange rate lookups and currency conversion
- Integration with exchange rate API (ExchangeRate-API, Fixer.io, or similar)
- API endpoints for:
  - Getting current exchange rates (cached with TTL)
  - Converting debt amounts to user's preferred currency
  - Getting exchange rate history (optional, for historical accuracy)
- Currency conversion service:
  - Real-time rate fetching with caching (reduce API calls)
  - Support for USD, CAD, BBD, BRL, EUR
  - Convert expense amounts when displaying in different currency
  - Handle currency conversion in debt calculations
- User preference management:
  - Set preferred display currency
  - API to update user currency preference
- Exchange rate caching strategy:
  - Cache rates for 1 hour (or configurable TTL)
  - Fallback to last known rate if API unavailable

**Deliverables**:
- Exchange rate API integration
- Currency conversion service
- Caching layer for exchange rates
- User currency preference management
- API endpoints for currency conversion

#### Task 2.6: SMS Notifications for External Participants (Future Feature)
**Scope**: Send SMS notifications to external expense participants
- Integration with SMS service (Twilio or AWS SNS)
- API endpoints for:
  - Sending expense breakdown via SMS
  - Sending payment reminders
  - Opt-in/opt-out management for SMS notifications
- SMS templates for expense notifications
- Phone number verification (optional)
- Include currency information in SMS notifications

**Deliverables**:
- SMS service integration
- Notification sending functionality
- User preference management for SMS notifications

### Phase 3: Chore Management Feature

#### Task 3.1: Chore Data Models
**Scope**: Design database models for chore scheduling
- Chore model (name, description, household, frequency, duration_estimate)
- ChoreAssignment model (chore, assigned_to, due_date, completed_at, status)
- Frequency types: daily, weekly, monthly, custom (cron-like)
- Recurrence logic storage

**Deliverables**:
- Chore and assignment database schema
- Database migrations

#### Task 3.2: Chore Scheduling Engine
**Scope**: Implement recurring chore generation
- Background job system (Celery or APScheduler)
- Recurrence calculation:
  - Daily: generate assignments for each day
  - Weekly: generate assignments for each week (Monday-Sunday window)
  - Monthly: generate assignments for each month
- Automatic assignment generation based on schedule
- Due date calculation based on frequency

**Deliverables**:
- Chore scheduling system
- Background job processor
- Recurrence logic

#### Task 3.3: Chore Management API
**Scope**: CRUD operations for chores and assignments
- API endpoints for:
  - Creating/editing/deleting chores
  - Assigning users to chores
  - Listing chores (by household, by user, by status)
  - Marking chores as completed
  - Viewing chore calendar
- Filtering: upcoming, overdue, completed
- Calendar view endpoint (grouped by date)

**Deliverables**:
- Complete chore management API
- Calendar view support

### Phase 4: To-Do List Feature

#### Task 4.1: To-Do Data Models
**Scope**: Design database models for shared to-do lists
- Todo model (title, description, household, created_by, priority, due_date)
- TodoClaim model (todo, claimed_by, claimed_at)
- TodoCompletion model (todo, completed_by, completed_at)
- Support for categories/tags

**Deliverables**:
- To-do list database schema
- Database migrations

#### Task 4.2: To-Do List API
**Scope**: Implement to-do list operations
- API endpoints for:
  - Creating/editing/deleting todos
  - Listing todos (by household, by status, by assignee)
  - Claiming a todo
  - Marking todos as complete
  - Unclaiming todos
- Filtering and sorting options

**Deliverables**:
- Complete to-do list API
- Claim/completion tracking

### Phase 5: Frontend - Web Application

#### Task 5.1: Web App Foundation
**Scope**: Set up React web application
- Initialize React project (Vite or Create React App)
- Set up routing (React Router)
- Configure API client (Axios or Fetch wrapper)
- Set up authentication flow (login, token storage)
- Basic layout and navigation structure

**Deliverables**:
- React web application skeleton
- Authentication UI
- Navigation structure

#### Task 5.2: Household Management UI
**Scope**: Web interface for household operations
- Household list/dashboard
- Create household form
- Household details page
- Invitation management UI
- Member list

**Deliverables**:
- Complete household management UI

#### Task 5.3: Expense Splitting UI
**Scope**: Web interface for expense management
- Expense list view
- Add expense form (with percentage split UI)
  - Currency selector (USD, CAD, BBD, BRL, EUR)
  - Support for adding external participants with email and phone number fields
  - Phone number input with validation and formatting
- Debt summary view
  - Currency conversion toggle/selector
  - Display debts in user's preferred currency or original currency
  - Show exchange rate used for conversion
  - Option to view all debts in a single currency
- Payment recording interface
  - Currency-aware payment entry
- Simplified debts view
  - Multi-currency support with conversion
- Expense history
  - Filter by currency
  - Show amounts in original currency with optional conversion

**Deliverables**:
- Complete expense management UI
- Currency selection and conversion UI

#### Task 5.4: Chore Management UI
**Scope**: Web interface for chores
- Chore list view
- Create/edit chore form
- Calendar view for chores
- Assignment interface
- Mark complete functionality
- Overdue/upcoming filters

**Deliverables**:
- Complete chore management UI

#### Task 5.5: To-Do List UI
**Scope**: Web interface for to-do lists
- To-do list view
- Create/edit todo form
- Claim/unclaim functionality
- Mark complete interface
- Filtering and sorting

**Deliverables**:
- Complete to-do list UI

#### Task 5.6: User Settings/Preferences UI
**Scope**: Web interface for user preferences
- Settings page/dashboard
- Currency preference selector (USD, CAD, BBD, BRL, EUR)
- Display currency conversion settings
- Other user preferences (timezone, notifications, etc.)

**Deliverables**:
- User settings UI
- Currency preference management

### Phase 6: Frontend - Mobile Application

#### Task 6.1: Mobile App Foundation
**Scope**: Set up React Native (Expo) application
- Initialize Expo project
- Set up navigation (React Navigation)
- Configure API client
- Set up authentication flow
- Basic app structure and theming

**Deliverables**:
- React Native app skeleton
- Authentication screens
- Navigation structure

#### Task 6.2: Mobile - Household Management
**Scope**: Mobile UI for household operations
- Household dashboard
- Create/join household screens
- Invitation management
- Member list

**Deliverables**:
- Mobile household management screens

#### Task 6.3: Mobile - Expense Splitting
**Scope**: Mobile UI for expenses
- Expense list and detail screens
- Add expense form
  - Currency selector (USD, CAD, BBD, BRL, EUR)
  - Support for adding external participants with email and phone number fields
  - Phone number input with validation (can use device's phone number picker)
- Debt summary screen
  - Currency conversion selector
  - Display debts in preferred currency
  - Show exchange rates
- Payment recording
  - Currency-aware payment entry
- Simplified debts view
  - Multi-currency support with conversion

**Deliverables**:
- Mobile expense management screens
- Currency selection and conversion UI

#### Task 6.4: Mobile - Chore Management
**Scope**: Mobile UI for chores
- Chore list screen
- Chore detail and completion
- Calendar view
- Create/edit chore screens

**Deliverables**:
- Mobile chore management screens

#### Task 6.5: Mobile - To-Do List
**Scope**: Mobile UI for to-do lists
- To-do list screen
- Create/edit todo screens
- Claim and complete functionality

**Deliverables**:
- Mobile to-do list screens

#### Task 6.6: Mobile - User Settings/Preferences
**Scope**: Mobile UI for user preferences
- Settings screen
- Currency preference selector (USD, CAD, BBD, BRL, EUR)
- Display currency conversion settings
- Other user preferences

**Deliverables**:
- Mobile user settings screens
- Currency preference management

### Phase 7: Infrastructure & Deployment

**Note**: Task 7.1 (Deployment Abstraction Layer) should be implemented early in development (during Phase 1 or early Phase 2) to ensure platform portability from the start.

#### Task 7.1: Deployment Abstraction Layer
**Scope**: Create platform-agnostic deployment configuration layer for multi-platform support
- Create deployment abstraction module (`app/core/deployment.py`)
  - Platform detection (Railway, Render, GCP, AWS, local)
  - Platform-specific configuration handling
  - Environment variable normalization
- Support for Railway.app deployment
  - Railway-specific configuration detection
  - Railway environment variable handling
  - Railway database connection string parsing
- Support for Render.com deployment (optional, for future portability)
  - Render-specific configuration detection
  - Render environment variable handling
  - Render database connection string parsing
- Platform-agnostic configuration defaults
  - Fallback values for local development
  - Platform detection via environment variables (`DEPLOYMENT_PLATFORM`, `RAILWAY_ENVIRONMENT`, `RENDER`)
- Documentation for platform-specific requirements
  - Environment variable documentation
  - Platform-specific deployment instructions
- Testing and validation
  - Test platform detection logic
  - Verify configuration loading for each platform
  - Ensure backward compatibility with local development

**Deliverables**:
- Deployment abstraction module
- Railway.app configuration support
- Render.com configuration support (optional)
- Platform detection and configuration loading
- Documentation for platform-specific setup
- Unit tests for deployment abstraction

**Implementation Notes**:
- Should be implemented early (Phase 1 or early Phase 2) to prevent platform-specific code from being introduced
- Keep platform-specific logic isolated in the abstraction layer
- All application code should use the abstraction layer, not platform-specific APIs directly
- Makes future migration between platforms straightforward (1-2 hours for Railway ↔ Render, 4-8 hours for Railway → GCP)

#### Task 7.2: Infrastructure as Code (Terraform)
**Scope**: Define infrastructure using Terraform
- Cloud provider selection and configuration
- Database instance (PostgreSQL)
- Application hosting (container service or serverless)
- Environment variables and secrets management
- Networking configuration (if needed)
- Email service configuration

**Deliverables**:
- Terraform configuration files
- Infrastructure documentation
- Deployment scripts

#### Task 7.3: CI/CD Pipeline
**Scope**: Set up automated deployment
- GitHub Actions workflows
- Build and test automation
- Docker image building
- Deployment to staging/production
- Database migration automation
- Platform-specific CI/CD configuration (Railway, Render, etc.)

**Deliverables**:
- CI/CD pipeline configuration
- Automated deployment process
- Platform-specific deployment workflows

#### Task 7.4: Production Deployment
**Scope**: Deploy application to production
- Set up production environment on Railway.app (primary platform)
- Configure domain and SSL
- Set up monitoring and logging
- Database backup strategy
- Environment configuration
- Optional: Set up Render.com as backup/secondary platform

**Deliverables**:
- Live production application on Railway.app
- Monitoring setup
- Documentation
- Optional: Secondary deployment on Render.com

## Database Schema Summary

### Core Tables
- `users` - User accounts
- `user_preferences` - User settings (preferred_currency, timezone, etc.)
- `households` - Household definitions
- `household_members` - User-household relationships with roles

### Expense Tables
- `expenses` - Expense records (includes currency field: USD, CAD, BBD, BRL, EUR)
- `expense_participants` - Who owes what for each expense (household members, includes currency)
- `payments` - Payment records between users (includes currency)
- `external_participants` - Non-household members in expenses (email, phone_number, name, percentage_owed, amount_owed, currency)
  - Phone numbers stored for future SMS notification feature
- `user_preferences` - User settings (preferred_currency for debt display)
- `exchange_rates` (optional cache table) - Cached exchange rates with timestamp

### Chore Tables
- `chores` - Chore definitions
- `chore_assignments` - Individual chore instances with due dates
- `chore_completions` - Completion records

### To-Do Tables
- `todos` - To-do items
- `todo_claims` - Who claimed which todo
- `todo_completions` - Completion records

### Invitation Tables
- `invitations` - Household invitations

## Security Considerations

1. **Authentication**: JWT tokens with secure storage
2. **Authorization**: Verify household membership for all operations
3. **Data Isolation**: Ensure users can only access their household data
4. **Email Security**: Secure invitation tokens with expiration
5. **API Security**: Rate limiting, input validation, SQL injection prevention
6. **Secrets Management**: Environment variables, no hardcoded credentials
7. **Exchange Rate API**: Secure API key storage, rate limiting to prevent abuse
8. **Currency Validation**: Validate currency codes to prevent injection attacks
9. **Exchange Rate Caching**: Cache rates to reduce API calls and improve security

## Free Tier Cloud Options

### Railway.app (Primary Platform)
- $5/month free credit
- PostgreSQL included
- Simple deployment
- Good for MVP and initial testing
- **Selected as primary deployment platform**

### Render.com (Secondary/Supported Platform)
- Free tier for web services (with limitations)
- PostgreSQL free tier available
- Simple setup
- **Supported via deployment abstraction layer (Task 7.1)**
- Easy migration path from Railway (1-2 hours)

### AWS/GCP (Future/Advanced)
- AWS: Free tier for 12 months, RDS PostgreSQL (limited)
- GCP: Free tier available, Cloud SQL PostgreSQL
- More configuration required
- Better for scaling and enterprise use
- **Supported via deployment abstraction layer (Task 7.1)**
- Medium complexity migration from Railway (4-8 hours)

## Development Workflow Recommendations

1. **Start with Backend**: Build and test API endpoints first
2. **Use API Testing**: Postman or similar for backend development
3. **Incremental Frontend**: Build web first, then mobile (or in parallel)
4. **Local Development**: Docker Compose for local database and services
5. **Version Control**: Git with feature branches
6. **Testing**: Unit tests for critical logic (expense calculations, debt simplification)

## Estimated Complexity

- **Backend API**: Medium-High (expense simplification algorithm is complex)
- **Web Frontend**: Medium
- **Mobile Frontend**: Medium
- **Infrastructure**: Low-Medium (simpler with Railway/Render)

## Next Steps

1. Review and refine this plan
2. Set up project repository structure
3. Begin with Task 1.1 (Backend API Foundation)
4. Implement Task 7.1 (Deployment Abstraction Layer) early in Phase 1 to ensure platform portability
5. Set up local development environment
6. Deploy to Railway.app for initial testing (with Render.com support via abstraction layer)
7. Create initial Terraform configuration for infrastructure planning (for future AWS/GCP migration)

