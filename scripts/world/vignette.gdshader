shader_type canvas_item;
// Full-screen photographic grade: vignette + subtle grain + slight warm/cool split.
uniform float strength = 0.55;
uniform float grain = 0.025;
uniform sampler2D screen_tex : hint_screen_texture, filter_linear;

float hash(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }

void fragment() {
	vec3 c = texture(screen_tex, SCREEN_UV).rgb;
	vec2 d = SCREEN_UV - 0.5;
	float v = 1.0 - dot(d, d) * strength * 1.6;
	c *= clamp(v, 0.0, 1.0);
	float lum = dot(c, vec3(0.299, 0.587, 0.114));
	c = mix(c, c * vec3(1.03, 1.0, 0.95), smoothstep(0.3, 0.8, lum));
	c = mix(c, c * vec3(0.95, 0.99, 1.05), 1.0 - smoothstep(0.0, 0.35, lum));
	c += (hash(SCREEN_UV * 1000.0 + TIME) - 0.5) * grain;
	COLOR = vec4(c, 1.0);
}
