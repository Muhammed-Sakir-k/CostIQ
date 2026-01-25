// ===============================
// GLOBAL CHART INSTANCE
// ===============================
let platformChartInstance = null;

// ===============================
// LOAD DASHBOARD DATA
// ===============================
fetch("/admin/click-stats")
.then(res => res.json())
.then(data => {

    // ===============================
    // KPI CARDS
    // ===============================
    animateCount(
    document.getElementById("totalClicks"),
    data.total_clicks
    );
    

    document.getElementById("topPlatform").innerText =
        data.platform_stats[0]?.platform || "-";

    // ===============================
    // BAR CHART (Clicks by Platform)
    // ===============================
    const ctx = document.getElementById("platformChart").getContext("2d");

// ✅ CREATE GRADIENT (THIS IS THE PART YOU ASKED ABOUT)
const gradient = ctx.createLinearGradient(0, 0, 0, 300);
gradient.addColorStop(0, "#38bdf8"); // light blue (top)
gradient.addColorStop(1, "#0ea5e9"); // darker blue (bottom)

// 🔥 Destroy old chart before creating new
if (platformChartInstance) {
    platformChartInstance.destroy();
}

platformChartInstance = new Chart(ctx, {
    type: "bar",
    data: {
        labels: data.platform_stats.map(p => p.platform),
        datasets: [{
            data: data.platform_stats.map(p => p.clicks),
            backgroundColor: gradient,   // 👈 GRADIENT USED HERE
            borderRadius: 8,
            barThickness: 45
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false }
        },
        animation: {
            duration: 1200,
            easing: "easeOutQuart"
        },
        scales: {
            y: {
                beginAtZero: true,
                ticks: {
                    stepSize: 1,               // 🔥 force whole numbers
                    precision: 0,              // 🔥 no decimals
                    callback: value => Math.round(value), // safety
                    color: "#94a3b8"
                },
                grid: {
                    color: "rgba(255,255,255,0.06)"
                }
            },
            x: {
                ticks: { color: "#94a3b8" },
                grid: { display: false }
            }
        }

    }
});


    // ===============================
    // CLICK DETAILS TABLE
    // ===============================
    const tbody = document.querySelector("#clickTable tbody");
    tbody.innerHTML = "";

    data.platform_stats.forEach(p => {
        tbody.innerHTML += `
            <tr>
                <td>${p.platform}</td>
                <td>${p.clicks}</td>
                <td>${p.last_price ? "₹" + p.last_price : "-"}</td>
            </tr>
        `;
    });
});

// ===============================
// VISITOR STATS
// ===============================
fetch("/admin/visitor-stats")
.then(res => res.json())
.then(data => {
    document.getElementById("visitorCount").innerText = data.total;
    document.getElementById("todayVisitorCount").innerText = data.today;
});

// ===============================
// CHANGE PASSWORD
// ===============================
function changePassword() {
    const oldPwd = document.getElementById("oldPwd");
    const newPwd = document.getElementById("newPwd");
    const msg = document.getElementById("pwdMsg");

    msg.innerText = "";
    msg.style.color = "black";

    if (!oldPwd.value || !newPwd.value) {
        msg.innerText = "Please fill all fields";
        msg.style.color = "red";
        return;
    }

    fetch("/admin/change-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            old_password: oldPwd.value,
            new_password: newPwd.value
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status) {
            msg.innerText = "✅ Password updated successfully";
            msg.style.color = "green";
            oldPwd.value = "";
            newPwd.value = "";
        } else {
            msg.innerText = "❌ " + (data.error || "Password update failed");
            msg.style.color = "red";
        }
    })
    .catch(() => {
        msg.innerText = "❌ Server error. Try again.";
        msg.style.color = "red";
    });
}
function animateCount(el, target, duration = 800) {
    if (!el) return;

    target = Number(target) || 0;

    if (target === 0) {
        el.innerText = "0";
        return;
    }

    let start = 0;
    const stepTime = Math.max(20, Math.floor(duration / target));

    const timer = setInterval(() => {
        start++;
        el.innerText = start;
        if (start >= target) {
            el.innerText = target;
            clearInterval(timer);
        }
    }, stepTime);
}
fetch("/admin/click-heatmap")
.then(res => res.json())
.then(data => {
    if (!data.hours || !data.hours.length) return;

    const ctx = document.getElementById("heatmapChart").getContext("2d");

    new Chart(ctx, {
        type: "bar",
        data: {
            labels: data.hours,
            datasets: [{
                label: "Clicks",
                data: data.counts,
                backgroundColor: "#f97316",
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1,        // ✅ whole numbers only
                        precision: 0,
                        callback: v => Math.round(v),
                        color: "#94a3b8"
                    },
                    grid: {
                        color: "rgba(255,255,255,0.06)"
                    }
                },
                x: {
                    ticks: { color: "#94a3b8" },
                    grid: { display: false }
                }
            }
        }
    });
});
