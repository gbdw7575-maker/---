import { useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu } from 'antd'
import {
  DashboardOutlined,
  HeartOutlined,
  MessageOutlined,
  FileTextOutlined,
  UserOutlined,
  SafetyCertificateOutlined,
  MedicineBoxOutlined,
} from '@ant-design/icons'
import { motion } from 'framer-motion'

const { Sider } = Layout

const menuItems = [
  { key: '/',           icon: <DashboardOutlined />,          label: '工作台' },
  { key: '/health',     icon: <HeartOutlined />,              label: '健康指标' },
  { key: '/assessment', icon: <SafetyCertificateOutlined />,  label: '风险评估' },
  { key: '/chat',       icon: <MessageOutlined />,            label: 'AI 咨询' },
  { key: '/ocr',        icon: <FileTextOutlined />,           label: '报告识别' },
  { key: '/classify',   icon: <MedicineBoxOutlined />,        label: '影像分类' },
  { key: '/profile',    icon: <UserOutlined />,               label: '个人档案' },
]

export default function Sidebar({ collapsed, onCollapse, compact = false }) {
  const navigate = useNavigate()
  const location = useLocation()

  return (
    <Sider
      collapsible={!compact}
      collapsed={collapsed}
      onCollapse={onCollapse}
      width={220}
      collapsedWidth={64}
      style={{
        borderRight: '1px solid #f0f0f0',
        height: '100vh',
        position: 'fixed',
        left: 0,
        top: 0,
        bottom: 0,
        zIndex: 100,
        background: '#fff',
      }}
    >
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
        style={{
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderBottom: '1px solid #f0f0f0',
        }}
      >
        <span
          className="gradient-text"
          style={{
            fontSize: collapsed ? 18 : 18,
            fontWeight: 700,
            whiteSpace: 'nowrap',
            overflow: 'hidden',
          }}
        >
          {collapsed ? '♥' : '♥ 健康管理'}
        </span>
      </motion.div>

      <Menu
        mode="inline"
        selectedKeys={[location.pathname]}
        items={menuItems}
        onClick={({ key }) => navigate(key)}
        style={{ borderRight: 'none', marginTop: 4 }}
      />
    </Sider>
  )
}
