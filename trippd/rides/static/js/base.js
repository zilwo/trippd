setTimeout(() => {
  const alert = document.getElementById("alerting-message");
  if (alert) {
    alert.remove();
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
