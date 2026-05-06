(function () {
  'use strict';

  const CHECK_DELAY_MS = 350;

  function setStatus(node, state, message) {
    if (!node) return;

    node.classList.remove('text-muted', 'text-success', 'text-danger');
    if (state === 'available') {
      node.classList.add('text-success');
    } else if (state === 'unavailable') {
      node.classList.add('text-danger');
    } else {
      node.classList.add('text-muted');
    }
    node.textContent = message || '';
  }

  function initAvailabilityCheck(form) {
    const urlInput = form.querySelector('#booking-availability-url');
    const spaceInput = form.querySelector('#booking-space-id');
    const startInput = form.querySelector('#datetime_start');
    const endInput = form.querySelector('#datetime_end');
    const submitButton = form.querySelector('#submit-btn');
    const statusNode = form.querySelector('#availability-info');

    if (!urlInput || !spaceInput || !startInput || !endInput || !submitButton) {
      return;
    }

    let timerId = null;
    let controller = null;

    function setAvailabilityState(state, message) {
      form.dataset.availabilityState = state;
      submitButton.disabled = state !== 'available';
      setStatus(statusNode, state, message);
    }

    async function checkAvailability() {
      if (form.dataset.bookingIntervalValid !== 'true') {
        setAvailabilityState('idle', '');
        return;
      }

      if (controller) {
        controller.abort();
      }
      controller = new AbortController();
      setAvailabilityState('checking', 'Проверяем доступность...');

      const params = new URLSearchParams({
        space_id: spaceInput.value,
        check_in: startInput.value,
        check_out: endInput.value,
      });

       try {
         const response = await fetch(`${urlInput.value}?${params.toString()}`, {
           headers: { 'X-Requested-With': 'XMLHttpRequest' },
           signal: controller.signal,
           credentials: 'same-origin',
         });

         const data = await response.json();

         if (!data.available) {
           setAvailabilityState('unavailable', data.message || 'Выбранный интервал недоступен.');
           return;
         }

         setAvailabilityState('available', data.message || 'Слот свободен.');
       } catch (error) {
        if (error.name === 'AbortError') {
          return;
        }
        console.error('Availability check error:', error);
        setAvailabilityState('unavailable', 'Не удалось проверить доступность. Попробуйте еще раз.');
      }
    }

    function scheduleCheck() {
      window.clearTimeout(timerId);
      setAvailabilityState('checking', 'Проверяем доступность...');
      timerId = window.setTimeout(checkAvailability, CHECK_DELAY_MS);
    }

    form.addEventListener('booking:interval-change', (event) => {
      if (!event.detail || !event.detail.isValid) {
        window.clearTimeout(timerId);
        if (controller) {
          controller.abort();
        }
        setAvailabilityState('idle', '');
        return;
      }
      scheduleCheck();
    });

    form.addEventListener('submit', (event) => {
      if (form.dataset.availabilityState !== 'available') {
        event.preventDefault();
        scheduleCheck();
      }
    });

    setAvailabilityState('idle', '');
  }

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-booking-calendar]').forEach(initAvailabilityCheck);
  });
})();
