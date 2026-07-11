import { Layout, Typography, Tag } from 'antd'
import { ClockCircleOutlined } from '@ant-design/icons'
import { useState, useEffect } from 'react'

const { Header: AntHeader } = Layout

export default function Header() {
  const [time, setTime] = useState(new Date())

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  return (
    <AntHeader
      className="glass"
      style={{
        height: 56,
        lineHeight: '56px',
        padding: '0 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'flex-end',
        borderBottom: '1px solid rgba(0,0,0,0.06)',
        position: 'sticky',
        top: 0,
        zIndex: 99,
      }}
    >
      <Tag icon={<ClockCircleOutlined />} color="default" style={{ marginRight: 0 }}>
        {time.toLocaleString('zh-CN', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: false,
        })}
      </Tag>
    </AntHeader>
  )
}
