# Frontend Web Application

This is the React web application for the Household Management system. It's built with TypeScript, Vite, Material UI, and React Router.

## Architecture Overview

The frontend follows a simple, modular architecture that's easy to understand and extend:

```
frontend/
├── src/
│   ├── api/              # Backend API communication
│   │   ├── client.ts     # Axios instance with interceptors
│   │   └── auth.ts        # Authentication API functions
│   ├── components/        # Reusable UI components
│   │   ├── MainLayout.tsx      # Main app layout (header, navigation)
│   │   └── ProtectedRoute.tsx # Route protection wrapper
│   ├── pages/            # Main application pages/views
│   │   ├── LoginPage.tsx       # User login
│   │   ├── RegisterPage.tsx   # User registration
│   │   └── DashboardPage.tsx   # Main dashboard
│   ├── stores/           # State management (Zustand)
│   │   └── authStore.ts  # Authentication state
│   ├── theme/            # Material UI theme configuration
│   │   └── index.ts      # Theme setup
│   ├── utils/            # Utility functions
│   │   └── timezone.ts   # Timezone detection
│   ├── test/             # Test setup
│   │   └── setup.ts      # Vitest configuration
│   ├── App.tsx           # Main app component (routing)
│   └── main.tsx          # Application entry point
```

## How It Works

### 1. **API Client** (`src/api/client.ts`)

The API client is a configured Axios instance that:
- Sets the base URL for all API requests
- Automatically adds JWT tokens to requests (from localStorage)
- Handles 401 errors by clearing tokens and redirecting to login

**Usage:**
```typescript
import apiClient from '@/api/client';

// Make a request - token is added automatically
const response = await apiClient.get('/some-endpoint');
```

### 2. **Authentication Store** (`src/stores/authStore.ts`)

The auth store manages all authentication state using Zustand. It's simpler than Redux and uses a straightforward "store" pattern.

**What it does:**
- Keeps track of whether the user is logged in
- Stores user information
- Provides `login()`, `register()`, `logout()`, and `checkAuth()` functions
- Automatically saves/loads state from localStorage

**Usage:**
```typescript
import { useAuthStore } from '@/stores/authStore';

function MyComponent() {
  const { user, isAuthenticated, login, logout } = useAuthStore();

  // Use the state and functions
  if (isAuthenticated) {
    return <div>Hello, {user?.email}</div>;
  }
}
```

### 3. **Routing** (`src/App.tsx`)

The app uses React Router for navigation. Routes are defined in `App.tsx`:

- `/login` - Public login page
- `/register` - Public registration page
- `/` - Protected dashboard (requires authentication)

**Protected Routes:**
The `ProtectedRoute` component wraps routes that require authentication. If the user isn't logged in, they're redirected to `/login`.

### 4. **Pages**

Pages are the main views of the application:

- **LoginPage**: Simple login form
- **RegisterPage**: Registration form with automatic timezone detection
- **DashboardPage**: Main landing page for authenticated users (placeholder for now)

### 5. **Components**

Reusable components:

- **MainLayout**: Provides the standard layout (header, navigation, content area)
- **ProtectedRoute**: Wraps routes that require authentication

## Getting Started

### Prerequisites

- Node.js (v20.15.1 or higher recommended)
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Set up environment variables:
Create a `.env` file in the `frontend/` directory:
```
VITE_API_URL=http://localhost:8000
```

3. Start the development server:
```bash
npm run dev
```

The app will be available at `http://localhost:5173` (or another port if 5173 is busy).

### Building for Production

```bash
npm run build
```

This creates an optimized production build in the `dist/` directory.

## Development Workflow

### Adding a New Page

1. Create a new file in `src/pages/` (e.g., `MyNewPage.tsx`)
2. Add a route in `src/App.tsx`:
```typescript
<Route path="/my-page" element={<MyNewPage />} />
```

### Adding a New API Endpoint

1. Add a function in the appropriate file in `src/api/` (or create a new file)
2. Use `apiClient` to make requests:
```typescript
export const myNewFunction = async (data: MyDataType) => {
  const response = await apiClient.post('/my-endpoint', data);
  return response.data;
};
```

### Adding State Management

For simple state, you can use React's `useState`. For shared state across components, create a new Zustand store in `src/stores/`:

```typescript
import { create } from 'zustand';

export const useMyStore = create((set) => ({
  data: null,
  setData: (data) => set({ data }),
}));
```

## Testing

Tests are written using Vitest and React Testing Library.

Run tests:
```bash
npm test
```

Run tests in watch mode:
```bash
npm test -- --watch
```

Run tests with UI:
```bash
npm run test:ui
```

## Key Concepts for Beginners

### 1. **Components**

Components are reusable pieces of UI. They're just functions that return JSX (HTML-like syntax):

```typescript
function MyComponent() {
  return <div>Hello World</div>;
}
```

### 2. **State**

State is data that can change. When state changes, React automatically re-renders the component:

```typescript
const [count, setCount] = useState(0);
// count is the value, setCount is the function to change it
```

### 3. **Props**

Props are data passed from a parent component to a child:

```typescript
function Child({ name }: { name: string }) {
  return <div>Hello, {name}</div>;
}

function Parent() {
  return <Child name="Alice" />;
}
```

### 4. **Hooks**

Hooks are special functions that let you use React features. Common ones:
- `useState` - for component state
- `useEffect` - for side effects (API calls, subscriptions, etc.)
- `useNavigate` - for programmatic navigation

### 5. **Async/Await**

For API calls and other asynchronous operations:

```typescript
async function fetchData() {
  try {
    const data = await apiClient.get('/endpoint');
    console.log(data);
  } catch (error) {
    console.error('Error:', error);
  }
}
```

## Common Patterns

### Making an API Call

```typescript
import apiClient from '@/api/client';

async function getData() {
  const response = await apiClient.get('/endpoint');
  return response.data;
}
```

### Using the Auth Store

```typescript
import { useAuthStore } from '@/stores/authStore';

function MyComponent() {
  const { user, login, logout } = useAuthStore();

  const handleLogin = async () => {
    try {
      await login({ email: 'user@example.com', password: 'password' });
      // User is now logged in
    } catch (error) {
      // Handle error
    }
  };
}
```

### Navigation

```typescript
import { useNavigate } from 'react-router-dom';

function MyComponent() {
  const navigate = useNavigate();

  const goToPage = () => {
    navigate('/some-page');
  };
}
```

## Troubleshooting

### "Cannot find module '@/...'"

Make sure your import uses the `@/` alias:
```typescript
import { something } from '@/api/client'; // ✅ Correct
import { something } from './api/client'; // ❌ Wrong (but also works)
```

### "401 Unauthorized" errors

This usually means:
1. Your token expired - try logging in again
2. The backend isn't running - make sure it's running on the port specified in `.env`

### CORS errors

Make sure the backend CORS settings allow requests from `http://localhost:5173` (or whatever port Vite is using).

## Next Steps

As you build out more features, you'll likely want to:

1. Add more pages (households, expenses, chores, todos)
2. Create more API functions in `src/api/`
3. Add more Zustand stores for complex state
4. Create reusable UI components in `src/components/`
5. Add more tests as you add features

## Resources

- [React Documentation](https://react.dev)
- [React Router Documentation](https://reactrouter.com)
- [Material UI Documentation](https://mui.com)
- [Zustand Documentation](https://zustand-demo.pmnd.rs)
- [Vite Documentation](https://vitejs.dev)
