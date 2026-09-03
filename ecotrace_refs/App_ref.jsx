import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

// Pages
import Home from './pages/Home';
import LoginPage from './pages/auth/LoginPage';
import RegisterPage from './pages/auth/RegisterPage';

// Dashboards
import ParticulierDashboard from './pages/particulier/ParticulierDashboard';
import EntrepriseDashboard from './pages/entreprise/EntrepriseDashboard';
import TransporteurDashboard from './pages/transporteur/TransporteurDashboard';
import ResponsableLogistiqueDashboard from './pages/responsable-logistique/ResponsableLogistiqueDashboard';
import TechnicienDashboard from './pages/technicien/TechnicienDashboard';
import AdministrateurDashboard from './pages/administrateur/AdministrateurDashboard';

import './App.css';

// Composant pour protéger les routes authentifiées
const ProtectedRoute = ({ children, requiredRole = null }) => {
  const token = localStorage.getItem('accessToken');
  const userRole = localStorage.getItem('userRole');

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  if (requiredRole && userRole !== requiredRole) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

// Composant pour rediriger vers le bon dashboard selon le rôle
const DashboardRedirect = () => {
  const userRole = localStorage.getItem('userRole');

  switch (userRole) {
    case 'PARTICULIER':
      return <Navigate to="/dashboard/particulier" replace />;
    case 'ENTREPRISE':
      return <Navigate to="/dashboard/entreprise" replace />;
    case 'TRANSPORTEUR':
      return <Navigate to="/dashboard/transporteur" replace />;
    case 'TECHNICIEN':
      return <Navigate to="/dashboard/technicien" replace />;
    case 'ADMINISTRATEUR':
      return <Navigate to="/dashboard/administrateur" replace />;
    case 'RESPONSABLE_LOGISTIQUE':
      return <Navigate to="/dashboard/responsable-logistique" replace />;
    default:
      return <Navigate to="/login" replace />;
  }
};

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          {/* Routes publiques */}
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Redirection automatique vers le bon dashboard */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardRedirect />
              </ProtectedRoute>
            }
          />

          {/* Dashboards spécifiques par rôle */}
          <Route
            path="/dashboard/particulier"
            element={
              <ProtectedRoute requiredRole="PARTICULIER">
                <ParticulierDashboard />
              </ProtectedRoute>
            }
          />

          <Route
            path="/dashboard/entreprise"
            element={
              <ProtectedRoute requiredRole="ENTREPRISE">
                <EntrepriseDashboard />
              </ProtectedRoute>
            }
          />

          <Route
            path="/dashboard/transporteur"
            element={
              <ProtectedRoute requiredRole="TRANSPORTEUR">
                <TransporteurDashboard />
              </ProtectedRoute>
            }
          />

          <Route
            path="/dashboard/responsable-logistique"
            element={
              <ProtectedRoute requiredRole="RESPONSABLE_LOGISTIQUE">
                <ResponsableLogistiqueDashboard />
              </ProtectedRoute>
            }
          />

          <Route 
            path="/dashboard/technicien" 
            element={
              <ProtectedRoute requiredRole="TECHNICIEN">
                <TechnicienDashboard />
              </ProtectedRoute>
            } 
          />

          <Route 
            path="/dashboard/administrateur" 
            element={
              <ProtectedRoute requiredRole="ADMINISTRATEUR">
                <AdministrateurDashboard />
              </ProtectedRoute>
            } 
          />




          {/* Route par défaut - redirection */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;