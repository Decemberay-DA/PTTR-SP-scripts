float PerlinNoise(float value, float frequency, int octaves, int seed)
{
    float noiseSum = 0.0;
    float amplitude = 0.5;
    for (int octave = 0; octave < octaves - 1; octave++)
    {
        float v = value * frequency + float(seed) * 12.468;

        float noise_a = 0.0;
        {
            int n = int(v) + seed * 137;
            n = n << 13 ^ n;
            noise_a = (1.0 - ((n * (n * n * 15731 + 789221) + 1376312589) & 0x7fffffff) / 1073741824.0);
        }
        float noise_b = 0.0;
        {
            int n = int(v) + 1 + seed * 137;
            n = n << 13 ^ n;
            noise_a = (1.0 - ((n * (n * n * 15731 + 789221) + 1376312589) & 0x7fffffff) / 1073741824.0);
        }
        float a = noise_a;
        float b = noise_b;
        float fade = v - floor(v);
        float t = fade * fade * fade * (fade * (fade * 6 - 15) + 10);;
        noiseSum += lerp(a, b, t) * amplitude;
        frequency *= 2;
        amplitude *= 0.5;
    }
    return noiseSum;
}

result = float3(
    PerlinNoise(-value, frequency, octaves, seed),
    PerlinNoise(value + 465.321, frequency, octaves, seed),
    PerlinNoise(value, frequency, octaves, seed),
);
