import { useState } from 'react'
import {
  Card, Upload, Button, message, Typography, Row, Col, Tag,
  Descriptions, Table, Space, Alert, Divider,
} from 'antd'
import {
  InboxOutlined, FileTextOutlined, ScanOutlined,
  ReloadOutlined, CheckCircleOutlined,
} from '@ant-design/icons'
import { motion } from 'framer-motion'
import { ocrApi } from '../../api'
import Loading from '../../components/common/Loading'
import EmptyState from '../../components/common/EmptyState'

const { Dragger } = Upload
const { Title, Text } = Typography

export default function OCRUpload() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleFile = async (file) => {
    if (!file.type?.startsWith('image/')) {
      message.error('请选择图片文件')
      return Upload.LIST_IGNORE
    }
    if (file.size > 8 * 1024 * 1024) {
      message.error('图片不能超过 8 MB')
      return Upload.LIST_IGNORE
    }

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const reader = new FileReader()
      reader.onload = async (e) => {
        const base64 = e.target.result.split(',')[1]
        try {
          const res = await ocrApi.recognize({ image_base64: base64 }, { auto_save: true })
          setResult(res.data)
          message.success(`识别完成，提取到 ${res.data.indicators?.length || 0} 项指标`)
        } catch (err) {
          const detail = err.response?.data?.detail || '识别服务暂不可用'
          setError(detail)
          message.error(detail)
        } finally {
          setLoading(false)
        }
      }
      reader.readAsDataURL(file)
    } catch {
      setLoading(false)
      message.error('读取文件失败')
    }

    return false // prevent upload
  }

  const statusMap = {
    normal: { color: 'green', text: '正常' },
    abnormal_high: { color: 'red', text: '偏高' },
    abnormal_low: { color: 'orange', text: '偏低' },
  }

  return (
    <div className="page-enter">
      <Row gutter={[16, 16]}>
        <Col xs={24} md={10}>
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
          >
            <Card title={<span><ScanOutlined /> 上传体检报告</span>}>
              <Dragger
                accept="image/jpeg,image/png,image/bmp,image/webp"
                showUploadList={false}
                beforeUpload={handleFile}
                disabled={loading}
              >
                {loading ? (
                  <Loading text="正在识别..." />
                ) : (
                  <motion.div
                    animate={{ y: [0, -4, 0] }}
                    transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
                  >
                    <p className="ant-upload-drag-icon">
                      <InboxOutlined />
                    </p>
                    <p className="ant-upload-text">点击或拖拽体检报告图片到此区域</p>
                    <p className="ant-upload-hint">
                      支持 JPG / PNG / BMP / WebP 格式
                    </p>
                  </motion.div>
                )}
              </Dragger>

              <Alert
                style={{ marginTop: 16 }}
                type="info"
                showIcon
                message="识别流程"
                description="识别关键指标的单次值、最小值、最大值、平均值及各自参考范围，再分别评估并保存"
              />

              {result && (
                <Alert
                  style={{ marginTop: 16 }}
                  type="success"
                  showIcon
                  icon={<CheckCircleOutlined />}
                  message={`识别成功！共 ${result.indicators?.length || 0} 项指标`}
                  description={
                    result.detected_info && (
                      <span>
                        检测到个人信息：
                        {result.detected_info.age && `年龄 ${result.detected_info.age}`}
                        {result.detected_info.gender && `、性别 ${result.detected_info.gender}`}
                        {!result.detected_info.age && !result.detected_info.gender && '无'}
                      </span>
                    )
                  }
                />
              )}

              {error && (
                <Alert
                  style={{ marginTop: 16 }}
                  type="error"
                  showIcon
                  message="识别失败"
                  description={error}
                />
              )}
            </Card>
          </motion.div>
        </Col>

        <Col xs={24} md={14}>
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
          >
            <Card
              title={<span><FileTextOutlined /> 识别结果</span>}
              extra={
                result && (
                  <Button
                    size="small"
                    icon={<ReloadOutlined />}
                    onClick={() => setResult(null)}
                  >
                    清空
                  </Button>
                )
              }
            >
              {!result && !error && (
                <EmptyState
                  icon={<ScanOutlined style={{ fontSize: 48, color: '#d9d9d9' }} />}
                  title="等待上传"
                  description="上传体检报告后，识别结果将在此显示"
                />
              )}

              {result && (
                <div className="stagger-children">
                  {/* Indicators Table */}
                  {result.indicators?.length > 0 && (
                    <>
                      <Text strong style={{ fontSize: 15 }}>📋 提取的指标</Text>
                      <Table
                        dataSource={result.indicators}
                        columns={[
                          { title: '名称', dataIndex: 'name', key: 'name' },
                          {
                            title: '统计类型', dataIndex: 'statistic_type', key: 'statistic_type',
                            render: v => ({ min: '最小值', max: '最大值', average: '平均值', single: '单次值' }[v] || '单次值'),
                          },
                          { title: '数值', dataIndex: 'value', key: 'value' },
                          { title: '单位', dataIndex: 'unit', key: 'unit', render: v => v || '—' },
                          {
                            title: '参考范围', key: 'reference',
                            render: (_, row) => row.reference_min != null || row.reference_max != null
                              ? `${row.reference_min ?? '—'} - ${row.reference_max ?? '—'}` : '—',
                          },
                        ]}
                        rowKey="name"
                        size="small"
                        pagination={false}
                        style={{ marginTop: 8 }}
                      />
                    </>
                  )}

                  <Divider />

                  {/* Raw Text */}
                  <details>
                    <summary style={{ cursor: 'pointer', color: '#666', fontSize: 13 }}>
                      📄 查看 OCR 原始文本
                    </summary>
                    <pre style={{
                      marginTop: 8,
                      padding: 12,
                      background: '#f5f5f5',
                      borderRadius: 8,
                      fontSize: 12,
                      maxHeight: 200,
                      overflow: 'auto',
                      whiteSpace: 'pre-wrap',
                    }}>
                      {result.raw_text}
                    </pre>
                  </details>
                </div>
              )}
            </Card>
          </motion.div>
        </Col>
      </Row>
    </div>
  )
}
