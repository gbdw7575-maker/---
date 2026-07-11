import { useState, useEffect } from 'react'
import {
  Card, Form, Input, InputNumber, Select, Button, Row, Col,
  message, Descriptions, Tag, Divider, Typography, Space,
} from 'antd'
import {
  UserOutlined, SaveOutlined, ReloadOutlined,
  HeartOutlined, ManOutlined, WomanOutlined,
} from '@ant-design/icons'
import { motion } from 'framer-motion'
import { userApi } from '../../api'
import Loading from '../../components/common/Loading'

const { Title, Text } = Typography

export default function UserProfile() {
  const [form] = Form.useForm()
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => { loadUser() }, [])

  const loadUser = async () => {
    setLoading(true)
    try {
      const res = await userApi.getDefault()
      setUser(res.data)
      form.setFieldsValue(res.data)
    } catch {
      message.error('加载用户信息失败')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    try {
      const values = await form.validateFields()
      setSaving(true)
      const res = await userApi.update(user.id, values)
      setUser(res.data)
      message.success('保存成功')
    } catch (err) {
      if (err.errorFields) return
      message.error('保存失败')
    } finally {
      setSaving(false)
    }
  }

  const handleClear = async () => {
    try {
      const res = await userApi.update(user.id, {
        name: null, age: null, gender: null,
        height: null, weight: null, phone: null, medical_history: null,
      })
      setUser(res.data)
      form.resetFields()
      message.success('已清空所有字段')
    } catch {
      message.error('操作失败')
    }
  }

  if (loading) return <Loading fullPage />

  return (
    <div className="page-enter">
      <Row gutter={[16, 16]}>
        {/* Profile Form */}
        <Col xs={24} md={14}>
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
          >
            <Card
              title={<span><UserOutlined /> 个人信息</span>}
              extra={
                <Space>
                  <Button icon={<ReloadOutlined />} onClick={loadUser}>重置</Button>
                  <Button danger onClick={handleClear}>清空</Button>
                </Space>
              }
            >
              <Form form={form} layout="vertical" onFinish={handleSave}>
                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item name="name" label="姓名">
                      <Input placeholder="请输入姓名" prefix={<UserOutlined />} />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item name="age" label="年龄">
                      <InputNumber
                        min={0}
                        max={150}
                        style={{ width: '100%' }}
                        placeholder="请输入年龄"
                      />
                    </Form.Item>
                  </Col>
                </Row>

                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item name="gender" label="性别">
                      <Select placeholder="请选择性别" allowClear>
                        <Select.Option value="男"><ManOutlined /> 男</Select.Option>
                        <Select.Option value="女"><WomanOutlined /> 女</Select.Option>
                      </Select>
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item name="phone" label="手机号">
                      <Input placeholder="请输入手机号" />
                    </Form.Item>
                  </Col>
                </Row>

                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item name="height" label="身高 (cm)">
                      <InputNumber min={0} max={300} style={{ width: '100%' }} placeholder="cm" />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item name="weight" label="体重 (kg)">
                      <InputNumber min={0} max={500} style={{ width: '100%' }} placeholder="kg" />
                    </Form.Item>
                  </Col>
                </Row>

                <Form.Item name="medical_history" label="病史">
                  <Input.TextArea rows={3} placeholder="如有慢性病史请在此说明" />
                </Form.Item>

                <Form.Item>
                  <Button
                    type="primary"
                    htmlType="submit"
                    icon={<SaveOutlined />}
                    loading={saving}
                    size="large"
                    block
                  >
                    保存信息
                  </Button>
                </Form.Item>
              </Form>
            </Card>
          </motion.div>
        </Col>

        {/* Profile Summary */}
        <Col xs={24} md={10}>
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
          >
            <Card title={<span><HeartOutlined /> 健康摘要</span>}>
              <div style={{
                textAlign: 'center',
                padding: '20px 0',
              }}>
                <motion.div
                  animate={{ scale: [1, 1.05, 1] }}
                  transition={{ duration: 3, repeat: Infinity }}
                  style={{
                    width: 100,
                    height: 100,
                    borderRadius: '50%',
                    background: 'linear-gradient(135deg, #1677ff, #36cfc9)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto 16px',
                    fontSize: 40,
                    color: '#fff',
                    boxShadow: '0 4px 20px rgba(22,119,255,0.3)',
                  }}
                >
                  {user.gender === '男' ? '👨' : user.gender === '女' ? '👩' : '😊'}
                </motion.div>

                <Title level={4} style={{ margin: 0 }}>
                  {user.name || '未设置姓名'}
                </Title>
                <Text type="secondary">
                  {user.age ? `${user.age}岁` : ''}
                  {user.gender ? ` · ${user.gender}` : ''}
                </Text>
              </div>

              <Divider style={{ margin: '12px 0' }} />

              <Descriptions column={1} size="small" bordered>
                <Descriptions.Item label="身高">
                  {user.height ? `${user.height} cm` : <Text type="secondary">未设置</Text>}
                </Descriptions.Item>
                <Descriptions.Item label="体重">
                  {user.weight ? `${user.weight} kg` : <Text type="secondary">未设置</Text>}
                </Descriptions.Item>
                <Descriptions.Item label="BMI">
                  {user.bmi ? (
                    <Space>
                      <Text strong>{user.bmi}</Text>
                      <Tag color={
                        user.bmi < 18.5 ? 'orange' :
                        user.bmi < 24 ? 'green' :
                        user.bmi < 28 ? 'orange' : 'red'
                      }>
                        {user.bmi < 18.5 ? '偏瘦' :
                         user.bmi < 24 ? '正常' :
                         user.bmi < 28 ? '偏胖' : '肥胖'}
                      </Tag>
                    </Space>
                  ) : (
                    <Text type="secondary">需填写身高体重</Text>
                  )}
                </Descriptions.Item>
                <Descriptions.Item label="手机号">
                  {user.phone || <Text type="secondary">未设置</Text>}
                </Descriptions.Item>
                <Descriptions.Item label="病史">
                  {user.medical_history || <Text type="secondary">无</Text>}
                </Descriptions.Item>
              </Descriptions>
            </Card>

            {/* Quick Tips */}
            <Card style={{ marginTop: 16 }}>
              <div className="stagger-children">
                <Text strong>💡 小贴士</Text>
                <ul style={{ marginTop: 8, color: '#666', fontSize: 13, lineHeight: 2 }}>
                  <li>填写身高体重后会自动计算 BMI</li>
                  <li>上传体检报告时会自动提取年龄和性别</li>
                  <li>病史信息会纳入 AI 健康分析</li>
                </ul>
              </div>
            </Card>
          </motion.div>
        </Col>
      </Row>
    </div>
  )
}
