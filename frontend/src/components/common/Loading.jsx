import { Spin } from 'antd'
import { motion } from 'framer-motion'

export default function Loading({ text = '加载中...', fullPage = false }) {
  const content = (
    <motion.div
      className="loading-container"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 16,
        padding: 48,
      }}
    >
      <Spin size="large" />
      <span style={{ color: '#666', fontSize: 14 }}>{text}</span>
    </motion.div>
  )

  if (fullPage) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '60vh',
      }}>
        {content}
      </div>
    )
  }
  return content
}
