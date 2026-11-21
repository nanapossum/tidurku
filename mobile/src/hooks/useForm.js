import { useState } from 'react';

export default function useForm(initialValues, validate) {
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState({});

  function change(field, value) {
    setValues((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: undefined }));
  }

  function field(name) {
    return { value: values[name], error: errors[name], onChangeText: (value) => change(name, value) };
  }

  function submit(onValid) {
    const nextErrors = validate(values);
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length === 0) onValid(values);
  }

  function reset() {
    setValues(initialValues);
    setErrors({});
  }

  return { values, errors, field, change, submit, reset };
}
