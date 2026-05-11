function startTimer(duration, formId) {
  let timer = duration;
  const display = document.getElementById("time");
  const box = document.getElementById("timer");

  const interval = setInterval(function () {
    const minutes = Math.floor(timer / 60);
    const seconds = timer % 60;
    display.textContent =
      (minutes < 10 ? "0" : "") + minutes + ":" +
      (seconds < 10 ? "0" : "") + seconds;

    if (timer <= 60) box.classList.add("danger");

    if (--timer < 0) {
      clearInterval(interval);
      document.getElementById(formId).submit();
    }
  }, 1000);
}