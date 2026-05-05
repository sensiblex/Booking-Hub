(function () {
  'use strict';

  document.querySelectorAll('[data-carousel]').forEach((carousel) => {
    const slides = Array.from(carousel.querySelectorAll('[data-carousel-slide]'));
    const prev = carousel.querySelector('[data-carousel-prev]');
    const next = carousel.querySelector('[data-carousel-next]');
    let activeIndex = slides.findIndex((slide) => slide.classList.contains('active'));

    if (slides.length === 0) return;
    if (activeIndex < 0) activeIndex = 0;

    function show(index) {
      activeIndex = (index + slides.length) % slides.length;
      slides.forEach((slide, slideIndex) => {
        slide.classList.toggle('active', slideIndex === activeIndex);
      });
    }

    if (slides.length > 1) {
      carousel.dataset.carouselReady = 'true';
      if (prev) prev.addEventListener('click', () => show(activeIndex - 1));
      if (next) next.addEventListener('click', () => show(activeIndex + 1));
    }

    show(activeIndex);
  });
})();
