import { useState, useEffect, useCallback, useRef } from 'react'
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
  thyroid: '#eb2f96',
  electrolyte: '#1890ff',
  cardiac: '#fa541c',
  tumor_marker: '#531dab',
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
  const [selectedRowKeys, setSelectedRowKeys] = useState([])
  const [trendCategory, setTrendCategory] = useState('')
  const [trendDateRange, setTrendDateRange] = useState('30d')
  const [focusedTrend, setFocusedTrend] = useState(null) // 当前聚焦的指标名
  const userTouchedTrend = useRef(false)
  const trendChartRef = useRef(null)

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
      setSelectedRowKeys([])
      // 首次加载自动选第一个有数据的分类，避免不同单位混 Y 轴
      if (!userTouchedTrend.current) {
        const first = catRes.data.find(c => indRes.data.some(i => i.category === c.key))
        if (first) setTrendCategory(first.key)
      }
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

  const handleBatchDelete = async () => {
    try {
      const res = await healthApi.batchDelete(selectedRowKeys)
      message.success(`已删除 ${res.data.deleted_count} 项指标`)
      setSelectedRowKeys([])
      loadData()
    } catch {
      message.error('批量删除失败')
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

  // 1. 分类健康概览环形图 — 按分类展示正常/异常/高风险比例
  const ringCategories = riskSummary?.categories || {}
  const ringChartData = Object.entries(ringCategories).map(([key, cat]) => ({
    key,
    name: cat.name || categories.find(c => c.key === key)?.name || key,
    total: cat.total || 0,
    normal: cat.normal || 0,
    medium: cat.medium || 0,
    high: cat.high || 0,
  })).filter(c => c.total > 0)

  const ringOption = (cat) => ({
    tooltip: { trigger: 'item', formatter: '{b}: {c} 项 ({d}%)' },
    legend: { bottom: 0, itemWidth: 10, itemHeight: 10, textStyle: { fontSize: 11 } },
    color: ['#52c41a', '#faad14', '#ff4d4f'],
    series: [{
      type: 'pie',
      radius: ['45%', '70%'],
      center: ['50%', '45%'],
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 1 },
      label: { show: false },
      data: [
        { value: cat.normal, name: '正常' },
        { value: cat.medium, name: '中风险' },
        { value: cat.high, name: '高风险' },
      ],
    }],
  })

  // 2. 指标趋势图
  // 按分类 + 日期范围筛选
  const trendCutoff = trendDateRange === 'all' ? null : dayjs().subtract(parseInt(trendDateRange), 'day')
  const categoryIndicators = indicators
    .filter(i => !trendCategory || i.category === trendCategory)
    .filter(i => !trendCutoff || dayjs(i.measured_at || i.created_at).isAfter(trendCutoff))
  const uniqueNames = [...new Set(categoryIndicators.map(i => i.name))]

  // focusedTrend 变化时，手动触发 ECharts 的 highlight / downplay
  useEffect(() => {
    const inst = trendChartRef.current?.getEchartsInstance?.()
    if (!inst) return
    if (focusedTrend) {
      inst.dispatchAction({ type: 'highlight', seriesName: focusedTrend })
    } else {
      uniqueNames.forEach(name => inst.dispatchAction({ type: 'downplay', seriesName: name }))
    }
  }, [focusedTrend, uniqueNames])

  // 查找指标元信息
  const getRefRange = (name) => {
    const ind = indicators.find(i => i.name === name)
    if (ind?.reference_min != null && ind?.reference_max != null) {
      return [parseFloat(ind.reference_min), parseFloat(ind.reference_max)]
    }
    return null
  }

  // 同名字同日期多个值 → 优先取平均值，否则取平均
  const pickValueForDate = (name, dateStr) => {
    const items = indicators.filter(i =>
      i.name === name
      && (!trendCategory || i.category === trendCategory)
      && dayjs(i.measured_at || i.created_at).format('MM-DD') === dateStr
    )
    if (items.length === 0) return null
    const avg = items.find(i => i.stat_type === '平均值')
    if (avg) return parseFloat(avg.value) || null
    const vals = items.map(i => parseFloat(i.value)).filter(v => !isNaN(v))
    return vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : null
  }

  // X 轴用唯一日期并集
  const allDates = [...new Set(
    categoryIndicators.map(i => dayjs(i.measured_at || i.created_at).format('MM-DD'))
  )].sort()

  const colors = ['#1677ff', '#ff4d4f', '#faad14', '#52c41a', '#722ed1', '#13c2c2', '#eb2f96', '#fa541c']

  const trendOption = {
    // tooltip: 只显示当天有数据的指标，附带正常范围
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        // 过滤掉 value 为 null 的
        const valid = params.filter(p => p.value != null)
        if (valid.length === 0) return ''
        const date = valid[0].axisValue
        let html = `<div style="font-weight:600;margin-bottom:4px">${date}</div>`
        valid.forEach(p => {
          const ref = p.data?.ref || getRefRange(p.seriesName)
          const val = p.value
          let judge = ''
          if (ref) {
            judge = val < ref[0]
              ? `<span style="color:#faad14">⚠️ 偏低</span>`
              : val > ref[1]
                ? `<span style="color:#ff4d4f">⚠️ 偏高</span>`
                : `<span style="color:#52c41a">✓ 正常</span>`
          }
          const refStr = ref ? `<br/><span style="color:#888;font-size:11px">正常 ${ref[0]}~${ref[1]}</span>` : ''
          html += `<div style="margin:4px 0">
            ${p.marker} <b>${p.seriesName}</b>: ${val} ${refStr} ${judge}
          </div>`
        })
        return html
      },
    },
    legend: {
      data: uniqueNames,
      bottom: 0,
      type: 'scroll',
      textStyle: { fontSize: 11 },
    },
    grid: { left: '3%', right: '4%', bottom: uniqueNames.length > 5 ? '28%' : '15%', top: 30, containLabel: true },
    xAxis: { type: 'category', data: allDates, axisLabel: { rotate: 30 } },
    yAxis: { type: 'value' },
    series: uniqueNames.map((name, idx) => {
      const refRange = getRefRange(name)
      const color = colors[idx % colors.length]
      // data 存对象：{ value, ref, name, date } —— tooltip formatter 里可直接取用
      const data = allDates.map(date => {
        const val = pickValueForDate(name, date)
        if (val == null) return null
        return {
          value: val,
          ref: refRange,
          name,
          date,
        }
      })
      const isFocused = focusedTrend ? focusedTrend === name : false
      const isAllDimmed = focusedTrend !== null && !isFocused
      return {
        name,
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: isAllDimmed ? 3 : 6,
        lineStyle: { width: isFocused ? 2.5 : 1.5, opacity: isAllDimmed ? 0.3 : 1 },
        itemStyle: { color, opacity: isAllDimmed ? 0.3 : 1 },
        emphasis: { focus: 'series', lineStyle: { width: 3 } },
        data,
        // 正常范围参考带：默认隐藏，点击选中后才显示
        markArea: refRange && isFocused ? {
          silent: true,
          itemStyle: { color: 'rgba(82, 196, 26, 0.18)' },
          label: {
            show: true,
            position: 'insideEndTop',
            formatter: `正常 ${refRange[0]}~${refRange[1]}`,
            fontSize: 10,
            color: '#389e0d',
          },
          data: [[{ yAxis: refRange[0] }, { yAxis: refRange[1] }]],
        } : undefined,
      }
    }),
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
      title: '统计类型',
      dataIndex: 'statistic_type',
      key: 'statistic_type',
      width: 90,
      render: (type) => ({ min: '最小值', max: '最大值', average: '平均值', single: '单次值' }[type] || '单次值'),
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
              message.success('分析完成，结果已保存')
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
          <Popconfirm
            title={`确认删除已勾选的 ${selectedRowKeys.length} 项指标？`}
            onConfirm={handleBatchDelete}
            disabled={selectedRowKeys.length === 0}
          >
            <Button danger icon={<DeleteOutlined />} disabled={selectedRowKeys.length === 0}>
              删除勾选项{selectedRowKeys.length > 0 ? ` (${selectedRowKeys.length})` : ''}
            </Button>
          </Popconfirm>
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
                  rowSelection={{ selectedRowKeys, onChange: setSelectedRowKeys }}
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
                  {/* 分类健康概览 — 环形图网格 */}
                  <Col xs={24}>
                    <Card title="分类健康概览（正常 / 中风险 / 高风险）" size="small">
                      {ringChartData.length > 0 ? (
                        <Row gutter={[12, 12]}>
                          {ringChartData.map(cat => (
                            <Col xs={12} sm={8} md={6} key={cat.key}>
                              <div style={{ textAlign: 'center' }}>
                                <ReactEChartsCore
                                  option={ringOption(cat)}
                                  style={{ height: 180 }}
                                  notMerge
                                />
                                <div style={{ fontSize: 12, color: '#666', marginTop: -8 }}>
                                  {cat.name} <span style={{ color: '#999' }}>({cat.total}项)</span>
                                </div>
                              </div>
                            </Col>
                          ))}
                        </Row>
                      ) : (
                        <EmptyState title="暂无指标数据" description="添加指标后即可查看分类健康概览" />
                      )}
                    </Card>
                  </Col>

                  {/* 指标趋势 — 日期 + 分类筛选 */}
                  <Col xs={24}>
                    <Card
                      title="指标趋势"
                      size="small"
                      extra={
                        <Space size={8}>
                          <Select
                            value={trendDateRange}
                            style={{ width: 110 }}
                            onChange={(v) => setTrendDateRange(v)}
                            options={[
                              { value: '7d', label: '近 7 天' },
                              { value: '30d', label: '近 30 天' },
                              { value: '90d', label: '近 90 天' },
                              { value: 'all', label: '全部' },
                            ]}
                          />
                          <Select
                            placeholder="全部分类"
                            allowClear
                            value={trendCategory || undefined}
                            style={{ width: 130 }}
                            onChange={(v) => { userTouchedTrend.current = true; setTrendCategory(v || '') }}
                            options={categories.map(c => ({ value: c.key, label: c.name }))}
                          />
                        </Space>
                      }
                    >
                      {uniqueNames.length > 0 ? (
                        <ReactEChartsCore
                          ref={trendChartRef}
                          option={trendOption}
                          style={{ height: 320 }}
                          notMerge
                          onEvents={{
                            click: (params) => {
                              if (params.componentType === 'series') {
                                // 点击折线 → 聚焦 / 再次点击取消
                                setFocusedTrend(prev => prev === params.seriesName ? null : params.seriesName)
                              }
                            },
                            legendselectchanged: (params) => {
                              // legend 被点击时：如果只剩 1 个 series 被选中 → 聚焦它；否则取消聚焦
                              const selected = Object.entries(params.selected).filter(([, v]) => v).map(([k]) => k)
                              if (selected.length === 1) {
                                setFocusedTrend(selected[0])
                              } else {
                                setFocusedTrend(null)
                              }
                            },
                          }}
                        />
                      ) : (
                        <EmptyState title={indicators.length === 0 ? '暂无数据' : '当前分类无指标'} />
                      )}
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
        destroyOnHidden
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
