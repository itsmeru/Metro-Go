export function addPin(stationGroup, x, y, color, label) {
    
    const svg = d3.select(stationGroup.ownerSVGElement);
    
    const pinColors = {
        "起": "#2563eb",
        "迄": "rgb(206, 0, 0)"
    };
    
    const pinColor = pinColors[label] || color;

    const pin = d3.select(stationGroup).append("g")
        .attr("class", "pin-marker")
        .attr("transform", `translate(${x+1.7},${y - 3})`);

    const filterId = `drop-shadow-${label.replace(/\s+/g, '-')}`;
    const filter = svg.append("defs")
        .append("filter")
        .attr("id", filterId)
        .attr("height", "140%");

    filter.append("feGaussianBlur")
        .attr("in", "SourceAlpha")
        .attr("stdDeviation", 2)
        .attr("result", "blur");
    filter.append("feOffset")
        .attr("in", "blur")
        .attr("dx", 1)
        .attr("dy", 2)
        .attr("result", "offsetBlur");
    const feMerge = filter.append("feMerge");
    feMerge.append("feMergeNode").attr("in", "offsetBlur");
    feMerge.append("feMergeNode").attr("in", "SourceGraphic");

    
    
    const pulseAnimation = svg.append("defs")
        .append("radialGradient")
        .attr("id", `pulse-${label}`)
        .attr("r", "60%");

    pulseAnimation.append("animate")
        .attr("attributeName", "r")
        .attr("values", "0%;50%;0%")
        .attr("dur", "2s")
        .attr("repeatCount", "indefinite");

    const bottomGroup = pin.append("g")
        .attr("transform", "translate(0, 5)");


    bottomGroup.append("circle")  // 内圈
        .attr("r", 7)
        .attr("fill", pinColor  )


 
    const mainShape = pin.append("path")
        .attr("d", "M0-25c-7 0-12.5 5.5-12.5 12.5 0 8.25 12.5 25 12.5 25s12.5-16.75 12.5-25c0-7-5.5-12.5-12.5-12.5z")
        .attr("fill",  pinColor  )
        .attr("transform", "scale(2.3) translate(0, -12)");

    // 白色背景
    const whiteBg = pin.append("circle")
        .attr("cx", 0)
        .attr("cy", -55)
        .attr("r", 22)
        .attr("fill", "white");

    const text = pin.append("text")
        .attr("text-anchor", "middle")
        .attr("dy", "-1.85em")
        .attr("fill",  pinColor  )
        .attr("font-weight", "bold")
        .attr("font-size", "26px")
        .text(label);
        

    pin.attr("filter", `url(#${filterId})`);

   

    svg.node().appendChild(pin.node());
}