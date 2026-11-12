shader_type canvas_item;
// Rubber conveyor belt with ribs scrolling along UV.x (UV.x in metres, UV.y across 0..1).
uniform float offset = 0.0;

void fragment() {
	float u = UV.x - offset;
	float f = fract(u * 4.0);
	float rib = smoothstep(0.30, 0.45, f) * (1.0 - smoothstep(0.55, 0.70, f));
	float edge = smoothstep(0.0, 0.12, UV.y) * smoothstep(1.0, 0.88, UV.y);
	float rail_hi = smoothstep(0.0, 0.05, UV.y) * (1.0 - smoothstep(0.05, 0.1, UV.y));
	vec3 rubber = vec3(0.035, 0.035, 0.04) + rib * 0.045;
	vec3 frame = vec3(0.30, 0.31, 0.32) + rail_hi * 0.25;
	vec3 col = mix(frame, rubber, edge);
	// rollers every metre visible through the frame
	float roller = smoothstep(0.92, 1.0, fract(UV.x)) * (1.0 - edge);
	col += roller * 0.08;
	COLOR = vec4(col, 1.0);
}
