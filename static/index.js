// new file
window.addEventListener("DOMContentLoaded",function() {
  const track = document.getElementById('carousel_track');
  const slides = Array.from(track.children);

  const nextButton = document.getElementById('carousel_button--right');
  const prevButton = document.getElementById('carousel_button--left')

  const dotsCarousel = document.getElementById('carousel_nav');
  const dots = Array.from(dotsCarousel.children);

  const slideWidth = slides[0].getBoundingClientRect().width;

  const setSlidePosition = (slide, index) => {
    slide.style.left = slideWidth * index + 'px';
  };
  
  slides.forEach(setSlidePosition);

  const moveToSlide = (track, currentSlide, targetSlide) => {
    track.style.transform = 'translateX(-' + targetSlide.style.left + ')';
    currentSlide.classList.remove('current-slide');
    targetSlide.classList.add('current-slide');
  }
  
  const updateDots = (currentDot, dotTarget) => {
    currentDot.classList.remove('current-slide');
    dotTarget.classList.add('current-slide');
  }

  const arrowsCarousel = (slides, prevButton, nextButton, targetIndex) => {
    if (targetIndex === 0) {
      prevButton.classList.add('is-hidden');
      nextButton.classList.remove('is-hidden');
    } else if (targetIndex === slides.length - 1) {
      prevButton.classList.remove('is-hidden');
      nextButton.classList.add('is-hidden');
    } else {
      prevButton.classList.remove('is-hidden');
      nextButton.classList.remove('is-hidden');
    }
  }

  prevButton.addEventListener('click', e => {
    const currentSlide = track.querySelector('.current-slide');
    const prevSlide = currentSlide.previousElementSibling;
    const currentDot = dotsCarousel.querySelector('.current-slide');
    const prevDot = currentDot.previousElementSibling;
    const prevIndex = slides.findIndex(slide => slide === prevSlide);

    moveToSlide(track, currentSlide, prevSlide);
    updateDots(currentDot, prevDot);
    arrowsCarousel(slides, prevButton, nextButton, prevIndex);
  });

  if (nextButton) {
    nextButton.addEventListener('click', e => {
      const currentSlide = track.querySelector('.current-slide');
      const nextSlide = currentSlide.nextElementSibling;
      const currentDot = dotsCarousel.querySelector('.current-slide');
      const nextDot = currentDot.nextElementSibling;
      const nextIndex = slides.findIndex(slide => slide === nextSlide);
      moveToSlide(track, currentSlide, nextSlide);
      updateDots(currentDot, nextDot);
      
      arrowsCarousel(slides, prevButton, nextButton, nextIndex);
    });
  } else {
    console.log("nextButton does not exist")
  }

  dotsCarousel.addEventListener('click', e => {
    const dotTarget = e.target.closest('button');
  
    if(!dotTarget) return;

    const currentSlide = track.querySelector('.current-slide');
    const currentDot = dotsCarousel.querySelector('.current-slide');
    const targetIndex = dots.findIndex(dot => dot === dotTarget);
    const targetSlide = slides[targetIndex];

    moveToSlide(track, currentSlide, targetSlide);
    updateDots(currentDot, dotTarget);

    arrowsCarousel(slides, prevButton, nextButton, targetIndex);
  })
});


