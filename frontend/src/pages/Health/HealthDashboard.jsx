import { useState, useEffect, useCallback } from 'react'
import {
  Card, Table, Button, Tag, Space, Modal, Form, Input, Select,
  DatePicker, message, Row, Col, Statistic, Popconfirm, Tabs,
} from 'antd'
import {
  PlusOutlined, DeleteOutlined, EditOutlined, ReloadOutlined,
  BarChartOutlined, RobotOutlined,
} from '@ant-design/icons'
import { motion } from 'framer-motion'
import ReactEChartsCore from 'echarts-for-react'
import dayjs from 'dayjs'
import { healthApi } from '../../api'
import Loading from '../../components/common/Loading'
import EmptyState from '../../components/common/EmptyState'
import AddIndicatorModal from './AddIndicatorModal'

const statusMap = {
  normal: { color: 'green', text: '正常' },
  abnormal_high: { color: 'red', text: '偏高' },
  abnormal_low: { color: 'orange', text: '偏低' },
}

const riskMap = {
  low: { color: 'green', text: '低' },
  medium: { color: 'orange', text: '中' },
  high: { color: 'red', text: '高' },
}

const categoryColors = {
  blood_sugar: '#1677ff',
  blood_pressure: '#ff4d4f',
  blood_fat: '#faad14',
  liver: '#52c41a',
  kidney: '#722ed1',
  blood_routine: '#13c2c2',
}

export default function HealthDashboard() {
  const [loading, setLoading] = useState(true)
  const [indicators, setIndicators] = useState([])
  const [categories, setCategories] = useState([])
  const [riskSummary, setRiskSummary] = useState(null)
  const [addModalOpen, setAddModalOpen] = useState(false)
  const [editing, setEditing] = useState(null)
  const [editForm] = Form.useForm()
  const [activeTab, setActiveTab] = useState('list')

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const [indRes, catRes, riskRes] = await Promise.all([
        healthApi.list(),
        healthApi.categories(),
        healthApi.riskSummary(),
      ])
      setIndicators(indRes.data)
      setCategories(catRes.data)
      setRiskSummary(riskRes.data)
    } catch (err) {
      message.error('加载数据失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { loadData() }, [loadData])

  const handleDelete = async (id) => {
    try {
      await healthApi.delete(id)
      message.success('删除成功')
      loadData()
    } catch {
      message.error('删除失败')
    }
  }

  const handleEdit = (record) => {
    setEditing(record)
    editForm.setFieldsValue({
      ...record,
      measured_at: record.measured_at ? dayjs(record.measured_at) : null,
    })
  }

  const handleEditSave = async () => {
    try {
      const values = await editForm.validateFields()
      await healthApi.update(editing.id, {
        ...values,
        measured_at: values.measured_at?.format('YYYY-MM-DD HH:mm:ss'),
      })
      message.success('更新成功')
      setEditing(null)
      loadData()
    } catch {
      // validation error
    }
  }

  // ── Charts ──
  const chartData = indicators
    .filter(i => i.status === 'abnormal_high' || i.status === 'abnormal_low')
    .slice(0, 10)

  const barOption = {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '8%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: chartData.map(i => i.name), axisLabel: { rotate: 30 } },
    yAxis: { type: 'value' },
    series: [{
      type: 'bar',
      data: chartData.map(i => ({
        value: parseFloat(i.value) || 0,
        itemStyle: {
          color: i.risk_level === 'high' ? '#ff4d4f'
            : i.risk_level === 'medium' ? '#faad14' : '#52c41a',
          borderRadius: [4, 4, 0, 0],
        },
      })),
      barWidth: 30,
    }],
  }

  const trendOption = {
    tooltip: { trigger: 'axis' },
    legend: { data: [...new Set(indicators.map(i => i.name))], bottom: 0 },
    grid: { left: '3%', right: '4%', bottom: '20%', containLabel: true },
    xAxis: { type: 'category', data: indicators.map(i => dayjs(i.created_at).format('MM-DD')) },
    yAxis: { type: 'value' },
    series: [...new Set(indicators.map(i => i.name))].map(name => ({
      name,
      type: 'line',
      smooth: true,
      data: indicators.filter(i => i.name === name).map(i => parseFloat(i.value) || 0),
      symbol: 'circle',
      symbolSize: 6,
    })),
  }

  // ── Table columns ──
  const columns = [
    {
      title: '指标名称',
      dataIndex: 'name',
      key: 'name',
      width: 130,
      render: (text, record) => (
        <span style={{ fontWeight: 500 }}>
          {text}
          <Tag
            color={categoryColors[record.category] || '#999'}
            style={{ marginLeft: 6, fontSize: 11 }}
          >
            {categories.find(c => c.key === record.category)?.name || record.category}
          </Tag>
        </span>
      ),
    },
    {
      title: '数值',
      dataIndex: 'value',
      key: 'value',
      width: 100,
      render: (val, record) => (
        <span style={{ fontWeight: 600, fontSize: 15 }}>
          {val}
          {record.unit && <span style={{ fontSize: 12, color: '#999', marginLeft: 2 }}>{record.unit}</span>}
        </span>
      ),
      sorter: (a, b) => parseFloat(a.value) - parseFloat(b.value),
    },
    {
      title: '正常范围',
      dataIndex: 'normal_range',
      key: 'normal_range',
      width: 140,
      render: (val) => val || <span style={{ color: '#ccc' }}>—</span>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status) => {
        const info = statusMap[status]
        return info
          ? <Tag color={info.color}>{info.text}</Tag>
          : <Tag>未知</Tag>
      },
    },
    {
      title: '风险',
      dataIndex: 'risk_level',
      key: 'risk_level',
      width: 80,
      render: (level) => {
        const info = riskMap[level]
        return info
          ? <Tag color={info.color}>{info.text}</Tag>
          : <Tag>—</Tag>
      },
    },
    {
      title: '建议',
      dataIndex: 'suggestion',
      key: 'suggestion',
      ellipsis: true,
      render: (val) => val || <span style={{ color: '#ccc' }}>—</span>,
    },
    {
      title: '来源',
      dataIndex: 'source',
      key: 'source',
      width: 70,
      render: (src) => <Tag>{src === 'ocr' ? 'OCR' : src === 'manual' ? '手动' : src}</Tag>,
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_, record) => (
        <Space>
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)} />
          <Popconfirm title="确认删除？" onConfirm={() => handleDelete(record.id)}>
            <Button type="link" size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  if (loading) return <Loading fullPage />

  return (
    <div className="page-enter">
      <Row gutter={[16, 16]} className="stagger-children">
        <Col xs={12} sm={6}>
          <motion.div whileHover={{ y: -4 }} className="metric-card">
            <div className="value" style={{ color: '#1677ff' }}>{indicators.length}</div>
            <div className="label">总指标</div>
          </motion.div>
        </Col>
        <Col xs={12} sm={6}>
          <motion.div whileHover={{ y: -4 }} className="metric-card">
            <div className="value" style={{ color: '#52c41a' }}>{riskSummary?.normal_count || 0}</div>
            <div className="label">正常</div>
          </motion.div>
        </Col>
        <Col xs={12} sm={6}>
          <motion.div whileHover={{ y: -4 }} className="metric-card">
            <div className="value" style={{ color: '#faad14' }}>{riskSummary?.abnormal_count || 0}</div>
            <div className="label">异常</div>
          </motion.div>
        </Col>
        <Col xs={12} sm={6}>
          <motion.div whileHover={{ y: -4 }} className="metric-card">
            <div className="value" style={{ color: '#ff4d4f' }}>{riskSummary?.high_risk_count || 0}</div>
            <div className="label">高风险</div>
          </motion.div>
        </Col>
      </Row>

      {/* Actions */}
      <Card style={{ marginTop: 16 }} className="animate-fade-in">
        <Space wrap>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setAddModalOpen(true)}>
            添加指标
          </Button>
          <Button icon={<RobotOutlined />} onClick={async () => {
            try {
              const res = await healthApi.aiAnalyze()
              Modal.info({
                title: 'AI 综合分析',
                width: 600,
                content: (
                  <div style={{ maxHeight: 400, overflow: 'auto', whiteSpace: 'pre-wrap', lineHeight: 1.8 }}>
                    {res.data.analysis}
                  </div>
                ),
              })
            } catch { message.warning('AI 分析暂时不可用') }
          }}>
            AI 综合分析
          </Button>
          <Button icon={<ReloadOutlined />} onClick={loadData}>刷新</Button>
        </Space>
      </Card>

      {/* Tabs: Table / Chart */}
      <Card style={{ marginTop: 16 }} className="animate-fade-in-up">
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={[
            {
              key: 'list',
              label: <span><BarChartOutlined /> 列表视图</span>,
              children: indicators.length === 0 ? (
                <EmptyState
                  title="暂无指标数据"
                  description="点击「添加指标」开始记录您的健康数据"
                  actionText="添加指标"
                  onAction={() => setAddModalOpen(true)}
                />
              ) : (
                <Table
                  dataSource={indicators}
                  columns={columns}
                  rowKey="id"
                  size="middle"
                  pagination={{
                    pageSize: 15,
                    showSizeChanger: true,
                    showTotal: (t) => `共 ${t} 项`,
                  }}
                  scroll={{ x: 900 }}
                />
              ),
            },
            {
              key: 'chart',
              label: <span><BarChartOutlined /> 图表视图</span>,
              children: (
                <Row gutter={[16, 16]}>
                  <Col xs={24} lg={12}>
                    <Card title="异常指标分布" size="small">
                      {chartData.length > 0
                        ? <ReactEChartsCore option={barOption} style={{ height: 300 }} />
                        : <EmptyState title="暂无异常指标" />}
                    </Card>
                  </Col>
                  <Col xs={24} lg={12}>
                    <Card title="指标趋势" size="small">
                      {indicators.length > 0
                        ? <ReactEChartsCore option={trendOption} style={{ height: 300 }} />
                        : <EmptyState title="暂无数据" />}
                    </Card>
                  </Col>
                </Row>
              ),
            },
          ]}
        />
      </Card>

      {/* Add Modal */}
      <AddIndicatorModal
        open={addModalOpen}
        onClose={() => setAddModalOpen(false)}
        onSuccess={() => { setAddModalOpen(false); loadData() }}
      />

      {/* Edit Modal */}
      <Modal
        title="编辑指标"
        open={!!editing}
        onOk={handleEditSave}
        onCancel={() => setEditing(null)}
        destroyOnClose
      >
        <Form form={editForm} layout="vertical">
          <Form.Item name="name" label="名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="value" label="数值" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="unit" label="单位">
            <Input />
          </Form.Item>
          <Form.Item name="measured_at" label="测量时间">
            <DatePicker showTime style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
