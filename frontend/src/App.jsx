import { Routes, Route, Navigate } from 'react-router-dom'
import { ConfigProvider, theme } from 'antd'
import AppLayout from './components/Layout/Layout'
import ErrorBoundary from './components/common/ErrorBoundary'
import Dashboard from './pages/Dashboard/Dashboard'
import HealthDashboard from './pages/Health/HealthDashboard'
import Assessment from './pages/Assessment/Assessment'
import ChatView from './pages/Chat/ChatView'
import OCRUpload from './pages/OCR/OCRUpload'
import ImageClassify from './pages/Classify/ImageClassify'
import UserProfile from './pages/Profile/UserProfile'

export default function App() {
  return (
    <ErrorBoundary>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/health" element={<HealthDashboard />} />
          <Route path="/assessment" element={<Assessment />} />
          <Route path="/chat" element={<ChatView />} />
          <Route path="/ocr" element={<OCRUpload />} />
          <Route path="/classify" element={<ImageClassify />} />
          <Route path="/profile" element={<UserProfile />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppLayout>
    </ErrorBoundary>
  )
}
