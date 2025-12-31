/**
 * Main App Component
 *
 * This is the root component that sets up routing for the entire application.
 * It defines all the routes and which components to show for each URL.
 */

import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { useEffect } from 'react';
import { MainLayout } from './components/MainLayout';
import { ProtectedRoute } from './components/ProtectedRoute';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { DashboardPage } from './pages/DashboardPage';
import { HouseholdListPage } from './pages/HouseholdListPage';
import { CreateHouseholdPage } from './pages/CreateHouseholdPage';
import { HouseholdDetailsPage } from './pages/HouseholdDetailsPage';
import { AcceptInvitationPage } from './pages/AcceptInvitationPage';
import { useAuthStore } from './stores/authStore';

/**
 * App - Main application component with routing
 *
 * Routes:
 * - /login - Login page (public)
 * - /register - Registration page (public)
 * - / - Dashboard (protected, requires login)
 */
function App() {
  const { checkAuth, isAuthenticated } = useAuthStore();

  // Check if user is authenticated when app loads
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route
          path="/login"
          element={
            // If already logged in, redirect to dashboard
            isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />
          }
        />
        <Route
          path="/register"
          element={
            // If already logged in, redirect to dashboard
            isAuthenticated ? <Navigate to="/" replace /> : <RegisterPage />
          }
        />

        {/* Protected routes - require authentication */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <MainLayout>
                <DashboardPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/households"
          element={
            <ProtectedRoute>
              <MainLayout>
                <HouseholdListPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/households/new"
          element={
            <ProtectedRoute>
              <MainLayout>
                <CreateHouseholdPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/households/:id"
          element={
            <ProtectedRoute>
              <MainLayout>
                <HouseholdDetailsPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/invitations/accept"
          element={
            <ProtectedRoute>
              <MainLayout>
                <AcceptInvitationPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />

        {/* Catch-all: redirect to home if route not found */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
