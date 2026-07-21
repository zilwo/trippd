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

  flatpickr("#expected_finish_time", {
    enableTime: true,
    dateFormat: "Y-m-d H:i",
  });

  flatpickr("#departure_date", {
    dateFormat: "Y-m-d",
  });

  flatpickr("#activity_start_time", {
    enableTime: true,
    dateFormat: "Y-m-d H:i",
  });
});
