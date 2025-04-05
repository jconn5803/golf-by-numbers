// Overall references
const filterForm = document.getElementById("filterForm");
// For the strokes gained chart, we now expect a div container (not a canvas)
const sgChartContainer = document.getElementById("sgChart");
const distanceHistogramCanvas = document.getElementById("distanceHistogram");

// Overall tab card elements
const scoringAvgCard = document.getElementById("scoringAvgCard");
const scoringVsParCard = document.getElementById("scoringVsParCard");
const totalRoundsCard = document.getElementById("totalRoundsCard");
const par3Card = document.getElementById("par3Card");
const par4Card = document.getElementById("par4Card");
const par5Card = document.getElementById("par5Card");

// Overall tab: Reference for the line chart
const roundPerformanceCanvas = document.getElementById("roundPerformanceChart");
let roundPerformanceChart;

// Tee tab elements
const teeSGCard = document.getElementById("teeSGCard");
const teeDistanceCard = document.getElementById("teeDistanceCard");
let teeMissChart;

// Approach tab elements
const approachSGCard = document.getElementById("approachSGCard");
const approachGirCard = document.getElementById("approachGirCard");
// (We use D3 for the miss directions)

// Short Game tab elements
const upDownPercentCard = document.getElementById("upDownPercentCard");
const aroundGreenSGCard = document.getElementById("aroundGreenSGCard");

// Putting tab elements
const puttingSGCard = document.getElementById("puttingSGCard");

// Chart.js variable for the distance histogram (strokes gained now uses D3)
let distanceHistogram; 

filterForm.addEventListener("submit", function(e) {
  e.preventDefault();
  updateDashboard();
});

async function updateRoundPerformanceChart(params) {
  const roundRes = await fetch(`/api/rounds?${params.toString()}`);
  const roundData = await roundRes.json();

  const labels = roundData.map(r => `Round ${r.roundID}`);
  const scores = roundData.map(r => r.score_to_par);
  const tooltips = roundData.map(r => ({
    course: r.course_name,
    date: r.date_played,
    score: r.score_to_par
  }));

  if (roundPerformanceChart) {
    roundPerformanceChart.destroy();
  }

  roundPerformanceChart = new Chart(roundPerformanceCanvas, {
    type: "line",
    data: {
      labels: labels,
      datasets: [{
        label: "Score to Par",
        data: scores,
        borderColor: "rgba(75, 192, 192, 1)",
        backgroundColor: "rgba(75, 192, 192, 0.2)",
        borderWidth: 2,
        pointRadius: 5,
        pointHoverRadius: 7,
        pointBackgroundColor: "rgba(75, 192, 192, 1)"
      }]
    },
    options: {
      responsive: true,
      plugins: {
        tooltip: {
          callbacks: {
            title: (context) => {
              const index = context[0].dataIndex;
              return `Course: ${tooltips[index].course}`;
            },
            label: (context) => {
              const index = context.dataIndex;
              return [
                `Date Played: ${tooltips[index].date}`,
                `Score: ${tooltips[index].score}`
              ];
            }
          }
        },
        annotation: {
          annotations: {
            zeroLine: {
              type: 'line',
              yMin: 0,
              yMax: 0,
              borderColor: 'red',
              borderDash: [5, 5],
              borderWidth: 2,
            }
          }
        }
      },
      scales: {
        x: {
          title: {
            display: true,
            text: "Rounds Played"
          },
          ticks: { display: false }
        },
        y: {
          beginAtZero: true,
          title: { display: true, text: "Score to Par" }
        }
      }
    }
  });
}

async function updateApproachTable(params) {
  try {
    const response = await fetch(`/api/approach_table?${params.toString()}`);
    if (!response.ok) throw new Error("Failed to fetch Approach Table data");

    const data = await response.json(); // { approachData: [{ distanceRange, sgPerShot, avgProximity, greenHitPct }, ...] }
    const tableBody = document.getElementById("approachTableBody");
    if (!tableBody) {
      console.error("No table body with id 'approachTableBody' found.");
      return;
    }

    tableBody.innerHTML = "";
    
    if (data.approachData && Array.isArray(data.approachData)) {
      data.approachData.forEach(row => {
        console.log("Row data:", row);
        const displaySg = row.sgPerShot > 0 ? `+${row.sgPerShot}` : row.sgPerShot;
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${row.distanceRange}</td>
          <td>${displaySg}</td>
          <td>${row.avgProximity}</td>
          <td>${row.greenHitPct}%</td>
        `;
        tableBody.appendChild(tr);
      });
    }
  } catch (err) {
    console.error("Error updating approach table:", err);
  }
}

async function updateDashboard() {
  const params = new URLSearchParams({
    course: document.getElementById("course").value,
    round: document.getElementById("round").value,
    startDate: document.getElementById("startDate").value,
    endDate: document.getElementById("endDate").value,
  });

  // 1) Overall Stats
  const statsRes = await fetch(`/api/dashboard_stats?${params.toString()}`);
  const statsData = await statsRes.json();
  
  totalRoundsCard.textContent = statsData.total_rounds;

  if (statsData.total_rounds === 0){
    scoringAvgCard.textContent = "--";
    scoringVsParCard.textContent = "--";
    par3Card.textContent = "--";
    par4Card.textContent = "--";
    par5Card.textContent = "--";
  } else {
    scoringAvgCard.textContent = statsData.scoring_avg;
    scoringVsParCard.textContent = statsData.scoring_avg_to_par > 0 
      ? `+${statsData.scoring_avg_to_par}` 
      : statsData.scoring_avg_to_par;
    par3Card.textContent = statsData.par3_avg;
    par4Card.textContent = statsData.par4_avg;
    par5Card.textContent = statsData.par5_avg;
  }

  // 2) Overall Strokes Gained Chart (using D3.js inline)
  // Remove any previous SVG in the container.
  d3.select("#sgChart").select("svg").remove();

  const container = sgChartContainer;
  const containerWidth = container.clientWidth || 400;
  const margin = { top: 20, right: 20, bottom: 40, left: 40 };
  const width = containerWidth - margin.left - margin.right;
  const height = 300 - margin.top - margin.bottom;

  const svg = d3.select("#sgChart")
    .append("svg")
    .attr("width", containerWidth)
    .attr("height", height + margin.top + margin.bottom)
    .attr("viewBox", `0 0 ${containerWidth} ${height + margin.top + margin.bottom}`)
    .attr("preserveAspectRatio", "xMidYMid meet")
    .append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

  // Fetch strokes gained data.
  const sgRes = await fetch(`/api/sg_by_shot_type?${params.toString()}`);
  const sgData = await sgRes.json();
  console.log(sgData)

  // Conditionally abbreviate the labels on small screens.
if (window.innerWidth < 1000) {
  sgData.labels = sgData.labels.map(label => {
    switch(label) {
      case "Off the Tee":
        return "OTT";
      case "Approach":
        return "APP";
      case "Around the Green":
        return "ATG";
      case "Putting":
        return "PUT";
      default:
        return label;
    }
  });
}

  const x = d3.scaleBand()
    .domain(sgData.labels)
    .range([0, width])
    .padding(0.1);

  const yMin = d3.min(sgData.values, d => d);
  const yMax = d3.max(sgData.values, d => d);
  const y = d3.scaleLinear()
    .domain([Math.min(0, yMin), yMax])
    .nice()
    .range([height, 0]);

  // Draw the bars.
// Draw the bars with custom fill and stroke.
svg.selectAll(".bar")
  .data(sgData.values)
  .enter()
  .append("rect")
  .attr("class", "bar")
  .attr("x", (d, i) => x(sgData.labels[i]))
  .attr("y", d => d >= 0 ? y(d) : y(0))
  // .on("mouseover", onMouseOver )
  // .on("mouseout", onMouseOut )
  .attr("width", x.bandwidth())
  .transition()
  .ease(d3.easeLinear)
  .duration(1000)
  .delay(function(d,i){ return i*50})
  .attr("height", d => Math.abs(y(d) - y(0)))
  .attr("fill", d => d >= 0 ? "#90ee90" : "#ffcccb")    // Light green for positive, light red for negative.
  .attr("stroke", d => d >= 0 ? "#006400" : "#8B0000")    // Dark green for positive, dark red for negative.
  .attr("stroke-width", 1);



// Add labels to each bar (rounded to 2 decimal places).
svg.selectAll(".bar-label")
.data(sgData.values)
.enter()
.append("text")
.attr("class", "bar-label")
.attr("x", (d, i) => x(sgData.labels[i]) + x.bandwidth() / 2)
.attr("y", d => d >= 0 ? y(d) - 10 : y(d) + 22)
.attr("fill", d => d >= 0 ? "green" : "red")
.attr("text-anchor", "middle")
.text(d => d.toFixed(2));

// Draw a horizontal black line for the x-axis.
svg.append("line")
.attr("x1", 0)
.attr("x2", width)
.attr("y1", y(0))
.attr("y2", y(0))
.attr("stroke", "black");

// Add labels to each bar using the JSON key, positioned based on the data value.
svg.selectAll(".bar-labels")
  .data(sgData.values)
  .enter()
  .append("text")
  .attr("class", "bar-label")
  .attr("x", (d, i) => x(sgData.labels[i]) + x.bandwidth() / 2)
  .attr("y", d => d > 0 ? y(0) + 20 : y(0) - 10)
  .attr("fill", "grey")
  .attr("text-anchor", "middle")
  .text((d, i) => sgData.labels[i]);



  // 3) Round Performance Chart
  updateRoundPerformanceChart(params);

  // 4) Tee Stats
  const teeRes = await fetch(`/api/tee_stats?${params.toString()}`);
  const teeData = await teeRes.json();

  if (statsData.total_rounds === 0){
    teeSGCard.textContent = "--";
    teeDistanceCard.textContent = "--";
    document.getElementById("teeLieCard").textContent = "--%";
  } else {
    teeSGCard.textContent = teeData.avg_off_tee_sg > 0 
      ? `+${teeData.avg_off_tee_sg}` 
      : teeData.avg_off_tee_sg;
    teeDistanceCard.textContent = Math.round(teeData.avg_tee_distance) + "yds";
    document.getElementById("teeLieCard").textContent = teeData.cumulativeLiePct + "%";
  }
  let leftCount = 0, rightCount = 0, centerCount = 0;
  const directions = teeData.miss_directions;
  const counts = teeData.miss_counts;
  let totalShots = 0;
  for (let i = 0; i < directions.length; i++) {
    const dir = directions[i].toLowerCase();
    const count = counts[i];
    totalShots += count;
    if (dir.includes("left")) {
      leftCount += count;
    } else if (dir.includes("right")) {
      rightCount += count;
    } else {
      centerCount += count;
    }
  }
  if (totalShots > 0) {
    const leftPct = (leftCount / totalShots) * 100;
    const rightPct = (rightCount / totalShots) * 100;
    const centerPct = (centerCount / totalShots) * 100;
    document.getElementById("leftMissSection").style.width = `${leftPct}%`;
    document.getElementById("leftMissSection").textContent = leftCount > 0 ? `Left ${leftPct.toFixed(1)}%` : "";
    document.getElementById("centerHitSection").style.width = `${centerPct}%`;
    document.getElementById("centerHitSection").style.left = `${leftPct}%`;
    document.getElementById("centerHitSection").textContent = centerCount > 0 ? `Fairway ${centerPct.toFixed(1)}%` : "";
    document.getElementById("rightMissSection").style.width = `${rightPct}%`;
    document.getElementById("rightMissSection").style.left = `${leftPct + centerPct}%`;
    document.getElementById("rightMissSection").textContent = rightCount > 0 ? `Right ${rightPct.toFixed(1)}%` : "";
  }

  // 5) Approach Stats (Using D3.js for the miss visualization)
  const approachRes = await fetch(`/api/approach_stats?${params.toString()}`);
  const approachData = await approachRes.json();
  
  if (statsData.total_rounds === 0){
    approachSGCard.textContent = "--";
    approachGirCard.textContent = "--";
  } else {
    approachSGCard.textContent = approachData.avg_approach_sg > 0 
      ? `+${approachData.avg_approach_sg}` 
      : approachData.avg_approach_sg;
    approachGirCard.textContent = approachData.gir_percent + "%";
  }

  const missData = approachData.miss_directions.map((dir, i) => ({
    direction: dir,
    frequency: approachData.miss_counts[i]
  }));

  const totalApproachShotsForD3 = approachData.total_approach_shots || 0;
  const girShots = Math.round((approachData.greens_hit / 100) * totalApproachShotsForD3);

  d3.select("#approachMissChart").selectAll("*").remove();

  const widthD3 = 400,
        heightD3 = 400,
        marginD3 = 20,
        radius = Math.min(widthD3, heightD3) / 2 - marginD3;

  const svgApproach = d3.select("#approachMissChart")
                .append("svg")
                .attr("width", widthD3)
                .attr("height", heightD3)
                .append("g")
                .attr("transform", `translate(${widthD3/2},${heightD3/2})`);

  const tooltip = d3.select("body")
    .append("div")
    .attr("class", "d3-tooltip")
    .style("position", "absolute")
    .style("padding", "4px 8px")
    .style("font", "12px sans-serif")
    .style("background", "lightsteelblue")
    .style("border-radius", "4px")
    .style("pointer-events", "none")
    .style("opacity", 0);

  const numSlices = missData.length;
  const angleDelta = 2 * Math.PI / numSlices;
  const maxFreq = d3.max(missData, d => d.frequency);
  const rScale = d3.scaleLinear()
                   .domain([0, maxFreq])
                   .range([radius * 0.3, radius]);

  const dataWithAngles = missData.map((d, i) => ({
    direction: d.direction,
    frequency: d.frequency,
    startAngle: i * angleDelta + (22.5 * Math.PI / 180),
    endAngle: (i + 1) * angleDelta + (22.5 * Math.PI / 180)
  }));

  const arc = d3.arc()
                .innerRadius(radius * 0.3)
                .outerRadius(d => rScale(d.frequency))
                .startAngle(d => d.startAngle)
                .endAngle(d => d.endAngle);

  svgApproach.selectAll("path")
      .data(dataWithAngles)
      .enter()
      .append("path")
      .attr("d", arc)
      .attr("fill", 'red')
      .attr("stroke", "white")
      .style("stroke-width", "2px")
      .on("mouseover", function(event, d) {
         tooltip.transition().duration(200).style("opacity", 0.9);
         tooltip.html(`<strong>${d.direction}</strong>: ${d.frequency}`)
                .style("left", (event.pageX + 10) + "px")
                .style("top", (event.pageY - 28) + "px");
      })
      .on("mousemove", function(event, d) {
         tooltip.style("left", (event.pageX + 10) + "px")
                .style("top", (event.pageY - 28) + "px");
      })
      .on("mouseout", function(event, d) {
         tooltip.transition().duration(500).style("opacity", 0);
      });

  const centerRadius = radius * 0.3;
  svgApproach.append("circle")
      .attr("cx", 0)
      .attr("cy", 0)
      .attr("r", centerRadius)
      .attr("fill", "green")
      .attr("opacity", 0.8);

  svgApproach.append("text")
      .attr("text-anchor", "middle")
      .attr("dy", "0.35em")
      .style("font-size", "14px")
      .style("fill", "white")
      .text(`Green: ${approachData.greens_hit.toFixed(1)}%`);

  // 6) Update Approach Shots Table
  await updateApproachTable(params);

  // 7) Short Game Stats
  const sgShortRes = await fetch(`/api/short_game_stats?${params.toString()}`);
  const sgShortData = await sgShortRes.json();
  
  if (statsData.total_rounds === 0){
    upDownPercentCard.textContent = "--";
    aroundGreenSGCard.textContent = "--";
  } else {
    aroundGreenSGCard.textContent = sgShortData.avg_around_green_sg > 0 
      ? `+${sgShortData.avg_around_green_sg}` 
      : sgShortData.avg_around_green_sg;
    upDownPercentCard.textContent = sgShortData.up_down_percent + "%";
  }

  const bunkerContainer = document.getElementById("bunkerTableBody");
  bunkerContainer.innerHTML = "";
  const noBunkerData = !sgShortData.bunkerData || sgShortData.bunkerData.length === 0
                      || sgShortData.bunkerData.every(row => 
                            row.avgProximity === 0 && row.upDownPercent === 0
                          );
  if (!sgShortData.bunkerData) {
    console.warn("No bunkerData array in sgShortData");
    return; 
  }
  sgShortData.bunkerData.forEach(row => {
    const tr = document.createElement("tr");
    if (noBunkerData) {
      tr.innerHTML = `
        <td>${row.distanceRange}</td>
        <td>--</td>
        <td>--</td>
      `;
    } else {
      tr.innerHTML = `
        <td>${row.distanceRange}</td>
        <td>${row.avgProximity}</td>
        <td>${row.upDownPercent}%</td>
      `;
    }
    bunkerContainer.appendChild(tr);
  });

  // 8) Non-Bunker Shots Table
  const nonBunkerContainer = document.getElementById("nonBunkerTableBody");
  nonBunkerContainer.innerHTML = "";
  const noNonBunkerData = !sgShortData.nonBunkerData || sgShortData.nonBunkerData.length === 0
                          || sgShortData.nonBunkerData.every(row => 
                              row.avgProximity === 0 && row.upDownPercent === 0
                            );
  if (!sgShortData.nonBunkerData) {
    console.warn("No nonBunkerData array in sgShortData");
    return;
  }
  sgShortData.nonBunkerData.forEach(row => {
    const tr = document.createElement("tr");
    if (noNonBunkerData) {
      tr.innerHTML = `
        <td>${row.distanceRange}</td>
        <td>--</td>
        <td>--</td>
      `;
    } else {
      tr.innerHTML = `
        <td>${row.distanceRange}</td>
        <td>${row.avgProximity}</td>
        <td>${row.upDownPercent}%</td>
      `;
    }
    nonBunkerContainer.appendChild(tr);
  });

  // 9) Putting Stats
  const puttingRes = await fetch(`/api/putting_stats?${params.toString()}`);
  const puttingData = await puttingRes.json();
  
  if (statsData.total_rounds === 0){
    puttingSGCard.textContent = "--";
  } else {
    puttingSGCard.textContent = puttingData.avg_putting_sg > 0 
      ? `+${puttingData.avg_putting_sg}` 
      : puttingData.avg_putting_sg;
  }

  const puttingTableBody = document.getElementById("puttingTableBody");
  puttingTableBody.innerHTML = "";
  const noPuttingData = !puttingData.puttingData || puttingData.puttingData.length === 0
    || puttingData.puttingData.every(row =>
        row.makeRate === 0 && row.threePuttAvoid === 0 && row.avgNextPuttDist === 0
      );
  if (puttingData.puttingData && Array.isArray(puttingData.puttingData)) {
    puttingData.puttingData.forEach(row => {
      const tr = document.createElement("tr");
      if (noPuttingData) {
        tr.innerHTML = `
          <td>${row.distanceRange}</td>
          <td>--</td>
          <td>--</td>
          <td>--</td>
        `;
      } else {
        tr.innerHTML = `
          <td>${row.distanceRange}</td>
          <td>${row.makeRate}%</td>
          <td>${row.threePuttAvoid}%</td>
          <td>${row.avgNextPuttDist}</td>
        `;
      }
      puttingTableBody.appendChild(tr);
    });
  }

  // 10) Distance Histogram (Overall)
  const histRes = await fetch(`/api/distance_histogram?${params.toString()}`);
  const histData = await histRes.json();
  if (distanceHistogram) {
    distanceHistogram.destroy();
  }
  const distCtx = distanceHistogramCanvas.getContext("2d");
  distanceHistogram = new Chart(distCtx, {
    type: "bar",
    data: {
      labels: histData.bin_labels,
      datasets: [{
        label: "Count of Shots",
        data: histData.bin_counts,
        backgroundColor: "rgba(54, 162, 235, 0.6)",
        borderColor: "rgba(54, 162, 235, 1)",
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      scales: {
        x: {
          title: {
            display: true,
            text: "Distance From Hole (Yards)"
          }
        },
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: "Count of Shots"
          }
        }
      }
    }
  });
}

document.addEventListener("DOMContentLoaded", updateDashboard);
