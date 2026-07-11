import { useEffect, useState } from 'react'
import { Layout as AntLayout } from 'antd'
import { useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import Sidebar from './Sidebar'
import Header from './Header'

const { Content } = AntLayout

export default function AppLayout({ children }) {
  const [collapsed, setCollapsed] = useState(false)
  const [isMobile, setIsMobile] = useState(() => window.matchMedia('(max-width: 767px)').matches)
  const location = useLocation()
  const sidebarCollapsed = isMobile || collapsed

  useEffect(() => {
    const query = window.matchMedia('(max-width: 767px)')
    const handleChange = event => setIsMobile(event.matches)
    query.addEventListener('change', handleChange)
    return () => query.removeEventListener('change', handleChange)
  }, [])

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Sidebar collapsed={sidebarCollapsed} onCollapse={setCollapsed} compact={isMobile} />

      <AntLayout style={{
        marginLeft: sidebarCollapsed ? 64 : 220,
        transition: 'margin-left 0.2s',
        minWidth: 0,
      }}>
        <Header compact={isMobile} />

        <Content style={{ padding: isMobile ? 12 : 24, minHeight: 'calc(100vh - 56px)' }}>
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -16 }}
              transition={{ duration: 0.25, ease: 'easeOut' }}
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </Content>
      </AntLayout>
    </AntLayout>
  )
}
