import { useState, useEffect } from 'react'
import { Modal, Form, Input, Select, DatePicker, message } from 'antd'
import { healthApi, userApi } from '../../api'
import dayjs from 'dayjs'

export default function AddIndicatorModal({ open, onClose, onSuccess }) {
  const [form] = Form.useForm()
  const [categories, setCategories] = useState([])
  const [userId, setUserId] = useState(null)
  const [loading, setLoading] = useState(false)
  const selectedCategory = Form.useWatch('category', form)
  const indicatorOptions = categories.find(item => item.key === selectedCategory)?.indicators || []

  useEffect(() => {
    if (open) {
      form.resetFields()
      setUserId(null)
      Promise.all([healthApi.categories(), userApi.getDefault()])
        .then(([categoryResponse, userResponse]) => {
          setCategories(categoryResponse.data)
          setUserId(userResponse.data.id)
        })
        .catch(() => message.error('加载指标选项失败'))
    }
  }, [open])

  const handleCategoryChange = () => {
    form.setFieldsValue({ name: undefined, unit: undefined })
  }

  const handleNameChange = (name) => {
    const indicator = indicatorOptions.find(item => item.name === name)
    form.setFieldValue('unit', indicator?.unit)
  }

  const handleOk = async () => {
    try {
      const values = await form.validateFields()
      setLoading(true)
      await healthApi.create({
        ...values,
        user_id: userId,
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
      okButtonProps={{ disabled: !userId }}
      destroyOnHidden
      width={500}
    >
      <Form form={form} layout="vertical" initialValues={{ source: 'manual', measured_at: dayjs() }}>
        <Form.Item name="category" label="分类" rules={[{ required: true, message: '请选择分类' }]}>
          <Select placeholder="选择分类" onChange={handleCategoryChange}>
            {categories.map(c => (
              <Select.Option key={c.key} value={c.key}>{c.name}</Select.Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item name="name" label="指标名称" rules={[{ required: true, message: '请选择指标名称' }]}>
          <Select
            placeholder={selectedCategory ? '选择指标名称' : '请先选择分类'}
            disabled={!selectedCategory}
            showSearch
            optionFilterProp="label"
            options={indicatorOptions.map(item => ({ label: item.name, value: item.name }))}
            onChange={handleNameChange}
          />
        </Form.Item>

        <Form.Item name="value" label="检测值" rules={[{ required: true, message: '请输入数值' }]}>
          <Input placeholder="如：6.5" />
        </Form.Item>

        <Form.Item name="unit" label="单位">
          <Input placeholder="选择指标后自动填写" readOnly />
        </Form.Item>

        <Form.Item name="measured_at" label="测量时间">
          <DatePicker showTime style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item name="source" hidden><Input /></Form.Item>
      </Form>
    </Modal>
  )
}
