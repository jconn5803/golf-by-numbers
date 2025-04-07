// Overall references
const filterForm = document.getElementById("filterForm");
// For the strokes gained chart, we now expect a div container (not a canvas)
const sgChartContainer = document.getElementById("sgChart");
console.log(sgChartContainer)
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


// Approach tab elements
const approachSGCard = document.getElementById("approachSGCard");
const approachGirCard = document.getElementById("approachGirCard");


// Short Game tab elements
const upDownPercentCard = document.getElementById("upDownPercentCard");
const aroundGreenSGCard = document.getElementById("aroundGreenSGCard");


// Putting tab elements
const puttingSGCard = document.getElementById("puttingSGCard");



// Chart.js variable for the distance histogram (strokes gained now uses D3)
let distanceHistogram;

// Event Listeners
filterForm.addEventListener("submit", function(e) {
  e.preventDefault();
  updateDashboard();
});

document.addEventListener("DOMContentLoaded", updateDashboard);

//────────────────────────────
// Existing functions remain
//────────────────────────────

async function updateRoundPerformanceChart(params) {
  // Fetch rounds data.
  const roundRes = await fetch(`/api/rounds?${params.toString()}`);
  let roundData = await roundRes.json();

  // Sort rounds chronologically by date_played.
  roundData.sort((a, b) => new Date(a.date_played) - new Date(b.date_played));

  // Create labels (using "Round {roundID}") in sorted order.
  const labels = roundData.map(r => `Round ${r.roundID}`);
  const scores = roundData.map(r => r.score_to_par);
  const tooltips = roundData.map(r => ({
    course: r.course_name,
    date: r.date_played,
    score: r.score_to_par
  }));

  // Remove any existing SVG.
  const container = d3.select(roundPerformanceCanvas);
  container.select("svg").remove();

  // Define margins and dimensions.
  const margin = { top: 20, right: 30, bottom: 50, left: 50 };
  const containerWidth = container.node().clientWidth || 400;
  const width = containerWidth - margin.left - margin.right;
  const height = 300 - margin.top - margin.bottom;

  // Create the SVG container.
  const svg = container.append("svg")
    .attr("width", containerWidth)
    .attr("height", height + margin.top + margin.bottom)
    .attr("viewBox", `0 0 ${containerWidth} ${height + margin.top + margin.bottom}`)
    .attr("preserveAspectRatio", "xMidYMid meet")
    .append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

  // Use the sorted roundData as the domain for a point scale.
  const xScale = d3.scalePoint()
    .domain(roundData)  // Domain is the array of round objects.
    .range([0, width])
    .padding(0.5);

  // Create the y scale based on the score values.
  const yMin = d3.min(scores);
  const yMax = d3.max(scores);
  const yScale = d3.scaleLinear()
    .domain([Math.min(0, yMin), yMax])
    .nice()
    .range([height, 0]);

  // Create the x-axis using a custom tick format to display the date.
  const xAxis = d3.axisBottom(xScale)
    .tickFormat(d => d3.timeFormat("%b %d")(new Date(d.date_played)));
  svg.append("g")
    .attr("class", "x-axis")
    .attr("transform", `translate(0, ${height})`)
    .call(xAxis)
    .selectAll("text")
    .attr("transform", "rotate(-45)")
    .style("text-anchor", "end");

  // Create the y-axis with a custom tick formatter to add a plus sign for positive scores.
  const yAxis = d3.axisLeft(yScale)
    .tickFormat(d => d >= 0 ? `+${d}` : d);
  svg.append("g")
    .attr("class", "y-axis")
    .call(yAxis);

  // Append axis titles.
  svg.append("text")
    .attr("class", "x-axis-title")
    .attr("x", width / 2)
    .attr("y", height + margin.bottom - 5)
    .attr("text-anchor", "middle")
    .text("Date Played");

  svg.append("text")
    .attr("class", "y-axis-title")
    .attr("transform", "rotate(-90)")
    .attr("x", -height / 2)
    .attr("y", -margin.left + 15)
    .attr("text-anchor", "middle")
    .text("Score to Par");

  // Create the line generator.
  const line = d3.line()
    .x((d, i) => xScale(roundData[i]))
    .y((d, i) => yScale(scores[i]))
    .curve(d3.curveMonotoneX);

  // Append the line path.
  svg.append("path")
    .datum(scores)
    .attr("fill", "none")
    .attr("stroke", "steelblue")
    .attr("stroke-width", 2)
    .attr("d", line);

  // Create a tooltip div.
  const tooltip = d3.select("body")
    .append("div")
    .attr("class", "d3-tooltip")
    .style("position", "absolute")
    .style("padding", "6px")
    .style("background", "rgba(0, 0, 0, 0.6)")
    .style("color", "white")
    .style("border-radius", "4px")
    .style("pointer-events", "none")
    .style("opacity", 0);

  // Append circles at each data point with tooltip interactions.
  svg.selectAll("circle")
    .data(scores)
    .enter()
    .append("circle")
    .attr("cx", (d, i) => xScale(roundData[i]))
    .attr("cy", (d, i) => yScale(scores[i]))
    .attr("r", 5)
    .attr("fill", "white")
    .attr("stroke", "steelblue")
    .attr("stroke-width", 2)
    .on("mouseover", function(event, d) {
      const index = svg.selectAll("circle").nodes().indexOf(this);
      tooltip.transition().duration(200).style("opacity", 0.9);
      const scoreDisplay = tooltips[index].score >= 0 
                           ? `+${tooltips[index].score}` 
                           : tooltips[index].score;
      tooltip.html(`<strong>Course:</strong> ${tooltips[index].course}<br/>
                    <strong>Date Played:</strong> ${tooltips[index].date}<br/>
                    <strong>Score:</strong> ${scoreDisplay}`)
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

  // Append a horizontal dashed red line at y = 0.
  svg.append("line")
    .attr("x1", 0)
    .attr("x2", width)
    .attr("y1", yScale(0))
    .attr("y2", yScale(0))
    .attr("stroke", "red")
    .attr("stroke-dasharray", "5,5")
    .attr("stroke-width", 2);
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

//────────────────────────────
// New Visual Functions
//────────────────────────────

async function updateOverallStats(params) {
  const statsRes = await fetch(`/api/dashboard_stats?${params.toString()}`);
  const statsData = await statsRes.json();

  totalRoundsCard.textContent = statsData.total_rounds;

  if (statsData.total_rounds === 0) {
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
  return statsData; // Return for use in other functions if needed.
}

async function updateStrokesGainedChart(params) {
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
  console.log(sgData);

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
  svg.selectAll(".bar")
    .data(sgData.values)
    .enter()
    .append("rect")
    .attr("class", "bar")
    .attr("x", (d, i) => x(sgData.labels[i]))
    .attr("y", d => d >= 0 ? y(d) : y(0))
    .attr("width", x.bandwidth())
    .transition()
    .ease(d3.easeLinear)
    .duration(1000)
    .delay((d, i) => i * 50)
    .attr("height", d => Math.abs(y(d) - y(0)))
    .attr("fill", d => d >= 0 ? "#90ee90" : "#ffcccb")
    .attr("stroke", d => d >= 0 ? "#006400" : "#8B0000")
    .attr("stroke-width", 1);

  // Add labels to each bar.
  svg.selectAll(".bar-label")
    .data(sgData.values)
    .enter()
    .append("text")
    .attr("class", "bar-label")
    .attr("x", (d, i) => x(sgData.labels[i]) + x.bandwidth() / 2)
    .attr("y", d => d >= 0 ? y(d) - 10 : y(d) + 22)
    .attr("fill", d => d >= 0 ? "green" : "red")
    .attr("text-anchor", "middle")
    .text(d => d > 0 ? `+${d.toFixed(2)}` : d.toFixed(2));

  // Draw a horizontal line for the x-axis.
  svg.append("line")
    .attr("x1", 0)
    .attr("x2", width)
    .attr("y1", y(0))
    .attr("y2", y(0))
    .attr("stroke", "black");

  // Add labels below the x-axis.
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
}

async function updateTeeStats(params, statsData) {
  const teeRes = await fetch(`/api/tee_stats?${params.toString()}`);
  const teeData = await teeRes.json();

  if (statsData.total_rounds === 0) {
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
}

async function updateApproachStats(params, statsData) {
  const approachRes = await fetch(`/api/approach_stats?${params.toString()}`);
  const approachData = await approachRes.json();
  
  if (statsData.total_rounds === 0) {
    approachSGCard.textContent = "--";
    approachGirCard.textContent = "--";
  } else {
    approachSGCard.textContent = approachData.avg_approach_sg > 0 
      ? `+${approachData.avg_approach_sg}` 
      : approachData.avg_approach_sg;
    approachGirCard.textContent = approachData.gir_percent + "%";
  }

  // Use total approach shots from the JSON to calculate percentages
  const totalApproachShots = approachData.total_approach_shots;

  // Map miss directions to include frequency and percentage relative to total approach shots
  const missData = approachData.miss_directions.map((dir, i) => {
    const count = approachData.miss_counts[i];
    const percentage = totalApproachShots > 0 ? ((count / totalApproachShots) * 100).toFixed(1) : 0;
    return { direction: dir, frequency: count, percentage: percentage };
  });

  // Clear the previous chart content
  d3.select("#approachMissChart").selectAll("*").remove();

  // Call the function to create the D3 chart
  createApproachMissChart(missData, approachData);

  // Update approach table
  await updateApproachTable(params);
}



// New function to update a SG chart with a 10-round rolling average.
// New responsive updateSgChart function
async function updateSgChart(containerId, endpointUrl, sgField) {
  try {
    // Fetch data from the endpoint.
    const res = await fetch(endpointUrl);
    let data = await res.json();

    // Sort data chronologically based on date_played.
    data.sort((a, b) => new Date(a.date_played) - new Date(b.date_played));

    // Compute a 10-round rolling average for the provided sgField.
    data.forEach((d, i) => {
      const start = Math.max(0, i - 9);
      const windowData = data.slice(start, i + 1);
      const sum = windowData.reduce((acc, cur) => acc + cur[sgField], 0);
      d.rollingAvg = sum / windowData.length;
    });

    // Select the container and remove any existing SVG.
    const container = d3.select(`#${containerId}`);
    container.select("svg").remove();

    // Define margins and dimensions based on the container's current width.
    const margin = { top: 20, right: 30, bottom: 50, left: 50 };
    const containerWidth = container.node().clientWidth || 400;
    const width = containerWidth - margin.left - margin.right;
    const height = 300 - margin.top - margin.bottom;

    // Create the SVG container with a viewBox for responsiveness.
    const svg = container.append("svg")
      .attr("width", containerWidth)
      .attr("height", height + margin.top + margin.bottom)
      .attr("viewBox", `0 0 ${containerWidth} ${height + margin.top + margin.bottom}`)
      .attr("preserveAspectRatio", "xMidYMid meet")
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    // Create an x-scale using the roundID values.
    const xScale = d3.scalePoint()
      .domain(data.map(d => d.roundID))
      .range([0, width])
      .padding(0.5);

    // Create a y-scale based on the raw SG and rolling average values.
    const yMin = d3.min(data, d => Math.min(d[sgField], d.rollingAvg));
    const yMax = d3.max(data, d => Math.max(d[sgField], d.rollingAvg));
    const yScale = d3.scaleLinear()
      .domain([Math.min(0, yMin), yMax])
      .nice()
      .range([height, 0]);

    // Append the x-axis.
    const xAxis = d3.axisBottom(xScale);
    svg.append("g")
      .attr("class", "x-axis")
      .attr("transform", `translate(0, ${height})`)
      .call(xAxis)
      .selectAll("text")
      .attr("transform", "rotate(-45)")
      .style("text-anchor", "end");

    // Append the y-axis.
    const yAxis = d3.axisLeft(yScale);
    svg.append("g")
      .attr("class", "y-axis")
      .call(yAxis);

    // Add axis titles.
    svg.append("text")
      .attr("class", "x-axis-title")
      .attr("x", width / 2)
      .attr("y", height + margin.bottom - 5)
      .attr("text-anchor", "middle")
      .text("Round ID");

    svg.append("text")
      .attr("class", "y-axis-title")
      .attr("transform", "rotate(-90)")
      .attr("x", -height / 2)
      .attr("y", -margin.left + 15)
      .attr("text-anchor", "middle")
      .text("Strokes Gained");

    // Generate the line for raw SG values.
    const lineRaw = d3.line()
      .x(d => xScale(d.roundID))
      .y(d => yScale(d[sgField]))
      .curve(d3.curveMonotoneX);

    svg.append("path")
      .datum(data)
      .attr("fill", "none")
      .attr("stroke", "steelblue")
      .attr("stroke-width", 2)
      .attr("d", lineRaw);

    // Generate the line for the 10-round rolling average.
    const lineRolling = d3.line()
      .x(d => xScale(d.roundID))
      .y(d => yScale(d.rollingAvg))
      .curve(d3.curveMonotoneX);

    svg.append("path")
      .datum(data)
      .attr("fill", "none")
      .attr("stroke", "orange")
      .attr("stroke-dasharray", "5,5")
      .attr("stroke-width", 2)
      .attr("d", lineRolling);

    // Append circles for each raw SG data point.
    svg.selectAll("circle")
      .data(data)
      .enter()
      .append("circle")
      .attr("cx", d => xScale(d.roundID))
      .attr("cy", d => yScale(d[sgField]))
      .attr("r", 4)
      .attr("fill", "white")
      .attr("stroke", "steelblue")
      .attr("stroke-width", 2);

  } catch (error) {
    console.error(`Error updating chart for ${containerId}:`, error);
  }
}




function createApproachMissChart(missData, approachData) {
  // Get container width (default to 400 if not available)
  const container = d3.select("#approachMissChart");
  const containerWidth = container.node().clientWidth || 400;
  const widthD3 = containerWidth;
  const heightD3 = containerWidth; // Use a square chart; adjust as needed.
  const marginD3 = 20;
  const radius = Math.min(widthD3, heightD3) / 2 - marginD3;

  // Create an SVG that scales responsively.
  const svgApproach = container.append("svg")
    .attr("width", "100%")
    .attr("height", heightD3)
    .attr("viewBox", `0 0 ${widthD3} ${heightD3}`)
    .attr("preserveAspectRatio", "xMidYMid meet")
    .append("g")
    .attr("transform", `translate(${widthD3 / 2}, ${heightD3 / 2})`);

  // Create tooltip
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

  // Prepare the data with fixed angular slices.
  const dataWithAngles = missData.map((d, i) => ({
    direction: d.direction,
    frequency: d.frequency,
    percentage: d.percentage,
    startAngle: i * angleDelta + (22.5 * Math.PI / 180),
    endAngle: (i + 1) * angleDelta + (22.5 * Math.PI / 180)
  }));

  // Define the arc with a fixed inner and outer radius.
  const arc = d3.arc()
    .innerRadius(radius * 0.5)
    .outerRadius(radius)
    .startAngle(d => d.startAngle)
    .endAngle(d => d.endAngle);

  // Append the arcs for each miss direction with a color gradient.
  svgApproach.selectAll("path")
    .data(dataWithAngles)
    .enter()
    .append("path")
    .attr("d", arc)
    .attr("fill", d => {
      // Convert the percentage (0-100) to a number.
      const perc = +d.percentage;
      // Compute a logarithmic factor between 0 and 1.
      const factor = Math.log(perc + 1) / Math.log(101);
      // Interpolate from white (0% miss) to red (100% miss).
      return d3.interpolateRgb("white", "red")(factor);
    })
    .attr("stroke", "#8B0000") // darker red border for the slices.
    .style("stroke-width", "2px")
    .on("mouseover", function(event, d) {
      tooltip.transition().duration(200).style("opacity", 0.9);
      tooltip.html(`<strong>${d.direction}</strong>: ${d.frequency} (${d.percentage}%)`)
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

  // Append percentage labels at the centroid of each arc.
  svgApproach.selectAll("text.label")
    .data(dataWithAngles)
    .enter()
    .append("text")
    .attr("class", "label")
    .attr("transform", d => {
      const c = arc.centroid(d);
      return `translate(${c[0]}, ${c[1]})`;
    })
    .attr("text-anchor", "middle")
    .attr("dy", ".35em")
    .text(d => d.percentage + "%")
    .style("font-size", "16px")
    .style("fill", "black");

  // Draw the inner circle to represent the green hit rate.
  const centerRadius = radius * 0.5;
  svgApproach.append("circle")
    .attr("cx", 0)
    .attr("cy", 0)
    .attr("r", centerRadius)
    .attr("fill", "#90EE90")   // light green fill.
    .attr("stroke", "#006400") // dark green border.
    .style("stroke-width", "2px")
    .attr("opacity", 0.8);

  svgApproach.append("text")
    .attr("text-anchor", "middle")
    .attr("dy", "0.35em")
    .style("font-size", "16px")
    .style("fill", "black")
    .text(`Green: ${approachData.greens_hit.toFixed(1)}%`);
}




async function updateShortGameStats(params, statsData) {
  const sgShortRes = await fetch(`/api/short_game_stats?${params.toString()}`);
  const sgShortData = await sgShortRes.json();
  
  if (statsData.total_rounds === 0) {
    upDownPercentCard.textContent = "--";
    aroundGreenSGCard.textContent = "--";
  } else {
    aroundGreenSGCard.textContent = sgShortData.avg_around_green_sg > 0 
      ? `+${sgShortData.avg_around_green_sg}` 
      : sgShortData.avg_around_green_sg;
    upDownPercentCard.textContent = sgShortData.up_down_percent + "%";
  }

  // Update bunker table.
  const bunkerContainer = document.getElementById("bunkerTableBody");
  bunkerContainer.innerHTML = "";
  const noBunkerData = !sgShortData.bunkerData || sgShortData.bunkerData.length === 0 ||
                        sgShortData.bunkerData.every(row => row.avgProximity === 0 && row.upDownPercent === 0);
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

  // Update non-bunker table.
  const nonBunkerContainer = document.getElementById("nonBunkerTableBody");
  nonBunkerContainer.innerHTML = "";
  const noNonBunkerData = !sgShortData.nonBunkerData || sgShortData.nonBunkerData.length === 0 ||
                           sgShortData.nonBunkerData.every(row => row.avgProximity === 0 && row.upDownPercent === 0);
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
}

async function updatePuttingStats(params, statsData) {
  const puttingRes = await fetch(`/api/putting_stats?${params.toString()}`);
  const puttingData = await puttingRes.json();
  
  if (statsData.total_rounds === 0) {
    puttingSGCard.textContent = "--";
  } else {
    puttingSGCard.textContent = puttingData.avg_putting_sg > 0 
      ? `+${puttingData.avg_putting_sg}` 
      : puttingData.avg_putting_sg;
  }

  const puttingTableBody = document.getElementById("puttingTableBody");
  puttingTableBody.innerHTML = "";
  const noPuttingData = !puttingData.puttingData || puttingData.puttingData.length === 0 ||
    puttingData.puttingData.every(row =>
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
}

//────────────────────────────
// Distance Histogram Functions
//────────────────────────────

async function updateDistanceHistogram(params) {
  const histRes = await fetch(`/api/distance_histogram?${params.toString()}`);
  const histData = await histRes.json();

  // Remove any existing SVG and tooltip.
  d3.select("#distanceHistogram").select("svg").remove();
  d3.selectAll(".tooltip").remove();

  // Prepare data by combining bin labels, counts, and avg strokes gained.
  const data_histogram = histData.bin_labels.map((label, i) => ({
    label: label,
    count: histData.bin_counts[i],
    avg_sg: histData.bin_avg_sg[i]
  }));

  console.log(data_histogram);

  const container_histogram = d3.select("#distanceHistogram");
  const containerWidth_histogram = container_histogram.node().clientWidth || 400;
  const margin_histogram = { top: 20, right: 20, bottom: 50, left: 50 };
  const width_histogram = containerWidth_histogram - margin_histogram.left - margin_histogram.right;
  const height_histogram = 300 - margin_histogram.top - margin_histogram.bottom;

  // Create the SVG container.
  const svg_histogram = container_histogram.append("svg")
    .attr("width", containerWidth_histogram)
    .attr("height", height_histogram + margin_histogram.top + margin_histogram.bottom)
    .attr("viewBox", `0 0 ${containerWidth_histogram} ${height_histogram + margin_histogram.top + margin_histogram.bottom}`)
    .attr("preserveAspectRatio", "xMidYMid meet")
    .append("g")
    .attr("transform", `translate(${margin_histogram.left},${margin_histogram.top})`);

  // Create x scale as a band scale for the bin labels.
  const x_histogram = d3.scaleBand()
    .domain(data_histogram.map(d => d.label))
    .range([0, width_histogram])
    .padding(0.1);

  // Create y scale as a linear scale for the counts.
  const y_histogram = d3.scaleLinear()
    .domain([0, d3.max(data_histogram, d => d.count)])
    .nice()
    .range([height_histogram, 0]);

  // Non-linearity exponents. Adjust these to change the gradient steepness.
  const exponentGreen = 0.8;  // For positive avg SG values (0 to 1)
  const exponentRed = 0.8;    // For negative avg SG values (0 to -1)

  // Helper function to get the bar fill color using a non-linear transformation.
  function getBarColor(avg_sg) {
    if (avg_sg < 0) {
      let t = Math.min(Math.abs(avg_sg) / 1, 1);
      t = Math.pow(t, exponentRed);
      return d3.interpolateReds(t);
    } else {
      let t = Math.min(avg_sg / 1, 1);
      t = Math.pow(t, exponentGreen);
      return d3.interpolateGreens(t);
    }
  }

  // Helper function for a constant border color.
  function getBarBorderColor(avg_sg) {
    return avg_sg >= 0 ? d3.interpolateGreens(0.8) : d3.interpolateReds(0.8);
  }

  // Define a tooltip div that is hidden by default.
  const tooltip = d3.select("body")
    .append("div")
    .attr("class", "tooltip")
    .style("position", "absolute")
    .style("padding", "6px")
    .style("background", "rgba(0, 0, 0, 0.6)")
    .style("color", "white")
    .style("border-radius", "4px")
    .style("pointer-events", "none")
    .style("opacity", 0);

  // Create the bars and attach event listeners.
  const bars = svg_histogram.selectAll(".bar")
    .data(data_histogram)
    .enter()
    .append("rect")
    .attr("class", "bar")
    .attr("x", d => x_histogram(d.label))
    // Start bars at the bottom with zero height for transition.
    .attr("y", y_histogram(0))
    .attr("width", x_histogram.bandwidth())
    .attr("height", 0)
    .attr("fill", d => getBarColor(d.avg_sg))
    .attr("stroke", d => getBarBorderColor(d.avg_sg))
    .attr("stroke-width", 1)
    .on("mouseover", function(event, d) {
      tooltip.transition().duration(200).style("opacity", 0.9);
      tooltip.html(`<strong>${d.label}</strong>: ${d.count}<br/>Avg SG: ${d.avg_sg.toFixed(2)}`);
    })
    .on("mousemove", function(event, d) {
      tooltip.style("left", (event.pageX + 10) + "px")
             .style("top", (event.pageY - 28) + "px");
    })
    .on("mouseout", function(event, d) {
      tooltip.transition().duration(500).style("opacity", 0);
    });

  // Transition to animate bar height.
  bars.transition()
    .ease(d3.easeLinear)
    .duration(1000)
    .delay((d, i) => i * 10)
    .attr("y", d => y_histogram(d.count))
    .attr("height", d => height_histogram - y_histogram(d.count));

  // Filter tick values to show one in every 10, excluding index 0.
  const tickValues = x_histogram.domain().filter((d, i) => i % 10 === 0 && i !== 0);

  // Add the x-axis at the bottom with custom tick formatting.
  svg_histogram.append("g")
    .attr("class", "x-axis")
    .attr("transform", `translate(0, ${height_histogram})`)
    .call(
      d3.axisBottom(x_histogram)
        .tickValues(tickValues)
        .tickFormat(function(d) {
          const i = x_histogram.domain().indexOf(d);
          if (i === 10) return d.substring(0, 2);
          return d.substring(0, 3);
        })
    );

  // (Y-axis removed as per requirement)

  // Add an x-axis title.
  svg_histogram.append("text")
    .attr("class", "x-axis-title")
    .attr("x", width_histogram / 2)
    .attr("y", height_histogram + margin_histogram.bottom - 10)
    .attr("text-anchor", "middle")
    .text("Distance From Hole (Yards)");
}

// Displays the histogram in a vertical manner for mobile screen width
async function updateDistanceHistogramVertical(params) {
  const histRes = await fetch(`/api/distance_histogram?${params.toString()}`);
  const histData = await histRes.json();

  // Remove any existing SVG and tooltip.
  d3.select("#distanceHistogram").select("svg").remove();
  d3.selectAll(".tooltip").remove();

  // Prepare data: each bin has a label, count, and average strokes gained.
  const data_histogram = histData.bin_labels.map((label, i) => ({
    label: label,
    count: histData.bin_counts[i],
    avg_sg: histData.bin_avg_sg[i]
  }));

  console.log(data_histogram);

  const container = d3.select("#distanceHistogram");
  const containerWidth = container.node().clientWidth || 400;
  // Set a fixed height for the chart; adjust as needed.
  const margin = { top: 20, right: 20, bottom: 50, left: 30 };
  const width = containerWidth - margin.left - margin.right;
  const height = 600 - margin.top - margin.bottom;

  // Create the SVG container.
  const svg = container.append("svg")
    .attr("width", containerWidth)
    .attr("height", height + margin.top + margin.bottom)
    .attr("viewBox", `0 0 ${containerWidth} ${height + margin.top + margin.bottom}`)
    .attr("preserveAspectRatio", "xMidYMid meet")
    .append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

  // For horizontal bars:
  // x scale: linear scale for count values.
  const x = d3.scaleLinear()
    .domain([0, d3.max(data_histogram, d => d.count)])
    .nice()
    .range([0, width]);

  // y scale: band scale for bin labels.
  const y = d3.scaleBand()
    .domain(data_histogram.map(d => d.label))
    .range([0, height])
    .padding(0.1);

  // Non-linearity exponents (adjust these to change gradient steepness).
  const exponentGreen = 0.8;  // For avg SG values between 0 and 1.
  const exponentRed = 0.8;    // For avg SG values between 0 and -1.

  // Helper function to get the fill color using a non-linear transformation.
  function getBarColor(avg_sg) {
    if (avg_sg < 0) {
      let t = Math.min(Math.abs(avg_sg) / 1, 1);
      t = Math.pow(t, exponentRed);
      return d3.interpolateReds(t);
    } else {
      let t = Math.min(avg_sg / 1, 1);
      t = Math.pow(t, exponentGreen);
      return d3.interpolateGreens(t);
    }
  }

  // Helper function for a constant border color.
  function getBarBorderColor(avg_sg) {
    return avg_sg >= 0 ? d3.interpolateGreens(0.8) : d3.interpolateReds(0.8);
  }

  // Define tooltip.
  const tooltip = d3.select("body")
    .append("div")
    .attr("class", "tooltip")
    .style("position", "absolute")
    .style("padding", "6px")
    .style("background", "rgba(0, 0, 0, 0.6)")
    .style("color", "white")
    .style("border-radius", "4px")
    .style("pointer-events", "none")
    .style("opacity", 0);

  // Create horizontal bars.
  const bars = svg.selectAll(".bar")
    .data(data_histogram)
    .enter()
    .append("rect")
    .attr("class", "bar")
    // y position is based on the bin label.
    .attr("y", d => y(d.label))
    .attr("x", 0)
    .attr("height", y.bandwidth())
    // Start with zero width for transition.
    .attr("width", 0)
    .attr("fill", d => getBarColor(d.avg_sg))
    .attr("stroke", d => getBarBorderColor(d.avg_sg))
    .attr("stroke-width", 1)
    .on("mouseover", function(event, d) {
      tooltip.transition().duration(200).style("opacity", 0.9);
      tooltip.html(`<strong>${d.label}</strong>: ${d.count}<br/>Avg SG: ${d.avg_sg.toFixed(2)}`);
    })
    .on("mousemove", function(event, d) {
      tooltip.style("left", (event.pageX + 10) + "px")
             .style("top", (event.pageY - 28) + "px");
    })
    .on("mouseout", function(event, d) {
      tooltip.transition().duration(500).style("opacity", 0);
    });

  // Animate bar widths.
  bars.transition()
    .ease(d3.easeLinear)
    .duration(1000)
    .delay((d, i) => i * 10)
    .attr("width", d => x(d.count));

  // Add y-axis (bin labels) on the left.
  svg.append("g")
    .attr("class", "y-axis")
    .call(d3.axisLeft(y)
      // Customize tick formatting if needed.
      .tickValues(y.domain().filter((d, i) => i % 10 === 0 && i !== 0))
      .tickFormat(function(d) { 
        const i = y.domain().indexOf(d);
        if (i === 10) return d.substring(0,2);
        return d.substring(0, 3); })
    );

  // Add an x-axis title.
  svg.append("text")
    .attr("class", "x-axis-title")
    .attr("x", width / 2)
    .attr("y", height + margin.bottom - 10)
    .attr("text-anchor", "middle")
    .text("Count of Shots");
}

//────────────────────────────
// Responsive Histogram Selector
//────────────────────────────

async function updateDistanceHistogramResponsive(params) {
  if (window.innerWidth < 1000) {
    await updateDistanceHistogramVertical(params);
  } else {
    await updateDistanceHistogram(params);
  }
}

//────────────────────────────
// Main Dashboard Updater
//────────────────────────────

async function updateDashboard() {
  const params = new URLSearchParams({
    course: document.getElementById("course").value,
    round: document.getElementById("round").value,
    round_type: document.getElementById("round_type").value,
    startDate: document.getElementById("startDate").value,
    endDate: document.getElementById("endDate").value,
  });

  // 1) Overall Stats
  const statsData = await updateOverallStats(params);
  
  // 2) Strokes Gained Chart
  await updateStrokesGainedChart(params);
  
  // 3) Round Performance Chart
  await updateRoundPerformanceChart(params);
  
  // 4) Tee Stats
  await updateTeeStats(params, statsData);
  
  // 5) Approach Stats (including D3 miss chart and table update)
  await updateApproachStats(params, statsData);
  
  // 6) Short Game Stats (up/down, bunker, non-bunker)
  await updateShortGameStats(params, statsData);
  
  // 7) Putting Stats
  await updatePuttingStats(params, statsData);
  
  // 8) Distance Histogram (Responsive: vertical for small screens, horizontal for larger)
  await updateDistanceHistogramResponsive(params);



  // New SG charts for each shot type:
  await updateSgChart("offTeeSgBarChart", "/api/last50_offtee", "sg_off_tee");
  await updateSgChart("approachSgBarChart", "/api/last50_approach", "sg_approach");
  await updateSgChart("aroundGreenSgBarChart", "/api/last50_around_green", "sg_around_green");
  await updateSgChart("puttingSgBarChart", "/api/last50_putting", "sg_putting");
}
