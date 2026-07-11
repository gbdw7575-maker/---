import { motion } from 'framer-motion'
import { InboxOutlined } from '@ant-design/icons'
import { Button } from 'antd'

export default function EmptyState({
  icon = <InboxOutlined style={{ fontSize: 48, color: '#d9d9d9' }} />,
  title = '暂无数据',
  description,
  actionText,
  onAction,
}) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '60px 20px',
        textAlign: 'center',
      }}
    >
      <motion.div
        animate={{ y: [0, -6, 0] }}
        transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
      >
        {icon}
      </motion.div>
      <h3 style={{ margin: '16px 0 8px', fontSize: 16, color: '#333' }}>{title}</h3>
      {description && (
        <p style={{ color: '#999', fontSize: 14, marginBottom: 16, maxWidth: 300 }}>
          {description}
        </p>
      )}
      {actionText && onAction && (
        <Button type="primary" onClick={onAction}>
          {actionText}
        </Button>
      )}
    </motion.div>
  )
}
