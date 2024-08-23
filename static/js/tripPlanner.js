export function addPin(stationGroup, x, y, color, label) {
    const svg = d3.select(stationGroup.ownerSVGElement);
    
    // 定義漸變
    const gradient = svg.append("defs")
        .append("radialGradient")
        .attr("id", `pinGradient-${label}`)
        .attr("cx", "30%")
        .attr("cy", "30%");

    gradient.append("stop")
        .attr("offset", "0%")
        .attr("stop-color", d3.rgb(color).brighter(1));

    gradient.append("stop")
        .attr("offset", "130%")
        .attr("stop-color", d3.rgb(color).darker(1));

    // 定義陰影濾鏡
    const filter = svg.append("defs")
        .append("filter")
        .attr("id", `drop-shadow-${label}`)
        .attr("height", "130%");

    filter.append("feGaussianBlur")
        .attr("in", "SourceAlpha")
        .attr("stdDeviation", 3)
        .attr("result", "blur");

    filter.append("feOffset")
        .attr("in", "blur")
        .attr("dx", 2)
        .attr("dy", 2)
        .attr("result", "offsetBlur");

    const feMerge = filter.append("feMerge");
    feMerge.append("feMergeNode")
        .attr("in", "offsetBlur");
    feMerge.append("feMergeNode")
        .attr("in", "SourceGraphic");

    const pin = d3.select(stationGroup).append("g")
        .attr("class", "pin-marker")
        .attr("transform", `translate(${x},${y})`);

    pin.append("circle")
        .attr("r", 0)
        .attr("fill", `url(#pinGradient-${label})`)
        .attr("filter", `url(#drop-shadow-${label})`)
        .transition()
        .duration(300)
        .attr("r", 20);

    pin.append("text")
        .attr("text-anchor", "middle")
        .attr("dy", ".3em")
        .attr("fill", "white")
        .attr("font-weight", "bold")
        .attr("font-size", "18px")
        .text(label);

    // 添加脈衝動畫
    pin.append("circle")
        .attr("r", 25)  // 初始半徑與主圓一致
        .attr("fill", "none")
        .attr("stroke", color)
        .attr("stroke-width", 3)  // 稍微增加線寬
        .attr("opacity", 1)
        .transition()
        .duration(1500)
        .attr("r", 40)  // 最終半徑從25增加到40
        .attr("opacity", 0)
        .on("end", function() { d3.select(this).remove(); });
}

