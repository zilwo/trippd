setTimeout(() => {
  const alert = document.querySelectorAll('.alerting-message');
  if (alert) {
    alert.forEach((a) => a.remove());
  }
}, 5000);



document.addEventListener("DOMContentLoaded", function () {
  // datetime picker
  flatpickr("#departure_time", {
    enableTime: true,
    dateFormat: "Y-m-d H:i",
  });

  flatpickr("#expected_arrival_time", {
    enableTime: true,
    dateFormat: "Y-m-d H:i",
  });
});

