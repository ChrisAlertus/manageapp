# Household Management Application

A comprehensive application for managing household expenses, chores, and to-do lists. Supports multiple households with cross-platform access (iOS, Android, Web).

## Features

### 1. Expense Splitting
- Split expenses with household members and external participants
- Custom percentage-based splits
- Track payments and debts
- Debt simplification algorithm (like Splitwise) to minimize transactions
- Support for joint bills with people outside your household

### 2. Chore Management
- Define recurring chores (daily, weekly, monthly)
- Assign chores to specific household members
- Calendar view of upcoming and overdue chores
- Mark completion within time windows
- Track chore history

### 3. Shared To-Do Lists
- Household-wide to-do lists
- Claim and complete tasks
- Prevent duplicate work (e.g., only one person buys milk)
- Persistent task management

### 4. Household Management
- Create and manage multiple households
- Email-based invitations
- Role-based access (owner, member)

## Technology Stack

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **Mobile**: React Native (Expo)
- **Web**: React
- **Infrastructure**: Railway.app / Render.com / AWS
- **Infrastructure as Code**: Terraform

## Project Structure

```
manageapp/
├── PROJECT_PLAN.md          # Detailed project plan with component breakdown
├── terraform/               # Infrastructure configuration
│   ├── main.tf             # Main Terraform configuration
│   ├── variables.tf        # Variable definitions
│   ├── terraform.tfvars.example  # Example variables file
│   └── README.md           # Infrastructure setup guide
├── backend/                # FastAPI backend (to be created)
├── frontend-web/           # React web application (to be created)
├── frontend-mobile/        # React Native mobile app (to be created)
└── README.md              # This file
```

## Getting Started

### 1. Review the Project Plan

Start by reading `PROJECT_PLAN.md` which breaks down the project into manageable component tasks. Each task can be assigned to an agent or worked on independently.

### 2. Choose Your Deployment Platform

Review `terraform/README.md` for infrastructure options:
- **Railway.app** (Recommended for free tier) - Simplest setup
- **Render.com** - Good free tier alternative
- **AWS** - More control, more complex

### 3. Development Workflow

The recommended development order:

1. **Phase 1**: Backend foundation and authentication
2. **Phase 2**: Expense splitting feature
3. **Phase 3**: Chore management feature
4. **Phase 4**: To-do list feature
5. **Phase 5**: Web frontend
6. **Phase 6**: Mobile frontend
7. **Phase 7**: Infrastructure and deployment

### 4. Local Development Setup

(To be created when starting development)

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend Web
cd frontend-web
npm install
npm run dev

# Frontend Mobile
cd frontend-mobile
npm install
npx expo start
```

## Component Tasks

The project is broken down into the following main component tasks (see `PROJECT_PLAN.md` for details):

### Backend Tasks
- Task 1.1: Backend API Foundation
- Task 1.2: Household Management Core
- Task 1.3: Email Invitation System
- Task 2.1-2.4: Expense Splitting (Models, CRUD, Payments, Simplification)
- Task 3.1-3.3: Chore Management (Models, Scheduling, API)
- Task 4.1-4.2: To-Do Lists (Models, API)

### Frontend Tasks
- Task 5.1-5.5: Web Application (Foundation, Households, Expenses, Chores, Todos)
- Task 6.1-6.5: Mobile Application (Foundation, Households, Expenses, Chores, Todos)

### Infrastructure Tasks
- Task 7.1: Infrastructure as Code (Terraform)
- Task 7.2: CI/CD Pipeline
- Task 7.3: Production Deployment

## Database Schema

The application uses PostgreSQL with the following main entities:

- **Users**: User accounts and authentication
- **Households**: Household definitions
- **Household Members**: User-household relationships
- **Expenses**: Expense records with participants
- **Payments**: Payment tracking
- **Chores**: Chore definitions and assignments
- **Todos**: Shared to-do items
- **Invitations**: Email-based household invitations

See `PROJECT_PLAN.md` for detailed schema information.

## Security

- JWT-based authentication
- Household-scoped data access
- Secure invitation tokens
- Environment-based secrets management
- HTTPS/SSL for all traffic

## Free Tier Considerations

The application is designed to work within free tier limits:

- **Database**: 20GB storage (sufficient for thousands of households)
- **Storage**: Minimal (mostly database, no file storage needed)
- **Email**: 100-62,000 emails/month depending on provider
- **Compute**: Sufficient for small to medium usage

## Contributing

This is a personal project, but the structure allows for:
- Independent development of components
- Agent-assisted development
- Modular architecture

## License

 GPL-3.0 license

## Next Steps

1. Review `PROJECT_PLAN.md` to understand the full scope
2. Review `terraform/README.md` to choose deployment platform
3. Start with Task 1.1: Backend API Foundation
4. Set up local development environment
5. Begin implementing features incrementally

