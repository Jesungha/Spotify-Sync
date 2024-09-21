document.addEventListener("DOMContentLoaded", () => {
  const colorBox = document.getElementById("color-box");
  const socket = io.connect("http://localhost:3000"); // Connect to your Socket.io server.
  console.log("Connected to Socket.io server.");
  loop = undefined;
  socket.on("new_sequence", (data) => {
    console.log("newdata", data);
    if (loop) {
      clearInterval(loop);
      loop = undefined;
    }

    const { progress_ms, interval, sequence, frames } = data;
    let index = Math.floor(progress_ms / interval);

    loop = setInterval(() => {
      if (index >= 0 && index < sequence.length) {
        const [r, g, b] = sequence[index];

        const frame = frames[index];
        let levelStr = "";
        for (let i = 0; i < frame.length; i++) {
          const level = Math.floor(frame[i] * 10);
          levelStr += `${i}: ${"=".repeat(level)}${" ".repeat(10 - level)}\n`;
        }
        document.getElementById("levels").innerText = levelStr;

        const time = index * interval;
        document.getElementById("time").innerText = `${time / 1000}s`;

        colorBox.style.backgroundColor = `rgb(${r}, ${g}, ${b})`;
        index++;
      } else {
        clearInterval(loop);
        loop = undefined;
      }
    }, interval);
  });
});
