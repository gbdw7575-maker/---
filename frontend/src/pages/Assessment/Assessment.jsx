import { useState, useEffect } from 'react'
import {
  Card, Row, Col, Tag, List, Typography, Progress, Spin, Divider, Alert,
} from 'antd'
import {
  SafetyCertificateOutlined, WarningOutlined,
  CheckCircleOutlined, RiseOutlined,
} from '@ant-design/icons'
import { motion } from 'framer-motion'
import { healthApi } from '../../api'
import EmptyState from '../../components/common/EmptyState'

const { Text, Title } = Typography

const categoryConfig = {
  blood_sugar: { icon: '🩸', color: '#1677ff', order: 1 },
  blood_pressure: { icon: '❤️', color: '#ff4d4f', order: 2 },
  blood_fat: { icon: '🧪', color: '#faad14', order: 3 },
  liver: { icon: '🫁', color: '#52c41a', order: 4 },
  kidney: { icon: '🫘', color: '#722ed1', order: 5 },
  blood_routine: { icon: '🔬', color: '#13c2c2', order: 6 },
}

export default function Assessment() {
  const [loading, setLoading] = useState(true)
  const [risk, setRisk] = useState(null)
  const [indicators, setIndicators] = useState([])

  useEffect(() => {
    Promise.all([
      healthApi.riskSummary(),
      healthApi.list(),
    ]).then(([riskRes, indRes]) => {
      setRisk(riskRes.data)
      setIndicators(indRes.data)
    }).catch(() => {}).finally(() => setLoading(false))
  }, [])

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '120px auto' }} />

  if (!risk || indicators.length === 0) {
    return (
      <div className="page-enter">
        <EmptyState
          icon={<SafetyCertificateOutlined style={{ fontSize: 48, color: '#d9d9d9' }} />}
          title="暂无评估数据"
          description="请先添加健康指标，系统将自动进行风险评估"
        />
      </div>
    )
  }

  const abnormalCount = risk.abnormal_count || 0
  const totalCount = risk.total_count || 1
  const healthScore = Math.round((1 - abnormalCount / totalCount) * 100)

  return (
    <div className="page-enter">
      {/* Health Score */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
      >
        <Card style={{ textAlign: 'center', marginBottom: 16 }}>
          <Title level={4}><SafetyCertificateOutlined /> 健康评分</Title>
          <Progress
            type="dashboard"
            percent={healthScore}
            strokeColor={{
              '0%': healthScore >= 80 ? '#52c41a' : healthScore >= 60 ? '#faad14' : '#ff4d4f',
              '100%': healthScore >= 80 ? '#73d13d' : healthScore >= 60 ? '#ffc53d' : '#ff7875',
            }}
            size={120}
            format={pct => (
              <div>
                <div style={{ fontSize: 28, fontWeight: 700 }}>{pct}</div>
                <div style={{ fontSize: 12 }}>分</div>
              </div>
            )}
          />
          <div style={{ marginTop: 8 }}>
            <Tag
              color={healthScore >= 80 ? 'green' : healthScore >= 60 ? 'orange' : 'red'}
              style={{ fontSize: 14, padding: '2px 16px', borderRadius: 20 }}
            >
              {healthScore >= 80 ? '良好' : healthScore >= 60 ? '需关注' : '警告'}
            </Tag>
          </div>
          <Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
            {totalCount} 项指标中 {risk.normal_count || 0} 项正常，{abnormalCount} 项异常，
            {risk.high_risk_count || 0} 项高风险
          </Text>
        </Card>
      </motion.div>

      {/* Risk by Category */}
      <Row gutter={[16, 16]}>
        {risk.categories && Object.entries(risk.categories)
          .sort((a, b) => (categoryConfig[a[0]]?.order || 99) - (categoryConfig[b[0]]?.order || 99))
          .map(([key, cat], idx) => {
            const config = categoryConfig[key] || { icon: '📊', color: '#999' }
            const catTotal = indicators.filter(i => i.category === key)
            const catAbnormal = catTotal.filter(i => i.status && i.status.includes('abnormal'))
            const isGood = cat.high === 0 && cat.medium === 0

            return (
              <Col xs={24} sm={12} lg={8} key={key}>
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.08 }}
                >
                  <Card
                    className="hover-lift"
                    style={{ borderLeft: `3px solid ${config.color}` }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Space>
                        <span style={{ fontSize: 20 }}>{config.icon}</span>
                        <Text strong style={{ fontSize: 15 }}>{cat.name}</Text>
                      </Space>
                      <Tag color={isGood ? 'green' : 'orange'}>
                        {isGood ? '正常' : '需关注'}
                      </Tag>
                    </div>

                    <div style={{ marginTop: 12 }}>
                      <Row gutter={8}>
                        <Col span={8} style={{ textAlign: 'center' }}>
                          <div style={{ fontSize: 20, fontWeight: 700, color: '#52c41a' }}>{cat.normal}</div>
                          <div style={{ fontSize: 12, color: '#999' }}>正常</div>
                        </Col>
                        <Col span={8} style={{ textAlign: 'center' }}>
                          <div style={{ fontSize: 20, fontWeight: 700, color: '#faad14' }}>{cat.medium}</div>
                          <div style={{ fontSize: 12, color: '#999' }}>中等风险</div>
                        </Col>
                        <Col span={8} style={{ textAlign: 'center' }}>
                          <div style={{ fontSize: 20, fontWeight: 700, color: '#ff4d4f' }}>{cat.high}</div>
                          <div style={{ fontSize: 12, color: '#999' }}>高风险</div>
                        </Col>
                      </Row>
                    </div>

                    {catAbnormal.length > 0 && (
                      <>
                        <Divider style={{ margin: '8px 0' }} />
                        <div>
                          {catAbnormal.slice(0, 3).map(ind => (
                            <div key={ind.id} style={{
                              display: 'flex',
                              justifyContent: 'space-between',
                              padding: '4px 0',
                              fontSize: 13,
                            }}>
                              <span>{ind.name}</span>
                              <Space>
                                <Text strong>{ind.value}{ind.unit}</Text>
                                <Tag
                                  color={ind.risk_level === 'high' ? 'red' : ind.risk_level === 'medium' ? 'orange' : 'green'}
                                  style={{ fontSize: 11 }}
                                >
                                  {ind.risk_level === 'high' ? '高风险' : ind.risk_level === 'medium' ? '中风险' : '低风险'}
                                </Tag>
                              </Space>
                            </div>
                          ))}
                          {catAbnormal.length > 3 && (
                            <Text type="secondary" style={{ fontSize: 12 }}>
                              ...还有 {catAbnormal.length - 3} 项异常
                            </Text>
                          )}
                        </div>
                      </>
                    )}
                  </Card>
                </motion.div>
              </Col>
            )
          })}
      </Row>
    </div>
  )
}
