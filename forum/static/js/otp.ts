// Frontend validation and UI enhancements for registration and OTP forms

// Bootstrap form validation
(() => {
  'use strict';
  window.addEventListener('load', () => {
    // Fetch all forms we want to apply custom validation to
    const forms = document.getElementsByClassName('needs-validation');
    Array.prototype.filter.call(forms, (form: HTMLFormElement) => {
      form.addEventListener('submit', (event: Event) => {
        if (!form.checkValidity()) {
          event.preventDefault();
          event.stopPropagation();
        }
        form.classList.add('was-validated');
      }, false);
    });
  }, false);
})();

// Additional OTP input enhancements
const otpInput = document.getElementById('otp') as HTMLInputElement | null;
if (otpInput) {
  otpInput.addEventListener('input', () => {
    // Allow only digits and max length 6
    otpInput.value = otpInput.value.replace(/\D/g, '').slice(0, 6);
  });
}
