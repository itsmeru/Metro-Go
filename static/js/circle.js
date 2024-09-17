export function createCountdownCircle() {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("width", "60");
    svg.setAttribute("height", "60");
    svg.setAttribute("viewBox", "0 0 36 36");
    svg.classList.add("countdown-circle");

    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circle.setAttribute("cx", "18");
    circle.setAttribute("cy", "18");
    circle.setAttribute("r", "16");
    circle.setAttribute("fill", "none");
    circle.setAttribute("stroke", "#e0e0e0");
    circle.setAttribute("stroke-width", "2");

    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("fill", "none");
    path.setAttribute("stroke", "#00a8ff");
    path.setAttribute("stroke-width", "2");
    path.setAttribute("d", "M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831");
    path.setAttribute("stroke-dasharray", "100, 100");

    const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
    text.setAttribute("x", "18");
    text.setAttribute("y", "20.35");
    text.setAttribute("text-anchor", "middle");
    text.setAttribute("font-size", "8");
    text.setAttribute("fill", "#00a8ff");

    svg.appendChild(circle);
    svg.appendChild(path);
    svg.appendChild(text);

    return svg;
}
export function updateCountdownCircle(svg, timeLeft, totalTime) {
    const path = svg.querySelector('path');
    const text = svg.querySelector('text');
    const percent = (timeLeft / totalTime) * 100;
    const dashArray = `${percent}, 100`;

    path.setAttribute("stroke-dasharray", dashArray);
    text.textContent = timeLeft;
}
