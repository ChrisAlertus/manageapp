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

#### Task 1.1: Backend API Foundation ✅
**Scope**: Set up FastAPI project structure, database models, and basic authentication
- Initialize FastAPI project with proper structure
- Set up SQLAlchemy models and database connection
- Implement user registration and login (JWT tokens)
- Create database migration system (Alembic)
- Set up environment configuration management
- Create basic API documentation structure
- Unit tests for:
  - Authentication logic (password hashing, JWT token creation/validation)
  - User model validation
  - Security utilities
  - Configuration management
- Integration tests for:
  - User registration and login workflows
  - Authentication endpoints
  - Database connection and migrations
  - Error handling scenarios
- Documentation:
  - API endpoint documentation (OpenAPI/Swagger)
  - Project structure documentation
  - Setup and installation guide (README)
  - Code documentation for core modules
  - Environment configuration guide

**Deliverables**:
- FastAPI application skeleton
- User model and authentication endpoints
- Database schema foundation
- Docker configuration for local development
- Unit test suite
- Integration test suite
- API documentation
- Setup documentation

#### Task 1.2: Household Management Core ✅
**Scope**: Implement household creation, membership, and basic operations
- Household model (name, description, created_at, etc.)
- User-Household relationship (many-to-many with roles: owner, member)
- API endpoints for:
  - Creating a household
  - Listing user's households
  - Getting household details
  - Leaving a household
  - Removing/kicking a member from a household (owners only)
  - Transferring ownership (assigning a new owner)
  - Deleting a household (owners only)
- Basic authorization middleware (verify household membership)
- Unit tests for:
  - Household model validation
  - Membership relationship logic
  - Authorization middleware functions
- Integration tests for:
  - Household creation and retrieval
  - Membership management workflows
  - Authorization enforcement
  - Error handling scenarios
- Documentation:
  - API endpoint documentation (OpenAPI/Swagger)
  - Update README with household management usage examples
  - Code documentation for models and authorization logic

**Deliverables**:
- Household CRUD operations
- Membership management endpoints
- Authorization logic
- Unit test suite
- Integration test suite
- API documentation updates

#### Task 1.3: Email Invitation System ✅
**Scope**: Implement email-based household invitations
- Invitation model (token, email, household, inviter, status, expires_at)
- Email service integration (SendGrid or AWS SES)
- API endpoints for:
  - Sending invitations
  - Accepting invitations (via token)
  - Listing pending invitations
  - Resending/canceling invitations
- Email templates for invitations
- Unit tests for:
  - Invitation token generation and validation
  - Email service integration (mocked)
  - Invitation expiration logic
  - Status transition logic
- Integration tests for:
  - End-to-end invitation flow (send, accept, cancel)
  - Token expiration handling
  - Email service error handling
  - Duplicate invitation prevention
- Documentation:
  - API endpoint documentation (OpenAPI/Swagger)
  - Email service integration guide
  - Update README with invitation workflow
  - Code documentation for invitation models and services

**Deliverables**:
- Invitation system with email integration
- Secure token-based invitation acceptance
- Email templates
- Unit test suite
- Integration test suite
- API documentation updates

#### Task 1.3.1: Email Confirmation on Registration
**Scope**: Send confirmation email to users when they register and implement email verification
- Add email verification fields to User model:
  - `email_verified` (boolean, default False)
  - `email_verification_token` (string, nullable, unique)
  - `email_verification_token_expires_at` (datetime, nullable)
- Email service integration for sending confirmation emails:
  - Welcome email template with confirmation link
  - Confirmation link includes secure token
  - Token expiration (e.g., 24-48 hours)
- API endpoints for:
  - Automatically send confirmation email on user registration
  - Verifying email address (via token)
  - Resending confirmation email
  - Checking email verification status
- Email templates:
  - Welcome email with confirmation link
  - Confirmation success email
- Token generation and validation:
  - Secure, unique tokens for each user
  - Token expiration handling
  - One-time use tokens (invalidate after verification)
- Unit tests for:
  - Email verification token generation and validation
  - Email service integration (mocked)
  - Token expiration logic
  - Email verification status updates
  - Resend confirmation logic
- Integration tests for:
  - End-to-end registration and confirmation flow
  - Token expiration handling
  - Email service error handling
  - Resend confirmation workflow
  - Duplicate verification prevention
- Documentation:
  - API endpoint documentation (OpenAPI/Swagger)
  - Email confirmation workflow guide
  - Update README with email verification process
  - Code documentation for email verification models and services

**Deliverables**:
- Email verification fields in User model
- Automatic confirmation email on registration
- Email verification endpoint with token validation
- Welcome and confirmation email templates
- Resend confirmation functionality
- Unit test suite
- Integration test suite
- API documentation updates

#### Task 1.4: User Preferences Management ✅
**Scope**: Implement user settings and preferences
- UserPreferences model (user, preferred_currency, timezone, language, etc.)
- API endpoints for:
  - Getting user preferences
  - Updating user preferences
  - Setting preferred currency (CAD(default), BRL, BBD, EUR, USD)
- Default preferences on user creation
- Currency preference validation
- Unit tests for:
  - Preference model validation
  - Currency validation logic
  - Default preference initialization
  - Preference update logic
- Integration tests for:
  - Preference CRUD operations
  - Currency validation enforcement
  - Default preference creation on user registration
  - Preference update workflows
- Documentation:
  - API endpoint documentation (OpenAPI/Swagger)
  - Update README with preference management examples
  - Supported currencies and timezone documentation
  - Code documentation for preference models

**Deliverables**:
- User preferences model and API
- Currency preference management
- Settings endpoints
- Unit test suite
- Integration test suite
- API documentation updates

#### Task 1.4.1: Timezone Selection (Future/Optional)
**Scope**: Allow users to select a timezone other than UTC
- **Why timezone preferences matter**:
  - Display dates/times in user's local timezone (expense dates, chore due dates, to-do deadlines)
  - Schedule notifications at appropriate local times
  - Calendar views showing times in user's timezone
  - Chore scheduling that respects user's local time
  - Better UX for international users in different timezones
- **Already Implemented (Task 1.4)**:
  - ✅ Timezone field in UserPreferences model (defaults to UTC)
  - ✅ Timezone validation (IANA timezone database) via `validate_timezone()` function
  - ✅ API endpoint to get timezone preference: `GET /api/v1/users/me/preferences`
  - ✅ API endpoint to update timezone preference: `PATCH /api/v1/users/me/preferences` (accepts `timezone` field)
  - ✅ Timezone detection during registration (optional `timezone` field in `UserCreate` schema)
  - ✅ Timezone validation in `UserPreferencesUpdate` schema
- **Still To Do (when implementing timezone-aware features)**:
  - Timezone selector UI (dropdown with common timezones or timezone search) - Frontend Task 5.6/6.6
  - Backend utility functions to convert UTC timestamps to user's preferred timezone for display
  - Apply timezone conversion in API responses when returning datetime fields (expenses, chores, todos, etc.)
  - Timezone-aware scheduling logic for chores and notifications
- **Note**: The API infrastructure for timezone preferences is complete. The remaining work is UI implementation and applying timezone conversions when displaying data to users.

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
- Unit tests for:
  - Model validation and constraints
  - Currency field validation
  - Relationship integrity
  - Percentage calculation logic
- Integration tests for:
  - Database schema creation and migrations
  - Model relationships and foreign keys
  - Data integrity constraints
- Documentation:
  - Database schema documentation
  - Model relationship diagrams
  - Update README with expense data model overview
  - Code documentation for all expense models

**Deliverables**:
- Complete expense-related database schema with currency support
- Database migrations
- Unit test suite
- Integration test suite
- Database schema documentation

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
- Unit tests for:
  - Percentage split validation logic
  - Currency validation
  - Phone number validation and formatting
  - Expense calculation logic
  - External participant handling
- Integration tests for:
  - Expense CRUD operations end-to-end
  - Percentage split validation enforcement
  - Currency validation enforcement
  - External participant creation and retrieval
  - Filtering and query operations
  - Authorization checks
- Documentation:
  - API endpoint documentation (OpenAPI/Swagger)
  - Update README with expense management examples
  - Phone number format documentation
  - Supported currencies documentation
  - Code documentation for expense service logic

**Deliverables**:
- Full expense management API
- Validation for percentage splits (must sum to 100%)
- Phone number validation and storage
- Currency selection and validation
- Unit test suite
- Integration test suite
- API documentation updates

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
- Unit tests for:
  - Debt calculation algorithms
  - Payment recording logic
  - Currency conversion calculations
  - Partial payment handling
  - Debt aggregation logic
- Integration tests for:
  - Payment recording and retrieval
  - Debt calculation accuracy
  - Multi-currency debt tracking
  - Payment history queries
  - Edge cases (overpayment, partial payments)
- Documentation:
  - API endpoint documentation (OpenAPI/Swagger)
  - Debt calculation algorithm documentation
  - Update README with payment tracking examples
  - Multi-currency debt tracking guide
  - Code documentation for payment and debt calculation logic

**Deliverables**:
- Payment tracking system
- Debt calculation endpoints
- Multi-currency debt tracking
- Unit test suite
- Integration test suite
- API documentation updates

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
- Unit tests for:
  - Debt graph construction
  - Simplification algorithm correctness
  - Multi-currency simplification logic
  - Edge cases (circular debts, zero debts, single currency)
  - Algorithm performance with various debt structures
- Integration tests for:
  - End-to-end debt simplification workflow
  - Multi-currency simplification scenarios
  - Simplified debt API endpoint
  - Virtual payment creation
  - Complex debt network simplification
- Documentation:
  - Algorithm explanation and complexity analysis
  - API endpoint documentation (OpenAPI/Swagger)
  - Update README with debt simplification examples
  - Multi-currency simplification guide
  - Code documentation for simplification algorithm

**Deliverables**:
- Debt simplification algorithm
- Simplified debt visualization endpoint
- Multi-currency debt simplification
- Unit test suite
- Integration test suite
- Algorithm documentation
- API documentation updates

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
- Unit tests for:
  - Exchange rate API integration (mocked)
  - Currency conversion calculations
  - Caching logic and TTL handling
  - Fallback mechanism
  - Rate fetching error handling
- Integration tests for:
  - Exchange rate API integration (with test API key or mocked)
  - Currency conversion accuracy
  - Caching behavior
  - Fallback to cached rates
  - API rate limiting handling
- Documentation:
  - Exchange rate API integration guide
  - API endpoint documentation (OpenAPI/Swagger)
  - Update README with currency conversion examples
  - Caching strategy documentation
  - Supported currencies and exchange rate sources
  - Code documentation for exchange rate service

**Deliverables**:
- Exchange rate API integration
- Currency conversion service
- Caching layer for exchange rates
- User currency preference management
- API endpoints for currency conversion
- Unit test suite
- Integration test suite
- API documentation updates

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
- Unit tests for:
  - SMS service integration (mocked)
  - SMS template rendering
  - Phone number validation
  - Opt-in/opt-out logic
  - Currency formatting in SMS
- Integration tests for:
  - SMS sending workflow (with test credentials or mocked)
  - Notification delivery tracking
  - Opt-in/opt-out enforcement
  - Error handling for SMS failures
- Documentation:
  - SMS service integration guide
  - API endpoint documentation (OpenAPI/Swagger)
  - Update README with SMS notification setup
  - SMS template documentation
  - Code documentation for SMS service

**Deliverables**:
- SMS service integration
- Notification sending functionality
- User preference management for SMS notifications
- Unit test suite
- Integration test suite
- API documentation updates

### Phase 3: Chore Management Feature

#### Task 3.1: Chore Data Models
**Scope**: Design database models for chore scheduling
- Chore model (name, description, household, frequency, duration_estimate)
- ChoreAssignment model (chore, assigned_to, due_date, completed_at, status)
- Frequency types: daily, weekly, monthly, custom (cron-like)
- Recurrence logic storage
- Unit tests for:
  - Model validation and constraints
  - Frequency type validation
  - Recurrence logic parsing
  - Relationship integrity
- Integration tests for:
  - Database schema creation and migrations
  - Model relationships and foreign keys
  - Data integrity constraints
- Documentation:
  - Database schema documentation
  - Model relationship diagrams
  - Update README with chore data model overview
  - Frequency type documentation
  - Code documentation for chore models

**Deliverables**:
- Chore and assignment database schema
- Database migrations
- Unit test suite
- Integration test suite
- Database schema documentation

#### Task 3.2: Chore Scheduling Engine
**Scope**: Implement recurring chore generation
- Background job system (Celery or APScheduler)
- Recurrence calculation:
  - Daily: generate assignments for each day
  - Weekly: generate assignments for each week (Monday-Sunday window)
  - Monthly: generate assignments for each month
- Automatic assignment generation based on schedule
- Due date calculation based on frequency
- Unit tests for:
  - Recurrence calculation logic
  - Due date calculation for each frequency type
  - Assignment generation logic
  - Background job scheduling
  - Edge cases (leap years, month boundaries, timezone handling)
- Integration tests for:
  - End-to-end chore scheduling workflow
  - Background job execution
  - Assignment generation accuracy
  - Multiple frequency types
  - Concurrent job handling
- Documentation:
  - Scheduling engine architecture documentation
  - Recurrence logic explanation
  - Background job setup guide
  - Update README with chore scheduling examples
  - Code documentation for scheduling engine

**Deliverables**:
- Chore scheduling system
- Background job processor
- Recurrence logic
- Unit test suite
- Integration test suite
- Architecture documentation

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
- Unit tests for:
  - Chore CRUD operations logic
  - Assignment logic
  - Filtering and query logic
  - Calendar view generation
  - Status transition logic
- Integration tests for:
  - Chore CRUD operations end-to-end
  - Assignment workflows
  - Filtering and query operations
  - Calendar view accuracy
  - Authorization checks
  - Status updates
- Documentation:
  - API endpoint documentation (OpenAPI/Swagger)
  - Update README with chore management examples
  - Calendar view API documentation
  - Filtering options documentation
  - Code documentation for chore service logic

**Deliverables**:
- Complete chore management API
- Calendar view support
- Unit test suite
- Integration test suite
- API documentation updates

### Phase 4: To-Do List Feature

#### Task 4.1: To-Do Data Models
**Scope**: Design database models for shared to-do lists
- Todo model (title, description, household, created_by, priority, due_date)
- TodoClaim model (todo, claimed_by, claimed_at)
- TodoCompletion model (todo, completed_by, completed_at)
- Support for categories/tags
- Unit tests for:
  - Model validation and constraints
  - Priority validation
  - Relationship integrity
  - Category/tag handling
- Integration tests for:
  - Database schema creation and migrations
  - Model relationships and foreign keys
  - Data integrity constraints
- Documentation:
  - Database schema documentation
  - Model relationship diagrams
  - Update README with to-do data model overview
  - Priority levels documentation
  - Code documentation for to-do models

**Deliverables**:
- To-do list database schema
- Database migrations
- Unit test suite
- Integration test suite
- Database schema documentation

#### Task 4.2: To-Do List API
**Scope**: Implement to-do list operations
- API endpoints for:
  - Creating/editing/deleting todos
  - Listing todos (by household, by status, by assignee)
  - Claiming a todo
  - Marking todos as complete
  - Unclaiming todos
- Filtering and sorting options
- Unit tests for:
  - Todo CRUD operations logic
  - Claim/unclaim logic
  - Completion tracking logic
  - Filtering and sorting logic
  - Status transition logic
- Integration tests for:
  - Todo CRUD operations end-to-end
  - Claim/unclaim workflows
  - Completion workflows
  - Filtering and sorting operations
  - Authorization checks
  - Concurrent claim handling
- Documentation:
  - API endpoint documentation (OpenAPI/Swagger)
  - Update README with to-do list examples
  - Filtering and sorting options documentation
  - Code documentation for to-do service logic

**Deliverables**:
- Complete to-do list API
- Claim/completion tracking
- Unit test suite
- Integration test suite
- API documentation updates

### Phase 5: Frontend - Web Application

#### Task 5.1: Web App Foundation
**Scope**: Set up React web application
- Initialize React project (Vite or Create React App)
- Set up routing (React Router)
- Configure API client (Axios or Fetch wrapper)
- Set up authentication flow (login, token storage)
  - **Timezone detection**: Detect user's timezone during registration using `Intl.DateTimeFormat().resolvedOptions().timeZone` and include it in registration request (backend already supports this)
- Basic layout and navigation structure
  - registration page
  - logged in user page with placeholders for navigating to create / view households
- Unit tests for:
  - API client configuration
  - Authentication utilities
  - Route components
  - Navigation logic
- Integration tests for:
  - Authentication flow end-to-end
  - API client error handling
  - Route protection
  - Token storage and retrieval
- Documentation:
  - Project setup guide
  - Architecture overview
  - Update README with web app setup instructions
  - API client usage documentation
  - Authentication flow documentation

**Deliverables**:
- React web application skeleton
- Authentication UI
- Navigation structure
- Unit test suite
- Integration test suite
- Setup and architecture documentation

#### Task 5.2: Household Management UI
**Scope**: Web interface for household operations
- Household list/dashboard
- Create household form
- Household details page
- Member list
  - Transfer ownership screen/flow (select new owner from members, confirm)
  - Remove/kick member action (owners only, confirm)
- Invitation management UI
  - View outstanding invitations (pending, not expired)
  - Send invitation (email + role)
  - Resend invitation
  - Revoke/cancel invitation
  - Accept invitation screen/route (token-based deep link / URL)
- Unit tests for:
  - React components
  - Form validation
  - State management
  - UI interaction logic
- Integration tests for:
  - Household CRUD operations via UI
  - Invitation management workflows
  - Member management workflows
  - Error handling and user feedback
- Documentation:
  - Component documentation
  - Update README with household UI usage
  - User guide for household management
  - UI/UX design decisions

**Deliverables**:
- Complete household management UI
- Unit test suite
- Integration test suite
- User documentation

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
- Unit tests for:
  - Expense form validation
  - Currency conversion UI logic
  - Percentage split calculations
  - Phone number validation UI
  - Component rendering and interactions
- Integration tests for:
  - Expense creation and management workflows
  - Currency conversion UI
  - Payment recording workflows
  - Debt visualization
  - External participant management
- Documentation:
  - Component documentation
  - Update README with expense UI usage
  - User guide for expense management
  - Currency conversion UI guide
  - UI/UX design decisions

**Deliverables**:
- Complete expense management UI
- Currency selection and conversion UI
- Unit test suite
- Integration test suite
- User documentation

#### Task 5.4: Chore Management UI
**Scope**: Web interface for chores
- Chore list view
- Create/edit chore form
- Calendar view for chores
- Assignment interface
- Mark complete functionality
- Overdue/upcoming filters
- Unit tests for:
  - Chore form validation
  - Calendar view logic
  - Filter logic
  - Component rendering
- Integration tests for:
  - Chore management workflows
  - Calendar view interactions
  - Assignment workflows
  - Completion workflows
  - Filtering functionality
- Documentation:
  - Component documentation
  - Update README with chore UI usage
  - User guide for chore management
  - Calendar view documentation
  - UI/UX design decisions

**Deliverables**:
- Complete chore management UI
- Unit test suite
- Integration test suite
- User documentation

#### Task 5.5: To-Do List UI
**Scope**: Web interface for to-do lists
- To-do list view
- Create/edit todo form
- Claim/unclaim functionality
- Mark complete interface
- Filtering and sorting
- Unit tests for:
  - Todo form validation
  - Claim/unclaim logic
  - Filtering and sorting logic
  - Component rendering
- Integration tests for:
  - Todo management workflows
  - Claim/unclaim workflows
  - Completion workflows
  - Filtering and sorting functionality
- Documentation:
  - Component documentation
  - Update README with to-do UI usage
  - User guide for to-do lists
  - UI/UX design decisions

**Deliverables**:
- Complete to-do list UI
- Unit test suite
- Integration test suite
- User documentation

#### Task 5.6: User Settings/Preferences UI
**Scope**: Web interface for user preferences
- Settings page/dashboard
- Currency preferences page/section:
  - Currency preference selector dropdown with all supported currencies (CAD (default), USD, EUR, BBD, BRL)
  - Display current preferred currency
  - Save/update currency preference via API
  - Visual feedback on successful update
- Display currency conversion settings
- Other user preferences (timezone, notifications, etc.)
  - **Timezone detection note**: When implementing timezone-aware features (Task 1.4.1), detect user's timezone using `Intl.DateTimeFormat().resolvedOptions().timeZone` and allow users to override it via timezone selector
- Unit tests for:
  - Settings form validation
  - Preference update logic
  - Component rendering
- Integration tests for:
  - Settings update workflows
  - Preference persistence
  - Currency preference changes
- Documentation:
  - Component documentation
  - Update README with settings UI usage
  - User guide for preferences
  - UI/UX design decisions

**Deliverables**:
- User settings UI
- Currency preference management
- Unit test suite
- Integration test suite
- User documentation

### Phase 6: Frontend - Mobile Application

#### Task 6.1: Mobile App Foundation
**Scope**: Set up React Native (Expo) application
- Initialize Expo project
- Set up navigation (React Navigation)
- Configure API client
- Set up authentication flow
  - **Timezone detection**: Detect user's timezone during registration using `Intl.DateTimeFormat().resolvedOptions().timeZone` (works on both iOS and Android) and include it in registration request (backend already supports this)
- Basic app structure and theming
- Unit tests for:
  - API client configuration
  - Authentication utilities
  - Navigation logic
  - Theme configuration
- Integration tests for:
  - Authentication flow end-to-end
  - API client error handling
  - Route protection
  - Token storage and retrieval
- Documentation:
  - Mobile app setup guide
  - Architecture overview
  - Update README with mobile app setup instructions
  - API client usage documentation
  - Authentication flow documentation

**Deliverables**:
- React Native app skeleton
- Authentication screens
- Navigation structure
- Unit test suite
- Integration test suite
- Setup and architecture documentation

#### Task 6.2: Mobile - Household Management
**Scope**: Mobile UI for household operations
- Household dashboard
- Create/join household screens
- Member list
  - Transfer ownership screen/flow (select new owner from members, confirm)
  - Remove/kick member action (owners only, confirm)
- Invitation management
  - View outstanding invitations (pending, not expired)
  - Send invitation (email + role)
  - Resend invitation
  - Revoke/cancel invitation
  - Accept invitation screen/flow (token-based deep link)
- Unit tests for:
  - React Native components
  - Form validation
  - State management
  - UI interaction logic
- Integration tests for:
  - Household CRUD operations via mobile UI
  - Invitation management workflows
  - Member management workflows
  - Error handling and user feedback
- Documentation:
  - Component documentation
  - Update README with mobile household UI usage
  - User guide for household management
  - Mobile UI/UX design decisions

**Deliverables**:
- Mobile household management screens
- Unit test suite
- Integration test suite
- User documentation

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
- Unit tests for:
  - Expense form validation
  - Currency conversion UI logic
  - Percentage split calculations
  - Phone number validation UI
  - Component rendering and interactions
- Integration tests for:
  - Expense creation and management workflows
  - Currency conversion UI
  - Payment recording workflows
  - Debt visualization
  - External participant management
- Documentation:
  - Component documentation
  - Update README with mobile expense UI usage
  - User guide for expense management
  - Currency conversion UI guide
  - Mobile UI/UX design decisions

**Deliverables**:
- Mobile expense management screens
- Currency selection and conversion UI
- Unit test suite
- Integration test suite
- User documentation

#### Task 6.4: Mobile - Chore Management
**Scope**: Mobile UI for chores
- Chore list screen
- Chore detail and completion
- Calendar view
- Create/edit chore screens
- Unit tests for:
  - Chore form validation
  - Calendar view logic
  - Component rendering
- Integration tests for:
  - Chore management workflows
  - Calendar view interactions
  - Completion workflows
- Documentation:
  - Component documentation
  - Update README with mobile chore UI usage
  - User guide for chore management
  - Mobile UI/UX design decisions

**Deliverables**:
- Mobile chore management screens
- Unit test suite
- Integration test suite
- User documentation

#### Task 6.5: Mobile - To-Do List
**Scope**: Mobile UI for to-do lists
- To-do list screen
- Create/edit todo screens
- Claim and complete functionality
- Unit tests for:
  - Todo form validation
  - Claim/unclaim logic
  - Component rendering
- Integration tests for:
  - Todo management workflows
  - Claim/unclaim workflows
  - Completion workflows
- Documentation:
  - Component documentation
  - Update README with mobile to-do UI usage
  - User guide for to-do lists
  - Mobile UI/UX design decisions

**Deliverables**:
- Mobile to-do list screens
- Unit test suite
- Integration test suite
- User documentation

#### Task 6.6: Mobile - User Settings/Preferences
**Scope**: Mobile UI for user preferences
- Settings screen
- Currency preferences section:
  - Currency preference selector (picker/dropdown) with all supported currencies (CAD (default), USD, EUR, BBD, BRL)
  - Display current preferred currency
  - Save/update currency preference via API
  - Visual feedback on successful update
- Display currency conversion settings
- Other user preferences
  - **Timezone detection note**: When implementing timezone-aware features (Task 1.4.1), detect user's timezone using `Intl.DateTimeFormat().resolvedOptions().timeZone` and allow users to override it via timezone selector
- Unit tests for:
  - Settings form validation
  - Preference update logic
  - Component rendering
- Integration tests for:
  - Settings update workflows
  - Preference persistence
  - Currency preference changes
- Documentation:
  - Component documentation
  - Update README with mobile settings UI usage
  - User guide for preferences
  - Mobile UI/UX design decisions

**Deliverables**:
- Mobile user settings screens
- Currency preference management
- Unit test suite
- Integration test suite
- User documentation

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
- Unit tests for:
  - Platform detection logic
  - Configuration loading for each platform
  - Environment variable normalization
  - Fallback mechanism
  - Database connection string parsing
- Integration tests for:
  - End-to-end configuration loading
  - Platform-specific configuration scenarios
  - Local development compatibility
  - Error handling for missing configurations
- Documentation:
  - Deployment abstraction architecture
  - Platform-specific setup guides
  - Environment variable reference
  - Update README with deployment instructions
  - Migration guide between platforms
  - Code documentation for deployment module

**Deliverables**:
- Deployment abstraction module
- Railway.app configuration support
- Render.com configuration support (optional)
- Platform detection and configuration loading
- Documentation for platform-specific setup
- Unit test suite
- Integration test suite
- Deployment documentation

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
- Unit tests for:
  - Terraform configuration validation
  - Variable validation
  - Resource configuration logic
- Integration tests for:
  - Terraform plan validation
  - Infrastructure provisioning (in test environment)
  - Configuration correctness
- Documentation:
  - Terraform configuration guide
  - Infrastructure architecture documentation
  - Update README with infrastructure setup
  - Deployment procedures
  - Environment variable management guide
  - Code documentation for Terraform modules

**Deliverables**:
- Terraform configuration files
- Infrastructure documentation
- Deployment scripts
- Unit test suite
- Integration test suite
- Infrastructure documentation

#### Task 7.3: CI/CD Pipeline
**Scope**: Set up automated deployment
- GitHub Actions workflows
- Build and test automation
- Docker image building
- Deployment to staging/production
- Database migration automation
- Platform-specific CI/CD configuration (Railway, Render, etc.)
- Unit tests for:
  - CI/CD workflow validation
  - Build script logic
  - Deployment script validation
- Integration tests for:
  - CI/CD pipeline execution (in test environment)
  - Build process validation
  - Deployment process validation
  - Database migration automation
- Documentation:
  - CI/CD pipeline architecture
  - GitHub Actions workflow documentation
  - Update README with CI/CD setup
  - Deployment procedures
  - Troubleshooting guide
  - Code documentation for CI/CD scripts

**Deliverables**:
- CI/CD pipeline configuration
- Automated deployment process
- Platform-specific deployment workflows
- Unit test suite
- Integration test suite
- CI/CD documentation

#### Task 7.4: Production Deployment
**Scope**: Deploy application to production
- Set up production environment on Railway.app (primary platform)
- Configure domain and SSL
- Set up monitoring and logging
- Database backup strategy
- Environment configuration
- Optional: Set up Render.com as backup/secondary platform
- Unit tests for:
  - Production configuration validation
  - Monitoring setup validation
  - Backup script logic
- Integration tests for:
  - Production deployment validation
  - Monitoring and logging verification
  - Backup process validation
  - SSL configuration verification
- Documentation:
  - Production deployment guide
  - Monitoring and logging setup
  - Database backup procedures
  - Update README with production deployment instructions
  - Troubleshooting guide
  - Runbook for common operations
  - Code documentation for production scripts

**Deliverables**:
- Live production application on Railway.app
- Monitoring setup
- Documentation
- Optional: Secondary deployment on Render.com
- Unit test suite
- Integration test suite
- Production deployment documentation

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

### Phase 8: Nice to Have's

#### Task 8.1: Enhanced PII Encryption at Rest (Future/Optional)
**Scope**: Implement application-level encryption for sensitive PII data
- **Database-level encryption**: Leverage PostgreSQL Transparent Data Encryption (TDE) or cloud provider encryption for database at rest
- **Application-level encryption for PII**:
  - Encrypt phone numbers using deterministic encryption (allows searchable queries while protecting data)
  - Encrypt full names using AES-GCM encryption (decrypt on read, not searchable)
  - Keep email addresses plaintext (required for authentication, lookups, and unique constraints)
- **Key Management Service (KMS) integration**:
  - Research and select KMS provider (AWS KMS, HashiCorp Vault, Google Cloud KMS, or Azure Key Vault)
  - Implement key rotation strategy
  - Secure key storage and access control
  - Environment-based key management (development vs production)
- **Implementation considerations**:
  - Performance impact assessment (encryption/decryption overhead)
  - Searchability trade-offs (deterministic vs non-deterministic encryption)
  - Migration strategy for existing plaintext data
  - Backup and recovery procedures for encrypted data
- **Documentation**:
  - Encryption architecture documentation
  - KMS provider selection and setup guide
  - Key rotation procedures
  - Data migration guide for existing users

**Deliverables**:
- Database encryption configuration
- Application-level encryption utilities for phone numbers and names
- KMS integration and key management
- Encryption/decryption service layer
- Migration scripts for existing data
- Documentation and security guidelines

**Note**: This is a future enhancement for enhanced security. For MVP, database-level encryption provided by cloud providers (Railway, Render, AWS, etc.) is sufficient. Application-level encryption adds complexity and should be considered when handling highly sensitive data or meeting specific compliance requirements.

#### Task 8.2: Recurring Expenses with Predetermined Splits
**Scope**: Implement the ability to set up recurring expenses (bills) with a saved split ratio between household members.
- **Data Models**:
  - `RecurringExpense` model (amount_estimate, description, frequency, household, category, currency, status)
  - `RecurringSplit` model (recurring_expense, user, percentage_owed)
- **Recurrence Logic**:
  - Support for monthly, quarterly, yearly, or custom billing cycles
  - Integration with background job system to generate individual `Expense` records on the billing date
- **Split Configuration**:
  - Allow users to "save" a specific split for a recurring bill (e.g., insurance, taxes, utilities)
  - Auto-generate individual expenses with this pre-set split when the billing period triggers
  - Support manual adjustment of the final amount before the expense is finalized if it varies by period
- **Notifications**:
  - Notify household members when a new recurring expense has been generated
- **Unit/Integration Tests**:
  - Validate recurrence scheduling logic
  - Ensure correct split application when generating expenses
- **Documentation**:
  - Update API docs and user guide for recurring expenses

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

