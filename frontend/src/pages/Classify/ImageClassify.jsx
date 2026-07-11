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
  AD: { color: '#d48806', label: '建议观察' },
  BCC: { color: '#d4380d', label: '尽快就医' },
  ECZEMA: { color: '#1677ff', label: '建议观察' },
  MEL: { color: '#cf1322', label: '尽快就医' },
  WARTS: { color: '#389e0d', label: '注意防护' },
}

function readFileAsBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (event) => {
      const dataUrl = event.target.result
      resolve({ dataUrl, base64: dataUrl.split(',')[1] })
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
    Promise.all([classifyApi.status(), classifyApi.classes()])
      .then(([statusResponse, classesResponse]) => {
        setModelStatus(statusResponse.data)
        setClasses(classesResponse.data)
      })
      .catch(() => setError('无法连接影像初筛服务'))
      .finally(() => setStatusLoading(false))
  }, [])

  const topPrediction = useMemo(() => result?.predictions?.[0] || null, [result])
  const statusReady = modelStatus?.runtime_available && modelStatus?.model_file_exists

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
    setFileName(file.name)
    try {
      const { dataUrl, base64 } = await readFileAsBase64(file)
      setPreview(dataUrl)
      const response = await classifyApi.classifySkin({ image_base64: base64 }, { topk })
      setResult(response.data)
      if (response.data.success) {
        message.success('图片分析完成')
      } else {
        setError(response.data.error || '模型暂不可用')
      }
    } catch (requestError) {
      const detail = requestError.response?.data?.detail || '图片分析服务暂不可用'
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

  return (
    <div className="page-enter">
      <Row gutter={[16, 16]}>
        <Col xs={24} md={9}>
          <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }}>
            <Card title={<span><MedicineBoxOutlined /> 皮肤影像初筛</span>}>
              <Space direction="vertical" size={16} style={{ width: '100%' }}>
                <Dragger
                  accept="image/jpeg,image/png,image/webp,image/bmp"
                  showUploadList={false}
                  beforeUpload={handleFile}
                  disabled={loading || !statusReady}
                >
                  {loading ? (
                    <Loading text="正在分析图片..." />
                  ) : (
                    <div>
                      <p className="ant-upload-drag-icon"><InboxOutlined /></p>
                      <p className="ant-upload-text">点击或拖入清晰的皮肤照片</p>
                      <p className="ant-upload-hint">支持 JPG、PNG、WebP、BMP，最大 8 MB</p>
                    </div>
                  )}
                </Dragger>

                <Space align="center" style={{ justifyContent: 'space-between', width: '100%' }}>
                  <Text type="secondary">候选结果数</Text>
                  <Select
                    value={topk}
                    onChange={setTopk}
                    style={{ width: 96 }}
                    options={[1, 3, 5].map(value => ({ value, label: `Top ${value}` }))}
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
                    <Text type="secondary" style={{ display: 'block', marginTop: 8 }}>{fileName}</Text>
                  </div>
                )}

                <Alert
                  type="warning"
                  showIcon
                  message="仅用于健康教育和初步筛查"
                  description="结果不能代替医生面诊、皮肤镜检查或病理诊断。病变快速增大、出血、破溃、明显疼痛或颜色不均时，请及时就医。"
                />
              </Space>
            </Card>
          </motion.div>
        </Col>

        <Col xs={24} md={15}>
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}>
            <Card
              title={<span><ExperimentOutlined /> 分析结果</span>}
              extra={(result || preview || error) && (
                <Button size="small" icon={<ReloadOutlined />} onClick={clearResult}>清空</Button>
              )}
            >
              {statusLoading && <Loading text="正在检查模型状态..." />}

              {!statusLoading && modelStatus && (
                <Alert
                  style={{ marginBottom: 16 }}
                  type={statusReady ? 'success' : 'error'}
                  showIcon
                  icon={statusReady ? <CheckCircleOutlined /> : <WarningOutlined />}
                  message={statusReady ? '轻量分类模型可用' : '分类模型尚未安装'}
                  description={statusReady
                    ? `${modelStatus.model_name} · ${modelStatus.model_size_mb} MB · ${modelStatus.runtime}`
                    : '请安装 onnxruntime 并运行模型下载脚本。'}
                />
              )}

              {!result && !error && !preview && !statusLoading && (
                <EmptyState
                  icon={<MedicineBoxOutlined style={{ fontSize: 48, color: '#d9d9d9' }} />}
                  title="等待图片"
                  description="上传局部清晰照片后，这里会显示相似类别。"
                />
              )}

              {error && <Alert type="error" showIcon message="分析失败" description={error} />}

              {result?.success && (
                <div>
                  <Alert
                    style={{ marginBottom: 16 }}
                    type={result.uncertain ? 'warning' : 'info'}
                    showIcon
                    message={result.uncertain ? '结果置信度较低' : '图片相似度结果'}
                    description={result.notice}
                  />

                  {topPrediction && (
                    <div style={{ padding: 16, border: '1px solid #e5e7eb', borderRadius: 8, marginBottom: 16 }}>
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
                        <Paragraph style={{ marginBottom: 0 }}>{topPrediction.description}</Paragraph>
                      </Space>
                    </div>
                  )}

                  <Space direction="vertical" size={12} style={{ width: '100%' }}>
                    {result.predictions.map((item) => (
                      <div key={item.class_short} style={{ padding: '10px 0', borderBottom: '1px solid #f0f0f0' }}>
                        <Space style={{ justifyContent: 'space-between', width: '100%' }} align="start">
                          <div>
                            <Space wrap>
                              <Text strong>{item.class_name}</Text>
                              <Tag>{item.class_short}</Tag>
                            </Space>
                            <Text type="secondary" style={{ display: 'block', marginTop: 4 }}>
                              {item.description}
                            </Text>
                          </div>
                          <Text strong>{Math.round(item.probability * 100)}%</Text>
                        </Space>
                      </div>
                    ))}
                  </Space>
                </div>
              )}
            </Card>

            <Card title="支持的初筛类别" style={{ marginTop: 16 }}>
              <Descriptions size="small" column={{ xs: 1, sm: 2 }}>
                {classes.map(item => (
                  <Descriptions.Item key={item.short} label={item.short}>{item.name}</Descriptions.Item>
                ))}
              </Descriptions>
            </Card>
          </motion.div>
        </Col>
      </Row>
    </div>
  )
}
