const form = document.getElementById("predictionForm");
const resultCard = document.getElementById("resultCard");
const resultText = document.getElementById("resultText");
const confidenceText = document.getElementById("confidenceText");

let gaugeChart;

function debounce(func, delay) {
    let timeout;
    return (...args) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), delay);
    };
}

async function livePredict() {

    let formData = new FormData(form);
    let jsonData = {};

    formData.forEach((value, key) => {
        if(value !== "") {
            jsonData[key] = isNaN(value) ? value : Number(value);
        }
    });

    if(Object.keys(jsonData).length < 5) return;

    const response = await fetch("/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(jsonData)
    });

    const result = await response.json();

    if(result.error) return;

    resultCard.classList.remove("hidden");
    resultCard.classList.add("show");

    let prob = result.probability;

    resultText.innerText = result.prediction === 1
        ? "Rain Expected 🌧"
        : "No Rain ☀️";

    confidenceText.innerText = "Confidence Level: " + prob + "%";

    updateGauge(prob);
}

function updateGauge(value) {

    if(gaugeChart) gaugeChart.destroy();

    const ctx = document.getElementById('gaugeChart');

    gaugeChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [value, 100 - value],
                backgroundColor: [
                    value > 50 ? "#16a34a" : "#2563eb",
                    "#e5e7eb"
                ],
                borderWidth: 0
            }]
        },
        options: {
            cutout: "80%",
            plugins: { legend: { display: false } }
        }
    });
}

form.addEventListener("input", debounce(livePredict, 800));
