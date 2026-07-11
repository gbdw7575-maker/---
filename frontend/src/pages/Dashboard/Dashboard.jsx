import { useState, useEffect } from 'react'
import { Row, Col, Card, Statistic, Tag, List, Typography, Button, Spin, Alert } from 'antd'
import {
  HeartOutlined,
  RiseOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  RobotOutlined,
  ArrowRightOutlined,
} from '@ant-design/icons'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { healthApi, userApi } from '../../api'
import ReactEChartsCore from 'echarts-for-react'

const { Text, Title } = Typography

export default function Dashboard() {
  const [loading, setLoading] = useState(true)
  const [user, setUser] = useState(null)
  const [indicators, setIndicators] = useState([])
  const [risk, setRisk] = useState(null)
  const [suggestions, setSuggestions] = useState(null)
  const [aiAnalysis, setAiAnalysis] = useState(null)
  const [aiLoading, setAiLoading] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [userRes, indRes, riskRes, sugRes] = await Promise.all([
        userApi.getDefault(),
        healthApi.list(),
        healthApi.riskSummary(),
        healthApi.suggestions(),
      ])
      setUser(userRes.data)
      setIndicators(indRes.data)
      setRisk(riskRes.data)
      setSuggestions(sugRes.data)
    } catch (err) {
      console.error('Failed to load dashboard data:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleAiAnalyze = async () => {
    setAiLoading(true)
    try {
      const res = await healthApi.aiAnalyze()
      setAiAnalysis(res.data)
    } catch {
      // AI unavailable
    } finally {
      setAiLoading(false)
    }
  }

  // ── Charts ──
  const categoryChartOption = {
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, textStyle: { fontSize: 12 } },
    series: [{
      type: 'pie',
      radius: ['45%', '70%'],
      center: ['50%', '45%'],
      avoidLabelOverlap: false,
      label: { show: false },
      emphasis: {
        label: { show: true, fontSize: 14, fontWeight: 'bold' },
        itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.2)' },
      },
      data: risk?.categories
        ? Object.entries(risk.categories).map(([key, val]) => ({
            name: val.name,
            value: val.total,
          }))
        : [],
      itemStyle: {
        borderRadius: 6,
        borderColor: '#fff',
        borderWidth: 2,
      },
      color: ['#1677ff', '#52c41a', '#faad14', '#ff4d4f', '#722ed1', '#13c2c2'],
    }],
  }

  // ── Risk level helper ──
  const riskLevelInfo = {
    low:    { color: '#52c41a', text: '低风险', icon: <CheckCircleOutlined /> },
    medium: { color: '#faad14', text: '中等风险', icon: <WarningOutlined /> },
    high:   { color: '#ff4d4f', text: '高风险', icon: <RiseOutlined /> },
  }

  const categories = [
    {
      key: 'blood_sugar',
      title: '血糖',
      icon: '🩸',
      color: '#1677ff',
      indicator: indicators.filter(i => i.category === 'blood_sugar'),
    },
    {
      key: 'blood_pressure',
      title: '血压',
      icon: '❤️',
      color: '#ff4d4f',
      indicator: indicators.filter(i => i.category === 'blood_pressure'),
    },
    {
      key: 'blood_fat',
      title: '血脂',
      icon: '🧪',
      color: '#faad14',
      indicator: indicators.filter(i => i.category === 'blood_fat'),
    },
    {
      key: 'liver',
      title: '肝功能',
      icon: '🫁',
      color: '#52c41a',
      indicator: indicators.filter(i => i.category === 'liver'),
    },
    {
      key: 'kidney',
      title: '肾功能',
      icon: '🫘',
      color: '#722ed1',
      indicator: indicators.filter(i => i.category === 'kidney'),
    },
    {
      key: 'blood_routine',
      title: '血常规',
      icon: '🔬',
      color: '#13c2c2',
      indicator: indicators.filter(i => i.category === 'blood_routine'),
    },
  ]

  if (loading) {
    return <Spin size="large" style={{ display: 'block', margin: '120px auto' }} />
  }

  const riskInfo = riskLevelInfo[risk?.overall_risk] || riskLevelInfo.low

  return (
    <div className="page-enter">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <Title level={4} style={{ marginBottom: 4 }}>
          👋 欢迎回来{user?.name ? `，${user.name}` : ''}
        </Title>
        <Text type="secondary" style={{ fontSize: 14 }}>
          这是您的健康概览，所有数据一目了然
        </Text>
      </motion.div>

      {/* Metric Cards */}
      <Row gutter={[16, 16]} style={{ marginTop: 20 }} className="stagger-children">
        <Col xs={12} sm={6}>
          <motion.div whileHover={{ y: -4 }} className="metric-card">
            <div className="value" style={{ color: '#1677ff' }}>{indicators.length}</div>
            <div className="label">📊 指标总数</div>
          </motion.div>
        </Col>
        <Col xs={12} sm={6}>
          <motion.div whileHover={{ y: -4 }} className="metric-card">
            <div className="value" style={{ color: '#52c41a' }}>{risk?.normal_count || 0}</div>
            <div className="label">✅ 正常指标</div>
          </motion.div>
        </Col>
        <Col xs={12} sm={6}>
          <motion.div whileHover={{ y: -4 }} className="metric-card">
            <div className="value" style={{ color: '#faad14' }}>{risk?.abnormal_count || 0}</div>
            <div className="label">⚠️ 异常指标</div>
          </motion.div>
        </Col>
        <Col xs={12} sm={6}>
          <motion.div whileHover={{ y: -4 }} className="metric-card">
            <div className="value" style={{ color: riskInfo.color }}>{risk?.high_risk_count || 0}</div>
            <div className="label">🚨 高风险</div>
          </motion.div>
        </Col>
      </Row>

      {/* Risk & Chart Row */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        {/* Overall Risk */}
        <Col xs={24} md={8}>
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2, duration: 0.4 }}
          >
            <Card
              title={<span><HeartOutlined /> 整体风险评估</span>}
              className="hover-lift"
            >
              <div style={{
                textAlign: 'center',
                padding: '12px 0',
              }}>
                <div style={{
                  width: 80,
                  height: 80,
                  borderRadius: '50%',
                  background: riskInfo.color + '18',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto 12px',
                  fontSize: 36,
                  color: riskInfo.color,
                  border: `2px solid ${riskInfo.color}40`,
                }}>
                  {riskInfo.icon}
                </div>
                <Tag color={riskInfo.color} style={{ fontSize: 16, padding: '4px 20px', borderRadius: 20 }}>
                  {riskInfo.text}
                </Tag>
                <div style={{ marginTop: 12 }}>
                  <Text type="secondary">
                    {risk?.abnormal_count > 0
                      ? `${risk.abnormal_count} 项异常，${risk.high_risk_count} 项高风险`
                      : '所有指标正常，继续保持！'}
                  </Text>
                </div>
              </div>
            </Card>
          </motion.div>
        </Col>

        {/* Category Pie Chart */}
        <Col xs={24} md={8}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.4 }}
          >
            <Card title="📊 指标分布" className="hover-lift">
              <ReactEChartsCore
                option={categoryChartOption}
                style={{ height: 200 }}
                notMerge
              />
            </Card>
          </motion.div>
        </Col>

        {/* Category Quick View */}
        <Col xs={24} md={8}>
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4, duration: 0.4 }}
          >
            <Card title="📋 分类概览" className="hover-lift">
              <List
                size="small"
                dataSource={categories.filter(c => c.indicator.length > 0)}
                renderItem={cat => {
                  const abnormal = cat.indicator.filter(i =>
                    i.status && i.status.includes('abnormal')
                  ).length
                  const catRisk = risk?.categories?.[cat.key]
                  const highCount = catRisk?.high || 0
                  return (
                    <List.Item
                      style={{ padding: '8px 0', cursor: 'pointer' }}
                      onClick={() => navigate('/health')}
                    >
                      <span>{cat.icon} {cat.title}</span>
                      <span>
                        {highCount > 0 && (
                          <Tag color="red" style={{ marginRight: 4 }}>{highCount}高风险</Tag>
                        )}
                        {abnormal > 0 && (
                          <Tag color="orange">{abnormal}异常</Tag>
                        )}
                        <Tag>{cat.indicator.length}项</Tag>
                      </span>
                    </List.Item>
                  )
                }}
              />
              {categories.filter(c => c.indicator.length > 0).length === 0 && (
                <div style={{ textAlign: 'center', padding: 12, color: '#999' }}>
                  暂无指标数据，请先添加
                </div>
              )}
            </Card>
          </motion.div>
        </Col>
      </Row>

      {/* AI Analysis & Suggestions Row */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        {/* AI Analysis */}
        <Col xs={24} md={12}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.4 }}
          >
            <Card
              title={<span><RobotOutlined /> AI 健康分析</span>}
              className="hover-lift"
              extra={
                <Button
                  type="link"
                  icon={<RobotOutlined />}
                  loading={aiLoading}
                  onClick={handleAiAnalyze}
                  disabled={indicators.length === 0}
                >
                  {aiAnalysis ? '重新分析' : '开始分析'}
                </Button>
              }
            >
              {indicators.length === 0 ? (
                <Alert
                  message="暂无数据"
                  description="请先添加健康指标后再进行 AI 分析"
                  type="info"
                  showIcon
                />
              ) : aiAnalysis ? (
                <div
                  style={{
                    maxHeight: 300,
                    overflow: 'auto',
                    fontSize: 14,
                    lineHeight: 1.8,
                    whiteSpace: 'pre-wrap',
                  }}
                  dangerouslySetInnerHTML={{ __html: aiAnalysis.analysis }}
                />
              ) : (
                <div style={{ textAlign: 'center', padding: '20px 0', color: '#999' }}>
                  <RobotOutlined style={{ fontSize: 36, display: 'block', marginBottom: 12 }} />
                  <Text type="secondary">
                    {indicators.length > 0
                      ? '点击「开始分析」获取 AI 健康解读'
                      : '添加指标后可开启 AI 分析'}
                  </Text>
                </div>
              )}
            </Card>
          </motion.div>
        </Col>

        {/* Suggestions */}
        <Col xs={24} md={12}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6, duration: 0.4 }}
          >
            <Card
              title="💪 健康建议"
              className="hover-lift"
              extra={
                <Button type="link" size="small" onClick={() => navigate('/health')}>
                  查看详情 <ArrowRightOutlined />
                </Button>
              }
            >
              {suggestions ? (
                <div className="stagger-children">
                  {suggestions.diet?.length > 0 && (
                    <div style={{ marginBottom: 12 }}>
                      <Text strong style={{ color: '#1677ff' }}>🥗 饮食建议</Text>
                      <ul style={{ margin: '4px 0 0 16px', color: '#666', fontSize: 13 }}>
                        {suggestions.diet.map((s, i) => <li key={i}>{s}</li>)}
                      </ul>
                    </div>
                  )}
                  {suggestions.exercise?.length > 0 && (
                    <div style={{ marginBottom: 12 }}>
                      <Text strong style={{ color: '#52c41a' }}>🏃 运动建议</Text>
                      <ul style={{ margin: '4px 0 0 16px', color: '#666', fontSize: 13 }}>
                        {suggestions.exercise.map((s, i) => <li key={i}>{s}</li>)}
                      </ul>
                    </div>
                  )}
                  {suggestions.lifestyle?.length > 0 && (
                    <div style={{ marginBottom: 12 }}>
                      <Text strong style={{ color: '#722ed1' }}>😴 作息建议</Text>
                      <ul style={{ margin: '4px 0 0 16px', color: '#666', fontSize: 13 }}>
                        {suggestions.lifestyle.map((s, i) => <li key={i}>{s}</li>)}
                      </ul>
                    </div>
                  )}
                  {suggestions.medical?.length > 0 && (
                    <div>
                      <Text strong style={{ color: '#ff4d4f' }}>🏥 就医建议</Text>
                      <ul style={{ margin: '4px 0 0 16px', color: '#666', fontSize: 13 }}>
                        {suggestions.medical.map((s, i) => <li key={i}>{s}</li>)}
                      </ul>
                    </div>
                  )}
                </div>
              ) : (
                <Alert message="暂无建议" type="info" showIcon />
              )}
            </Card>
          </motion.div>
        </Col>
      </Row>
    </div>
  )
}
