export function addPin(stationGroup, x, y, color, label) {
    const svg = d3.select(stationGroup.ownerSVGElement);
    
    const pinColors = {
        "start": "#4A90E2",
        "end": "#FF9500"
    };
    const pinColor = pinColors[color] || color;

    const pin = d3.select(stationGroup).append("g")
        .attr("class", "pin-marker")
        .attr("transform", `translate(${x},${y - 8})`);

    // 添加阴影效果
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

    // 添加脉冲动画
    const pulseAnimation = svg.append("defs")
        .append("radialGradient")
        .attr("id", `pulse-${label}`)
        .attr("r", "50%");

    pulseAnimation.append("animate")
        .attr("attributeName", "r")
        .attr("values", "0%;50%;0%")
        .attr("dur", "2s")
        .attr("repeatCount", "indefinite");

    // 创建底部小圆点和白色圆环
    const bottomGroup = pin.append("g")
        .attr("transform", "translate(0, 5)");

    bottomGroup.append("circle")  // 白色外圈
        .attr("r", 15)
        .attr("fill", "white");

    bottomGroup.append("circle")  // 彩色内圈
        .attr("r", 8)
        .attr("fill", pinColor);

    // 添加脉冲效果
    bottomGroup.append("circle")
        .attr("r", 8)
        .attr("fill", `url(#pulse-${label})`)
        .style("opacity", 0.5);

    // 创建主体形状
    const mainShape = pin.append("path")
        .attr("d", "M0-25c-7 0-12.5 5.5-12.5 12.5 0 8.25 12.5 25 12.5 25s12.5-16.75 12.5-25c0-7-5.5-12.5-12.5-12.5z")
        .attr("fill", pinColor)
        .attr("transform", "scale(1.65) translate(0, -15)");

    // 创建白色圆形背景
    const whiteBg = pin.append("circle")
        .attr("cx", 0)
        .attr("cy", -42)
        .attr("r", 17)
        .attr("fill", "white");

    // 添加文字标签
    const text = pin.append("text")
        .attr("text-anchor", "middle")
        .attr("dy", "-1.8em")
        .attr("fill", "#000000")
        .attr("font-weight", "bold")
        .attr("font-size", "20px")
        .text(label);

    pin.attr("filter", `url(#${filterId})`);

    // 添加悬停效果
    pin.on("mouseover", function() {
        mainShape.transition().duration(200).attr("transform", "scale(1.75) translate(0, -14)");
        whiteBg.transition().duration(200).attr("r", 18);
        text.transition().duration(200).attr("font-size", "21px");
    }).on("mouseout", function() {
        mainShape.transition().duration(200).attr("transform", "scale(1.65) translate(0, -15)");
        whiteBg.transition().duration(200).attr("r", 17);
        text.transition().duration(200).attr("font-size", "20px");
    });

    // 添加点击波纹效果
    function addClickRipple(x, y) {
        const ripple = pin.append("circle")
            .attr("cx", x)
            .attr("cy", y)
            .attr("r", 0)
            .style("fill", "none")
            .style("stroke", pinColor)
            .style("stroke-opacity", 1)
            .style("stroke-width", 3);

        ripple.transition()
            .duration(1000)
            .attr("r", 50)
            .style("stroke-opacity", 0)
            .remove();
    }

    // 添加点击事件监听器
    pin.on("click", function(event) {
        const [x, y] = d3.pointer(event);
        addClickRipple(x, y);
        
        // 添加缩放动画
        mainShape.transition()
            .duration(200)
            .attr("transform", "scale(1.8) translate(0, -14)")
            .transition()
            .duration(200)
            .attr("transform", "scale(1.65) translate(0, -15)");
        
        whiteBg.transition()
            .duration(200)
            .attr("r", 19)
            .transition()
            .duration(200)
            .attr("r", 17);
        
        text.transition()
            .duration(200)
            .attr("font-size", "22px")
            .transition()
            .duration(200)
            .attr("font-size", "20px");
    });

    svg.node().appendChild(pin.node());
}