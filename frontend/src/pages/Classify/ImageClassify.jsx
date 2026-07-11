import { useEffect, useMemo, useState } from 'react'
import {
  Alert, Button, Card, Col, Descriptions, Image, Progress, Row,
  Select, Space, Tag, Typography, Upload, message,
} from 'antd'
import {
  CheckCircleOutlined, ExperimentOutlined, InboxOutlined,
  MedicineBoxOutlined, ReloadOutlined, WarningOutlined,
} from '@ant-design/icons'
import { motion } from 'framer-motion'
import { classifyApi } from '../../api'
import EmptyState from '../../components/common/EmptyState'
import Loading from '../../components/common/Loading'

const { Dragger } = Upload
const { Text, Title, Paragraph } = Typography

const riskMeta = {
  MEL: { color: '#ff4d4f', label: '高关注' },
  BCC: { color: '#fa8c16', label: '需就医' },
  AKIEC: { color: '#faad14', label: '需复查' },
  BKL: { color: '#52c41a', label: '多为良性' },
  NV: { color: '#52c41a', label: '多为良性' },
  VASC: { color: '#1677ff', label: '常见良性' },
  DF: { color: '#13c2c2', label: '常见良性' },
}

function readFileAsBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (event) => {
      const value = event.target.result
      resolve({
        dataUrl: value,
        base64: value.split(',')[1],
      })
    }
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

export default function ImageClassify() {
  const [loading, setLoading] = useState(false)
  const [statusLoading, setStatusLoading] = useState(true)
  const [modelStatus, setModelStatus] = useState(null)
  const [classes, setClasses] = useState([])
  const [topk, setTopk] = useState(3)
  const [preview, setPreview] = useState(null)
  const [fileName, setFileName] = useState('')
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([
      classifyApi.status(),
      classifyApi.classes(),
    ]).then(([statusRes, classesRes]) => {
      setModelStatus(statusRes.data)
      setClasses(classesRes.data)
    }).catch(() => {
      setError('无法获取影像分类服务状态')
    }).finally(() => setStatusLoading(false))
  }, [])

  const topPrediction = useMemo(() => {
    return result?.predictions?.[0] || null
  }, [result])

  const handleFile = async (file) => {
    const isImage = file.type?.startsWith('image/')
    if (!isImage) {
      message.error('请上传图片文件')
      return Upload.LIST_IGNORE
    }

    const isSmallEnough = file.size / 1024 / 1024 <= 8
    if (!isSmallEnough) {
      message.error('图片大小不能超过 8MB')
      return Upload.LIST_IGNORE
    }

    setLoading(true)
    setError(null)
    setResult(null)
    setFileName(file.name)

    try {
      const { dataUrl, base64 } = await readFileAsBase64(file)
      setPreview(dataUrl)

      const res = await classifyApi.classifySkin({ image_base64: base64 }, { topk })
      setResult(res.data)

      if (res.data.success) {
        message.success('分类完成')
      } else {
        setError(res.data.error || '模型暂不可用')
        message.warning(res.data.error || '模型暂不可用')
      }
    } catch (err) {
      const detail = err.response?.data?.detail || '分类服务暂不可用'
      setError(detail)
      message.error(detail)
    } finally {
      setLoading(false)
    }

    return false
  }

  const clearResult = () => {
    setPreview(null)
    setFileName('')
    setResult(null)
    setError(null)
  }

  const statusReady = modelStatus?.torch_available && modelStatus?.model_file_exists

  return (
    <div className="page-enter">
      <Row gutter={[16, 16]}>
        <Col xs={24} md={9}>
          <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }}>
            <Card title={<span><MedicineBoxOutlined /> 皮肤影像分类</span>}>
              <Space direction="vertical" size={16} style={{ width: '100%' }}>
                <Dragger
                  accept="image/jpeg,image/png,image/webp,image/bmp"
                  showUploadList={false}
                  beforeUpload={handleFile}
                  disabled={loading}
                >
                  {loading ? (
                    <Loading text="正在分析影像..." />
                  ) : (
                    <motion.div
                      animate={{ y: [0, -4, 0] }}
                      transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
                    >
                      <p className="ant-upload-drag-icon">
                        <InboxOutlined />
                      </p>
                      <p className="ant-upload-text">点击或拖拽皮肤照片到此区域</p>
                      <p className="ant-upload-hint">
                        支持 JPG / PNG / WebP / BMP，建议使用清晰、无遮挡的局部照片
                      </p>
                    </motion.div>
                  )}
                </Dragger>

                <Space align="center" style={{ justifyContent: 'space-between', width: '100%' }}>
                  <Text type="secondary">返回结果数</Text>
                  <Select
                    value={topk}
                    onChange={setTopk}
                    style={{ width: 96 }}
                    options={[1, 3, 5, 7].map(value => ({ value, label: `Top ${value}` }))}
                    disabled={loading}
                  />
                </Space>

                {preview && (
                  <div>
                    <Image
                      src={preview}
                      alt={fileName || '待分析图片'}
                      style={{ width: '100%', maxHeight: 260, objectFit: 'cover', borderRadius: 8 }}
                    />
                    <Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
                      {fileName}
                    </Text>
                  </div>
                )}

                <Alert
                  type="warning"
                  showIcon
                  message="结果仅供健康管理参考"
                  description="影像分类不能替代医生面诊、皮肤镜检查或病理诊断；若皮损快速变化、出血、疼痛或颜色不均，请及时就医。"
                />
              </Space>
            </Card>
          </motion.div>
        </Col>

        <Col xs={24} md={15}>
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
          >
            <Card
              title={<span><ExperimentOutlined /> 分类结果</span>}
              extra={
                (result || preview || error) && (
                  <Button size="small" icon={<ReloadOutlined />} onClick={clearResult}>
                    清空
                  </Button>
                )
              }
            >
              {!result && !error && !preview && (
                <EmptyState
                  icon={<MedicineBoxOutlined style={{ fontSize: 48, color: '#d9d9d9' }} />}
                  title="等待上传"
                  description="上传皮肤照片后，AI 分类结果将在此显示"
                />
              )}

              {statusLoading && <Loading text="正在检查模型状态..." />}

              {!statusLoading && modelStatus && (
                <Alert
                  style={{ marginBottom: 16 }}
                  type={statusReady ? 'success' : 'info'}
                  showIcon
                  icon={statusReady ? <CheckCircleOutlined /> : <WarningOutlined />}
                  message={statusReady ? '分类模型可用' : '模型尚未加载'}
                  description={
                    statusReady
                      ? `设备：${modelStatus.device || 'cpu'}`
                      : '请确认已安装 PyTorch 并放置 HAM10000 权重文件后再进行真实分类。'
                  }
                />
              )}

              {error && (
                <Alert
                  style={{ marginBottom: 16 }}
                  type="error"
                  showIcon
                  message="分类失败"
                  description={error}
                />
              )}

              {result?.success && (
                <div className="stagger-children">
                  {topPrediction && (
                    <div style={{
                      padding: 16,
                      border: `1px solid ${(riskMeta[topPrediction.class_short]?.color || '#1677ff')}40`,
                      borderRadius: 8,
                      background: `${riskMeta[topPrediction.class_short]?.color || '#1677ff'}10`,
                      marginBottom: 16,
                    }}>
                      <Space direction="vertical" size={6} style={{ width: '100%' }}>
                        <Space wrap>
                          <Title level={5} style={{ margin: 0 }}>{topPrediction.class_name}</Title>
                          <Tag color={riskMeta[topPrediction.class_short]?.color || 'blue'}>
                            {riskMeta[topPrediction.class_short]?.label || '参考结果'}
                          </Tag>
                        </Space>
                        <Progress
                          percent={Math.round(topPrediction.probability * 100)}
                          strokeColor={riskMeta[topPrediction.class_short]?.color || '#1677ff'}
                        />
                        <Paragraph style={{ marginBottom: 0 }}>
                          {topPrediction.description}
                        </Paragraph>
                      </Space>
                    </div>
                  )}

                  <Space direction="vertical" size={12} style={{ width: '100%' }}>
                    {result.predictions.map((item) => {
                      const meta = riskMeta[item.class_short] || { color: '#1677ff', label: '参考结果' }
                      return (
                        <div
                          key={item.class_short}
                          style={{
                            padding: '12px 0',
                            borderBottom: '1px solid #f0f0f0',
                          }}
                        >
                          <Space style={{ justifyContent: 'space-between', width: '100%' }} align="start">
                            <div>
                              <Space wrap>
                                <Text strong>{item.class_name}</Text>
                                <Tag color={meta.color}>{item.class_short}</Tag>
                                <Tag>{meta.label}</Tag>
                              </Space>
                              <Text type="secondary" style={{ display: 'block', marginTop: 4 }}>
                                {item.description}
                              </Text>
                            </div>
                            <Text strong style={{ color: meta.color }}>
                              {Math.round(item.probability * 100)}%
                            </Text>
                          </Space>
                        </div>
                      )
                    })}
                  </Space>
                </div>
              )}
            </Card>

            <Card title="支持类别" style={{ marginTop: 16 }}>
              <Descriptions size="small" column={{ xs: 1, sm: 2 }}>
                {classes.map(item => (
                  <Descriptions.Item key={item.short} label={item.short}>
                    {item.name}
                  </Descriptions.Item>
                ))}
              </Descriptions>
            </Card>
          </motion.div>
        </Col>
      </Row>
    </div>
  )
}
