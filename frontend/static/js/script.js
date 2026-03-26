let chart;
console.log("✅ Script loaded");

/* ================================
   NOTIFICATIONS
================================ */
if ("Notification" in window) {
    Notification.requestPermission().then(p => {
        console.log("Notification permission:", p);
    });
}

/* ================================
   SECTION VISIBILITY CONTROLLER
================================ */
function showSection(sectionId) {
    const sections = [
        "hero",
        "features",
        "how",
        "about",
        "resultsSection"
    ];

    sections.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.classList.add("hidden");
    });

    const target = document.getElementById(sectionId);
    if (target) {
        target.classList.remove("hidden");
        target.scrollIntoView({ behavior: "smooth" });
    }
}

/* ================================
   FORM HANDLER
================================ */
function handleSearch(e) {
    e.preventDefault(); // prevent page reload
    searchProduct();
}

/* ================================
   SEARCH PRODUCT
================================ */
function searchProduct() {
    console.log("🔥 searchProduct CALLED");

    const query = document.getElementById("search").value.trim();
    if (!query) return;

    showSection("resultsSection");

    fetch(`http://127.0.0.1:5000/search?q=${encodeURIComponent(query)}`)
        .then(res => res.json())
        .then(data => {
            console.log("DATA RECEIVED:", data);

            if (!data || data.length === 0) return;

            const container = document.getElementById("result");
            container.innerHTML = "";

            // 🔥 Sort lowest price first (extra safety)
            data.sort((a, b) => a.price - b.price);

            let sliderHTML = `
                <div class="swiper mySwiper">
                    <div class="swiper-wrapper">
            `;

            data.forEach(item => {
                sliderHTML += `
                    <div class="swiper-slide product-card">
                        <img src="${item.thumbnail || ''}" 
                             onerror="this.src='https://via.placeholder.com/200'"
                             class="product-img" />

                        <h3>${item.name}</h3>
                        <p>${item.platform}</p>

                        <h2>₹${item.price}</h2>

                        <div class="rating ${item.color}">
                            ${item.score}/10
                        </div>
                    </div>
                `;
            });

            sliderHTML += `
                    </div>
                    <div class="swiper-button-next"></div>
                    <div class="swiper-button-prev"></div>
                </div>
            `;

            container.innerHTML = sliderHTML;

            // 🔥 Initialize Swiper
            new Swiper(".mySwiper", {
                navigation: {
                    nextEl: ".swiper-button-next",
                    prevEl: ".swiper-button-prev",
                },
                loop: false,
            });

            // 🔔 ALERT CHECK
            const alertInput = document.getElementById("alertPrice");
            const alertPrice = alertInput ? Number(alertInput.value) : NaN;

            if (!isNaN(alertPrice)) {
                runPriceAlertCheck(data, alertPrice);
            }

            loadHistory(query);
            loadIntelligence();
            showAlternatives(data);
        })
        .catch(err => console.error("Search failed:", err));
}

/* ================================
   PRICE HISTORY CHART
================================ */
function loadHistory(productName) {
    fetch(`http://127.0.0.1:5000/history?name=${encodeURIComponent(productName)}`)
        .then(res => res.json())
        .then(data => {
            if (!data || Object.keys(data).length === 0) return;

            const labels = [];
            const datasets = [];
            const platforms = Object.keys(data).slice(0, 5);

            platforms.forEach((platform, idx) => {
                const prices = data[platform].map(p => p.price);
                const times = data[platform].map(p => p.ts);

                if (labels.length === 0) labels.push(...times);

                const colors = ["#2563eb", "#16a34a", "#f97316", "#dc2626", "#7c3aed"];

                datasets.push({
                    label: platform,
                    data: prices,
                    borderColor: colors[idx % colors.length],
                    fill: false,
                    tension: 0.35
                });
            });

            const canvas = document.getElementById("priceChart");
            if (!canvas) return;

            const ctx = canvas.getContext("2d");
            if (chart) chart.destroy();

            chart = new Chart(ctx, {
                type: "line",
                data: { labels, datasets },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: "bottom" }
                    }
                }
            });
        });
}

/* ================================
   BEST TIME TO BUY (STATIC CONTENT)
================================ */
function loadIntelligence() {
    const box = document.getElementById("intelligenceBox");
    if (!box) return;

    box.innerHTML = `
        <div class="ai-info">
            <h4>📊 Best Time to Buy</h4>
            <p>
                We continuously track prices across platforms to understand
                stability, drops, and sale patterns.
            </p>
            <ul>
                <li>📉 Price movement trends</li>
                <li>🛒 Platform price stability</li>
                <li>📆 Seasonal discounts</li>
            </ul>
            <small>
                Insights improve automatically as more price data is collected.
            </small>
        </div>
    `;
}

/* ================================
   ALTERNATIVE OPTIONS
================================ */
function showAlternatives(data) {
    const box = document.getElementById("alternativeBox");
    box.innerHTML = "";

    if (!data || data.length === 0) {
        box.innerHTML = "<p>No alternative options found.</p>";
        return;
    }

    data.sort((a, b) => a.price - b.price);

    data.forEach((item, index) => {
        const isBest = index === 0;
        const link = item.link || "#";

        box.innerHTML += `
            <div class="alt-item ${isBest ? "best" : ""}">
                <div class="alt-left">
                    <strong>${item.platform}</strong>
                    <span class="alt-price">₹${item.price}</span>
                    ${isBest ? '<span class="best-badge">Best Price</span>' : ''}
                </div>

                <a href="${link}"
                   target="_blank"
                   class="buy-btn ${isBest ? "best" : ""}">
                   Buy Now →
                </a>
            </div>
        `;
    });
}

/* ================================
   PRICE ALERT
================================ */
function runPriceAlertCheck(data, alertPrice) {
    let bestDeal = null;

    data.forEach(item => {
        if (item.price <= alertPrice) {
            if (!bestDeal || item.price < bestDeal.price) {
                bestDeal = item;
            }
        }
    });

    if (!("Notification" in window)) return;
    if (Notification.permission !== "granted") return;

    if (bestDeal) {
        new Notification("SmartPrice Alert 🚨", {
            body: `Price dropped on ${bestDeal.platform} to ₹${bestDeal.price}`
        });
    } else {
        new Notification("SmartPrice Update ⏳", {
            body: "Price has not reached your target yet."
        });
    }
}
fetch("/api/buy-decision")
  .then(res => res.json())
  .then(data => {
    const box = document.getElementById("buyDecisionBox");
    box.innerHTML = ""; // clear old content

    data.forEach(item => {
      const div = document.createElement("div");
      div.className = `decision ${item.action.toLowerCase()}`;
      div.innerHTML = `
        <span>${item.action} — ${item.platform}</span>
        <p>${item.reason}</p>
      `;
      box.appendChild(div);
    });
  });
fetch("/api/price-history")
  .then(res => res.json())
  .then(data => {
    new Chart(document.getElementById("priceChart"), {
      type: "line",
      data: {
        labels: data.labels,
        datasets: [{
          label: "Best Price Trend",
          data: data.prices,
          borderColor: "#2563eb",
          backgroundColor: "rgba(37,99,235,0.1)",
          fill: true,
          tension: 0.4,
          pointRadius: 4
        }]
      },
      options: {
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: {
            ticks: {
              callback: value => "₹" + value
            }
          }
        }
      }
    });
  });

