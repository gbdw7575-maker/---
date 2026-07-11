import { useState, useEffect, useRef } from 'react'
import {
  Row, Col, Card, List, Button, Input, message, Space, Typography,
  Popconfirm, Avatar, Badge, Upload, Modal,
} from 'antd'
import {
  SendOutlined, PlusOutlined, DeleteOutlined,
  RobotOutlined, UserOutlined, PictureOutlined,
} from '@ant-design/icons'
import { motion, AnimatePresence } from 'framer-motion'
import { chatApi, userApi } from '../../api'
import Loading from '../../components/common/Loading'
import EmptyState from '../../components/common/EmptyState'

const { Text, Title } = Typography
const { TextArea } = Input

export default function ChatView() {
  const [sessions, setSessions] = useState([])
  const [currentSession, setCurrentSession] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [loading, setLoading] = useState(true)
  const [imageBase64, setImageBase64] = useState(null)
  const messagesEndRef = useRef(null)

  useEffect(() => { loadSessions() }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const loadSessions = async () => {
    try {
      const res = await chatApi.listSessions()
      setSessions(res.data)
      if (res.data.length > 0) {
        setCurrentSession(res.data[0])
      }
    } catch {} finally { setLoading(false) }
  }

  const loadMessages = async (sessionId) => {
    try {
      const res = await chatApi.listMessages(sessionId)
      setMessages(res.data)
    } catch {}
  }

  const switchSession = (session) => {
    setCurrentSession(session)
    loadMessages(session.id)
  }

  const createSession = async () => {
    try {
      const userRes = await userApi.getDefault()
      const res = await chatApi.createSession({ user_id: userRes.data.id })
      setSessions(prev => [res.data, ...prev])
      setCurrentSession(res.data)
      setMessages([])
    } catch { message.error('创建会话失败') }
  }

  const deleteSession = async (id) => {
    try {
      await chatApi.deleteSession(id)
      const updated = sessions.filter(s => s.id !== id)
      setSessions(updated)
      if (currentSession?.id === id) {
        setCurrentSession(updated[0] || null)
        setMessages([])
        if (updated[0]) loadMessages(updated[0].id)
      }
    } catch { message.error('删除失败') }
  }

  const handleSend = async () => {
    if (!input.trim() && !imageBase64) return
    if (!currentSession) {
      message.warning('请先创建或选择一个会话')
      return
    }

    const userMsg = input.trim()
    setInput('')
    setSending(true)

    // Optimistic UI
    const tempMsg = { id: Date.now(), role: 'user', content: userMsg }
    setMessages(prev => [...prev, tempMsg])

    try {
      const res = await chatApi.send({
        session_id: currentSession.id,
        message: userMsg,
        image_base64: imageBase64,
      })
      setMessages(prev => [
        ...prev.filter(m => m.id !== tempMsg.id || m.role !== 'user'),
        { id: Date.now(), role: 'user', content: userMsg },
        { id: Date.now() + 1, role: 'assistant', content: res.data.reply },
      ])
      setImageBase64(null)
      // Refresh sessions to update title
      const sessRes = await chatApi.listSessions()
      setSessions(sessRes.data)
    } catch {
      message.error('发送失败')
      setMessages(prev => prev.filter(m => m.id !== tempMsg.id))
    } finally { setSending(false) }
  }

  const handleImageUpload = (file) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      const base64 = e.target.result.split(',')[1]
      setImageBase64(base64)
    }
    reader.readAsDataURL(file)
    return false // prevent upload
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  if (loading) return <Loading fullPage />

  return (
    <div className="page-enter" style={{ height: 'calc(100vh - 100px)' }}>
      <Row gutter={16} style={{ height: '100%' }}>
        {/* Session List */}
        <Col xs={24} md={6}>
          <Card
            title={<span><RobotOutlined /> 会话列表</span>}
            extra={
              <Button type="primary" size="small" icon={<PlusOutlined />} onClick={createSession}>
                新建
              </Button>
            }
            style={{ height: '100%' }}
            bodyStyle={{ padding: 0, overflow: 'auto', maxHeight: 'calc(100% - 56px)' }}
          >
            {sessions.length === 0 ? (
              <EmptyState title="暂无会话" description="点击「新建」开始咨询" />
            ) : (
              <List
                dataSource={sessions}
                renderItem={session => (
                  <List.Item
                    onClick={() => switchSession(session)}
                    style={{
                      cursor: 'pointer',
                      padding: '12px 16px',
                      background: currentSession?.id === session.id ? '#e6f4ff' : 'transparent',
                      borderLeft: currentSession?.id === session.id ? '3px solid #1677ff' : '3px solid transparent',
                      transition: 'all 0.2s',
                    }}
                    actions={[
                      <Popconfirm title="删除会话？" onConfirm={(e) => { e?.stopPropagation(); deleteSession(session.id) }}>
                        <DeleteOutlined
                          style={{ color: '#999' }}
                          onClick={(e) => e.stopPropagation()}
                        />
                      </Popconfirm>,
                    ]}
                  >
                    <List.Item.Meta
                      avatar={<Avatar icon={<RobotOutlined />} style={{ background: '#1677ff' }} />}
                      title={<Text ellipsis style={{ maxWidth: 120 }}>{session.title || '新会话'}</Text>}
                      description={
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          {session.updated_at ? session.updated_at.slice(0, 16).replace('T', ' ') : ''}
                        </Text>
                      }
                    />
                  </List.Item>
                )}
              />
            )}
          </Card>
        </Col>

        {/* Chat Area */}
        <Col xs={24} md={18}>
          <Card
            style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
            bodyStyle={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              padding: 0,
              overflow: 'hidden',
            }}
          >
            {/* Messages */}
            <div style={{
              flex: 1,
              overflow: 'auto',
              padding: 20,
              display: 'flex',
              flexDirection: 'column',
              gap: 12,
            }}>
              {!currentSession ? (
                <EmptyState
                  title="选择或新建会话"
                  description="从左侧选择一个会话，或点击「新建」开始 AI 健康咨询"
                  actionText="新建会话"
                  onAction={createSession}
                />
              ) : messages.length === 0 ? (
                <div style={{
                  flex: 1,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#999',
                }}>
                  <RobotOutlined style={{ fontSize: 48, marginBottom: 16, color: '#d9d9d9' }} />
                  <Text type="secondary">有什么健康问题想咨询吗？</Text>
                </div>
              ) : (
                <AnimatePresence>
                  {messages.map(msg => (
                    <motion.div
                      key={msg.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.2 }}
                      style={{
                        display: 'flex',
                        justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                      }}
                    >
                      <div className={msg.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-ai'}>
                        {msg.content}
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div style={{
              borderTop: '1px solid #f0f0f0',
              padding: '12px 16px',
              background: '#fafafa',
            }}>
              {imageBase64 && (
                <div style={{ marginBottom: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
                  <PictureOutlined style={{ color: '#1677ff' }} />
                  <Text type="secondary" style={{ fontSize: 12 }}>已选择一张图片</Text>
                  <Button size="small" type="link" onClick={() => setImageBase64(null)}>移除</Button>
                </div>
              )}
              <Space.Compact style={{ width: '100%' }}>
                <Upload
                  accept="image/*"
                  showUploadList={false}
                  beforeUpload={handleImageUpload}
                >
                  <Button icon={<PictureOutlined />} />
                </Upload>
                <TextArea
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="输入健康问题... (Enter 发送, Shift+Enter 换行)"
                  autoSize={{ minRows: 1, maxRows: 4 }}
                  style={{ flex: 1 }}
                  disabled={!currentSession}
                />
                <Button
                  type="primary"
                  icon={<SendOutlined />}
                  onClick={handleSend}
                  loading={sending}
                  disabled={!input.trim() && !imageBase64}
                >
                  发送
                </Button>
              </Space.Compact>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  )
}
