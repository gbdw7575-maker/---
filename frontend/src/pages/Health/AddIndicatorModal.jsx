import { useState, useEffect } from 'react'
import { Modal, Form, Input, Select, DatePicker, message } from 'antd'
import { healthApi } from '../../api'
import dayjs from 'dayjs'

export default function AddIndicatorModal({ open, onClose, onSuccess }) {
  const [form] = Form.useForm()
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (open) {
      healthApi.categories().then(res => setCategories(res.data)).catch(() => {})
    }
  }, [open])

  const handleOk = async () => {
    try {
      const values = await form.validateFields()
      setLoading(true)
      await healthApi.create({
        ...values,
        measured_at: values.measured_at?.format('YYYY-MM-DD HH:mm:ss'),
      })
      message.success('指标添加成功！规则引擎已自动评估。')
      form.resetFields()
      onSuccess()
    } catch (err) {
      if (err.errorFields) return // validation error
      message.error('添加失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal
      title="添加健康指标"
      open={open}
      onOk={handleOk}
      onCancel={onClose}
      confirmLoading={loading}
      destroyOnClose
      width={500}
    >
      <Form form={form} layout="vertical" initialValues={{ source: 'manual' }}>
        <Form.Item name="category" label="分类" rules={[{ required: true, message: '请选择分类' }]}>
          <Select placeholder="选择分类">
            {categories.map(c => (
              <Select.Option key={c.key} value={c.key}>{c.name}</Select.Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item name="name" label="指标名称" rules={[{ required: true, message: '请输入名称' }]}>
          <Input placeholder="如：空腹血糖" />
        </Form.Item>

        <Form.Item name="value" label="检测值" rules={[{ required: true, message: '请输入数值' }]}>
          <Input placeholder="如：6.5" />
        </Form.Item>

        <Form.Item name="unit" label="单位">
          <Input placeholder="如：mmol/L" />
        </Form.Item>

        <Form.Item name="measured_at" label="测量时间">
          <DatePicker showTime style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item name="source" hidden><Input /></Form.Item>
      </Form>
    </Modal>
  )
}
