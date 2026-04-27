(function () {
  'use strict';

  const HOUR_IN_MS = 60 * 60 * 1000;

  function formatMoney(value) {
    return `${Math.ceil(value).toLocaleString('ru-RU')} ₽`;
  }

  function setInvalid(input, message) {
    input.classList.add('is-invalid');
    input.classList.remove('is-valid');

    let feedback = input.parentElement.querySelector('.invalid-feedback');
    if (!feedback) {
      feedback = document.createElement('div');
      feedback.className = 'invalid-feedback';
      input.insertAdjacentElement('afterend', feedback);
    }
    feedback.textContent = message;
  }

  function setValid(input) {
    input.classList.remove('is-invalid');
    if (input.value) {
      input.classList.add('is-valid');
    }
  }

  function initBookingCalendar(form) {
    const startInput = form.querySelector('#datetime_start');
    const endInput = form.querySelector('#datetime_end');
    const submitButton = form.querySelector('#submit-btn');
    const totalPrice = form.querySelector('#total-price');
    const durationInfo = form.querySelector('#duration-info');
    const pricePerHour = Number(form.dataset.pricePerHour || 0);

    if (!startInput || !endInput || !submitButton || !totalPrice || !durationInfo || !window.flatpickr) {
      return;
    }

    let startPicker;
    let endPicker;

    function availabilityAllowsSubmit() {
      return !['checking', 'unavailable'].includes(form.dataset.availabilityState);
    }

    function notifyIntervalChange(isValid) {
      form.dataset.bookingIntervalValid = isValid ? 'true' : 'false';

      if (form.dataset.bookingSubmitting === 'true') {
        return;
      }

      form.dispatchEvent(new CustomEvent('booking:interval-change', {
        detail: {
          isValid,
          startTime: startInput.value,
          endTime: endInput.value,
        },
      }));
    }

    function resetSummary(message) {
      totalPrice.textContent = '0 ₽';
      durationInfo.textContent = message || '';
      submitButton.disabled = true;
      notifyIntervalChange(false);
    }

    function calculateTotal() {
      const start = startPicker.selectedDates[0];
      const end = endPicker.selectedDates[0];

      if (!start || !end) {
        resetSummary('');
        return;
      }

      if (end <= start) {
        setInvalid(endInput, 'Окончание должно быть позже начала.');
        resetSummary('Выберите корректный интервал бронирования.');
        return;
      }

      setValid(startInput);
      setValid(endInput);

      const diffHours = (end - start) / HOUR_IN_MS;
      const total = diffHours * pricePerHour;
      totalPrice.textContent = formatMoney(total);
      durationInfo.textContent = `Длительность: ${diffHours.toFixed(1)} ч.`;
      submitButton.disabled = !availabilityAllowsSubmit();
      notifyIntervalChange(true);
    }

    startPicker = window.flatpickr(startInput, {
      enableTime: true,
      dateFormat: 'Y-m-d H:i',
      locale: window.flatpickr.l10ns.ru,
      minDate: 'today',
      minuteIncrement: 30,
      time_24hr: true,
      defaultHour: 9,
      onChange(selectedDates) {
        const start = selectedDates[0];
        if (!start) {
          resetSummary('');
          return;
        }

        const nextEnd = new Date(start.getTime() + HOUR_IN_MS);
        endPicker.set('minDate', start);

        if (!endPicker.selectedDates[0] || endPicker.selectedDates[0] <= start) {
          endPicker.setDate(nextEnd, true);
        }

        calculateTotal();
      },
    });

    endPicker = window.flatpickr(endInput, {
      enableTime: true,
      dateFormat: 'Y-m-d H:i',
      locale: window.flatpickr.l10ns.ru,
      minDate: 'today',
      minuteIncrement: 30,
      time_24hr: true,
      defaultHour: 10,
      onChange: calculateTotal,
    });

    form.addEventListener('submit', (event) => {
      form.dataset.bookingSubmitting = 'true';
      calculateTotal();
      delete form.dataset.bookingSubmitting;

      if (submitButton.disabled) {
        event.preventDefault();
        if (!startPicker.selectedDates[0]) {
          setInvalid(startInput, 'Выберите начало бронирования.');
          startInput.focus();
        } else if (!endPicker.selectedDates[0] || endPicker.selectedDates[0] <= startPicker.selectedDates[0]) {
          setInvalid(endInput, 'Выберите окончание позже начала.');
          endInput.focus();
        }
      }
    });

    resetSummary('');
  }

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-booking-calendar]').forEach(initBookingCalendar);
  });
})();
