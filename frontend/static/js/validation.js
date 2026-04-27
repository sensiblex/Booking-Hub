(function () {
  'use strict';

  const rules = {
    username(value) {
      if (!value.trim()) return 'Введите имя пользователя.';
      if (value.trim().length < 3) return 'Имя пользователя должно быть не короче 3 символов.';
      return '';
    },
    email(value) {
      if (!value.trim()) return 'Введите email.';
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim())) return 'Введите корректный email.';
      return '';
    },
    password(value) {
      if (!value) return 'Введите пароль.';
      if (value.length < 8) return 'Пароль должен содержать минимум 8 символов.';
      return '';
    },
    passwordConfirm(value, passwordValue) {
      if (!value) return 'Повторите пароль.';
      if (value !== passwordValue) return 'Пароли не совпадают.';
      return '';
    },
  };

  function getErrorNode(input) {
    let node = input.parentElement.querySelector('.js-validation-error');
    if (!node) {
      node = document.createElement('div');
      node.className = 'invalid-feedback js-validation-error';
      input.insertAdjacentElement('afterend', node);
    }
    return node;
  }

  function setFieldState(input, message) {
    const errorNode = getErrorNode(input);
    if (message) {
      input.classList.add('is-invalid');
      input.classList.remove('is-valid');
      errorNode.textContent = message;
      return false;
    }

    input.classList.remove('is-invalid');
    if (input.value.trim()) {
      input.classList.add('is-valid');
    }
    errorNode.textContent = '';
    return true;
  }

  function validateField(input, form) {
    const password = form.querySelector('[name="password1"], [name="password"]');

    if (input.name === 'username') {
      return setFieldState(input, rules.username(input.value));
    }
    if (input.name === 'email') {
      return setFieldState(input, rules.email(input.value));
    }
    if (input.name === 'password' || input.name === 'password1') {
      const isValid = setFieldState(input, rules.password(input.value));
      const confirmation = form.querySelector('[name="password2"]');
      if (confirmation && confirmation.value) {
        validateField(confirmation, form);
      }
      return isValid;
    }
    if (input.name === 'password2') {
      return setFieldState(input, rules.passwordConfirm(input.value, password ? password.value : ''));
    }

    if (input.required && !input.value.trim()) {
      return setFieldState(input, 'Заполните это поле.');
    }
    return setFieldState(input, '');
  }

  function initForm(form) {
    const fields = form.querySelectorAll('input[required], input[type="email"], input[type="password"]');

    fields.forEach((field) => {
      field.addEventListener('input', () => validateField(field, form));
      field.addEventListener('blur', () => validateField(field, form));
    });

    form.addEventListener('submit', (event) => {
      const isValid = Array.from(fields).every((field) => validateField(field, form));
      if (!isValid) {
        event.preventDefault();
        const firstInvalid = form.querySelector('.is-invalid');
        if (firstInvalid) {
          firstInvalid.focus();
        }
      }
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-client-validation]').forEach(initForm);
  });
})();
